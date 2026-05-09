"""Unit tests for HippoRAG benchmark dataset schema and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
)
from evaluation.hipporag_comparison.build_evidence_packets import (
    EvidenceSource,
    build_evidence_packets,
    is_low_value_source,
    select_book_sources,
)
from evaluation.hipporag_comparison.export_corpus import CANONICAL_BOOK_DIRS
from evaluation.hipporag_comparison.validate_benchmark_dataset import (
    validate_benchmark_dataset,
)


def make_item(
    item_id: str = "BM5B-KOTLER-001",
    required_sources: list[str] | None = None,
    book_scope: BookScope = BookScope.KOTLER,
) -> BenchmarkItem:
    """Create a valid benchmark item fixture."""

    return BenchmarkItem(
        id=item_id,
        question="How should a marketer apply this source-grounded principle?",
        gold_answer=(
            "A correct answer should explain the marketing principle, connect it to "
            "the cited source evidence, and state the practical implication for a "
            "marketer."
        ),
        answer_key_facts=[
            "The answer must name the relevant marketing principle.",
            "The answer must connect the principle to the cited source evidence.",
        ],
        required_sources=required_sources
        or ["kotler_and_armstrong_principles_of_marketing::chunk_1"],
        book_scope=book_scope,
        question_type=QuestionType.APPLICATION,
        difficulty=Difficulty.MEDIUM,
        evidence_digest=(
            "The selected source explains a marketing principle and provides enough "
            "support for a practical application question."
        ),
    )


def write_fixture_chunks(parsed_root: Path, book_dir: str, chunk_id: str) -> None:
    """Write one parsed chunk fixture for a canonical book."""

    book_path = parsed_root / book_dir
    book_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [
            {
                "chunk_id": chunk_id,
                "content": f"Detailed source text for {book_dir}.",
                "metadata": {
                    "author": "Author",
                    "original_document": f"{book_dir}.pdf",
                    "pages": [1],
                    "section_summary": f"Summary for {book_dir}.",
                    "source": f"Source for {book_dir}.",
                    "word_count": 120,
                },
            }
        ]
    }
    (book_path / "chunks.json").write_text(json.dumps(payload), encoding="utf-8")


def make_source(
    source_id: str,
    source: str,
    excerpt: str,
    word_count: int = 300,
) -> EvidenceSource:
    """Create an evidence source fixture."""

    return EvidenceSource(
        source_id=source_id,
        book_slug="kotler_and_armstrong_principles_of_marketing",
        source=source,
        pages=[1],
        section_summary="Useful strategic marketing section summary.",
        excerpt=excerpt,
        word_count=word_count,
    )


def test_benchmark_item_accepts_valid_single_book_source() -> None:
    """Single-book items should validate when source slugs match scope."""

    item = make_item()

    assert item.book_scope is BookScope.KOTLER
    assert item.required_sources == [
        "kotler_and_armstrong_principles_of_marketing::chunk_1"
    ]


def test_benchmark_item_rejects_cross_book_with_one_book() -> None:
    """Cross-book items need at least two source book slugs."""

    with pytest.raises(ValidationError):
        make_item(
            item_id="BM5B-CROSS-001",
            required_sources=["kotler_and_armstrong_principles_of_marketing::chunk_1"],
            book_scope=BookScope.CROSS_BOOK,
        )


def test_benchmark_dataset_rejects_duplicate_ids() -> None:
    """Dataset item IDs should be unique."""

    with pytest.raises(ValidationError):
        BenchmarkDataset(
            description="A source-grounded test dataset for duplicate ID validation.",
            items=[make_item(), make_item()],
        )


def test_validate_benchmark_dataset_reports_missing_sources(tmp_path: Path) -> None:
    """Validator should reject required sources absent from metadata."""

    dataset_path = tmp_path / "dataset.json"
    metadata_path = tmp_path / "metadata.json"
    dataset = BenchmarkDataset(
        description="A source-grounded test dataset for missing source validation.",
        items=[make_item()],
    )
    dataset_path.write_text(dataset.model_dump_json(), encoding="utf-8")
    metadata_path.write_text(json.dumps({"sources": {}}), encoding="utf-8")

    report = validate_benchmark_dataset(dataset_path, metadata_path)

    assert not report.is_valid
    assert report.item_count == 1
    assert "missing source" in report.errors[0]


def test_validate_benchmark_dataset_accepts_existing_sources(tmp_path: Path) -> None:
    """Validator should accept datasets whose required sources exist in metadata."""

    source_id = "kotler_and_armstrong_principles_of_marketing::chunk_1"
    dataset_path = tmp_path / "dataset.json"
    metadata_path = tmp_path / "metadata.json"
    dataset = BenchmarkDataset(
        description="A source-grounded test dataset for valid source validation.",
        items=[make_item(required_sources=[source_id])],
    )
    dataset_path.write_text(dataset.model_dump_json(), encoding="utf-8")
    metadata_path.write_text(
        json.dumps({"sources": {source_id: {"source_id": source_id}}}),
        encoding="utf-8",
    )

    report = validate_benchmark_dataset(dataset_path, metadata_path)

    assert report.is_valid
    assert (
        report.distribution_summary["book_scope"][
            "kotler_and_armstrong_principles_of_marketing"
        ]
        == 1
    )


def test_build_evidence_packets_uses_canonical_books(tmp_path: Path) -> None:
    """Evidence packet builder should use canonical books and cross-book packets."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    packets = build_evidence_packets(
        parsed_root=tmp_path,
        per_book_limit=1,
        cross_book_limit=2,
    )

    single_book_packets = [
        packet for packet in packets if packet.candidate_scope != "cross_book"
    ]
    cross_book_packets = [
        packet for packet in packets if packet.candidate_scope == "cross_book"
    ]
    assert len(single_book_packets) == len(CANONICAL_BOOK_DIRS)
    assert len(cross_book_packets) == 2
    assert all(packet.sources for packet in packets)


def test_low_value_source_filter_rejects_index_and_reference_chunks() -> None:
    """Evidence selection should reject index and citation-list chunks."""

    index_source = make_source(
        "kotler_and_armstrong_principles_of_marketing::index",
        "Appendices > Index",
        "The Index provides a detailed alphabetical list of topics.",
    )
    reference_source = make_source(
        "strategic_brand_management::refs",
        "Chapter 6: Integrated Marketing Communications",
        "48. Mike Chapman, “What Clicks Worldwide,” Adweek, 30 May 2011.",
    )
    useful_source = make_source(
        "kotler_and_armstrong_principles_of_marketing::useful",
        "Chapter 7: Customer Value-Driven Marketing Strategy",
        (
            "This content outlines segmentation, targeting, differentiation, "
            "and positioning."
        ),
    )

    assert is_low_value_source(index_source)
    assert is_low_value_source(reference_source)
    assert not is_low_value_source(useful_source)


def test_select_book_sources_filters_low_value_sources() -> None:
    """Selected evidence should prefer useful chapter chunks over long indexes."""

    source_lookup = {
        "index": make_source(
            "kotler_and_armstrong_principles_of_marketing::index",
            "Appendices > Index",
            "The Index provides a detailed alphabetical list of topics.",
            word_count=900,
        ),
        "useful": make_source(
            "kotler_and_armstrong_principles_of_marketing::useful",
            "Chapter 7: Customer Value-Driven Marketing Strategy",
            (
                "This content outlines segmentation, targeting, differentiation, "
                "and positioning."
            ),
            word_count=300,
        ),
    }

    selected = select_book_sources(source_lookup, per_book_limit=1)

    selected_ids = [
        source.source_id
        for source in selected["kotler_and_armstrong_principles_of_marketing"]
    ]
    assert selected_ids == ["kotler_and_armstrong_principles_of_marketing::useful"]
