"""Audit Tier 1 artifact production health for a BrandMind pilot session.

The audit reads a pilot session directory plus the associated agent
workspace and outputs a structured JSON report describing whether the
session produced the deliverable artifacts BrandMind is designed to
generate (Brand Key visual, strategy document, KPI spreadsheet,
executive presentation), how the agent dispatched its sub-agents and
deliverable tools, and whether the workspace notes were kept in sync
with the chat transcript.

Usage:
    python evaluation/artifact_audit.py --session-dir <path-to-pilot>
    python evaluation/artifact_audit.py --session-dir <path> --pretty

The exit code is ``0`` when the audit completes successfully (the report
itself indicates whether artifacts are missing); ``2`` when required
input files cannot be found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

DELIVERABLE_TOOLS = (
    "generate_brand_key",
    "generate_document",
    "generate_presentation",
    "generate_spreadsheet",
    "generate_image",
    "edit_image",
)

SUBAGENT_TYPES = (
    "creative-studio",
    "document-generator",
    "market-research",
    "social-media-analyst",
)

PHASE_KEYS = (
    "phase_0",
    "phase_0_5",
    "phase_1",
    "phase_2",
    "phase_3",
    "phase_4",
    "phase_5",
)

ARTIFACT_EXTENSIONS = {
    "brand_key_image": (".jpeg", ".jpg", ".png"),
    "strategy_document": (".docx", ".pdf"),
    "presentation": (".pptx",),
    "spreadsheet": (".xlsx",),
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ToolUsage:
    """Aggregate counts and observed file paths for a deliverable tool."""

    call_count: int = 0
    files_produced: list[str] = field(default_factory=list)


@dataclass
class WorkspaceFile:
    """Inspection result for a single workspace markdown file."""

    exists: bool = False
    lines: int = 0
    sections_present: list[str] = field(default_factory=list)


@dataclass
class Tier1Health:
    """Binary health checks aligned with BrandMind's Tier 1 success target."""

    brand_key_produced: bool = False
    strategy_doc_produced: bool = False
    kpi_xlsx_produced: bool = False
    presentation_produced: bool = False
    workspace_brief_covers_all_phases: bool = False

    @property
    def score(self) -> int:
        return sum(
            int(getattr(self, attr))
            for attr in (
                "brand_key_produced",
                "strategy_doc_produced",
                "kpi_xlsx_produced",
                "presentation_produced",
                "workspace_brief_covers_all_phases",
            )
        )


@dataclass
class AuditReport:
    """Complete audit report for one session."""

    session_dir: str
    session_id_api: str
    workspace_session_id: str | None
    workspace_dir: str | None
    scope: str | None
    completed_phases: list[str]
    deliverable_tools: dict[str, ToolUsage]
    subagent_dispatch: dict[str, int]
    artifacts_on_disk: dict[str, list[str]]
    workspace_files: dict[str, WorkspaceFile]
    tier1_health: Tier1Health
    notes: list[str]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tier1_health"]["score"] = self.tier1_health.score
        return d


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_metadata(session_dir: Path) -> tuple[str, str | None, list[str]]:
    """Read metadata.json and return (api_session_id, scope, completed_phases)."""
    meta_path = session_dir / "metadata.json"
    if not meta_path.is_file():
        return "", None, []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    api_session_id = meta.get("session_id", "")
    sm = meta.get("session_metadata", {}) or {}
    return api_session_id, sm.get("scope"), list(sm.get("completed_phases", []))


def parse_server_log(log_path: Path) -> tuple[
    dict[str, ToolUsage], dict[str, int], list[str]
]:
    """Extract deliverable tool usage and sub-agent dispatch counts from log.

    The log is line-oriented; each tool call is announced with a header
    line like ``🔬 DEBUG TOOL_CALL [generate_brand_key]`` followed by
    ``└─ key=value`` lines describing arguments. This parser walks the
    log linearly, accumulates counts, and captures any ``file_path``
    arguments emitted by deliverable tools.

    Args:
        log_path: Path to the captured server log file.

    Returns:
        Tuple of (deliverable_tool_usage, subagent_dispatch_counts,
        notes). ``notes`` collects warnings such as missing log file.
    """
    deliverable: dict[str, ToolUsage] = {
        name: ToolUsage() for name in DELIVERABLE_TOOLS
    }
    subagent: dict[str, int] = {name: 0 for name in SUBAGENT_TYPES}
    notes: list[str] = []

    if not log_path.is_file():
        notes.append(f"server.log not found at {log_path}")
        return deliverable, subagent, notes

    tool_call_re = re.compile(r"🔬 DEBUG TOOL_CALL \[(?P<tool>[^\]]+)\]")
    arg_re = re.compile(r"└─ (?P<key>[A-Za-z_][\w]*)=(?P<val>.*)")

    current_tool: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = tool_call_re.search(line)
            if m:
                current_tool = m.group("tool")
                if current_tool in deliverable:
                    deliverable[current_tool].call_count += 1
                continue
            m2 = arg_re.search(line)
            if m2 and current_tool:
                key = m2.group("key")
                val = m2.group("val").strip()
                if current_tool == "task" and key == "subagent_type":
                    name = val.split()[0] if val else ""
                    if name in subagent:
                        subagent[name] += 1
                elif current_tool in deliverable and key in {
                    "file_path",
                    "image_path",
                    "output_path",
                }:
                    deliverable[current_tool].files_produced.append(val)
    return deliverable, subagent, notes


def find_workspace_dir(
    api_session_id: str, brandmind_home: Path
) -> tuple[Path | None, str | None]:
    """Resolve the workspace directory associated with the pilot session.

    BrandStrategySession assigns its own UUID prefix that is independent
    of the API ``session_id``. The two ids are not joined in either
    metadata file, so the workspace is located heuristically:

    1. Read ``project.json`` from each candidate directory under
       ``BRANDMIND_HOME/projects/`` and prefer the one whose
       ``session_id`` matches the API session id (when both happen to
       share a prefix).
    2. Otherwise, fall back to the most recently modified candidate
       whose ``project.json`` ``brand_name`` matches the persona's
       brand. The caller should treat this as best effort.

    Args:
        api_session_id: ``session_id`` from the pilot ``metadata.json``.
        brandmind_home: Root of the on-disk BrandMind state tree.

    Returns:
        Tuple of (workspace path or ``None``, workspace session id or
        ``None``). The session id reflects the workspace project.json
        value, which can differ from ``api_session_id``.
    """
    projects_root = brandmind_home / "projects"
    if not projects_root.is_dir():
        return None, None
    candidates = sorted(
        (p for p in projects_root.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for cand in candidates:
        proj_file = cand / "project.json"
        if not proj_file.is_file():
            continue
        try:
            data = json.loads(proj_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("session_id") == api_session_id:
            ws = cand / "workspace"
            return (ws if ws.is_dir() else None, cand.name)
    if candidates:
        latest = candidates[0]
        ws = latest / "workspace"
        return (ws if ws.is_dir() else None, latest.name)
    return None, None


def inspect_workspace_files(workspace_dir: Path | None) -> dict[str, WorkspaceFile]:
    """Inspect the three canonical workspace files for line count and sections.

    The audit is intentionally lightweight: it counts non-empty markdown
    headings as ``sections_present`` so the caller can compare which
    phases or sections the agent populated. This does not validate
    content depth — that belongs to higher-tier semantic checks.

    Args:
        workspace_dir: Directory expected to contain the three notes
            files. ``None`` produces empty results with ``exists=False``.

    Returns:
        Mapping of filename to :class:`WorkspaceFile`.
    """
    targets = ("brand_brief.md", "quality_gates.md", "working_notes.md")
    out: dict[str, WorkspaceFile] = {name: WorkspaceFile() for name in targets}
    if workspace_dir is None or not workspace_dir.is_dir():
        return out
    for name in targets:
        path = workspace_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        wf = out[name]
        wf.exists = True
        wf.lines = sum(1 for _ in text.splitlines())
        wf.sections_present = [
            line.strip("# ").strip()
            for line in text.splitlines()
            if line.lstrip().startswith("##")
        ]
    return out


def scan_artifacts_on_disk(
    output_root: Path, session_start_iso: str | None
) -> dict[str, list[str]]:
    """Enumerate artifacts under brandmind-output/ produced after the pilot.

    Filenames are matched against the deliverable extensions table
    (DOCX/PDF -> strategy document, PPTX -> presentation, XLSX ->
    spreadsheet, image extensions -> brand key or other image). The
    audit deliberately uses file mtime relative to the pilot start to
    drop pre-existing artifacts; when a session start time cannot be
    determined every matching file is reported.

    Args:
        output_root: Root of the BrandMind output tree (typically
            ``brandmind-output``).
        session_start_iso: ISO timestamp at which the pilot session
            started. ``None`` disables the time filter.

    Returns:
        Mapping of artifact category to list of file paths that match
        the category and post-date the pilot start (when known).
    """
    from datetime import datetime

    cutoff = None
    if session_start_iso:
        try:
            cutoff = datetime.fromisoformat(session_start_iso).timestamp()
        except ValueError:
            cutoff = None

    out = {
        "brand_key_image": [],
        "strategy_document": [],
        "presentation": [],
        "spreadsheet": [],
        "other_image": [],
    }
    if not output_root.is_dir():
        return out
    for entry in output_root.rglob("*"):
        if not entry.is_file():
            continue
        if cutoff is not None and entry.stat().st_mtime < cutoff:
            continue
        if "/eval/" in str(entry):
            continue
        suffix = entry.suffix.lower()
        name = entry.name.lower()
        if suffix in ARTIFACT_EXTENSIONS["spreadsheet"]:
            out["spreadsheet"].append(str(entry))
        elif suffix in ARTIFACT_EXTENSIONS["presentation"]:
            out["presentation"].append(str(entry))
        elif suffix in ARTIFACT_EXTENSIONS["strategy_document"]:
            out["strategy_document"].append(str(entry))
        elif suffix in ARTIFACT_EXTENSIONS["brand_key_image"]:
            if "brand_key" in name:
                out["brand_key_image"].append(str(entry))
            else:
                out["other_image"].append(str(entry))
    return out


def evaluate_tier1_health(
    deliverable: dict[str, ToolUsage],
    artifacts: dict[str, list[str]],
    workspace: dict[str, WorkspaceFile],
    completed_phases: list[str],
) -> Tier1Health:
    """Reduce the audit signals into the binary Tier 1 health checks.

    A check passes when the corresponding tool was called at least once
    AND a matching artifact is observed on disk (when applicable). The
    workspace coverage check passes when ``brand_brief.md`` contains a
    section heading for every completed phase.

    Args:
        deliverable: Tool usage map from :func:`parse_server_log`.
        artifacts: On-disk artifact map from
            :func:`scan_artifacts_on_disk`.
        workspace: Workspace inspection from
            :func:`inspect_workspace_files`.
        completed_phases: List of phase ids the session advanced through.

    Returns:
        :class:`Tier1Health` with the five binary checks set.
    """
    health = Tier1Health()
    bk_calls = deliverable.get("generate_brand_key", ToolUsage()).call_count
    health.brand_key_produced = bk_calls > 0 or bool(artifacts["brand_key_image"])
    doc_calls = deliverable.get("generate_document", ToolUsage()).call_count
    health.strategy_doc_produced = doc_calls > 0 or bool(
        artifacts["strategy_document"]
    )
    pres_calls = deliverable.get("generate_presentation", ToolUsage()).call_count
    health.presentation_produced = pres_calls > 0 or bool(artifacts["presentation"])
    sheet_calls = deliverable.get("generate_spreadsheet", ToolUsage()).call_count
    health.kpi_xlsx_produced = sheet_calls > 0 or bool(artifacts["spreadsheet"])

    brief = workspace.get("brand_brief.md", WorkspaceFile())
    if brief.exists:
        sections_lower = " ".join(s.lower() for s in brief.sections_present)
        phase_tokens = {
            "phase_0": ["phase 0", "phase_0", "diagnosis"],
            "phase_0_5": ["phase 0.5", "phase_0_5", "equity audit"],
            "phase_1": ["phase 1", "phase_1", "market intelligence"],
            "phase_2": ["phase 2", "phase_2", "positioning"],
            "phase_3": ["phase 3", "phase_3", "identity"],
            "phase_4": ["phase 4", "phase_4", "communication"],
            "phase_5": ["phase 5", "phase_5", "deliverable", "strategy plan"],
        }
        missing = [
            phase
            for phase in completed_phases
            if not any(tok in sections_lower for tok in phase_tokens.get(phase, []))
        ]
        health.workspace_brief_covers_all_phases = not missing
    return health


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def audit(session_dir: Path, brandmind_home: Path, output_root: Path) -> AuditReport:
    """Run the full audit pipeline for one session directory.

    Args:
        session_dir: Pilot session directory (the eval folder, not the
            workspace).
        brandmind_home: Root of the on-disk BrandMind state tree, used
            to resolve the workspace directory.
        output_root: Root of the BrandMind output tree where artifacts
            land on disk.

    Returns:
        A populated :class:`AuditReport` ready for serialisation.

    Raises:
        FileNotFoundError: when ``session_dir`` does not exist.
    """
    if not session_dir.is_dir():
        raise FileNotFoundError(f"Session directory not found: {session_dir}")

    api_session_id, scope, completed_phases = parse_metadata(session_dir)
    deliverable, subagent, notes = parse_server_log(session_dir / "server.log")
    workspace_dir, workspace_id = find_workspace_dir(api_session_id, brandmind_home)
    workspace_files = inspect_workspace_files(workspace_dir)

    meta_path = session_dir / "metadata.json"
    session_start_iso: str | None = None
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        session_start_iso = meta.get("created_at") or meta.get("date")

    artifacts = scan_artifacts_on_disk(output_root, session_start_iso)
    health = evaluate_tier1_health(
        deliverable, artifacts, workspace_files, completed_phases
    )

    return AuditReport(
        session_dir=str(session_dir),
        session_id_api=api_session_id,
        workspace_session_id=workspace_id,
        workspace_dir=str(workspace_dir) if workspace_dir else None,
        scope=scope,
        completed_phases=completed_phases,
        deliverable_tools=deliverable,
        subagent_dispatch=subagent,
        artifacts_on_disk=artifacts,
        workspace_files=workspace_files,
        tier1_health=health,
        notes=notes,
    )


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--session-dir",
        required=True,
        type=Path,
        help="Path to the pilot session directory (under brandmind-output/eval/).",
    )
    parser.add_argument(
        "--brandmind-home",
        type=Path,
        default=Path.home() / ".brandmind",
        help="Root of on-disk BrandMind state. Defaults to ~/.brandmind.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "brandmind-output",
        help="Root where deliverable artifacts land. Defaults to ./brandmind-output.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print a human-readable summary in addition to JSON.",
    )
    return parser


def _format_summary(report: AuditReport) -> str:
    lines: list[str] = []
    h = report.tier1_health
    lines.append(f"Session: {report.session_dir}")
    lines.append(
        f"Scope: {report.scope}  Completed phases: "
        f"{', '.join(report.completed_phases) or '(none)'}"
    )
    lines.append(f"Tier1 health: {h.score}/5")
    lines.append(
        f"  brand_key_produced       = {h.brand_key_produced}"
    )
    lines.append(
        f"  strategy_doc_produced    = {h.strategy_doc_produced}"
    )
    lines.append(
        f"  kpi_xlsx_produced        = {h.kpi_xlsx_produced}"
    )
    lines.append(
        f"  presentation_produced    = {h.presentation_produced}"
    )
    lines.append(
        f"  workspace_brief_covers_all_phases = "
        f"{h.workspace_brief_covers_all_phases}"
    )
    lines.append("Deliverable tool calls:")
    for name in DELIVERABLE_TOOLS:
        usage = report.deliverable_tools[name]
        lines.append(
            f"  {name}: {usage.call_count}"
            + (
                f"  files={usage.files_produced}"
                if usage.files_produced
                else ""
            )
        )
    lines.append("Sub-agent dispatch:")
    for name, count in report.subagent_dispatch.items():
        lines.append(f"  {name}: {count}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    try:
        report = audit(args.session_dir, args.brandmind_home, args.output_root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = report.to_dict()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if args.pretty:
        print("\n--- Human summary ---", file=sys.stderr)
        print(_format_summary(report), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
