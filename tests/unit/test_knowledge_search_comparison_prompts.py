"""Unit tests for knowledge-search comparison prompt routing."""

from __future__ import annotations

import asyncio
import sys
import types
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.agents import (
    BRANDMIND_DOC_TOOL_DESCRIPTION,
    BRANDMIND_KG_RESULT_HINT,
    BRANDMIND_KG_TOOL_DESCRIPTION,
    HIPPORAG_TOOL_DESCRIPTION,
    HYBRID_SEARCH_TOOL_DESCRIPTION,
    NO_SEARCH_TOOL_ERROR,
    TOOL_BUDGET_EXHAUSTED_MESSAGE,
    AgentRunnerConfig,
    ToolCallBudget,
    build_brandmind_recovery_context,
    build_brandmind_recovery_system_prompt,
    build_document_search_attempts,
    create_langchain_agent,
    format_brandmind_kg_output,
    infer_source_filters_from_query,
    litellm_openai_base_url,
    question_requests_source_details,
    record_document_search_with_recovery,
    run_brandmind_agent,
    run_direct_tool_answer_flow,
    run_langchain_answer_flow,
    should_recover_brandmind_document_evidence,
)
from evaluation.knowledge_search_comparison.prompts import (
    build_answer_agent_system_prompt,
    build_judge_prompt,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonSystem,
    ToolTrace,
)
from tests.unit.test_knowledge_search_comparison_fake_flows import (
    FakeSearchTool,
    make_item,
)


def test_answer_agent_prompts_share_contract_but_differ_by_system() -> None:
    """Each compared system should receive its native tool-use guidance."""

    prompts = {
        system: build_answer_agent_system_prompt(system) for system in ComparisonSystem
    }

    assert all(
        "Write the final answer in Vietnamese." in text for text in prompts.values()
    )
    assert all("preserve the order" in text for text in prompts.values())
    assert all("named outputs" in text for text in prompts.values())
    assert all("bounded to the requested scope" in text for text in prompts.values())
    assert "knowledge graph" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "document-search" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "adaptive dual-retrieval" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "document-search first" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "KG-to-docs" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "use the graph as" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert "every named component" in prompts[ComparisonSystem.BRANDMIND_AGENT]
    assert (
        "single hybrid document-search tool"
        in prompts[ComparisonSystem.HYBRID_SEARCH_AGENT]
    )
    assert "native retriever output" in prompts[ComparisonSystem.HIPPORAG_AGENT]
    assert len(set(prompts.values())) == len(ComparisonSystem)


def test_judge_prompt_includes_hard_metadata_when_present() -> None:
    """V2-hard judge prompts should expose source dependencies to the judge."""

    item_payload = make_item().model_dump(mode="json")
    item = BenchmarkItem(
        **{
            **item_payload,
            "id": "BM5B-HARD-001",
            "required_sources": [
                "kotler_and_armstrong_principles_of_marketing::chunk_1",
                "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2",
            ],
            "book_scope": "cross_book",
            "difficulty": "hard",
            "question_type": "synthesis",
            "answer_key_facts": [
                "The answer must use source one.",
                "The answer must use source two.",
                "The answer must synthesize both sources.",
                "The answer must explain insufficiency.",
                "The answer must state the implication.",
            ],
            "reasoning_type": "strategy_synthesis",
            "single_source_sufficient": False,
            "answer_key_fact_sources": [
                {
                    "fact_index": 1,
                    "source_ids": [
                        "kotler_and_armstrong_principles_of_marketing::chunk_1"
                    ],
                    "role": "support",
                },
                {
                    "fact_index": 2,
                    "source_ids": [
                        "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2"
                    ],
                    "role": "support",
                },
                {
                    "fact_index": 3,
                    "source_ids": [
                        "kotler_and_armstrong_principles_of_marketing::chunk_1",
                        "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2",
                    ],
                    "role": "synthesis",
                },
                {
                    "fact_index": 4,
                    "source_ids": [
                        "kotler_and_armstrong_principles_of_marketing::chunk_1",
                        "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2",
                    ],
                    "role": "synthesis",
                },
            ],
        }
    )

    prompt = build_judge_prompt(item, candidate_answer="Candidate answer")

    assert "# Hard Multi-Hop Metadata" in prompt
    assert "reasoning_type: strategy_synthesis" in prompt
    assert "role=synthesis" in prompt


@pytest.mark.asyncio
async def test_direct_tool_flow_uses_system_specific_answer_prompt() -> None:
    """Fixture-friendly direct flows should not reuse one global prompt."""

    answer_client = CapturingAnswerClient()

    await run_direct_tool_answer_flow(
        item=make_item(),
        system=ComparisonSystem.HIPPORAG_AGENT,
        search_tool=FakeSearchTool(),
        answer_client=answer_client,
        config=AgentRunnerConfig(top_k=5),
    )

    assert answer_client.system_prompt is not None
    assert "HippoRAG" in answer_client.system_prompt
    assert "native retriever output" in answer_client.system_prompt


def test_langchain_agent_factory_uses_system_specific_answer_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live agent construction should pass the selected system prompt onward."""

    captured: dict[str, Any] = {}

    def fake_create_agent(
        *,
        model: Any,
        tools: list[Callable[..., Awaitable[str]]],
        system_prompt: str,
    ) -> object:
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        return object()

    monkeypatch.setitem(
        sys.modules,
        "langchain.agents",
        types.SimpleNamespace(create_agent=fake_create_agent),
    )
    monkeypatch.setitem(
        sys.modules,
        "langchain_google_genai",
        types.SimpleNamespace(ChatGoogleGenerativeAI=FakeChatGoogleGenerativeAI),
    )
    monkeypatch.setitem(
        sys.modules,
        "config.system_config",
        types.SimpleNamespace(SETTINGS=types.SimpleNamespace(GEMINI_API_KEY="test")),
    )

    async def fake_tool(query: str) -> str:
        return query

    create_langchain_agent(
        system=ComparisonSystem.BRANDMIND_AGENT,
        tools=[fake_tool],
        config=AgentRunnerConfig(top_k=5, max_tool_calls=3),
    )

    assert "knowledge graph" in captured["system_prompt"]
    assert "document-search" in captured["system_prompt"]
    assert "Use at most 3 tool calls" in captured["system_prompt"]
    assert captured["model"].kwargs["thinking_budget"] == 2000
    assert "thinking_level" not in captured["model"].kwargs
    assert captured["model"].kwargs["max_tokens"] == 8000


def test_langchain_agent_factory_uses_gemini3_thinking_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gemini 3 answer A/B should use thinking level, not 2.5 token budgets."""

    captured: dict[str, Any] = {}

    def fake_create_agent(
        *,
        model: Any,
        tools: list[Callable[..., Awaitable[str]]],
        system_prompt: str,
    ) -> object:
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        return object()

    monkeypatch.setitem(
        sys.modules,
        "langchain.agents",
        types.SimpleNamespace(create_agent=fake_create_agent),
    )
    monkeypatch.setitem(
        sys.modules,
        "langchain_google_genai",
        types.SimpleNamespace(ChatGoogleGenerativeAI=FakeChatGoogleGenerativeAI),
    )
    monkeypatch.setitem(
        sys.modules,
        "config.system_config",
        types.SimpleNamespace(SETTINGS=types.SimpleNamespace(GEMINI_API_KEY="test")),
    )

    async def fake_tool(query: str) -> str:
        return query

    create_langchain_agent(
        system=ComparisonSystem.BRANDMIND_AGENT,
        tools=[fake_tool],
        config=AgentRunnerConfig(
            answer_model="gemini-3.1-flash-lite",
            temperature=1.0,
            thinking_level="medium",
        ),
    )

    assert captured["model"].kwargs["model"] == "gemini-3.1-flash-lite"
    assert captured["model"].kwargs["temperature"] == 1.0
    assert captured["model"].kwargs["thinking_level"] == "medium"
    assert "thinking_budget" not in captured["model"].kwargs


def test_langchain_agent_factory_uses_litellm_openai_compatible_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GPT answer A/B should route through LiteLLM's OpenAI-compatible API."""

    captured: dict[str, Any] = {}

    def fake_create_agent(
        *,
        model: Any,
        tools: list[Callable[..., Awaitable[str]]],
        system_prompt: str,
    ) -> object:
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        return object()

    monkeypatch.setitem(
        sys.modules,
        "langchain.agents",
        types.SimpleNamespace(create_agent=fake_create_agent),
    )
    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI),
    )
    monkeypatch.setitem(
        sys.modules,
        "config.system_config",
        types.SimpleNamespace(
            SETTINGS=types.SimpleNamespace(
                GEMINI_API_KEY="test-gemini",
                LITELLM_API_KEY="test-litellm",
                LITELLM_PROXY_URL="http://localhost:4000",
            )
        ),
    )

    async def fake_tool(query: str) -> str:
        return query

    create_langchain_agent(
        system=ComparisonSystem.BRANDMIND_AGENT,
        tools=[fake_tool],
        config=AgentRunnerConfig(
            answer_provider="litellm",
            answer_model="gpt-5.4-mini",
            temperature=0.2,
            thinking_budget=None,
            thinking_level="medium",
        ),
    )

    assert captured["model"].kwargs["model"] == "gpt-5.4-mini"
    assert captured["model"].kwargs["base_url"] == "http://localhost:4000/v1"
    assert captured["model"].kwargs["temperature"] == 0.2
    assert captured["model"].kwargs["max_completion_tokens"] == 8000
    assert captured["model"].kwargs["reasoning_effort"] == "medium"


def test_litellm_openai_base_url_normalizes_proxy_root() -> None:
    """LiteLLM proxy URLs should point ChatOpenAI at the OpenAI-compatible path."""

    assert litellm_openai_base_url("http://localhost:4000") == (
        "http://localhost:4000/v1"
    )
    assert litellm_openai_base_url("http://localhost:4000/v1") == (
        "http://localhost:4000/v1"
    )


def test_tool_descriptions_include_routing_guidance() -> None:
    """Tool descriptions should carry routing guidance, not API docs only."""

    descriptions = [
        BRANDMIND_KG_TOOL_DESCRIPTION,
        BRANDMIND_DOC_TOOL_DESCRIPTION,
        HYBRID_SEARCH_TOOL_DESCRIPTION,
        HIPPORAG_TOOL_DESCRIPTION,
    ]

    assert all("Use when" in description for description in descriptions)
    assert all("Do not use" in description for description in descriptions)
    assert all("Returns" in description for description in descriptions)
    assert "source routing" in BRANDMIND_KG_TOOL_DESCRIPTION
    assert "question anchor" in BRANDMIND_KG_TOOL_DESCRIPTION
    assert "exact chapter" in BRANDMIND_DOC_TOOL_DESCRIPTION
    assert "source_chunk_id" in BRANDMIND_DOC_TOOL_DESCRIPTION
    assert "focused searches for missing anchors" in BRANDMIND_DOC_TOOL_DESCRIPTION
    assert "native HippoRAG" in HIPPORAG_TOOL_DESCRIPTION


def test_brandmind_kg_output_adds_next_action_hint() -> None:
    """KG outputs should carry a compact docs-next hint for small answer models."""

    output = format_brandmind_kg_output(
        "## Retrieved Knowledge from Knowledge Graph\nGraph evidence"
    )

    assert output.startswith("Context hint: KG search is a conceptual map")
    assert BRANDMIND_KG_RESULT_HINT in output
    assert "document search next" in output
    assert "Retrieved Knowledge" in output


def test_document_search_attempts_recover_brittle_source_filters() -> None:
    """Filtered doc calls should plan normalized and broad retries."""

    attempts = build_document_search_attempts(
        query="sự khác biệt giữa bán hàng cá nhân và khuyến mãi bán hàng",
        top_k=5,
        filter_by_book="Kotler & Armstrong",
        filter_by_chapter="Chương 16",
    )

    assert [
        (attempt.filter_by_book, attempt.filter_by_chapter, attempt.reason)
        for attempt in attempts
    ] == [
        ("Kotler & Armstrong", "Chương 16", "original"),
        (
            "Principles of Marketing 17th Edition",
            "Chapter 16",
            "normalized_filters",
        ),
        (None, "Chapter 16", "chapter_scope_after_empty_book_filter"),
        (
            "Principles of Marketing 17th Edition",
            None,
            "book_scope_after_empty_chapter_filter",
        ),
        (None, None, "broadened_after_empty_filters"),
    ]


def test_source_filters_can_be_inferred_from_clear_query_hints() -> None:
    """BrandMind doc calls should recover source scope when agents omit params."""

    assert infer_source_filters_from_query(
        query=(
            "quy trình thiết kế chiến lược marketing theo chương 7 "
            "của Kotler & Armstrong"
        ),
        filter_by_book=None,
        filter_by_chapter=None,
    ) == ("Principles of Marketing 17th Edition", "Chapter 7")


def test_explicit_source_filters_take_precedence_over_query_hints() -> None:
    """Explicit agent filters should not be overwritten by lexical hints."""

    assert infer_source_filters_from_query(
        query="chapter 7 Kotler & Armstrong",
        filter_by_book="Positioning",
        filter_by_chapter="Chapter 10",
    ) == ("Positioning", "Chapter 10")


def test_brandmind_recovery_predicate_targets_kg_only_detail_answers() -> None:
    """Docs recovery should target KG-only answers to source-detail questions."""

    kg_only_record = make_brandmind_record(
        tool_traces=[ToolTrace(tool_name="search_knowledge_graph", query="FTC FDA")]
    )
    docs_record = make_brandmind_record(
        tool_traces=[
            ToolTrace(tool_name="search_knowledge_graph", query="FTC FDA"),
            ToolTrace(tool_name="search_document_library", query="FTC FDA"),
        ]
    )

    assert should_recover_brandmind_document_evidence(
        question="Nếu một công ty tại Hoa Kỳ, tại sao FTC/FDA tác động marketing?",
        record=kg_only_record,
        enabled=True,
    )
    assert not should_recover_brandmind_document_evidence(
        question="Explain brand salience.",
        record=kg_only_record,
        enabled=True,
    )
    assert not should_recover_brandmind_document_evidence(
        question="Theo chương 12, biện pháp cụ thể nào?",
        record=docs_record,
        enabled=True,
    )
    assert not should_recover_brandmind_document_evidence(
        question="Theo chương 12, biện pháp cụ thể nào?",
        record=kg_only_record,
        enabled=False,
    )


def test_brandmind_recovery_prompt_prioritizes_recovered_documents() -> None:
    """Recovery context should make the document evidence the primary context."""

    assert question_requests_source_details(
        'Khái niệm "good-value pricing" được định nghĩa như thế nào?'
    )
    context = build_brandmind_recovery_context(
        prior_answer="Prior KG draft",
        recovered_context="Document evidence",
    )
    prompt = build_brandmind_recovery_system_prompt()

    assert context.index("Document evidence") < context.index("Prior KG draft")
    assert "recovered document evidence as the primary source" in prompt
    assert "Remove claims that are not supported" in prompt


@pytest.mark.asyncio
async def test_brandmind_evidence_recovery_runs_after_kg_only_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Optional recovery should add one docs call and rewrite KG-only answers."""

    import shared.agent_tools.retrieval as retrieval_tools

    async def fake_kg_search(query: str, max_results: int) -> str:
        return f"KG query={query}; max_results={max_results}"

    async def fake_doc_search(**kwargs: Any) -> str:
        return f"Document evidence for {kwargs['query']}"

    def fake_create_agent(
        *,
        system: ComparisonSystem,
        tools: list[Callable[..., Awaitable[str]]],
        config: AgentRunnerConfig,
    ) -> object:
        del system, config

        class KgOnlyAgent:
            async def ainvoke(
                self,
                *_args: Any,
                **_kwargs: Any,
            ) -> dict[str, list[Any]]:
                await tools[0]("FTC FDA impact on marketing performance USA")
                return {"messages": [types.SimpleNamespace(content="KG-only draft")]}

        return KgOnlyAgent()

    class FakeRecoveryClient:
        def __init__(self, config: AgentRunnerConfig) -> None:
            self.config = config

        async def answer(
            self,
            *,
            question: str,
            context: str,
            system_prompt: str,
        ) -> str:
            assert "Document evidence" in context
            assert "KG-only draft" in context
            assert "Evidence Recovery" in system_prompt
            return f"Recovered answer for {question}"

    monkeypatch.setattr(retrieval_tools, "search_knowledge_graph", fake_kg_search)
    monkeypatch.setattr(retrieval_tools, "search_document_library", fake_doc_search)
    monkeypatch.setattr(
        "evaluation.knowledge_search_comparison.agents.create_langchain_agent",
        fake_create_agent,
    )
    monkeypatch.setattr(
        "evaluation.knowledge_search_comparison.agents.create_answer_text_client",
        lambda config: FakeRecoveryClient(config),
    )

    item = make_item()
    item.question = "Nếu một công ty tại Hoa Kỳ, tại sao FTC/FDA tác động marketing?"
    record = await run_brandmind_agent(
        item=item,
        config=AgentRunnerConfig(
            top_k=5,
            max_tool_calls=3,
            brandmind_evidence_recovery=True,
        ),
    )

    assert record.final_answer.startswith("Recovered answer")
    assert [trace.tool_name for trace in record.tool_traces] == [
        "search_knowledge_graph",
        "search_document_library",
    ]


@pytest.mark.asyncio
async def test_document_search_recovery_retries_until_results() -> None:
    """BrandMind doc wrapper should not strand the agent on empty filters."""

    traces: list[ToolTrace] = []
    calls: list[tuple[str | None, str | None]] = []

    async def fake_search(attempt: Any) -> str:
        calls.append((attempt.filter_by_book, attempt.filter_by_chapter))
        if attempt.reason != "broadened_after_empty_filters":
            return "No results found."
        return "[1] Source: Chapter 16\n    Content: supported passage"

    output = await record_document_search_with_recovery(
        traces=traces,
        query="bán hàng cá nhân",
        top_k=5,
        filter_by_book="Unknown translated title",
        filter_by_chapter="Chương 16",
        call=fake_search,
    )

    assert calls == [
        ("Unknown translated title", "Chương 16"),
        ("Unknown translated title", "Chapter 16"),
        (None, "Chapter 16"),
        ("Unknown translated title", None),
        (None, None),
    ]
    assert len(traces) == 5
    assert "broadened_after_empty_filters" in output
    assert "supported passage" in output


@pytest.mark.asyncio
async def test_document_search_recovery_respects_tool_budget() -> None:
    """Internal recovery attempts should not bypass the benchmark tool budget."""

    traces: list[ToolTrace] = []
    calls: list[tuple[str | None, str | None]] = []

    async def fake_search(attempt: Any) -> str:
        calls.append((attempt.filter_by_book, attempt.filter_by_chapter))
        return "No results found."

    output = await record_document_search_with_recovery(
        traces=traces,
        query="bán hàng cá nhân",
        top_k=5,
        filter_by_book="Kotler & Armstrong",
        filter_by_chapter="Chương 16",
        call=fake_search,
        max_tool_calls=2,
    )

    assert calls == [
        ("Kotler & Armstrong", "Chương 16"),
        ("Principles of Marketing 17th Edition", "Chapter 16"),
    ]
    assert len(traces) == 2
    assert TOOL_BUDGET_EXHAUSTED_MESSAGE in output


@pytest.mark.asyncio
async def test_tool_call_budget_is_concurrency_safe() -> None:
    """Parallel tool calls should not reserve more live attempts than allowed."""

    budget = ToolCallBudget(max_calls=2)

    reservations = await asyncio.gather(*(budget.reserve() for _ in range(5)))

    assert reservations.count(True) == 2
    assert reservations.count(False) == 3


@pytest.mark.asyncio
async def test_langchain_flow_flags_answers_without_search_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Answer-flow records are invalid when the agent skips retrieval."""

    class NoToolAgent:
        async def ainvoke(self, *_args: Any, **_kwargs: Any) -> dict[str, list[Any]]:
            return {"messages": [types.SimpleNamespace(content="Unsupported answer")]}

    monkeypatch.setattr(
        "evaluation.knowledge_search_comparison.agents.create_langchain_agent",
        lambda **_kwargs: NoToolAgent(),
    )

    record = await run_langchain_answer_flow(
        item=make_item(),
        system=ComparisonSystem.HYBRID_SEARCH_AGENT,
        tools=[],
        traces=[],
        config=AgentRunnerConfig(top_k=5),
    )

    assert record.final_answer == "Unsupported answer"
    assert record.error == NO_SEARCH_TOOL_ERROR
    assert record.tool_traces == []


class CapturingAnswerClient:
    """Answer client test double that records the supplied system prompt."""

    def __init__(self) -> None:
        self.system_prompt: str | None = None

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Record prompt input and return a deterministic answer."""

        self.system_prompt = system_prompt
        return f"{question}\n{context}"


def make_brandmind_record(
    *,
    tool_traces: list[ToolTrace],
    error: str | None = None,
) -> AnswerFlowRecord:
    """Create a minimal BrandMind answer-flow record for recovery tests."""

    return AnswerFlowRecord(
        item_id="BM5B-KOTLER-001",
        question="Question?",
        system=ComparisonSystem.BRANDMIND_AGENT,
        final_answer="Answer",
        tool_traces=tool_traces,
        error=error,
    )


class FakeChatGoogleGenerativeAI:
    """LangChain model test double that captures construction kwargs."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class FakeChatOpenAI:
    """LangChain OpenAI-compatible model test double."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
