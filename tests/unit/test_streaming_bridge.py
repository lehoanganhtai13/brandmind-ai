"""Unit tests for server streaming response hygiene."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import cast

import pytest
from langchain_core.messages import AIMessageChunk
from langgraph.graph.state import CompiledStateGraph

from server.schemas.enums import SessionMode
from server.services.session_manager import ManagedSession, SessionManager
from server.streaming.bridge import (
    _InternalReminderFilter,
    collect_agent_response,
    stream_agent_response,
)
from shared.agent_middlewares.callback_types import StreamingTokenEvent


class _FakeStreamingAgent:
    """Deterministic agent double that streams fixed message chunks."""

    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    async def astream(
        self,
        *_args: object,
        **_kwargs: object,
    ) -> AsyncIterator[tuple[AIMessageChunk, dict[str, object]]]:
        """Yield configured chunks in the same shape as LangGraph streaming."""
        for chunk in self._chunks:
            yield AIMessageChunk(content=chunk), {}


def test_internal_reminder_filter_preserves_plain_text() -> None:
    """Plain user-facing text should pass through unchanged."""
    token_filter = _InternalReminderFilter()

    assert token_filter.feed("Xin chào ") == "Xin chào "
    assert token_filter.feed("em.") == "em."
    assert token_filter.flush() == ""


def test_internal_reminder_filter_removes_complete_block() -> None:
    """Internal reminder blocks should be removed from one streamed chunk."""
    token_filter = _InternalReminderFilter()

    output = token_filter.feed(
        "A<system-reminder>hidden plan</system-reminder>B"
    )

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
