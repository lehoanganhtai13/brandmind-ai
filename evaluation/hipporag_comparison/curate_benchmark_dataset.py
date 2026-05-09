"""Curate the final five-book benchmark dataset from candidate questions.

Business context:
    Candidate questions are useful only after a quality gate. The benchmark
    used for BrandMind vs HippoRAG comparison should exclude low-value source
    chunks, shallow gold answers, and redundant easy cases while preserving
    fixed coverage across the five books and cross-book synthesis.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    QuestionType,
)
from evaluation.hipporag_comparison.export_corpus import write_json

DEFAULT_CANDIDATE_PATH = Path(
    ".codex/benchmarks/hipporag/dataset/candidate_questions.json"
)
DEFAULT_EVIDENCE_PACKETS_PATH = Path(
    ".codex/benchmarks/hipporag/dataset/evidence_packets.json"
)
DEFAULT_OUTPUT_PATH = Path(
    "evaluation/hipporag_comparison/datasets/marketing_5books_benchmark_v1.json"
)
DEFAULT_REPORT_PATH = Path(".codex/benchmarks/hipporag/dataset/curation_report.json")

FINAL_DATASET_DESCRIPTION = (
    "Final source-grounded 150-item benchmark for comparing BrandMind and "
    "HippoRAG on five canonical marketing books."
)

QUESTION_TYPE_QUOTAS_25 = {
    QuestionType.MECHANISM: 5,
    QuestionType.DEFINITION: 4,
    QuestionType.COMPARE_CONTRAST: 4,
    QuestionType.APPLICATION: 4,
    QuestionType.SYNTHESIS: 4,
    QuestionType.DIAGNOSIS: 4,
}

LOW_VALUE_TEXT_PATTERN = re.compile(
    r"\b("
    r"index|appendix|appendices|mục lục|chỉ mục|tra cứu|"
    r"tài liệu tham khảo|bibliography|front matter|table of contents|"
    r"cover page|copyright|preface"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CandidateAudit:
    """Quality audit for one generated candidate."""

    item: BenchmarkItem
    score: int
    flags: list[str]
    source_sections: list[str]


def load_candidate_dataset(path: Path) -> BenchmarkDataset:
    """Load candidates from a generator artifact or raw dataset file."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    dataset_payload = payload.get("dataset") if isinstance(payload, dict) else None
    if dataset_payload is None:
        dataset_payload = payload
    return BenchmarkDataset.model_validate(dataset_payload)


def load_source_sections(evidence_packets_path: Path) -> dict[str, str]:
    """Load source section labels keyed by source ID."""

    payload = json.loads(evidence_packets_path.read_text(encoding="utf-8"))
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError(f"Expected packets list in {evidence_packets_path}")

    source_sections: dict[str, str] = {}
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        sources = packet.get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id", "")).strip()
            section = str(source.get("source", "")).strip()
            if source_id:
                source_sections[source_id] = section
    return source_sections


def audit_candidate(
    item: BenchmarkItem,
    source_sections_by_id: dict[str, str],
) -> CandidateAudit:
    """Compute deterministic quality flags and a curation score."""

    flags: list[str] = []
    joined_text = " ".join(
        [item.question, item.gold_answer, item.evidence_digest]
    ).lower()
    source_sections = [
        source_sections_by_id.get(source_id, "") for source_id in item.required_sources
    ]
    joined_sources = " ".join(source_sections).lower()

    if LOW_VALUE_TEXT_PATTERN.search(joined_text):
        flags.append("low_value_question_or_answer")
    if LOW_VALUE_TEXT_PATTERN.search(joined_sources):
        flags.append("low_value_source_section")
    if len(item.gold_answer.split()) < 55:
        flags.append("short_gold_answer")
    if len(item.answer_key_facts) < 3:
        flags.append("too_few_answer_key_facts")
    if len(item.answer_key_facts) > 6:
        flags.append("too_many_answer_key_facts")

    score = 100
    score -= 100 * sum(flag.startswith("low_value") for flag in flags)
    score -= 25 if "short_gold_answer" in flags else 0
    score -= 20 if "too_few_answer_key_facts" in flags else 0
    score -= 10 if "too_many_answer_key_facts" in flags else 0
    score += min(len(item.answer_key_facts), 5) * 3
    score += min(len(item.gold_answer.split()), 140) // 10
    if item.difficulty.value == "hard":
        score += 10
    elif item.difficulty.value == "medium":
        score += 5

    return CandidateAudit(
        item=item,
        score=score,
        flags=flags,
        source_sections=source_sections,
    )


def item_sort_key(audit: CandidateAudit) -> tuple[int, int, int, str]:
    """Sort candidates from most to least useful for curation."""

    return (
        audit.score,
        len(set(audit.source_sections)),
        len(audit.item.answer_key_facts),
        audit.item.id,
    )


def choose_scope_items(
    audits: list[CandidateAudit],
    target_count: int,
) -> list[BenchmarkItem]:
    """Choose a stratified set for one book scope."""

    acceptable = [audit for audit in audits if not audit.flags]
    if len(acceptable) < target_count:
        raise ValueError(
            f"Only {len(acceptable)} acceptable candidates for "
            f"{audits[0].item.book_scope.value}; need {target_count}."
        )

    selected: list[CandidateAudit] = []
    selected_ids: set[str] = set()
    by_type: dict[QuestionType, list[CandidateAudit]] = defaultdict(list)
    for audit in acceptable:
        by_type[audit.item.question_type].append(audit)

    for question_type, quota in QUESTION_TYPE_QUOTAS_25.items():
        ranked = sorted(by_type[question_type], key=item_sort_key, reverse=True)
        for audit in ranked[:quota]:
            selected.append(audit)
            selected_ids.add(audit.item.id)

    if len(selected) < target_count:
        ranked_remaining = sorted(
            (audit for audit in acceptable if audit.item.id not in selected_ids),
            key=item_sort_key,
            reverse=True,
        )
        selected.extend(ranked_remaining[: target_count - len(selected)])

    selected = sorted(selected[:target_count], key=lambda audit: audit.item.id)
    return [audit.item for audit in selected]


def curate_dataset(
    candidates: BenchmarkDataset,
    source_sections_by_id: dict[str, str],
    per_book_count: int = 25,
    cross_book_count: int = 25,
) -> tuple[BenchmarkDataset, dict[str, object]]:
    """Curate final benchmark items and return a review report."""

    audits = [audit_candidate(item, source_sections_by_id) for item in candidates.items]
    audits_by_scope: dict[BookScope, list[CandidateAudit]] = defaultdict(list)
    for audit in audits:
        audits_by_scope[audit.item.book_scope].append(audit)

    selected_items: list[BenchmarkItem] = []
    for scope in BookScope:
        target_count = (
            cross_book_count if scope is BookScope.CROSS_BOOK else per_book_count
        )
        selected_items.extend(choose_scope_items(audits_by_scope[scope], target_count))

    final_dataset = BenchmarkDataset(
        dataset_id="brandmind_marketing_5books_v1",
        dataset_version="1.0.0",
        description=FINAL_DATASET_DESCRIPTION,
        items=selected_items,
    )
    selected_ids = {item.id for item in selected_items}
    rejected = [audit for audit in audits if audit.item.id not in selected_ids]
    report = build_curation_report(final_dataset, audits, rejected)
    return final_dataset, report


def build_curation_report(
    final_dataset: BenchmarkDataset,
    audits: list[CandidateAudit],
    rejected: list[CandidateAudit],
) -> dict[str, object]:
    """Build a JSON-serializable curation report."""

    return {
        "selected_count": len(final_dataset.items),
        "rejected_count": len(rejected),
        "selected_distribution": final_dataset.distribution_summary(),
        "candidate_flag_counts": dict(
            Counter(flag for audit in audits for flag in audit.flags)
        ),
        "rejected_by_scope": dict(
            Counter(audit.item.book_scope.value for audit in rejected)
        ),
        "rejected_items": [
            {
                "id": audit.item.id,
                "book_scope": audit.item.book_scope.value,
                "question_type": audit.item.question_type.value,
                "difficulty": audit.item.difficulty.value,
                "score": audit.score,
                "flags": audit.flags,
                "question": audit.item.question,
                "source_sections": audit.source_sections,
            }
            for audit in sorted(rejected, key=lambda audit: audit.item.id)
        ],
    }


def write_final_dataset(dataset: BenchmarkDataset, output_path: Path) -> None:
    """Write the final benchmark dataset as raw schema JSON."""

    write_json(output_path, dataset.model_dump(mode="json"))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for final dataset curation."""

    parser = argparse.ArgumentParser(
        description="Curate final 150-item HippoRAG comparison benchmark.",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATE_PATH,
        help="Candidate generation artifact or raw BenchmarkDataset JSON.",
    )
    parser.add_argument(
        "--evidence-packets",
        type=Path,
        default=DEFAULT_EVIDENCE_PACKETS_PATH,
        help="Evidence packet artifact used to audit source sections.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Tracked final BenchmarkDataset JSON path.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Ignored curation report JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run final dataset curation from candidate artifacts."""

    args = parse_args()
    candidates = load_candidate_dataset(args.candidates)
    source_sections = load_source_sections(args.evidence_packets)
    final_dataset, report = curate_dataset(candidates, source_sections)
    write_final_dataset(final_dataset, args.output)
    write_json(args.report, report)
    print(
        f"Wrote {len(final_dataset.items)} final items to {args.output} "
        f"and report to {args.report}",
        flush=True,
    )


if __name__ == "__main__":
    main()
