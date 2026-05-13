"""Answer-flow agent wrappers for the knowledge-search comparison benchmark."""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, SecretStr

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.prompts import (
    build_answer_agent_system_prompt,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonSystem,
    ReasoningLevel,
    ToolTrace,
)
from evaluation.knowledge_search_comparison.source_mapping import SourceMapping

NO_SEARCH_TOOL_ERROR = "No search tool was called before the final answer."
DOC_SEARCH_NO_RESULTS = "No results found."
TOOL_BUDGET_EXHAUSTED_MESSAGE = (
    "Tool budget exhausted. Use the evidence already retrieved and write the "
    "final answer now; do not call another search tool."
)
BRANDMIND_KG_RESULT_HINT = "\n".join(
    [
        "Context hint: KG search is a conceptual map, not final proof.",
        (
            "For multi-part questions that combine several named concepts, "
            "frameworks, books, mechanisms, examples, or source-specific "
            "conditions, use document search next for the major anchors that "
            "are only summarized or missing here."
        ),
        (
            "A KG-only answer is appropriate only when this result explicitly "
            "contains every named component needed for the final answer. "
            "Otherwise, search the document library with the missing anchor "
            "terms and any source hints from this result."
        ),
    ]
)

BOOK_FILTER_ALIASES = {
    "armstrong": "Principles of Marketing 17th Edition",
    "byron sharp": "How Brands Grow: What Marketers Don't Know",
    "cialdini": "Influence: The Psychology of Persuasion (New and Expanded Edition)",
    "how brands grow": "How Brands Grow: What Marketers Don't Know",
    "influence": "Influence: The Psychology of Persuasion (New and Expanded Edition)",
    "keller": (
        "Strategic Brand Management: Building, Measuring, and Managing Brand Equity"
    ),
    "kotler": "Principles of Marketing 17th Edition",
    "kotler & armstrong": "Principles of Marketing 17th Edition",
    "kotler and armstrong": "Principles of Marketing 17th Edition",
    "positioning": "Positioning: The Battle for Your Mind",
    "principles of marketing": "Principles of Marketing 17th Edition",
    "strategic brand management": (
        "Strategic Brand Management: Building, Measuring, and Managing Brand Equity"
    ),
}

SOURCE_HINT_BOOK_ALIASES = {
    "byron sharp": "How Brands Grow: What Marketers Don't Know",
    "cialdini": "Influence: The Psychology of Persuasion (New and Expanded Edition)",
    "how brands grow": "How Brands Grow: What Marketers Don't Know",
    "influence": "Influence: The Psychology of Persuasion (New and Expanded Edition)",
    "keller": (
        "Strategic Brand Management: Building, Measuring, and Managing Brand Equity"
    ),
    "kotler & armstrong": "Principles of Marketing 17th Edition",
    "kotler and armstrong": "Principles of Marketing 17th Edition",
    "positioning": "Positioning: The Battle for Your Mind",
    "principles of marketing": "Principles of Marketing 17th Edition",
    "strategic brand management": (
        "Strategic Brand Management: Building, Measuring, and Managing Brand Equity"
    ),
}

BRANDMIND_KG_TOOL_DESCRIPTION = "\n".join(
    [
        "Search BrandMind's knowledge graph for conceptual marketing knowledge.",
        (
            "Use when the question needs framework selection, concept mapping, "
            "relationship reasoning, mechanism tracing, multi-hop links, or "
            "source routing before deeper reading."
        ),
        (
            "Do not use as final evidence for exact passages, caveats, named "
            "examples, author wording, or source-specific conditions; pair the "
            "graph lead with document search when those details matter."
        ),
        (
            "After reading the graph result, use document search for any "
            "question anchor that is only implied or summarized by the graph, "
            "especially in combine/compare/diagnose/application questions."
        ),
        (
            "Returns entities, relationship paths, verbalized facts, and "
            "source metadata; query should be abstract and relational, for "
            'example "brand positioning and differentiation relationship".'
        ),
    ]
)

BRANDMIND_DOC_TOOL_DESCRIPTION = "\n".join(
    [
        (
            "Search BrandMind's document library for original source passages "
            "from the indexed marketing books."
        ),
        (
            "Use when the answer needs exact chapter evidence, examples, "
            "caveats, author wording, lists, conditions, or verification of a "
            "knowledge-graph lead. Also use it for mechanisms or comparisons "
            "where precise source facts affect answer quality."
        ),
        (
            "Use source_chunk_id for exact verification of a KG fact; use "
            "book/chapter filters for scoped exploration of neighboring "
            "passages in the same source area. Do not use vague global "
            "keywords when KG metadata or the question gives a precise source "
            "scope."
        ),
        (
            "For distributed questions, run focused searches for missing "
            "anchors rather than one broad generic search. Query with the "
            "specific concept pair, example, principle, or source clue that "
            "the current evidence has not yet grounded."
        ),
        (
            "Returns ranked passages with source, book, and content preview; "
            "query should be specific and lexical, for example "
            '"rejection-then-retreat concession pressure".'
        ),
    ]
)

HYBRID_SEARCH_TOOL_DESCRIPTION = "\n".join(
    [
        (
            "Search the hybrid document index for marketing-book passages "
            "using the single-tool baseline retriever."
        ),
        (
            "Use when any definition, mechanism, example, comparison, or "
            "application needs source evidence from the five-book corpus."
        ),
        (
            "Do not use general marketing knowledge as a substitute for this "
            "tool; if the first result is thin, reformulate once with exact "
            "terms or named source clues."
        ),
        "Returns ranked passages with source, book, and content preview.",
    ]
)

HIPPORAG_TOOL_DESCRIPTION = "\n".join(
    [
        "Search native HippoRAG retriever output over the five-book corpus.",
        (
            "Use when the answer needs passages, source metadata, and "
            "retriever scores from HippoRAG's own retrieval behavior."
        ),
        (
            "Do not use this as a generated QA answer, and do not call or "
            "emulate HippoRAG's full QA mode."
        ),
        (
            "Returns native HippoRAG retrieval text that may include chunks, "
            "scores, and mapped source metadata."
        ),
    ]
)


class AgentRunnerConfig(BaseModel):
    """Runtime settings shared across answer-flow agents."""

    answer_provider: Literal["gemini", "litellm"] = "gemini"
    answer_model: str = "gemini-2.5-flash-lite"
    top_k: int = Field(default=5, gt=0)
    candidate_top_k: int = Field(default=10, gt=0)
    max_tool_calls: int = Field(default=4, gt=0)
    recursion_limit: int = Field(default=60, gt=0)
    temperature: float = 0.1
    thinking_budget: int | None = 2000
    thinking_level: ReasoningLevel | None = None
    brandmind_evidence_recovery: bool = False
    max_output_tokens: int = 8000
    api_key: str | None = None


class DocumentSearchAttempt(BaseModel):
    """One concrete document-search call after filter recovery planning."""

    query: str
    top_k: int
    filter_by_book: str | None = None
    filter_by_chapter: str | None = None
    reason: str


class ToolCallBudget:
    """Concurrency-safe budget for live retrieval attempts in one agent run."""

    def __init__(self, max_calls: int | None) -> None:
        self.max_calls = max_calls
        self.used_calls = 0
        self._lock = asyncio.Lock()

    async def reserve(self) -> bool:
        """Reserve one retrieval attempt if the run still has budget."""

        async with self._lock:
            if self.max_calls is not None and self.used_calls >= self.max_calls:
                return False
            self.used_calls += 1
            return True


class TextSearchTool(Protocol):
    """Protocol for fake or live text search tools used in direct flows."""

    async def __call__(self, *, query: str, top_k: int) -> str:
        """Return context text for a query."""


class AnswerTextClient(Protocol):
    """Protocol for LLM clients that synthesize final answers from context."""

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Return a final benchmark answer."""


class GeminiAnswerTextClient:
    """Gemini answer client for direct single-tool answer flows."""

    def __init__(self, config: AgentRunnerConfig) -> None:
        """Store runtime config without initializing network clients eagerly."""

        self.config = config

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Generate a final answer from retrieved context."""

        from config.system_config import SETTINGS
        from shared.model_clients.llm.google import (
            GoogleAIClientLLM,
            GoogleAIClientLLMConfig,
        )

        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model=self.config.answer_model,
                api_key=self.config.api_key or SETTINGS.GEMINI_API_KEY,
                system_instruction=system_prompt,
                temperature=self.config.temperature,
                **build_google_thinking_kwargs(self.config),
                max_tokens=self.config.max_output_tokens,
            )
        )
        response = await llm.acomplete(
            "# Retrieved Context\n\n"
            f"{context}\n\n"
            "# User Question\n\n"
            f"{question}\n\n"
            "Answer the question using the retrieved context."
        )
        return response.text


class LiteLLMAnswerTextClient:
    """OpenAI-compatible LiteLLM answer client for direct answer flows."""

    def __init__(self, config: AgentRunnerConfig) -> None:
        """Store runtime config without initializing network clients eagerly."""

        self.config = config

    async def answer(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str:
        """Generate a final answer from retrieved context through LiteLLM."""

        from openai import AsyncOpenAI

        from config.system_config import SETTINGS

        api_key = self.config.api_key or SETTINGS.LITELLM_API_KEY
        if not api_key:
            raise ValueError("LiteLLM answer provider requires LITELLM_API_KEY.")

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=litellm_openai_base_url(SETTINGS.LITELLM_PROXY_URL),
        )
        request: dict[str, Any] = {
            "model": self.config.answer_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "# Retrieved Context\n\n"
                        f"{context}\n\n"
                        "# User Question\n\n"
                        f"{question}\n\n"
                        "Answer the question using the retrieved context."
                    ),
                },
            ],
            "temperature": self.config.temperature,
            "max_completion_tokens": self.config.max_output_tokens,
        }
        if self.config.thinking_level:
            request["reasoning_effort"] = self.config.thinking_level
        response = await client.chat.completions.create(**request)
        return response.choices[0].message.content or ""


def create_answer_text_client(config: AgentRunnerConfig) -> AnswerTextClient:
    """Create the direct answer client that matches the configured provider."""

    if config.answer_provider == "litellm":
        return LiteLLMAnswerTextClient(config)
    return GeminiAnswerTextClient(config)


async def run_direct_tool_answer_flow(
    *,
    item: BenchmarkItem,
    system: ComparisonSystem,
    search_tool: TextSearchTool,
    answer_client: AnswerTextClient,
    config: AgentRunnerConfig,
    source_mapping: SourceMapping | None = None,
) -> AnswerFlowRecord:
    """Run a fixture-friendly answer flow with one explicit search call.

    This helper is for smoke tests and simple single-tool conditions. The
    live BrandMind condition uses ``run_brandmind_agent`` so tool choice remains
    autonomous.
    """

    started = time.perf_counter()
    trace: ToolTrace | None = None
    try:
        tool_started = time.perf_counter()
        context = await search_tool(query=item.question, top_k=config.top_k)
        trace = ToolTrace(
            tool_name=f"{system.value}_search",
            query=item.question,
            output_preview=context[:1200],
            source_ids=(
                source_mapping.source_ids_in_text(context)
                if source_mapping is not None
                else []
            ),
            latency_ms=elapsed_ms(tool_started),
        )
        answer = await answer_client.answer(
            question=item.question,
            context=context,
            system_prompt=build_answer_agent_system_prompt(system),
        )
        return AnswerFlowRecord(
            item_id=item.id,
            question=item.question,
            system=system,
            final_answer=answer,
            tool_traces=[trace],
            latency_ms=elapsed_ms(started),
        )
    except Exception as exc:
        traces = [trace] if trace is not None else []
        return AnswerFlowRecord(
            item_id=item.id,
            question=item.question,
            system=system,
            final_answer="",
            tool_traces=traces,
            latency_ms=elapsed_ms(started),
            error=str(exc),
        )


async def run_brandmind_agent(
    *,
    item: BenchmarkItem,
    config: AgentRunnerConfig,
    source_mapping: SourceMapping | None = None,
) -> AnswerFlowRecord:
    """Run BrandMind as an autonomous KG-plus-docs tool answer flow."""

    from shared.agent_tools.retrieval import (  # noqa: PLC0415
        search_document_library,
        search_knowledge_graph,
    )

    traces: list[ToolTrace] = []
    tool_budget = ToolCallBudget(config.max_tool_calls)

    async def search_knowledge_graph_tool(query: str) -> str:
        """Search BrandMind's knowledge graph for concepts and source pointers.

        Use this to orient a question, identify related concepts, or discover where
        source evidence may live. Do not treat graph summaries as enough for exact
        named examples, people, years, lists, or source-specific wording when the
        document library tool is also available.
        """

        if not await tool_budget.reserve():
            return TOOL_BUDGET_EXHAUSTED_MESSAGE

        async def call_kg() -> str:
            output = await search_knowledge_graph(
                query=query,
                max_results=config.candidate_top_k,
            )
            return format_brandmind_kg_output(output)

        return await record_text_tool_call(
            traces=traces,
            tool_name="search_knowledge_graph",
            query=query,
            source_mapping=source_mapping,
            call=call_kg,
        )

    async def search_document_library_tool(
        query: str,
        top_k: int = config.candidate_top_k,
        filter_by_book: str | None = None,
        filter_by_chapter: str | None = None,
        source_chunk_id: str | None = None,
    ) -> str:
        """Search BrandMind's document library for exact source passages.

        Use this when a question needs exact details, examples, named people,
        lists, or wording from the books, and to verify knowledge-graph findings.
        If the knowledge graph output provides a ``source_chunk_id``, pass it
        through to read that exact source chunk.
        Use ``filter_by_book`` or ``filter_by_chapter`` only when the question or
        prior tool output gives an exact source label; otherwise omit filters and
        search broadly with the key terms.
        """

        if source_chunk_id:
            if not await tool_budget.reserve():
                return TOOL_BUDGET_EXHAUSTED_MESSAGE
            tool_query = format_tool_query(query=query)
            return await record_text_tool_call(
                traces=traces,
                tool_name="search_document_library",
                query=f"{tool_query} (source_chunk_id={source_chunk_id})",
                source_mapping=source_mapping,
                call=lambda: search_document_library(
                    query=query,
                    top_k=min(top_k, config.candidate_top_k),
                    source_chunk_id=source_chunk_id,
                ),
            )

        return await record_document_search_with_recovery(
            traces=traces,
            query=query,
            top_k=min(top_k, config.candidate_top_k),
            filter_by_book=filter_by_book,
            filter_by_chapter=filter_by_chapter,
            source_mapping=source_mapping,
            tool_budget=tool_budget,
            call=lambda attempt: search_document_library(
                query=query,
                top_k=attempt.top_k,
                filter_by_book=attempt.filter_by_book,
                filter_by_chapter=attempt.filter_by_chapter,
            ),
        )

    search_knowledge_graph_tool.__doc__ = BRANDMIND_KG_TOOL_DESCRIPTION
    search_document_library_tool.__doc__ = BRANDMIND_DOC_TOOL_DESCRIPTION

    record = await run_langchain_answer_flow(
        item=item,
        system=ComparisonSystem.BRANDMIND_AGENT,
        tools=[search_knowledge_graph_tool, search_document_library_tool],
        traces=traces,
        config=config,
    )
    if should_recover_brandmind_document_evidence(
        question=item.question,
        record=record,
        enabled=config.brandmind_evidence_recovery,
    ):
        recovery_started = time.perf_counter()
        recovered_context = await search_document_library_tool(
            query=build_brandmind_recovery_query(item.question),
            top_k=config.candidate_top_k,
        )
        record.tool_traces = traces
        if is_recovered_document_context_usable(recovered_context):
            record.final_answer = await create_answer_text_client(config).answer(
                question=item.question,
                context=build_brandmind_recovery_context(
                    prior_answer=record.final_answer,
                    recovered_context=recovered_context,
                ),
                system_prompt=build_brandmind_recovery_system_prompt(),
            )
            record.latency_ms += elapsed_ms(recovery_started)
    return record


async def run_hybrid_search_agent(
    *,
    item: BenchmarkItem,
    config: AgentRunnerConfig,
    source_mapping: SourceMapping | None = None,
) -> AnswerFlowRecord:
    """Run the single-tool hybrid-search condition as an answer-flow agent."""

    from shared.agent_tools.retrieval import search_document_library  # noqa: PLC0415

    traces: list[ToolTrace] = []
    tool_budget = ToolCallBudget(config.max_tool_calls)

    async def search_hybrid_marketing_knowledge(query: str) -> str:
        """Search the hybrid document index for exact marketing source passages.

        Use this as the single available evidence source for definitions,
        mechanisms, examples, comparisons, and applications from the five-book
        corpus. If the first query is thin, reformulate once with the question's
        exact terms or named source clues instead of adding generic marketing
        theory.
        """

        if not await tool_budget.reserve():
            return TOOL_BUDGET_EXHAUSTED_MESSAGE
        return await record_text_tool_call(
            traces=traces,
            tool_name="search_hybrid_marketing_knowledge",
            query=query,
            source_mapping=source_mapping,
            call=lambda: search_document_library(
                query=query,
                top_k=config.candidate_top_k,
            ),
        )

    search_hybrid_marketing_knowledge.__doc__ = HYBRID_SEARCH_TOOL_DESCRIPTION

    return await run_langchain_answer_flow(
        item=item,
        system=ComparisonSystem.HYBRID_SEARCH_AGENT,
        tools=[search_hybrid_marketing_knowledge],
        traces=traces,
        config=config,
    )


async def run_hipporag_agent(
    *,
    item: BenchmarkItem,
    hipporag_search: TextSearchTool,
    config: AgentRunnerConfig,
    source_mapping: SourceMapping | None = None,
) -> AnswerFlowRecord:
    """Run HippoRAG native retrieval as a single search-tool answer flow."""

    traces: list[ToolTrace] = []
    tool_budget = ToolCallBudget(config.max_tool_calls)

    async def search_hipporag(query: str) -> str:
        """Search HippoRAG native retriever output over the five-book corpus.

        Use this as the single available evidence source for definitions,
        mechanisms, examples, comparisons, and applications. The output may mix
        passages, scores, and source metadata; ground the final answer in the
        retrieved passages and source labels.
        """

        if not await tool_budget.reserve():
            return TOOL_BUDGET_EXHAUSTED_MESSAGE
        return await record_text_tool_call(
            traces=traces,
            tool_name="search_hipporag",
            query=query,
            source_mapping=source_mapping,
            call=lambda: hipporag_search(query=query, top_k=config.top_k),
        )

    search_hipporag.__doc__ = HIPPORAG_TOOL_DESCRIPTION

    return await run_langchain_answer_flow(
        item=item,
        system=ComparisonSystem.HIPPORAG_AGENT,
        tools=[search_hipporag],
        traces=traces,
        config=config,
    )


async def run_langchain_answer_flow(
    *,
    item: BenchmarkItem,
    system: ComparisonSystem,
    tools: list[Callable[..., Awaitable[str]]],
    traces: list[ToolTrace],
    config: AgentRunnerConfig,
) -> AnswerFlowRecord:
    """Run a LangChain tool-calling agent and capture the final answer."""

    started = time.perf_counter()
    try:
        agent = create_langchain_agent(system=system, tools=tools, config=config)
        from langchain_core.messages import HumanMessage  # noqa: PLC0415

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=item.question)]},
            {"recursion_limit": config.recursion_limit},
        )
        record = AnswerFlowRecord(
            item_id=item.id,
            question=item.question,
            system=system,
            final_answer=extract_final_text(result),
            tool_traces=traces,
            latency_ms=elapsed_ms(started),
        )
        if not record.tool_traces:
            record.error = NO_SEARCH_TOOL_ERROR
        return record
    except Exception as exc:
        return AnswerFlowRecord(
            item_id=item.id,
            question=item.question,
            system=system,
            final_answer="",
            tool_traces=traces,
            latency_ms=elapsed_ms(started),
            error=str(exc),
        )


def create_langchain_agent(
    *,
    system: ComparisonSystem,
    tools: list[Callable[..., Awaitable[str]]],
    config: AgentRunnerConfig,
) -> Any:
    """Create a LangChain agent with the system-specific answer prompt."""

    from langchain.agents import create_agent

    tool_budget_prompt = (
        f"\n\n# Tool Budget\nUse at most {config.max_tool_calls} tool calls "
        "unless the retrieved evidence is clearly insufficient."
    )
    return create_agent(
        model=create_answer_chat_model(config),
        tools=tools,
        system_prompt=build_answer_agent_system_prompt(system) + tool_budget_prompt,
    )


def create_answer_chat_model(config: AgentRunnerConfig) -> Any:
    """Create the LangChain chat model for the configured answer provider."""

    if config.answer_provider == "litellm":
        return create_litellm_chat_model(config)
    return create_gemini_chat_model(config)


def create_gemini_chat_model(config: AgentRunnerConfig) -> Any:
    """Create the native Gemini LangChain chat model."""

    from langchain_google_genai import ChatGoogleGenerativeAI

    from config.system_config import SETTINGS

    return ChatGoogleGenerativeAI(
        google_api_key=config.api_key or SETTINGS.GEMINI_API_KEY,
        model=config.answer_model,
        temperature=config.temperature,
        max_tokens=config.max_output_tokens,
        **build_google_thinking_kwargs(config),
    )


def create_litellm_chat_model(config: AgentRunnerConfig) -> Any:
    """Create an OpenAI-compatible LangChain chat model backed by LiteLLM."""

    from langchain_openai import ChatOpenAI

    from config.system_config import SETTINGS

    api_key = config.api_key or SETTINGS.LITELLM_API_KEY
    if not api_key:
        raise ValueError("LiteLLM answer provider requires LITELLM_API_KEY.")

    return ChatOpenAI(
        model=config.answer_model,
        api_key=SecretStr(api_key),
        base_url=litellm_openai_base_url(SETTINGS.LITELLM_PROXY_URL),
        temperature=config.temperature,
        max_completion_tokens=config.max_output_tokens,
        reasoning_effort=config.thinking_level,
    )


async def record_document_search_with_recovery(
    *,
    traces: list[ToolTrace],
    query: str,
    top_k: int,
    filter_by_book: str | None,
    filter_by_chapter: str | None,
    call: Callable[[DocumentSearchAttempt], Awaitable[str]],
    source_mapping: SourceMapping | None = None,
    max_tool_calls: int | None = None,
    tool_budget: ToolCallBudget | None = None,
) -> str:
    """Search documents and recover when brittle source filters return no results."""

    attempt_outputs: list[tuple[DocumentSearchAttempt, str]] = []
    if tool_budget is None and max_tool_calls is not None:
        tool_budget = ToolCallBudget(max_tool_calls)
    source_scope = infer_source_filters_from_query(
        query=query,
        filter_by_book=filter_by_book,
        filter_by_chapter=filter_by_chapter,
    )
    attempts = build_document_search_attempts(
        query=query,
        top_k=top_k,
        filter_by_book=source_scope[0],
        filter_by_chapter=source_scope[1],
    )

    for attempt in attempts:
        if tool_budget is not None and not await tool_budget.reserve():
            attempt_outputs.append((attempt, TOOL_BUDGET_EXHAUSTED_MESSAGE))
            return format_recovered_document_output(attempt_outputs)

        async def run_attempt(search_attempt: DocumentSearchAttempt = attempt) -> str:
            return await call(search_attempt)

        output = await record_text_tool_call(
            traces=traces,
            tool_name="search_document_library",
            query=format_tool_query(
                query=attempt.query,
                filter_by_book=attempt.filter_by_book,
                filter_by_chapter=attempt.filter_by_chapter,
            ),
            source_mapping=source_mapping,
            call=run_attempt,
        )
        attempt_outputs.append((attempt, output))
        if not is_no_document_results(output):
            return format_recovered_document_output(attempt_outputs)

    return format_recovered_document_output(attempt_outputs)


def build_document_search_attempts(
    *,
    query: str,
    top_k: int,
    filter_by_book: str | None = None,
    filter_by_chapter: str | None = None,
) -> list[DocumentSearchAttempt]:
    """Build deterministic recovery attempts for fragile metadata filters."""

    attempts = [
        DocumentSearchAttempt(
            query=query,
            top_k=top_k,
            filter_by_book=filter_by_book,
            filter_by_chapter=filter_by_chapter,
            reason="original",
        )
    ]
    if not filter_by_book and not filter_by_chapter:
        return attempts

    normalized_book = normalize_book_filter(filter_by_book)
    normalized_chapter = normalize_chapter_filter(filter_by_chapter)
    if (normalized_book, normalized_chapter) != (filter_by_book, filter_by_chapter):
        attempts.append(
            DocumentSearchAttempt(
                query=query,
                top_k=top_k,
                filter_by_book=normalized_book,
                filter_by_chapter=normalized_chapter,
                reason="normalized_filters",
            )
        )

    if filter_by_book and normalized_chapter:
        attempts.append(
            DocumentSearchAttempt(
                query=query,
                top_k=top_k,
                filter_by_chapter=normalized_chapter,
                reason="chapter_scope_after_empty_book_filter",
            )
        )

    if filter_by_chapter and normalized_book:
        attempts.append(
            DocumentSearchAttempt(
                query=query,
                top_k=top_k,
                filter_by_book=normalized_book,
                reason="book_scope_after_empty_chapter_filter",
            )
        )

    attempts.append(
        DocumentSearchAttempt(
            query=query,
            top_k=top_k,
            reason="broadened_after_empty_filters",
        )
    )
    return deduplicate_document_attempts(attempts)


def format_brandmind_kg_output(output: str) -> str:
    """Add compact next-action guidance to BrandMind KG tool results."""

    return f"{BRANDMIND_KG_RESULT_HINT}\n\n{output}"


def normalize_book_filter(value: str | None) -> str | None:
    """Map common user-facing book aliases to indexed document titles."""

    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None

    folded = normalized.casefold()
    for alias, title in BOOK_FILTER_ALIASES.items():
        if alias in folded:
            return title
    return normalized


def normalize_chapter_filter(value: str | None) -> str | None:
    """Normalize Vietnamese or shorthand chapter labels to indexed source text."""

    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None

    match = re.search(
        r"(?:chapter|chương|ch\.)\s*(?:=|:)?\s*(\d+)",
        normalized,
        re.IGNORECASE,
    )
    if match:
        return f"Chapter {match.group(1)}"
    if normalized.isdigit():
        return f"Chapter {normalized}"
    return normalized


def infer_source_filters_from_query(
    *,
    query: str,
    filter_by_book: str | None,
    filter_by_chapter: str | None,
) -> tuple[str | None, str | None]:
    """Infer obvious metadata filters from source hints embedded in the query."""

    inferred_book = filter_by_book.strip() if filter_by_book else None
    inferred_chapter = filter_by_chapter.strip() if filter_by_chapter else None

    folded_query = query.casefold()
    if inferred_book is None:
        for alias, title in SOURCE_HINT_BOOK_ALIASES.items():
            if alias in folded_query:
                inferred_book = title
                break

    if inferred_chapter is None:
        inferred_chapter = extract_chapter_hint(query)

    return inferred_book, inferred_chapter


def extract_chapter_hint(text: str) -> str | None:
    """Extract a chapter filter when text contains a clear chapter reference."""

    match = re.search(
        r"(?:chapter|chương|ch\.)\s*(?:=|:)?\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"Chapter {match.group(1)}"
    return None


def deduplicate_document_attempts(
    attempts: list[DocumentSearchAttempt],
) -> list[DocumentSearchAttempt]:
    """Remove duplicate recovery attempts while preserving order."""

    unique_attempts: list[DocumentSearchAttempt] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for attempt in attempts:
        key = (attempt.query, attempt.filter_by_book, attempt.filter_by_chapter)
        if key in seen:
            continue
        seen.add(key)
        unique_attempts.append(attempt)
    return unique_attempts


def is_no_document_results(output: str) -> bool:
    """Return whether the document tool found no passages."""

    return output.strip().startswith(DOC_SEARCH_NO_RESULTS)


def is_recovered_document_context_usable(output: str) -> bool:
    """Return whether recovery produced document evidence worth synthesizing."""

    stripped = output.strip()
    return bool(stripped) and not stripped.startswith(
        (DOC_SEARCH_NO_RESULTS, TOOL_BUDGET_EXHAUSTED_MESSAGE)
    )


def format_recovered_document_output(
    attempt_outputs: list[tuple[DocumentSearchAttempt, str]],
) -> str:
    """Format one or more internal document-search attempts for the agent."""

    if len(attempt_outputs) == 1:
        return attempt_outputs[0][1]

    sections: list[str] = []
    for attempt, output in attempt_outputs:
        query = format_tool_query(
            query=attempt.query,
            filter_by_book=attempt.filter_by_book,
            filter_by_chapter=attempt.filter_by_chapter,
        )
        sections.append(
            f"### Document search attempt: {attempt.reason}\nQuery: {query}\n{output}"
        )
    return "\n\n".join(sections)


async def record_text_tool_call(
    *,
    traces: list[ToolTrace],
    tool_name: str,
    query: str,
    call: Callable[[], Awaitable[str]],
    source_mapping: SourceMapping | None = None,
) -> str:
    """Execute a text tool and append a trace without swallowing errors."""

    started = time.perf_counter()
    try:
        output = await call()
        trace = ToolTrace(
            tool_name=tool_name,
            query=query,
            output_preview=output[:1200],
            source_ids=(
                source_mapping.source_ids_in_text(output)
                if source_mapping is not None
                else []
            ),
            latency_ms=elapsed_ms(started),
        )
        traces.append(trace)
        return output
    except Exception as exc:
        traces.append(
            ToolTrace(
                tool_name=tool_name,
                query=query,
                output_preview="",
                latency_ms=elapsed_ms(started),
                error=str(exc),
            )
        )
        raise


def extract_final_text(result: Any) -> str:
    """Extract final text from a LangChain agent result."""

    if isinstance(result, dict) and result.get("messages"):
        for message in reversed(result["messages"]):
            content = getattr(message, "content", None)
            if content:
                return normalize_message_content(content)
    return ""


def normalize_message_content(content: Any) -> str:
    """Normalize LangChain message content into plain text."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "\n".join(part for part in text_parts if part)
    return str(content)


def format_tool_query(
    *,
    query: str,
    filter_by_book: str | None = None,
    filter_by_chapter: str | None = None,
) -> str:
    """Record filters alongside the semantic query for trace readability."""

    filters = []
    if filter_by_book:
        filters.append(f"book={filter_by_book}")
    if filter_by_chapter:
        filters.append(f"chapter={filter_by_chapter}")
    return f"{query} ({', '.join(filters)})" if filters else query


def should_recover_brandmind_document_evidence(
    *,
    question: str,
    record: AnswerFlowRecord,
    enabled: bool,
) -> bool:
    """Return whether BrandMind should run one docs recovery pass."""

    if not enabled or record.error:
        return False
    tool_names = [trace.tool_name for trace in record.tool_traces]
    if "search_knowledge_graph" not in tool_names:
        return False
    if "search_document_library" in tool_names:
        return False
    return question_requests_source_details(question)


def question_requests_source_details(question: str) -> bool:
    """Detect questions that need document evidence rather than KG summaries."""

    folded = question.casefold()
    source_detail_cues = [
        "dựa trên",
        "theo chương",
        "theo tài liệu",
        "chương",
        "chapter",
        "được định nghĩa",
        "khái niệm",
        "biện pháp cụ thể",
        "thách thức cụ thể",
        "nêu rõ",
        "so sánh",
        "mục tiêu cuối cùng",
    ]
    if any(cue in folded for cue in source_detail_cues):
        return True
    if re.search(r"\b[A-Z]{2,}(?:/[A-Z]{2,})?\b", question):
        return True
    return '"' in question or "'" in question


def build_brandmind_recovery_query(question: str) -> str:
    """Build a document query for BrandMind KG-only evidence recovery."""

    return question


def build_brandmind_recovery_context(
    *,
    prior_answer: str,
    recovered_context: str,
) -> str:
    """Place the KG-only draft after recovered source evidence."""

    return (
        "# Recovered Document Evidence\n\n"
        f"{recovered_context}\n\n"
        "# Prior KG-Oriented Draft\n\n"
        f"{prior_answer}"
    )


def build_brandmind_recovery_system_prompt() -> str:
    """Build the answer prompt for one BrandMind evidence-recovery pass."""

    return (
        build_answer_agent_system_prompt(ComparisonSystem.BRANDMIND_AGENT)
        + "\n\n# Evidence Recovery\n"
        "The prior draft used knowledge-graph context without document evidence. "
        "Rewrite the final answer using the recovered document evidence as the "
        "primary source for exact facts, examples, lists, and source-specific "
        "conditions. Keep useful high-level framing only when the recovered "
        "evidence supports it. Remove claims that are not supported by the "
        "recovered evidence."
    )


def elapsed_ms(started: float) -> int:
    """Return elapsed milliseconds from a ``time.perf_counter`` timestamp."""

    return int((time.perf_counter() - started) * 1000)


def is_gemini_3_model(model: str) -> bool:
    """Return whether the model name should use Gemini 3 thinking controls."""

    return "gemini-3" in model.casefold()


def build_google_thinking_kwargs(config: AgentRunnerConfig) -> dict[str, Any]:
    """Build mutually exclusive Google thinking parameters for the answer model."""

    if is_gemini_3_model(config.answer_model):
        return (
            {"thinking_level": config.thinking_level} if config.thinking_level else {}
        )
    return (
        {"thinking_budget": config.thinking_budget}
        if config.thinking_budget is not None
        else {}
    )


def litellm_openai_base_url(raw_url: str | None) -> str:
    """Return the OpenAI-compatible ``/v1`` endpoint for the LiteLLM proxy."""

    base_url = (raw_url or "http://localhost:4000").rstrip("/")
    return base_url if base_url.endswith("/v1") else f"{base_url}/v1"
