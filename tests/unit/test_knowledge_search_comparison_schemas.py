"""Unit tests for knowledge-search comparison result schemas."""

from __future__ import annotations

from pathlib import Path

from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    AnswerJudgeResult,
    ComparisonRunConfig,
    ComparisonRunResult,
    ComparisonSystem,
    ToolTrace,
)


def test_answer_judge_result_computes_fact_coverage() -> None:
    """Judge schema should compute coverage from covered and missing facts."""

    result = AnswerJudgeResult(
        is_correct=False,
        reasoning="One key fact is missing.",
        covered_facts=["fact A", "fact A"],
        missing_facts=["fact B"],
    )

    assert result.covered_facts == ["fact A"]
    assert result.fact_coverage == 0.5


def test_answer_flow_record_collects_unique_retrieved_sources() -> None:
    """Tool traces should expose source IDs as diagnostics."""

    record = AnswerFlowRecord(
        item_id="BM5B-KOTLER-001",
        question="What is customer value?",
        system=ComparisonSystem.BRANDMIND_AGENT,
        final_answer="Answer",
        tool_traces=[
            ToolTrace(
                tool_name="kg",
                query="customer value",
                source_ids=["book::chunk_1", "book::chunk_1"],
            ),
            ToolTrace(
                tool_name="docs",
                query="customer value",
                source_ids=["book::chunk_2"],
            ),
        ],
    )

    assert record.retrieved_source_ids == ["book::chunk_1", "book::chunk_2"]


def test_run_result_populates_system_summaries() -> None:
    """Run results should summarize accuracy, coverage, tools, and errors."""

    config = ComparisonRunConfig(
        dataset_path=Path("dataset.json"),
        output_path=Path("result.json"),
        systems=[ComparisonSystem.HYBRID_SEARCH_AGENT],
    )
    result = ComparisonRunResult(
        dataset_id="dataset",
        dataset_version="1",
        config=config,
        records=[
            AnswerFlowRecord(
                item_id="BM5B-KOTLER-001",
                question="Question?",
                system=ComparisonSystem.HYBRID_SEARCH_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=True,
                    reasoning="All facts covered.",
                    covered_facts=["fact A", "fact B"],
                ),
                tool_traces=[ToolTrace(tool_name="hybrid", query="Question?")],
                latency_ms=100,
            )
        ],
    )

    summary = result.summaries[0]
    assert summary.system is ComparisonSystem.HYBRID_SEARCH_AGENT
    assert summary.correct_items == 1
    assert summary.mean_fact_coverage == 1.0
    assert summary.mean_tool_calls == 1.0
