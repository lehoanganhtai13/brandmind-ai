"""Unit tests for final HippoRAG benchmark curation."""

from __future__ import annotations

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
)
from evaluation.hipporag_comparison.curate_benchmark_dataset import (
    audit_candidate,
    curate_dataset,
)

SCOPE_CODES = {
    BookScope.HOW_BRANDS_GROW: "HBG",
    BookScope.INFLUENCE: "INFLUENCE",
    BookScope.KOTLER: "KOTLER",
    BookScope.POSITIONING: "POSITIONING",
    BookScope.STRATEGIC_BRAND_MANAGEMENT: "SBM",
    BookScope.CROSS_BOOK: "CROSS",
}


def make_item(
    item_id: str,
    book_scope: BookScope,
    question_type: QuestionType,
    difficulty: Difficulty = Difficulty.MEDIUM,
    source_suffix: str = "chunk_1",
    gold_answer: str | None = None,
) -> BenchmarkItem:
    """Create a benchmark item fixture for curation tests."""

    if book_scope is BookScope.CROSS_BOOK:
        required_sources = [
            f"{BookScope.HOW_BRANDS_GROW.value}::{source_suffix}",
            f"{BookScope.INFLUENCE.value}::{source_suffix}",
        ]
    else:
        required_sources = [f"{book_scope.value}::{source_suffix}"]
    return BenchmarkItem(
        id=item_id,
        question=(
            "How should a marketer reason from this source-grounded evidence "
            "when making a strategy decision?"
        ),
        gold_answer=gold_answer
        or (
            "A strong answer should explain the core marketing principle, "
            "connect the principle to the cited evidence, identify the "
            "strategic implication, and state how a marketer should apply it "
            "in a realistic decision context. It should also describe the "
            "trade-off the marketer faces, explain why the evidence supports "
            "one course of action over another, and avoid adding claims that "
            "are not grounded in the required source."
        ),
        answer_key_facts=[
            "The answer must name the core marketing principle.",
            "The answer must connect the principle to the cited evidence.",
            "The answer must explain the strategic implication.",
        ],
        required_sources=required_sources,
        book_scope=book_scope,
        question_type=question_type,
        difficulty=difficulty,
        evidence_digest=(
            "The source provides enough evidence to judge whether the answer "
            "connects the marketing concept to a concrete decision."
        ),
    )


def make_dataset(per_scope_count: int = 30) -> BenchmarkDataset:
    """Create a candidate dataset with enough items for curation."""

    items: list[BenchmarkItem] = []
    type_cycle = list(QuestionType)
    for scope in BookScope:
        for index in range(1, per_scope_count + 1):
            code = SCOPE_CODES[scope]
            question_type = type_cycle[(index - 1) % len(type_cycle)]
            items.append(
                make_item(
                    item_id=f"BM5B-{code}-{index:03d}",
                    book_scope=scope,
                    question_type=question_type,
                    difficulty=(
                        Difficulty.HARD
                        if scope is BookScope.CROSS_BOOK
                        else Difficulty.MEDIUM
                    ),
                    source_suffix=f"chunk_{index}",
                )
            )
    return BenchmarkDataset(
        description="A source-grounded candidate dataset for curation tests.",
        items=items,
    )


def test_audit_candidate_flags_low_value_source_section() -> None:
    """Curation audit should reject index-like source sections."""

    item = make_item(
        "BM5B-KOTLER-001",
        BookScope.KOTLER,
        QuestionType.APPLICATION,
    )
    audit = audit_candidate(
        item,
        {
            item.required_sources[0]: "Appendices > Index",
        },
    )

    assert "low_value_source_section" in audit.flags


def test_curate_dataset_selects_150_stratified_items() -> None:
    """Final curation should select 25 items per scope."""

    candidates = make_dataset()
    source_sections = {
        source_id: "Chapter 1: Useful Marketing Content"
        for item in candidates.items
        for source_id in item.required_sources
    }

    final_dataset, report = curate_dataset(candidates, source_sections)

    assert len(final_dataset.items) == 150
    assert set(final_dataset.distribution_summary()["book_scope"].values()) == {25}
    assert report["selected_count"] == 150
    assert report["rejected_count"] == 30
