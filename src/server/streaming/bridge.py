"""Streaming bridge — merges agent events into a single async stream.

Dual-source event merge:
1. Middleware events → EventRouter → asyncio.Queue
2. agent.astream() chunks → extract thinking/token → asyncio.Queue

A single consumer yields from the queue as BaseAgentEvent instances.
The chat.py route serializes these to SSE format.

The chunk extraction logic mirrors tui/app.py:335-421 but pushes
to a queue instead of calling renderer methods directly.
"""

from __future__ import annotations

import asyncio
from asyncio import Queue
from collections.abc import AsyncGenerator
from typing import Literal

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from loguru import logger

from core.brand_strategy.session import set_active_session
from server.schemas.chat import MessageResponse, ToolCallInfo
from server.schemas.enums import SessionMode
from server.services.session_manager import ManagedSession, SessionManager
from shared.agent_middlewares.callback_types import (
    BaseAgentEvent,
    StreamingThinkingEvent,
    StreamingTokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)


class _StreamEnd(BaseAgentEvent):
    """Typed sentinel signaling the end of the event stream.

    Internal to the bridge — never sent to clients.
    """

    type: Literal["_stream_end"] = "_stream_end"


_STREAM_END = _StreamEnd()
_INTERNAL_REMINDER_START = "<system-reminder>"
_INTERNAL_REMINDER_END = "</system-reminder>"
_EMPTY_RESPONSE_FALLBACK = (
    "The last turn did not produce a visible response. "
    'Please send "continue" and I will pick up from the saved state.'
)


def _longest_suffix_prefix_match(text: str, prefix: str) -> int:
    """Return the longest suffix length in text that may continue as prefix."""
    max_length = min(len(text), len(prefix) - 1)
    for length in range(max_length, 0, -1):
        if prefix.startswith(text[-length:]):
            return length
    return 0


class _InternalReminderFilter:
    """Remove internal reminder blocks from streamed model-visible text."""

    def __init__(self) -> None:
        self._buffer = ""
        self._inside_internal_block = False

    def feed(self, text: str) -> str:
        """Accept one streamed chunk and return only user-facing text."""
        if not text:
            return ""

        self._buffer += text
        visible_parts: list[str] = []

        while self._buffer:
            if self._inside_internal_block:
                end_index = self._buffer.find(_INTERNAL_REMINDER_END)
                if end_index == -1:
                    keep = _longest_suffix_prefix_match(
                        self._buffer,
                        _INTERNAL_REMINDER_END,
                    )
                    self._buffer = self._buffer[-keep:] if keep else ""
                    break

                self._buffer = self._buffer[end_index + len(_INTERNAL_REMINDER_END) :]
                self._inside_internal_block = False
                continue

            start_index = self._buffer.find(_INTERNAL_REMINDER_START)
            if start_index != -1:
                visible_parts.append(self._buffer[:start_index])
                self._buffer = self._buffer[
                    start_index + len(_INTERNAL_REMINDER_START) :
                ]
                self._inside_internal_block = True
                continue

            keep = _longest_suffix_prefix_match(
                self._buffer,
                _INTERNAL_REMINDER_START,
            )
            emit_until = len(self._buffer) - keep
            visible_parts.append(self._buffer[:emit_until])
            self._buffer = self._buffer[emit_until:]
            break

        return "".join(visible_parts)

    def flush(self) -> str:
        """Return any safe buffered text and discard unterminated reminders."""
        if self._inside_internal_block:
            self._buffer = ""
            self._inside_internal_block = False
            return ""

        text = self._buffer
        self._buffer = ""
        return text


async def stream_agent_response(
    session: ManagedSession,
    content: str,
    manager: SessionManager,
) -> AsyncGenerator[BaseAgentEvent, None]:
    """Run agent and yield merged events from both sources.

    Flow:
    1. Acquire session lock (serialize per-session)
    2. For brand-strategy: acquire global brand_strategy_lock + set_active_session
    3. Redirect EventRouter to this message's Queue
    4. Run agent.astream() in background task — extract chunks → Queue
    5. Middleware events arrive via EventRouter → same Queue
    6. Yield from Queue until _StreamEnd sentinel
    7. Cleanup: clear router, release locks

    Args:
        session: The managed session to send the message to.
        content: User message content.
        manager: SessionManager (for brand_strategy_lock).

    Yields:
        BaseAgentEvent instances in chronological order.
    """
    event_queue: Queue[BaseAgentEvent] = Queue()

    await session.lock.acquire()
    bs_lock = manager.brand_strategy_lock
    holds_bs_lock = False

    try:
        # For brand-strategy: acquire global lock + set active session
        if session.mode is SessionMode.BRAND_STRATEGY:
            await bs_lock.acquire()
            holds_bs_lock = True
            set_active_session(session.brand_strategy_session)

        # Redirect middleware events to this message's queue
        session.event_router.set_queue(event_queue)

        # Ensure agent exists (lazy init)
        agent = session.ensure_agent()

        # Append user message to session history
        session.messages.append(HumanMessage(content=content))
        if (
            session.mode is SessionMode.BRAND_STRATEGY
            and session.brand_strategy_session is not None
        ):
            session.brand_strategy_session.begin_user_turn()

        # Update last active
        session.last_active = asyncio.get_event_loop().time()

        # Producer: run astream, extract chunks, push to queue
        # Accumulates response text so we can update session.messages
        # after streaming completes (astream doesn't return final state).
        accumulated_response: list[str] = []
        response_filter = _InternalReminderFilter()
        thinking_filter = _InternalReminderFilter()
        filters_flushed = False

        async def _flush_visible_text() -> None:
            nonlocal filters_flushed
            if filters_flushed:
                return

            thinking_tail = thinking_filter.flush()
            if thinking_tail:
                await event_queue.put(StreamingThinkingEvent(token=thinking_tail))

            response_tail = response_filter.flush()
            if response_tail:
                accumulated_response.append(response_tail)
                await event_queue.put(StreamingTokenEvent(token=response_tail))

            filters_flushed = True

        async def _run_astream() -> None:
            nonlocal accumulated_response
            thinking_done = False
            try:
                async for chunk, _metadata in agent.astream(
                    {"messages": session.messages},
                    {"recursion_limit": 200},
                    stream_mode="messages",
                ):
                    if not isinstance(chunk, AIMessageChunk):
                        continue

                    if isinstance(chunk.content, list):
                        for part in chunk.content:
                            if not isinstance(part, dict):
                                continue
                            if part.get("type") == "thinking":
                                text = part.get("thinking", "")
                                if text:
                                    visible_text = thinking_filter.feed(text)
                                    if not visible_text:
                                        continue
                                    if thinking_done:
                                        thinking_done = False
                                    await event_queue.put(
                                        StreamingThinkingEvent(token=visible_text)
                                    )
                            elif part.get("type") == "text":
                                text = part.get("text", "")
                                if text:
                                    visible_text = response_filter.feed(text)
                                    if not visible_text:
                                        continue
                                    if not thinking_done:
                                        await event_queue.put(
                                            StreamingThinkingEvent(token="", done=True)
                                        )
                                        thinking_done = True
                                    accumulated_response.append(visible_text)
                                    await event_queue.put(
                                        StreamingTokenEvent(token=visible_text)
                                    )

                    elif isinstance(chunk.content, str) and chunk.content:
                        visible_text = response_filter.feed(chunk.content)
                        if not visible_text:
                            continue
                        if not thinking_done:
                            await event_queue.put(
                                StreamingThinkingEvent(token="", done=True)
                            )
                            thinking_done = True
                        accumulated_response.append(visible_text)
                        await event_queue.put(StreamingTokenEvent(token=visible_text))

                    if chunk.tool_calls and not thinking_done:
                        await event_queue.put(
                            StreamingThinkingEvent(token="", done=True)
                        )
                        thinking_done = True

                await _flush_visible_text()

                response_text = "".join(accumulated_response)
                if not response_text.strip():
                    response_text = _EMPTY_RESPONSE_FALLBACK
                    accumulated_response.append(response_text)
                    await event_queue.put(StreamingTokenEvent(token=response_text))

                # Append AI response to session history for next turn
                if response_text:
                    session.messages.append(AIMessage(content=response_text))

            except Exception as exc:
                logger.exception(f"Agent stream failed: {exc}")
            finally:
                await _flush_visible_text()
                if not thinking_done:
                    await event_queue.put(StreamingThinkingEvent(token="", done=True))
                await event_queue.put(StreamingTokenEvent(token="", done=True))
                await event_queue.put(_STREAM_END)

        # Start producer in background
        producer = asyncio.create_task(_run_astream())

        # Consumer: yield events until stream end
        try:
            while True:
                event = await event_queue.get()
                if isinstance(event, _StreamEnd):
                    break
                yield event
        finally:
            if not producer.done():
                producer.cancel()

    finally:
        session.event_router.clear_queue()
        if holds_bs_lock:
            set_active_session(None)
            bs_lock.release()
        session.lock.release()


async def collect_agent_response(
    session: ManagedSession,
    content: str,
    manager: SessionManager,
) -> MessageResponse:
    """Non-streaming mode: collect all events and return MessageResponse.

    Internally iterates stream_agent_response() to gather the complete
    response text, tool calls, and updated metadata.

    Args:
        session: The managed session to send the message to.
        content: User message content.
        manager: SessionManager (for brand_strategy_lock).

    Returns:
        Complete MessageResponse with response text, metadata, and tool calls.
    """
    response_tokens: list[str] = []
    tool_calls: list[ToolCallInfo] = []
    pending_tool: dict[str, str] = {}

    async for event in stream_agent_response(session, content, manager):
        if isinstance(event, StreamingTokenEvent):
            if event.token and not event.done:
                response_tokens.append(event.token)
        elif isinstance(event, ToolCallEvent):
            pending_tool = {
                "tool_name": event.tool_name,
                "arguments": event.arguments,
            }
        elif isinstance(event, ToolResultEvent):
            tool_calls.append(
                ToolCallInfo(
                    tool_name=event.tool_name,
                    arguments=pending_tool.get("arguments", {}),
                    result=event.result,
                )
            )
            pending_tool = {}

    return MessageResponse(
        response="".join(response_tokens),
        metadata=session.to_session_info().metadata,
        tool_calls=tool_calls,
    )
