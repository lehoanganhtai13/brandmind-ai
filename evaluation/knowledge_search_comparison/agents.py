"""Answer-flow agent wrappers for the knowledge-search comparison benchmark."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkItem
from evaluation.knowledge_search_comparison.prompts import (
    ANSWER_AGENT_SYSTEM_PROMPT,
)
from evaluation.knowledge_search_comparison.schemas import (
    AnswerFlowRecord,
    ComparisonSystem,
    ToolTrace,
)
from evaluation.knowledge_search_comparison.source_mapping import SourceMapping


class AgentRunnerConfig(BaseModel):
    """Runtime settings shared across answer-flow agents."""

    answer_model: str = "gemini-2.5-flash-lite"
    top_k: int = Field(default=5, gt=0)
    candidate_top_k: int = Field(default=10, gt=0)
    max_tool_calls: int = Field(default=4, gt=0)
    recursion_limit: int = Field(default=60, gt=0)
    temperature: float = 0.1
    thinking_budget: int | None = 2000
    max_output_tokens: int = 8000
    api_key: str | None = None


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
                thinking_budget=self.config.thinking_budget,
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
            system_prompt=ANSWER_AGENT_SYSTEM_PROMPT,
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

    async def search_knowledge_graph_tool(query: str) -> str:
        """Search BrandMind's knowledge graph for concepts and source pointers."""

        return await record_text_tool_call(
            traces=traces,
            tool_name="search_knowledge_graph",
            query=query,
            source_mapping=source_mapping,
            call=lambda: search_knowledge_graph(
                query=query,
                max_results=config.candidate_top_k,
            ),
        )

    async def search_document_library_tool(
        query: str,
        top_k: int = config.candidate_top_k,
        filter_by_book: str | None = None,
        filter_by_chapter: str | None = None,
    ) -> str:
        """Search BrandMind's document library for targeted source passages."""

        tool_query = format_tool_query(
            query=query,
            filter_by_book=filter_by_book,
            filter_by_chapter=filter_by_chapter,
        )
        return await record_text_tool_call(
            traces=traces,
            tool_name="search_document_library",
            query=tool_query,
            source_mapping=source_mapping,
            call=lambda: search_document_library(
                query=query,
                top_k=min(top_k, config.candidate_top_k),
                filter_by_book=filter_by_book,
                filter_by_chapter=filter_by_chapter,
            ),
        )

    return await run_langchain_answer_flow(
        item=item,
        system=ComparisonSystem.BRANDMIND_AGENT,
        tools=[search_knowledge_graph_tool, search_document_library_tool],
        traces=traces,
        config=config,
    )


async def run_hybrid_search_agent(
    *,
    item: BenchmarkItem,
    config: AgentRunnerConfig,
    source_mapping: SourceMapping | None = None,
) -> AnswerFlowRecord:
    """Run the single-tool hybrid-search condition as an answer-flow agent."""

    from shared.agent_tools.retrieval import search_document_library  # noqa: PLC0415

    traces: list[ToolTrace] = []

    async def search_hybrid_marketing_knowledge(query: str) -> str:
        """Search BrandMind's hybrid document index for marketing knowledge."""

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

    async def search_hipporag(query: str) -> str:
        """Search HippoRAG native retriever output over the five-book corpus."""

        return await record_text_tool_call(
            traces=traces,
            tool_name="search_hipporag",
            query=query,
            source_mapping=source_mapping,
            call=lambda: hipporag_search(query=query, top_k=config.top_k),
        )

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
        agent = create_langchain_agent(tools=tools, config=config)
        from langchain_core.messages import HumanMessage  # noqa: PLC0415

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=item.question)]},
            {"recursion_limit": config.recursion_limit},
        )
        return AnswerFlowRecord(
            item_id=item.id,
            question=item.question,
            system=system,
            final_answer=extract_final_text(result),
            tool_traces=traces,
            latency_ms=elapsed_ms(started),
        )
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
    tools: list[Callable[..., Awaitable[str]]],
    config: AgentRunnerConfig,
) -> Any:
    """Create a LangChain agent with the shared benchmark answer prompt."""

    from langchain.agents import create_agent
    from langchain_google_genai import ChatGoogleGenerativeAI

    from config.system_config import SETTINGS

    model = ChatGoogleGenerativeAI(
        google_api_key=config.api_key or SETTINGS.GEMINI_API_KEY,
        model=config.answer_model,
        temperature=config.temperature,
        thinking_budget=config.thinking_budget,
        max_output_tokens=config.max_output_tokens,
    )
    tool_budget_prompt = (
        f"\n\n# Tool Budget\nUse at most {config.max_tool_calls} tool calls "
        "unless the retrieved evidence is clearly insufficient."
    )
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=ANSWER_AGENT_SYSTEM_PROMPT + tool_budget_prompt,
    )


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


def elapsed_ms(started: float) -> int:
    """Return elapsed milliseconds from a ``time.perf_counter`` timestamp."""

    return int((time.perf_counter() - started) * 1000)
