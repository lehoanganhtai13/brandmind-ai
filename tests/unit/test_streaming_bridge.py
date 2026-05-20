"""Unit tests for server streaming response hygiene."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import cast

import pytest
from langchain_core.messages import AIMessageChunk
from langgraph.graph.state import CompiledStateGraph

from core.brand_strategy import session as brand_strategy_session_store
from core.brand_strategy.session import BrandStrategySession, get_active_session
from server.schemas.enums import SessionMode
from server.services.session_manager import ManagedSession, SessionManager
from server.streaming.bridge import (
    _EMPTY_RESPONSE_FALLBACK,
    _AgentTurnTraceBuilder,
    _InternalReminderFilter,
    collect_agent_response,
    stream_agent_response,
)
from server.streaming.tool_call_matching import ToolCallMatcher
from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    StreamingTokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)


class _FakeStreamingAgent:
    """Deterministic agent double that streams fixed message chunks."""

    def __init__(self, chunks: list[str | AIMessageChunk]) -> None:
        self._chunks = chunks

    async def astream(
        self,
        *_args: object,
        **_kwargs: object,
    ) -> AsyncIterator[tuple[AIMessageChunk, dict[str, object]]]:
        """Yield configured chunks in the same shape as LangGraph streaming."""
        for chunk in self._chunks:
            if isinstance(chunk, AIMessageChunk):
                yield chunk, {}
            else:
                yield AIMessageChunk(content=chunk), {}


def test_internal_reminder_filter_preserves_plain_text() -> None:
    """Plain user-facing text should pass through unchanged."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("Xin chào ") == "Xin chào "
    assert token_filter.feed("em.") == "em."
    assert token_filter.flush() == ""


def test_tool_call_matcher_pairs_out_of_order_results_by_id() -> None:
    """Concurrent same-name tool calls should use ids before FIFO fallback."""
    matcher: ToolCallMatcher[dict[str, str]] = ToolCallMatcher()

    matcher.add("read_file", {"file_path": "/a"}, "call-a")
    matcher.add("read_file", {"file_path": "/b"}, "call-b")

    assert matcher.pop("read_file", "call-b") == {"file_path": "/b"}
    assert matcher.pop("read_file", "call-a") == {"file_path": "/a"}


def test_tool_call_matcher_keeps_legacy_fifo_fallback() -> None:
    """Old callback events without ids should still settle oldest-first."""
    matcher: ToolCallMatcher[dict[str, str]] = ToolCallMatcher()

    matcher.add("read_file", {"file_path": "/a"})
    matcher.add("read_file", {"file_path": "/b"})

    assert matcher.pop("read_file") == {"file_path": "/a"}
    assert matcher.pop("read_file") == {"file_path": "/b"}


def test_agent_turn_trace_builder_pairs_out_of_order_results_by_id() -> None:
    """Persisted traces should not attach results to the wrong same-name call."""
    trace_builder = _AgentTurnTraceBuilder()

    trace_builder.on_tool_call("read_file", {"file_path": "/a"}, "call-a")
    trace_builder.on_tool_call("read_file", {"file_path": "/b"}, "call-b")
    trace_builder.on_tool_result("read_file", "B result", "call-b")
    trace_builder.on_tool_result("read_file", "A result", "call-a")

    turn = trace_builder.finalize(duration_seconds=1.0)
    first = turn.timeline[0].tool_call
    second = turn.timeline[1].tool_call

    assert first is not None
    assert first.arguments == {"file_path": "/a"}
    assert first.result == "A result"
    assert second is not None
    assert second.arguments == {"file_path": "/b"}
    assert second.result == "B result"


def test_internal_reminder_filter_removes_complete_block() -> None:
    """Internal reminder blocks should be removed from one streamed chunk."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A<system-reminder>hidden plan</system-reminder>B")

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_reminder_filter_removes_split_block() -> None:
    """Internal reminder blocks should be removed even across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A<system") == "A"
    assert token_filter.feed("-reminder>hidden") == ""
    assert token_filter.feed(" plan</system-rem") == ""
    assert token_filter.feed("inder>B") == "B"
    assert token_filter.flush() == ""


def test_internal_reminder_filter_discards_unclosed_block_on_flush() -> None:
    """An unterminated internal block should not leak when the stream ends."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("Visible<system-reminder>hidden") == "Visible"
    assert token_filter.flush() == ""


def test_internal_filter_removes_complete_pseudo_tool_call() -> None:
    """Pseudo tool-call tags are internal and should not stream to users."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A<call:default_api:report_progress advance=true />B")

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_split_pseudo_tool_call() -> None:
    """Pseudo tool-call tags should be removed across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A<ca") == "A"
    assert token_filter.feed('ll:default_api:read_file file_path="/workspace') == ""
    assert token_filter.feed('/brand_brief.md" />B') == "B"
    assert token_filter.flush() == ""


def test_internal_filter_removes_raw_tool_xml_call() -> None:
    """Raw XML-like tool calls are internal and should not reach chat."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed('A<report_progress advance="true" />B')

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_split_raw_tool_xml_call() -> None:
    """Raw XML-like tool calls should be removed across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A<report") == "A"
    assert token_filter.feed('_progress advance="true" /') == ""
    assert token_filter.feed(">B") == "B"
    assert token_filter.flush() == ""


def test_internal_filter_preserves_markdown_html_breaks() -> None:
    """Only known internal tool tags should be stripped."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A<br>B")

    assert output == "A<br>B"
    assert token_filter.flush() == ""


def test_internal_filter_removes_commentary_blocks() -> None:
    """Commentary blocks are internal execution notes, not user-facing text."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A<commentary>hidden plan</commentary>B")

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_split_commentary_blocks() -> None:
    """Commentary blocks should be removed across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A<comm") == "A"
    assert token_filter.feed("entary>hidden") == ""
    assert token_filter.feed(" plan</comment") == ""
    assert token_filter.feed("ary>B") == "B"
    assert token_filter.flush() == ""


def test_internal_filter_removes_plan_check_blocks() -> None:
    """Plan-check blocks are internal self-checks, not user-facing text."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A<plan-check>Action: report_progress</plan-check>B")

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_split_plan_check_blocks() -> None:
    """Plan-check blocks should be removed across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A<plan") == "A"
    assert token_filter.feed("-check>Action: report") == ""
    assert token_filter.feed("_progress</plan") == ""
    assert token_filter.feed("-check>B") == "B"
    assert token_filter.flush() == ""


def test_internal_filter_preserves_tool_name_lines_by_default() -> None:
    """General chat can still discuss tool-call examples when relevant."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed("A\n`report_progress(advance=True)`\nB")

    assert output == "A\n`report_progress(advance=True)`\nB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_tool_name_lines_when_enabled() -> None:
    """Brand Strategy chat should drop leaked internal tool-call lines."""
    token_filter = _InternalReminderFilter(suppress_internal_tool_lines=True)

    output = token_filter.feed("A\n`report_progress(advance=True)` retry\nB")

    assert output == "A\n"
    assert token_filter.flush() == "B"


def test_internal_filter_removes_split_tool_name_lines_when_enabled() -> None:
    """Line filtering should hold partial tool lines until the newline arrives."""
    token_filter = _InternalReminderFilter(suppress_internal_tool_lines=True)

    assert token_filter.feed("A\n`report") == "A\n"
    assert token_filter.feed("_progress(advance=True)` retry\nB") == ""
    assert token_filter.flush() == "B"


def test_internal_filter_removes_tool_json_fence() -> None:
    """Fenced JSON tool payloads are internal and should not reach users."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed(
        'A```json\n{"action": "edit_file", "file_path": "/workspace/x"}\n```B'
    )

    assert output == "AB"
    assert token_filter.flush() == ""


def test_internal_filter_removes_split_tool_json_fence() -> None:
    """Fenced JSON tool payloads should be removed across chunk boundaries."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("A```j") == "A"
    assert token_filter.feed('son\n{"subagent_type": "document-generator"') == ""
    assert token_filter.feed(', "description": "build deck"}\n```B') == "B"
    assert token_filter.flush() == ""


def test_internal_filter_preserves_non_tool_json_fence() -> None:
    """Ordinary JSON examples should remain visible when they are not tool payloads."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed('A```json\n{"metric": "RPR"}\n```B')

    assert output == 'A```json\n{"metric": "RPR"}\n```B'
    assert token_filter.flush() == ""


@pytest.mark.asyncio
async def test_stream_agent_response_filters_tokens_and_history() -> None:
    """The streaming bridge should sanitize client output and session history."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.ASK,
        created_at=datetime.now(),
        last_active=0.0,
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(
            [
                "A<system",
                "-reminder>hidden</system-rem",
                "inder>B",
            ]
        ),
    )
    manager = SessionManager()
    tokens: list[str] = []

    async for event in stream_agent_response(session, "hello", manager):
        if isinstance(event, StreamingTokenEvent) and event.token and not event.done:
            tokens.append(event.token)

    assert "".join(tokens) == "AB"
    assert session.messages[-1].content == "AB"


@pytest.mark.asyncio
async def test_stream_agent_response_filters_pseudo_tool_calls() -> None:
    """Raw pseudo tool calls should be absent from client text and history."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.ASK,
        created_at=datetime.now(),
        last_active=0.0,
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(
            [
                "Đã cập nhật.",
                "<call:default_api:report_progress advance=true />",
                " Mình tiếp tục nhé.",
            ]
        ),
    )
    manager = SessionManager()
    tokens: list[str] = []

    async for event in stream_agent_response(session, "hello", manager):
        if isinstance(event, StreamingTokenEvent) and event.token and not event.done:
            tokens.append(event.token)

    assert "<call:" not in "".join(tokens)
    assert "".join(tokens) == "Đã cập nhật. Mình tiếp tục nhé."
    assert session.messages[-1].content == "Đã cập nhật. Mình tiếp tục nhé."


@pytest.mark.asyncio
async def test_stream_agent_response_filters_brand_strategy_internals() -> None:
    """Brand Strategy streams should suppress plan checks and tool-call lines."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.BRAND_STRATEGY,
        created_at=datetime.now(),
        last_active=0.0,
        brand_strategy_session=BrandStrategySession(),
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(
            [
                "A<plan",
                "-check>Action: report_progress</plan-check>B\n",
                "`report_progress(advance=True)` retry\n",
                "C",
            ]
        ),
    )
    manager = SessionManager()
    tokens: list[str] = []

    async for event in stream_agent_response(session, "hello", manager):
        if isinstance(event, StreamingTokenEvent) and event.token and not event.done:
            tokens.append(event.token)

    assert "".join(tokens) == "AB\nC"
    assert session.messages[-1].content == "AB\nC"


@pytest.mark.asyncio
async def test_stream_agent_response_discards_brand_strategy_pre_tool_text() -> None:
    """Brand Strategy chat should not persist draft text emitted before tools."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.BRAND_STRATEGY,
        created_at=datetime.now(),
        last_active=0.0,
        brand_strategy_session=BrandStrategySession(),
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(
            [
                AIMessageChunk(
                    content="Draft before tools. ",
                    tool_call_chunks=[
                        {
                            "name": "read_file",
                            "args": "{}",
                            "id": "tool-1",
                            "index": 0,
                        }
                    ],
                ),
                "Final answer after tools.",
            ]
        ),
    )
    manager = SessionManager()
    tokens: list[str] = []

    async for event in stream_agent_response(session, "hello", manager):
        if isinstance(event, StreamingTokenEvent) and event.token and not event.done:
            tokens.append(event.token)

    assert "".join(tokens) == "Final answer after tools."
    assert session.messages[-1].content == "Final answer after tools."


@pytest.mark.asyncio
async def test_stream_agent_response_marks_brand_strategy_user_turn() -> None:
    """Brand-strategy messages should advance the phase-guard turn counter."""
    strategy_session = BrandStrategySession()
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.BRAND_STRATEGY,
        created_at=datetime.now(),
        last_active=0.0,
        brand_strategy_session=strategy_session,
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(["hello"]),
    )
    manager = SessionManager()

    async for _event in stream_agent_response(session, "start", manager):
        pass

    assert strategy_session.turn_index == 1
    assert get_active_session() is None


@pytest.mark.asyncio
async def test_stream_agent_response_persists_brand_strategy_turn(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A completed brand-strategy turn should survive server restart."""
    monkeypatch.setattr(brand_strategy_session_store, "SESSIONS_DIR", tmp_path)
    strategy_session = BrandStrategySession(session_id="test-session")
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.BRAND_STRATEGY,
        created_at=datetime.now(),
        last_active=0.0,
        brand_strategy_session=strategy_session,
    )
    session.agent = cast(CompiledStateGraph, _FakeStreamingAgent(["Xin chào."]))
    manager = SessionManager()

    async for _event in stream_agent_response(session, "start", manager):
        pass

    restored = brand_strategy_session_store.load_session("test-session")
    assert restored is not None
    assert [message.type for message in restored.messages] == ["human", "ai"]
    assert restored.messages[0].content == "start"
    assert restored.messages[1].content == "Xin chào."
    assert len(restored.agent_traces) == 1


@pytest.mark.asyncio
async def test_collect_agent_response_returns_sanitized_text() -> None:
    """Non-streaming callers should receive the same sanitized response."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.ASK,
        created_at=datetime.now(),
        last_active=0.0,
    )
    session.agent = cast(
        CompiledStateGraph,
        _FakeStreamingAgent(
            [
                "Visible",
                "<system-reminder>hidden</system-reminder>",
                " text",
            ]
        ),
    )
    manager = SessionManager()

    response = await collect_agent_response(session, "hello", manager)

    assert response.response == "Visible text"
    assert session.messages[-1].content == "Visible text"


@pytest.mark.asyncio
async def test_collect_agent_response_pairs_tool_results_by_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-streaming tool-call summaries should survive out-of-order results."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.ASK,
        created_at=datetime.now(),
        last_active=0.0,
    )
    manager = SessionManager()
    events = [
        ToolCallEvent(
            tool_name="read_file",
            tool_call_id="call-a",
            arguments={"file_path": "/a"},
        ),
        ToolCallEvent(
            tool_name="read_file",
            tool_call_id="call-b",
            arguments={"file_path": "/b"},
        ),
        ToolResultEvent(
            tool_name="read_file",
            tool_call_id="call-b",
            result="B result",
        ),
        ToolResultEvent(
            tool_name="read_file",
            tool_call_id="call-a",
            result="A result",
        ),
        StreamingTokenEvent(token="Done."),
    ]

    async def fake_stream_agent_response(
        *_args: object,
        **_kwargs: object,
    ) -> AsyncIterator[BaseAgentEvent]:
        for event in events:
            yield event

    monkeypatch.setattr(
        "server.streaming.bridge.stream_agent_response",
        fake_stream_agent_response,
    )

    response = await collect_agent_response(session, "hello", manager)

    assert response.response == "Done."
    assert [(call.arguments, call.result) for call in response.tool_calls] == [
        ({"file_path": "/b"}, "B result"),
        ({"file_path": "/a"}, "A result"),
    ]


@pytest.mark.asyncio
async def test_collect_agent_response_returns_fallback_for_empty_text() -> None:
    """A tool-only or interrupted model turn should not return a blank reply."""
    session = ManagedSession(
        session_id="test-session",
        mode=SessionMode.ASK,
        created_at=datetime.now(),
        last_active=0.0,
    )
    session.agent = cast(CompiledStateGraph, _FakeStreamingAgent([""]))
    manager = SessionManager()

    response = await collect_agent_response(session, "hello", manager)

    assert response.response == _EMPTY_RESPONSE_FALLBACK
    assert session.messages[-1].content == _EMPTY_RESPONSE_FALLBACK
