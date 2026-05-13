"""Unit tests for comparison-runner checkpoint and concurrency controls."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.dataset import (
    DEFAULT_DATASET_PATH,
    load_benchmark_dataset,
)
from evaluation.knowledge_search_comparison.run_comparison import (
    append_checkpoint_record,
    attach_judge_result,
    build_default_checkpoint_path,
    load_checkpoint_records,
    run_comparison,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    AnswerJudgeResult,
    ComparisonRunConfig,
    ComparisonSystem,
)


class FailingJudge:
    """Fixture judge that raises like an exhausted provider would."""

    async def judge(
        self,
        *,
        item: BenchmarkItem,
        candidate_answer: str,
    ) -> AnswerJudgeResult:
        """Raise a deterministic judge failure."""

        del item, candidate_answer
        raise RuntimeError("provider exhausted")


@pytest.mark.asyncio
async def test_checkpoint_records_round_trip(tmp_path: Path) -> None:
    """Checkpoint JSONL should preserve completed answer-flow records."""

    checkpoint_path = tmp_path / "records.jsonl"
    record = AnswerFlowRecord(
        item_id="BM5B-KOTLER-001",
        question="Question?",
        system=ComparisonSystem.BRANDMIND_AGENT,
        final_answer="Answer",
    )

    import asyncio

    await append_checkpoint_record(
        path=checkpoint_path,
        record=record,
        lock=asyncio.Lock(),
    )

    loaded_records = load_checkpoint_records(checkpoint_path)

    assert len(loaded_records) == 1
    assert loaded_records[0].item_id == "BM5B-KOTLER-001"
    assert loaded_records[0].system is ComparisonSystem.BRANDMIND_AGENT


@pytest.mark.asyncio
async def test_run_comparison_resumes_without_duplicate_checkpoint_lines(
    tmp_path: Path,
) -> None:
    """Resume should skip records already present in the checkpoint."""

    checkpoint_path = tmp_path / "resume.records.jsonl"
    config = ComparisonRunConfig(
        dataset_path=DEFAULT_DATASET_PATH,
        output_path=tmp_path / "result.json",
        checkpoint_path=checkpoint_path,
        systems=[ComparisonSystem.HYBRID_SEARCH_AGENT],
        limit=1,
        dry_run_fixture=True,
        progress_interval=0,
    )

    first_result = await run_comparison(config)
    resumed_result = await run_comparison(config.model_copy(update={"resume": True}))

    assert len(first_result.records) == 1
    assert len(resumed_result.records) == 1
    assert len(checkpoint_path.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.asyncio
async def test_run_comparison_concurrency_keeps_all_fixture_records(
    tmp_path: Path,
) -> None:
    """Concurrent dry-run execution should keep deterministic output coverage."""

    checkpoint_path = tmp_path / "concurrent.records.jsonl"
    config = ComparisonRunConfig(
        dataset_path=DEFAULT_DATASET_PATH,
        output_path=tmp_path / "result.json",
        checkpoint_path=checkpoint_path,
        limit=2,
        concurrency=3,
        dry_run_fixture=True,
        progress_interval=0,
    )

    result = await run_comparison(config)

    assert len(result.records) == 6
    assert len(load_checkpoint_records(checkpoint_path)) == 6
    assert [record.item_id for record in result.records[:3]] == [
        result.records[0].item_id
    ] * 3


@pytest.mark.asyncio
async def test_attach_judge_result_keeps_record_on_judge_failure() -> None:
    """Judge provider errors should become record errors, not runner crashes."""

    record = AnswerFlowRecord(
        item_id="BM5B-KOTLER-001",
        question="Question?",
        system=ComparisonSystem.HYBRID_SEARCH_AGENT,
        final_answer="Answer",
    )

    judged_record = await attach_judge_result(
        record=record,
        item=load_benchmark_dataset(DEFAULT_DATASET_PATH).items[0],
        judge=FailingJudge(),
    )

    assert judged_record.judge is None
    assert judged_record.error == "Judge failed: provider exhausted"


def test_default_checkpoint_path_pairs_with_output_path(tmp_path: Path) -> None:
    """The default checkpoint should sit beside the final JSON artifact."""

    output_path = tmp_path / "full150.json"

    assert (
        build_default_checkpoint_path(output_path) == tmp_path / "full150.records.jsonl"
    )
