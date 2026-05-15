"""Deterministic chat-process audit for BrandMind pilot transcripts.

The audit complements LLM chat judges by surfacing measurable hygiene signals
that repeatedly drag chat scores: unsupported factual language, invented
metrics, excessive response length, repetition, and internal workflow leakage.
It is diagnostic only; it does not replace the scored judge rubric.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("research_claim", re.compile(r"\b(research shows|studies show)\b", re.I)),
    (
        "vietnamese_research_claim",
        re.compile(r"\b(nghiên cứu|khoa học chứng minh)\b", re.I),
    ),
    ("data_claim", re.compile(r"\b(data shows|market data|dữ liệu|thống kê)\b", re.I)),
    ("trend_claim", re.compile(r"\b(trend|xu hướng|Gen Z|millennial)\b", re.I)),
    (
        "authority_upgrade",
        re.compile(r"\b(Michelin|award[- ]winning|top[- ]tier)\b", re.I),
    ),
    (
        "precise_metric",
        re.compile(r"(?<!\w)(?:\d+(?:[.,]\d+)?\s?%|\d+\s?(?:x|k|K|M|m|triệu|tỷ))"),
    ),
    (
        "science_claim",
        re.compile(r"\b(oxytocin|cortisol|dopamine|psychology|tâm lý học)\b", re.I),
    ),
)

PROVENANCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(based on what you shared|based on your input)\b", re.I),
    re.compile(
        r"\b(dựa trên|từ dữ liệu bạn đưa|từ thông tin bạn chia sẻ)\b",
        re.I,
    ),
    re.compile(r"\b(giả thuyết|tạm xem|cần kiểm chứng|nếu đúng)\b", re.I),
    re.compile(
        r"\b(according to|theo Keller|theo Kotler|theo Sharp|theo Cialdini)\b",
        re.I,
    ),
    re.compile(r"\b(theo nguồn|nguồn|trích từ|chapter|chương)\b", re.I),
)

CAVEAT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(assumption|hypothesis|verify|validate|example)\b", re.I),
    re.compile(
        r"\b(giả thuyết|kiểm chứng|xác minh|ví dụ|chưa có dữ liệu)\b",
        re.I,
    ),
    re.compile(r"\b(tìm dữ liệu|cần dữ liệu|without data|no data yet)\b", re.I),
)

INTERNAL_LANGUAGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "phase_id",
        re.compile(r"\bPhase\s+\d(?:\.\d)?\b|\bphase_\d(?:_\d)?\b", re.I),
    ),
    (
        "tool_name",
        re.compile(r"\b(report_progress|task\(|list_artifacts|tool_calls?)\b", re.I),
    ),
    ("file_extension", re.compile(r"\b(DOCX|PPTX|XLSX|\.docx|\.pptx|\.xlsx)\b", re.I)),
    (
        "raw_scope_enum",
        re.compile(r"\b(NEW_BRAND|REPOSITIONING|FULL_REBRAND|REFRESH)\b"),
    ),
)


@dataclass(frozen=True)
class TurnAudit:
    """Per-turn deterministic chat hygiene signals."""

    turn: int
    assistant_chars: int
    claim_flags: dict[str, int]
    provenance_hits: int
    unsupported_claim_risk: int
    internal_language_flags: dict[str, int]
    adjacent_repeat_ratio: float | None = None


def _load_turns(transcript_path: Path) -> list[dict[str, Any]]:
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        turns = data.get("turns")
        if isinstance(turns, list):
            return turns
    raise ValueError(f"Unsupported transcript schema: {transcript_path}")


def _assistant_text(turn: dict[str, Any]) -> str:
    value = turn.get("agent", turn.get("assistant_response", turn.get("assistant", "")))
    return value if isinstance(value, str) else ""


def _turn_number(index: int, turn: dict[str, Any]) -> int:
    value = turn.get("turn", index + 1)
    return value if isinstance(value, int) else index + 1


def _count_patterns(
    text: str,
    patterns: tuple[tuple[str, re.Pattern[str]], ...],
) -> dict[str, int]:
    return {
        name: len(pattern.findall(text))
        for name, pattern in patterns
        if pattern.findall(text)
    }


def _provenance_hits(text: str) -> int:
    return sum(len(pattern.findall(text)) for pattern in PROVENANCE_PATTERNS)


def _has_provenance_or_caveat(text: str) -> bool:
    patterns = PROVENANCE_PATTERNS + CAVEAT_PATTERNS
    return any(pattern.search(text) for pattern in patterns)


def _sentence_fragments(text: str) -> list[str]:
    return [
        fragment.strip()
        for fragment in re.split(r"(?<=[.!?])\s+|\n+", text)
        if fragment.strip()
    ]


def _unsupported_claim_risk(text: str) -> int:
    risk = 0
    for fragment in _sentence_fragments(text):
        if fragment.endswith("?") or _has_provenance_or_caveat(fragment):
            continue
        claim_flags = _count_patterns(fragment, CLAIM_PATTERNS)
        risk += sum(claim_flags.values())
    return risk


def _word_windows(text: str, window_size: int = 8) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", text.lower())
    if len(words) < window_size:
        return set()
    return {
        tuple(words[index : index + window_size])
        for index in range(0, len(words) - window_size + 1)
    }


def _adjacent_repeat_ratio(previous: str, current: str) -> float:
    previous_windows = _word_windows(previous)
    current_windows = _word_windows(current)
    if not previous_windows or not current_windows:
        return 0.0
    overlap = len(previous_windows & current_windows)
    return overlap / max(len(current_windows), 1)


def audit_transcript(transcript_path: Path) -> dict[str, Any]:
    """Audit one transcript and return deterministic hygiene metrics."""

    turns = _load_turns(transcript_path)
    audits: list[TurnAudit] = []
    previous_text = ""
    totals: Counter[str] = Counter()

    for index, turn in enumerate(turns):
        text = _assistant_text(turn)
        claim_flags = _count_patterns(text, CLAIM_PATTERNS)
        internal_flags = _count_patterns(text, INTERNAL_LANGUAGE_PATTERNS)
        provenance_hits = _provenance_hits(text)
        unsupported_claim_risk = _unsupported_claim_risk(text)
        repeat_ratio = None
        if previous_text:
            repeat_ratio = round(_adjacent_repeat_ratio(previous_text, text), 3)

        audits.append(
            TurnAudit(
                turn=_turn_number(index, turn),
                assistant_chars=len(text),
                claim_flags=claim_flags,
                provenance_hits=provenance_hits,
                unsupported_claim_risk=unsupported_claim_risk,
                internal_language_flags=internal_flags,
                adjacent_repeat_ratio=repeat_ratio,
            )
        )
        totals.update({f"claim.{key}": value for key, value in claim_flags.items()})
        totals.update(
            {f"internal.{key}": value for key, value in internal_flags.items()}
        )
        totals["provenance_hits"] += provenance_hits
        totals["unsupported_claim_risk"] += unsupported_claim_risk
        previous_text = text

    lengths = [audit.assistant_chars for audit in audits]
    repeat_ratios = [
        audit.adjacent_repeat_ratio
        for audit in audits
        if audit.adjacent_repeat_ratio is not None
    ]
    long_turns = [audit.turn for audit in audits if audit.assistant_chars > 8000]
    repeat_turns = [
        audit.turn
        for audit in audits
        if (audit.adjacent_repeat_ratio or 0.0) >= 0.15
    ]
    unsupported_turns = [
        audit.turn
        for audit in audits
        if audit.unsupported_claim_risk >= 3
    ]

    return {
        "transcript": str(transcript_path),
        "turn_count": len(audits),
        "summary": {
            "mean_assistant_chars": round(mean(lengths), 1) if lengths else 0.0,
            "max_assistant_chars": max(lengths, default=0),
            "long_turns_over_8000_chars": long_turns,
            "mean_adjacent_repeat_ratio": round(mean(repeat_ratios), 3)
            if repeat_ratios
            else 0.0,
            "repeat_turns_ratio_ge_0_15": repeat_turns,
            "unsupported_claim_risk_turns_ge_3": unsupported_turns,
            "totals": dict(totals),
        },
        "turns": [asdict(audit) for audit in audits],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path, help="Path to transcript.json")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    result = audit_transcript(args.transcript)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
