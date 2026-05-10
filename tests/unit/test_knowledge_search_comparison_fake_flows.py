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
