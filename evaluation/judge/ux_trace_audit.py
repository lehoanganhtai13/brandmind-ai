"""Deterministic UX reliability audit for BrandMind pilot traces.

This audit is intentionally mechanical. It does not judge strategy quality;
it turns product-surface failures into counted signals that can be used as
regression gates before running expensive persona suites.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "scratchpad_edit_debug",
        re.compile(
            r"\b(Wait! Look at line|old_string|new_string|String to replace)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "raw_tool_or_todo_payload",
        re.compile(
            r"(├─\s*\{|\bTool\s+\w+\s+response\b|Executing\s+\w+|"
            r'"\s*todos\s*"\s*:\s*\[|\btool_name\b)',
            re.IGNORECASE,
        ),
    ),
    (
        "internal_tool_name",
        re.compile(
            r"\b(report_progress|task\(|list_artifacts|write_todos|"
            r"read_file|edit_file|tool_calls?)\b",
            re.IGNORECASE,
        ),
    ),
)

SURFACE_EXPOSURE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "local_or_workspace_path",
        re.compile(r"(/Users/|/workspace/|\.brandmind/|brandmind-output/)"),
    ),
)

TRUNCATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Target\s*=\s*35%\s+by\s+M\b", re.IGNORECASE),
    re.compile(r"\bby\s+M\s*$", re.IGNORECASE),
)

TOOL_CALL_RE = re.compile(
    r"DEBUG TOOL_CALL \[(?P<tool>[^\]]+)\](?:.*)$",
)
SUBAGENT_RE = re.compile(r"subagent_type=(?P<subagent>[\w-]+)")


@dataclass(frozen=True)
class TurnUxAudit:
    """Per-turn UX reliability signals."""

    turn: int
    elapsed_seconds: float
    assistant_chars: int
    tool_count: int
    repeated_tool_counts: dict[str, int]
    subagent_counts: dict[str, int]
    leak_flags: dict[str, int]
    surface_exposure_flags: dict[str, int]
    suspected_truncation: bool
    long_latency: bool
    very_long_latency: bool
    progress_event_count: int
    assumed_silent_gap_over_90s: bool


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_turns(transcript_path: Path) -> list[dict[str, Any]]:
    data = _read_json(transcript_path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("turns"), list):
        return data["turns"]
    raise ValueError(f"Unsupported transcript schema: {transcript_path}")


def _assistant_text(turn: dict[str, Any]) -> str:
    value = turn.get("agent", turn.get("assistant_response", turn.get("assistant", "")))
    return value if isinstance(value, str) else ""


def _metadata_turns(metadata_path: Path) -> list[dict[str, Any]]:
    data = _read_json(metadata_path)
    turns = data.get("turn_stats")
    if not isinstance(turns, list):
        raise ValueError(f"Unsupported metadata schema: {metadata_path}")
    return turns


def _tool_name(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("name") or value.get("tool_name") or "")
    return str(value)


def _count_leaks(text: str) -> dict[str, int]:
    return {
        name: len(pattern.findall(text))
        for name, pattern in LEAK_PATTERNS
        if pattern.findall(text)
    }


def _count_surface_exposures(text: str) -> dict[str, int]:
    return {
        name: len(pattern.findall(text))
        for name, pattern in SURFACE_EXPOSURE_PATTERNS
        if pattern.findall(text)
    }


def _is_suspected_truncation(text: str) -> bool:
    stripped = text.rstrip()
    return any(pattern.search(stripped) for pattern in TRUNCATION_PATTERNS)


def _server_log_subagent_sequence(server_log_path: Path) -> list[str | None]:
    """Return sub-agent labels aligned to task tool calls where possible."""

    if not server_log_path.is_file():
        return []

    pending_task_indexes: deque[int] = deque()
    task_subagents: list[str | None] = []

    for line in server_log_path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        tool_match = TOOL_CALL_RE.search(line)
        if tool_match:
            if tool_match.group("tool") == "task":
                task_subagents.append(None)
                pending_task_indexes.append(len(task_subagents) - 1)
            continue

        subagent_match = SUBAGENT_RE.search(line)
        if subagent_match and pending_task_indexes:
            task_subagents[pending_task_indexes.popleft()] = subagent_match.group(
                "subagent"
            )

    return task_subagents


def _assign_subagents_to_turns(
    metadata_turns: list[dict[str, Any]],
    server_log_path: Path,
) -> list[dict[str, int]]:
    """Best-effort alignment of task-call sub-agent types to metadata turns."""

    task_subagents = deque(_server_log_subagent_sequence(server_log_path))
    per_turn: list[dict[str, int]] = []

    for turn in metadata_turns:
        counts: Counter[str] = Counter()
        tools = [_tool_name(tool) for tool in turn.get("tools_used", []) or []]
        for tool in tools:
            if tool != "task":
                continue
            subagent = task_subagents.popleft() if task_subagents else None
            counts[subagent or "unknown"] += 1
        per_turn.append(dict(counts))

    return per_turn


def audit_run(eval_dir: Path) -> dict[str, Any]:
    """Audit one ``eval_run`` directory."""

    transcript_path = eval_dir / "transcript.json"
    metadata_path = eval_dir / "metadata.json"
    server_log_path = eval_dir / "server.log"

    transcript_turns = _load_turns(transcript_path)
    metadata_turns = _metadata_turns(metadata_path)
    subagents_by_turn = _assign_subagents_to_turns(metadata_turns, server_log_path)

    audits: list[TurnUxAudit] = []
    for index, metadata_turn in enumerate(metadata_turns):
        transcript_turn = (
            transcript_turns[index] if index < len(transcript_turns) else {}
        )
        text = _assistant_text(transcript_turn)
        tools = [_tool_name(tool) for tool in metadata_turn.get("tools_used", []) or []]
        repeated_tools = {
            tool: count for tool, count in Counter(tools).items() if count >= 3
        }
        elapsed = float(metadata_turn.get("elapsed_seconds") or 0.0)
        progress_count = 0
        audits.append(
            TurnUxAudit(
                turn=int(metadata_turn.get("turn") or index + 1),
                elapsed_seconds=elapsed,
                assistant_chars=len(text),
                tool_count=len(tools),
                repeated_tool_counts=repeated_tools,
                subagent_counts=subagents_by_turn[index]
                if index < len(subagents_by_turn)
                else {},
                leak_flags=_count_leaks(text),
                surface_exposure_flags=_count_surface_exposures(text),
                suspected_truncation=_is_suspected_truncation(text),
                long_latency=elapsed > 120,
                very_long_latency=elapsed > 240,
                progress_event_count=progress_count,
                assumed_silent_gap_over_90s=elapsed > 90 and progress_count == 0,
            )
        )

    latencies = [audit.elapsed_seconds for audit in audits]
    leak_turns = [audit.turn for audit in audits if audit.leak_flags]
    truncation_turns = [audit.turn for audit in audits if audit.suspected_truncation]
    very_long_turns = [audit.turn for audit in audits if audit.very_long_latency]
    silent_turns = [audit.turn for audit in audits if audit.assumed_silent_gap_over_90s]

    totals: Counter[str] = Counter()
    for audit in audits:
        totals.update({f"leak.{key}": value for key, value in audit.leak_flags.items()})
        totals.update(
            {
                f"surface.{key}": value
                for key, value in audit.surface_exposure_flags.items()
            }
        )
        totals.update(
            {f"subagent.{key}": value for key, value in audit.subagent_counts.items()}
        )
        totals["tool_calls"] += audit.tool_count
        totals["progress_events"] += audit.progress_event_count

    return {
        "eval_dir": str(eval_dir),
        "summary": {
            "turn_count": len(audits),
            "mean_elapsed_seconds": round(mean(latencies), 1) if latencies else 0.0,
            "max_elapsed_seconds": max(latencies, default=0.0),
            "turns_over_120s": [audit.turn for audit in audits if audit.long_latency],
            "turns_over_240s": very_long_turns,
            "leak_turns": leak_turns,
            "suspected_truncation_turns": truncation_turns,
            "assumed_silent_gap_over_90s_turns": silent_turns,
            "totals": dict(totals),
        },
        "turns": [asdict(audit) for audit in audits],
    }


def audit_suite(suite_root: Path) -> dict[str, Any]:
    """Audit all persona ``eval_run`` directories below a suite root."""

    runs = []
    for metadata_path in sorted(suite_root.glob("*/eval_run/metadata.json")):
        eval_dir = metadata_path.parent
        if any("failed" in part for part in eval_dir.parts):
            continue
        runs.append(audit_run(eval_dir))

    all_turns = [turn for run in runs for turn in run["turns"]]
    return {
        "suite_root": str(suite_root),
        "run_count": len(runs),
        "summary": {
            "max_elapsed_seconds": max(
                (turn["elapsed_seconds"] for turn in all_turns),
                default=0.0,
            ),
            "very_long_turn_count": sum(
                1 for turn in all_turns if turn["very_long_latency"]
            ),
            "leak_turn_count": sum(1 for turn in all_turns if turn["leak_flags"]),
            "suspected_truncation_count": sum(
                1 for turn in all_turns if turn["suspected_truncation"]
            ),
            "assumed_silent_gap_over_90s_count": sum(
                1 for turn in all_turns if turn["assumed_silent_gap_over_90s"]
            ),
        },
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Path to an eval_run directory or a suite root containing */eval_run.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    path = args.path
    result = (
        audit_run(path) if (path / "metadata.json").is_file() else audit_suite(path)
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
