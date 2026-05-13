"""Unit tests for fake answer-flow records and report generation."""

from __future__ import annotations

import asyncio

import pytest

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
)
from evaluation.knowledge_search_comparison.agents import (
    AgentRunnerConfig,
    run_direct_tool_answer_flow,
)
from evaluation.knowledge_search_comparison.judge import AnswerKeyFactJudge
from evaluation.knowledge_search_comparison.report import build_report_lines
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    AnswerJudgeResult,
    ComparisonRunConfig,
    ComparisonRunResult,
    ComparisonSystem,
)


class FakeSearchTool:
    """Fixture search tool that returns mapped source text."""

    async def __call__(self, *, query: str, top_k: int) -> str:
        """Return a deterministic context string."""

        return (
            f"Query={query}; top_k={top_k}; "
            "Source: kotler_and_armstrong_principles_of_marketing::chunk_1."
        )


class FakeAnswerClient:
    """Fixture answer client that echoes the answer-key fact."""

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Return an answer that intentionally covers the fixture fact."""

        return (
            "The answer must mention customer value. "
            f"Context seen: {context}. Prompt length: {len(system_prompt)}."
        )


def make_item() -> BenchmarkItem:
    """Create one valid benchmark item fixture."""

    return BenchmarkItem(
        id="BM5B-KOTLER-001",
        question="How should marketers reason about customer value?",
        gold_answer=(
            "A correct answer explains that marketers should understand "
            "customer value as the benefit customers receive relative to costs, "
            "then use that understanding to shape the offer."
        ),
        answer_key_facts=[
            "The answer must mention customer value.",
            "The answer should connect value to offer design.",
        ],
        required_sources=["kotler_and_armstrong_principles_of_marketing::chunk_1"],
        book_scope=BookScope.KOTLER,
        question_type=QuestionType.APPLICATION,
        difficulty=Difficulty.MEDIUM,
        evidence_digest=(
            "The source defines customer value and supports practical offer "
            "design decisions."
        ),
    )


@pytest.mark.asyncio
async def test_fake_direct_tool_flow_produces_valid_record() -> None:
    """Fake single-tool flows should produce serializable answer records."""

    item = make_item()
    record = await run_direct_tool_answer_flow(
        item=item,
        system=ComparisonSystem.HYBRID_SEARCH_AGENT,
        search_tool=FakeSearchTool(),
        answer_client=FakeAnswerClient(),
        config=AgentRunnerConfig(top_k=5),
    )

    record.judge = await AnswerKeyFactJudge().judge(
        item=item,
        candidate_answer=record.final_answer,
    )

    assert record.error is None
    assert record.final_answer
    assert len(record.tool_traces) == 1
    assert record.judge is not None
    assert record.judge.fact_coverage == 0.5
    assert record.model_dump(mode="json")["system"] == "hybrid_search_agent"


def test_report_lines_include_system_summary() -> None:
    """Text reports should surface system-level metrics."""

    item = make_item()
    config = ComparisonRunConfig(
        dataset_path=__file__,
        output_path=__file__,
        systems=[ComparisonSystem.HYBRID_SEARCH_AGENT],
    )
    record = ComparisonRunResult(
        dataset_id="fixture",
        dataset_version="1",
        config=config,
        records=[asyncio.run(asyncio_run_fake_flow(item))],
    )

    lines = build_report_lines(record)

    assert any("hybrid_search_agent" in line for line in lines)


def test_report_lines_include_judge_diagnostics() -> None:
    """Text reports should expose judge noise and concentrated deltas."""

    config = ComparisonRunConfig(
        dataset_path=__file__,
        output_path=__file__,
        systems=[
            ComparisonSystem.BRANDMIND_AGENT,
            ComparisonSystem.HYBRID_SEARCH_AGENT,
        ],
    )
    result = ComparisonRunResult(
        dataset_id="fixture",
        dataset_version="1",
        config=config,
        records=[
            AnswerFlowRecord(
                item_id="BM5B-KOTLER-008",
                question="Question?",
                system=ComparisonSystem.BRANDMIND_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=False,
                    reasoning="Unsupported extra detail despite full coverage.",
                    covered_facts=["fact A", "fact B"],
                    missing_facts=[],
                    unsupported_claims=["extra detail"],
                ),
            ),
            AnswerFlowRecord(
                item_id="BM5B-KOTLER-008",
                question="Question?",
                system=ComparisonSystem.HYBRID_SEARCH_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=True,
                    reasoning="All facts covered.",
                    covered_facts=["fact A", "fact B"],
                    missing_facts=[],
                    unsupported_claims=["extra detail"],
                ),
            ),
            AnswerFlowRecord(
                item_id="BM5B-KOTLER-027",
                question="Question?",
                system=ComparisonSystem.BRANDMIND_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=False,
                    reasoning="Two facts missing.",
                    covered_facts=["fact A"],
                    missing_facts=["fact B", "fact C"],
                ),
            ),
            AnswerFlowRecord(
                item_id="BM5B-KOTLER-027",
                question="Question?",
                system=ComparisonSystem.HYBRID_SEARCH_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=True,
                    reasoning="All facts covered.",
                    covered_facts=["fact A", "fact B", "fact C"],
                    missing_facts=[],
                ),
            ),
        ],
    )

    lines = build_report_lines(result)

    assert any("Deterministic evaluator v2 views:" in line for line in lines)
    assert any(
        (
            "brandmind_agent: raw_correct=0.0%, fact_complete=50.0%, "
            "strict_supported=0.0%, judged=2"
        )
        in line
        for line in lines
    )
    assert any(
        (
            "hybrid_search_agent: raw_correct=100.0%, fact_complete=100.0%, "
            "strict_supported=50.0%, judged=2"
        )
        in line
        for line in lines
    )
    assert any(
        "brandmind_agent: coverage_1_false=1 [BM5B-KOTLER-008]" in line
        for line in lines
    )
    assert any(
        "hybrid_search_agent: coverage_1_false=0 [-]" in line
        and "unsupported_accepted=1 [BM5B-KOTLER-008]" in line
        for line in lines
    )
    assert any(
        "BM5B-KOTLER-027: delta=66.7%" in line
        and "leaders=hybrid_search_agent(100.0%)" in line
        for line in lines
    )


def test_report_lines_include_v2_stratified_diagnostics() -> None:
    """Text reports should break v2-hard results down by metadata dimensions."""

    config = ComparisonRunConfig(
        dataset_path=__file__,
        output_path=__file__,
        systems=[ComparisonSystem.BRANDMIND_AGENT],
    )
    result = ComparisonRunResult(
        dataset_id="fixture",
        dataset_version="1",
        config=config,
        records=[
            AnswerFlowRecord(
                item_id="BM5B-HARD-001",
                question="Question?",
                book_scope="cross_book",
                question_type="synthesis",
                difficulty="hard",
                reasoning_type="strategy_synthesis",
                required_source_count=4,
                system=ComparisonSystem.BRANDMIND_AGENT,
                final_answer="Answer",
                judge=AnswerJudgeResult(
                    is_correct=True,
                    reasoning="All facts covered.",
                    covered_facts=["fact A", "fact B"],
                    missing_facts=[],
                ),
            )
        ],
    )

    lines = build_report_lines(result)

    assert any("Stratified diagnostics:" in line for line in lines)
    assert any("- reasoning_type:" in line for line in lines)
    assert any("strategy_synthesis" in line for line in lines)
    assert any("- required_source_count:" in line for line in lines)
    assert any("Judge diagnostics:" in line for line in lines)


async def asyncio_run_fake_flow(item: BenchmarkItem):
    """Build one fake record for the report test."""

    flow = await run_direct_tool_answer_flow(
        item=item,
        system=ComparisonSystem.HYBRID_SEARCH_AGENT,
        search_tool=FakeSearchTool(),
        answer_client=FakeAnswerClient(),
        config=AgentRunnerConfig(top_k=5),
    )
    flow.judge = await AnswerKeyFactJudge().judge(
        item=item,
        candidate_answer=flow.final_answer,
    )
    return flow
