"""Unit tests for re-judging existing comparison artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
)
from evaluation.knowledge_search_comparison.judge import AnswerKeyFactJudge
from evaluation.knowledge_search_comparison.rejudge_results import (
    build_rejudge_config,
    rejudge_records,
    resolve_dataset_path,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    AnswerJudgeResult,
    ComparisonRunConfig,
    ComparisonRunResult,
    ComparisonSystem,
)


def make_rejudge_item() -> BenchmarkItem:
    """Create a benchmark item fixture for re-judging tests."""

    return BenchmarkItem(
        id="BM5B-KOTLER-901",
        question="How should marketers reason about customer value in an offer?",
        gold_answer=(
            "A correct answer explains that customer value compares perceived "
            "benefits with customer costs, then connects that value judgment "
            "to offer design and positioning decisions."
        ),
        answer_key_facts=[
            "Customer value compares perceived benefits with customer costs.",
            "Customer value should guide offer design.",
        ],
        required_sources=["kotler_and_armstrong_principles_of_marketing::chunk_901"],
        book_scope=BookScope.KOTLER,
        question_type=QuestionType.APPLICATION,
        difficulty=Difficulty.MEDIUM,
        evidence_digest=(
            "The source explains customer value and how marketers use it to "
            "shape an offer."
        ),
    )


def make_rejudge_dataset() -> BenchmarkDataset:
    """Create a minimal benchmark dataset fixture."""

    return BenchmarkDataset(
        dataset_id="fixture",
        dataset_version="1",
        description="Fixture dataset for re-judging existing answers.",
        items=[make_rejudge_item()],
    )


def test_resolve_dataset_path_prefers_existing_result_path(tmp_path: Path) -> None:
    """Re-judge CLI should reuse the artifact dataset path when it exists."""

    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text("{}", encoding="utf-8")
    run_result = ComparisonRunResult(
        dataset_id="fixture",
        dataset_version="1",
        config=ComparisonRunConfig(
            dataset_path=dataset_path,
            output_path=tmp_path / "result.json",
        ),
        records=[],
    )

    assert (
        resolve_dataset_path(run_result=run_result, override_path=None) == dataset_path
    )


def test_build_rejudge_config_records_litellm_judge_provider(tmp_path: Path) -> None:
    """Re-judged artifacts should record the active judge provider and model."""

    config = build_rejudge_config(
        original_config=ComparisonRunConfig(
            dataset_path=tmp_path / "old_dataset.json",
            output_path=tmp_path / "old_result.json",
        ),
        dataset_path=tmp_path / "dataset.json",
        output_path=tmp_path / "result.json",
        judge_provider="auto",
        judge_model="claude-sonnet-4.6",
        judge_temperature=0.0,
        judge_thinking_budget=2000,
        judge_thinking_level=None,
    )

    assert config.judge_provider == "litellm"
    assert config.judge_model == "claude-sonnet-4.6"
    assert config.judge_thinking_budget is None


@pytest.mark.asyncio
async def test_rejudge_records_replaces_existing_judgment() -> None:
    """Re-judging should preserve answers and replace judge results."""

    item = make_rejudge_item()
    old_record = AnswerFlowRecord(
        item_id=item.id,
        question=item.question,
        system=ComparisonSystem.BRANDMIND_AGENT,
        final_answer="Customer value should guide offer design.",
        judge=AnswerJudgeResult(
            is_correct=True,
            reasoning="Old judgment.",
            covered_facts=item.answer_key_facts,
        ),
    )

    records = await rejudge_records(
        records=[old_record],
        dataset=make_rejudge_dataset(),
        judge=AnswerKeyFactJudge(),
    )

    assert records[0].final_answer == old_record.final_answer
    assert records[0].judge is not None
    assert records[0].judge.is_correct is False
    assert records[0].judge.reasoning != "Old judgment."
