"""Unit tests for final HippoRAG benchmark curation."""

from __future__ import annotations

from evaluation.hipporag_comparison.benchmark_schema import (
    AnswerKeyFactSource,
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
    ReasoningType,
)
from evaluation.hipporag_comparison.curate_benchmark_dataset import (
    audit_candidate,
    curate_dataset,
    curate_hard_dataset,
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


def make_hard_item(
    index: int,
    *,
    book_scope: BookScope,
    question_type: QuestionType,
    reasoning_type: ReasoningType,
    source_count: int,
) -> BenchmarkItem:
    """Create a v2-hard curation fixture item."""

    if book_scope is BookScope.CROSS_BOOK:
        source_books = list(BookScope)[:source_count]
        required_sources = [
            f"{source_book.value}::chunk_{index}"
            for source_book in source_books
            if source_book is not BookScope.CROSS_BOOK
        ][:source_count]
    else:
        required_sources = [
            f"{book_scope.value}::chunk_{index}_{source_index}"
            for source_index in range(1, source_count + 1)
        ]
    first_source = required_sources[0]
    second_source = required_sources[1]
    return BenchmarkItem(
        id=f"BM5B-HARD-{index:03d}",
        question=(
            "How should a marketer synthesize distributed evidence across "
            "multiple sources for a hard brand strategy decision?"
        ),
        gold_answer=(
            "A correct hard answer should combine multiple sources, explain "
            "why a single source is insufficient, connect the distributed "
            "evidence into one reasoning chain, diagnose the strategic risk, "
            "and state a grounded implication for action. It should also show "
            "which source contributes the market mechanism, which source "
            "contributes the behavioral or execution constraint, and why the "
            "final recommendation depends on their interaction rather than on "
            "a single isolated passage."
        ),
        answer_key_facts=[
            "The answer must use source one.",
            "The answer must use source two.",
            "The answer must synthesize source one and source two.",
            "The answer must explain why one source alone is insufficient.",
            "The answer must state the strategic implication.",
        ],
        required_sources=required_sources,
        book_scope=book_scope,
        question_type=question_type,
        difficulty=Difficulty.HARD,
        evidence_digest=(
            "The selected sources jointly require a multi-hop answer because "
            "each source contributes a distinct part of the final reasoning."
        ),
        reasoning_type=reasoning_type,
        single_source_sufficient=False,
        answer_key_fact_sources=[
            AnswerKeyFactSource(fact_index=1, source_ids=[first_source]),
            AnswerKeyFactSource(fact_index=2, source_ids=[second_source]),
            AnswerKeyFactSource(
                fact_index=3,
                source_ids=[first_source, second_source],
                role="synthesis",
            ),
            AnswerKeyFactSource(
                fact_index=4,
                source_ids=[first_source, second_source],
                role="synthesis",
            ),
            AnswerKeyFactSource(
                fact_index=5,
                source_ids=required_sources,
                role="support",
            ),
        ],
    )


def make_hard_dataset() -> BenchmarkDataset:
    """Create candidates that exactly satisfy v2-hard quotas."""

    items: list[BenchmarkItem] = []
    question_types = [
        QuestionType.MECHANISM,
        QuestionType.COMPARE_CONTRAST,
        QuestionType.APPLICATION,
        QuestionType.SYNTHESIS,
        QuestionType.DIAGNOSIS,
    ]
    reasoning_types = list(ReasoningType)
    source_counts = [*[2] * 20, *[3] * 60, *[4] * 50, *[5] * 20]
    for index in range(1, 151):
        book_scope = (
            BookScope.CROSS_BOOK
            if index <= 90
            else [
                BookScope.HOW_BRANDS_GROW,
                BookScope.INFLUENCE,
                BookScope.KOTLER,
                BookScope.POSITIONING,
                BookScope.STRATEGIC_BRAND_MANAGEMENT,
            ][index % 5]
        )
        items.append(
            make_hard_item(
                index,
                book_scope=book_scope,
                question_type=question_types[(index - 1) % len(question_types)],
                reasoning_type=reasoning_types[(index - 1) % len(reasoning_types)],
                source_count=source_counts[index - 1],
            )
        )
    return BenchmarkDataset(
        description="A hard multi-hop candidate dataset for curation tests.",
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


def test_curate_hard_dataset_selects_v2_quotas() -> None:
    """Hard curation should preserve the planned v2 source and scope quotas."""

    candidates = make_hard_dataset()
    source_sections = {
        source_id: f"Chapter {index}: {source_id} Useful Distributed Content"
        for index, item in enumerate(candidates.items, start=1)
        for source_id in item.required_sources
    }

    final_dataset, report = curate_hard_dataset(candidates, source_sections)

    summary = final_dataset.distribution_summary()
    cross_book_count = summary["book_scope"]["cross_book"]
    intra_book_count = len(final_dataset.items) - cross_book_count
    assert len(final_dataset.items) == 150
    assert cross_book_count == 90
    assert intra_book_count == 60
    assert summary["required_source_count"] == {"2": 20, "3": 60, "4": 50, "5": 20}
    assert set(summary["question_type"].values()) == {30}
    assert set(summary["reasoning_type"].values()) == {30}
    assert report["selected_count"] == 150
