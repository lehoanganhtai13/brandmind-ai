"""Build source-first evidence packets for benchmark curation.

Evidence packets are not final benchmark questions. They are compact groups of
source chunks that a human or later LLM generation task can use to produce
source-grounded questions, gold answers, answer key facts, and required source
IDs.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from evaluation.hipporag_comparison.export_corpus import build_records, write_json

DEFAULT_PACKET_OUTPUT = Path(".codex/benchmarks/hipporag/dataset/evidence_packets.json")
LOW_VALUE_SOURCE_LABELS = {
    "index",
    "appendices > index",
    "references",
    "bibliography",
    "glossary",
    "contents",
    "table of contents",
    "front matter",
}
REFERENCE_LIST_MARKERS = (
    "harvard business review",
    "wall street journal",
    "new york times",
    "new york:",
    "advertising age",
    "harvard business school press",
    "journal of",
    "doubleday",
    "currency",
    "see also",
    "www.",
    "http",
    "press",
    "adweek",
)
NUMBERED_REFERENCE_PATTERN = re.compile(r"^\s*\d{1,3}\.\s+\S+")


@dataclass(frozen=True)
class EvidenceSource:
    """One source chunk included in an evidence packet."""

    source_id: str
    book_slug: str
    source: str
    pages: list[int]
    section_summary: str
    excerpt: str
    word_count: int | None


@dataclass(frozen=True)
class EvidencePacket:
    """A compact evidence group used to curate benchmark questions."""

    packet_id: str
    candidate_scope: str
    difficulty_hint: str
    question_type_hint: str
    evidence_digest: str
    sources: list[EvidenceSource]


def compact_excerpt(text: str, max_chars: int = 900) -> str:
    """Create a stable one-line excerpt for review.

    Args:
        text: Source chunk text.
        max_chars: Maximum excerpt length.

    Returns:
        A compact excerpt that preserves the start of the source chunk.
    """

    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "..."


def build_source_lookup(parsed_root: Path) -> dict[str, EvidenceSource]:
    """Build a source lookup from canonical parsed documents.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Returns:
        Evidence sources keyed by stable source ID.
    """

    records, metadata_by_source_id = build_records(parsed_root)
    record_text_by_source_id = {record.title: record.text for record in records}
    return {
        source_id: EvidenceSource(
            source_id=source_id,
            book_slug=metadata.book_slug,
            source=metadata.source,
            pages=metadata.pages,
            section_summary=metadata.section_summary,
            excerpt=compact_excerpt(record_text_by_source_id[source_id]),
            word_count=metadata.word_count,
        )
        for source_id, metadata in metadata_by_source_id.items()
    }


def select_book_sources(
    source_lookup: dict[str, EvidenceSource],
    per_book_limit: int,
) -> dict[str, list[EvidenceSource]]:
    """Select high-signal sources for each canonical book.

    Args:
        source_lookup: Evidence sources keyed by source ID.
        per_book_limit: Maximum selected sources per book.

    Returns:
        Selected sources grouped by book slug.
    """

    grouped: dict[str, list[EvidenceSource]] = defaultdict(list)
    for source in source_lookup.values():
        if not is_low_value_source(source):
            grouped[source.book_slug].append(source)

    selected: dict[str, list[EvidenceSource]] = {}
    for book_slug, sources in grouped.items():
        selected[book_slug] = select_diverse_sources(sources, per_book_limit)
    return selected


def is_low_value_source(source: EvidenceSource) -> bool:
    """Return whether a source is unsuitable for benchmark question curation."""

    source_label = " ".join(source.source.lower().split())
    if source_label in LOW_VALUE_SOURCE_LABELS:
        return True
    if source_label.endswith("> index") or source_label.endswith("> references"):
        return True
    if source_label.endswith("> bibliography"):
        return True

    excerpt = source.excerpt.lower()
    if NUMBERED_REFERENCE_PATTERN.match(excerpt):
        return any(marker in excerpt[:700] for marker in REFERENCE_LIST_MARKERS)
    return False


def source_quality_key(source: EvidenceSource) -> tuple[int, int, str]:
    """Rank sources inside a section group by benchmark usefulness."""

    return (
        1 if source.section_summary else 0,
        source.word_count or 0,
        source.source_id,
    )


def source_group_key(source: EvidenceSource) -> str:
    """Return a section-level key used to diversify selected sources."""

    return source.source.strip() or source.source_id


def select_diverse_sources(
    sources: list[EvidenceSource],
    limit: int,
) -> list[EvidenceSource]:
    """Select high-quality sources while spreading coverage across sections."""

    grouped: dict[str, list[EvidenceSource]] = defaultdict(list)
    for source in sources:
        grouped[source_group_key(source)].append(source)

    ranked_groups = sorted(
        (
            sorted(group_sources, key=source_quality_key, reverse=True)
            for group_sources in grouped.values()
        ),
        key=lambda group_sources: source_quality_key(group_sources[0]),
        reverse=True,
    )

    selected: list[EvidenceSource] = []
    while len(selected) < limit and ranked_groups:
        next_groups: list[list[EvidenceSource]] = []
        for group_sources in ranked_groups:
            if len(selected) >= limit:
                break
            selected.append(group_sources[0])
            if len(group_sources) > 1:
                next_groups.append(group_sources[1:])
        ranked_groups = next_groups
    return selected


def infer_question_type_hint(index: int) -> str:
    """Rotate question type hints to encourage curation diversity."""

    hints = [
        "definition",
        "mechanism",
        "compare_contrast",
        "application",
        "synthesis",
        "diagnosis",
    ]
    return hints[index % len(hints)]


def infer_difficulty_hint(index: int, source_count: int) -> str:
    """Infer a simple difficulty hint from packet position and source count."""

    if source_count >= 2:
        return "hard"
    if index % 3 == 0:
        return "easy"
    return "medium"


def build_single_book_packets(
    selected_by_book: dict[str, list[EvidenceSource]],
) -> list[EvidencePacket]:
    """Build one-source packets for single-book benchmark curation."""

    packets: list[EvidencePacket] = []
    for book_slug, sources in sorted(selected_by_book.items()):
        for index, source in enumerate(sources, start=1):
            packets.append(
                EvidencePacket(
                    packet_id=f"{book_slug}-single-{index:03d}",
                    candidate_scope=book_slug,
                    difficulty_hint=infer_difficulty_hint(index, source_count=1),
                    question_type_hint=infer_question_type_hint(index),
                    evidence_digest=source.section_summary or source.source,
                    sources=[source],
                )
            )
    return packets


def build_cross_book_packets(
    selected_by_book: dict[str, list[EvidenceSource]],
    cross_book_limit: int,
) -> list[EvidencePacket]:
    """Build paired-source packets for cross-book benchmark curation."""

    book_slugs = sorted(selected_by_book)
    packets: list[EvidencePacket] = []
    packet_index = 1
    for left_index, left_book in enumerate(book_slugs):
        for right_book in book_slugs[left_index + 1 :]:
            left_sources = selected_by_book[left_book]
            right_sources = selected_by_book[right_book]
            pair_count = min(len(left_sources), len(right_sources), 3)
            for source_index in range(pair_count):
                left_source = left_sources[source_index]
                right_source = right_sources[source_index]
                left_summary = left_source.section_summary or left_source.source
                right_summary = right_source.section_summary or right_source.source
                packets.append(
                    EvidencePacket(
                        packet_id=f"cross-book-{packet_index:03d}",
                        candidate_scope="cross_book",
                        difficulty_hint="hard",
                        question_type_hint=infer_question_type_hint(packet_index),
                        evidence_digest=(
                            f"{left_source.book_slug}: {left_summary} | "
                            f"{right_source.book_slug}: {right_summary}"
                        ),
                        sources=[left_source, right_source],
                    )
                )
                packet_index += 1
                if len(packets) >= cross_book_limit:
                    return packets
    return packets


def build_evidence_packets(
    parsed_root: Path,
    per_book_limit: int = 40,
    cross_book_limit: int = 30,
) -> list[EvidencePacket]:
    """Build single-book and cross-book evidence packets.

    Args:
        parsed_root: Root directory containing parsed document folders.
        per_book_limit: Maximum single-book packets per canonical book.
        cross_book_limit: Maximum cross-book packets.

    Returns:
        Evidence packets in deterministic order.

    Raises:
        ValueError: If a limit is not positive.
    """

    if per_book_limit <= 0:
        raise ValueError("per_book_limit must be positive.")
    if cross_book_limit <= 0:
        raise ValueError("cross_book_limit must be positive.")

    source_lookup = build_source_lookup(parsed_root)
    selected_by_book = select_book_sources(source_lookup, per_book_limit=per_book_limit)
    return [
        *build_single_book_packets(selected_by_book),
        *build_cross_book_packets(selected_by_book, cross_book_limit=cross_book_limit),
    ]


def write_evidence_packets(packets: list[EvidencePacket], output_path: Path) -> None:
    """Write evidence packets as pretty JSON."""

    write_json(
        output_path,
        {
            "packet_count": len(packets),
            "packets": [
                {
                    **asdict(packet),
                    "source_ids": [source.source_id for source in packet.sources],
                }
                for packet in packets
            ],
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for evidence packet generation."""

    parser = argparse.ArgumentParser(
        description="Build source-first evidence packets for the 5-book benchmark.",
    )
    parser.add_argument(
        "--parsed-root",
        type=Path,
        default=Path("data/parsed_documents"),
        help="Root directory containing parsed document folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PACKET_OUTPUT,
        help="Output evidence packet JSON path.",
    )
    parser.add_argument(
        "--per-book-limit",
        type=int,
        default=40,
        help="Maximum selected single-book packets per canonical book.",
    )
    parser.add_argument(
        "--cross-book-limit",
        type=int,
        default=30,
        help="Maximum selected cross-book packets.",
    )
    return parser.parse_args()


def main() -> None:
    """Run evidence packet generation from the command line."""

    args = parse_args()
    packets = build_evidence_packets(
        parsed_root=args.parsed_root,
        per_book_limit=args.per_book_limit,
        cross_book_limit=args.cross_book_limit,
    )
    write_evidence_packets(packets, args.output)


if __name__ == "__main__":
    main()
