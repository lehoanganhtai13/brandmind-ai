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
from typing import Any, Literal

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from loguru import logger

from core.brand_strategy.session import (
    PersistedAgentTurn,
    PersistedTimelineEntry,
    PersistedToolCall,
    format_turn_duration,
    set_active_session,
)
from server.schemas.chat import MessageResponse, ToolCallInfo
from server.schemas.enums import SessionMode
from server.services.session_manager import ManagedSession, SessionManager
from server.streaming.tool_call_matching import ToolCallMatcher
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
_COMMENTARY_START = "<commentary>"
_COMMENTARY_END = "</commentary>"
_PLAN_CHECK_START = "<plan-check"
_PLAN_CHECK_END = "</plan-check>"
_PSEUDO_TOOL_CALL_STARTS = (
    "<call:",
    "<report_progress",
    "<tool",
    "<task",
    "<function_call",
)
_PSEUDO_TOOL_CALL_END = ">"
_JSON_FENCE_START = "```json"
_JSON_FENCE_END = "```"
_PSEUDO_TOOL_JSON_MARKERS = (
    '"action"',
    '"file_path"',
    '"old_string"',
    '"new_string"',
    '"advance"',
    '"subagent_type"',
    '"todos"',
    '"scope"',
)
_INTERNAL_TOOL_LINE_MARKERS = (
    "`report_progress",
    "`write_todos",
    "`task(",
    "`list_artifacts",
    "report_progress(",
    "write_todos",
    "task(subagent_type=",
    "list_artifacts(",
)
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


def _longest_suffix_prefix_match_any(text: str, prefixes: tuple[str, ...]) -> int:
    """Return the longest suffix length that may continue as any prefix."""
    return max(_longest_suffix_prefix_match(text, prefix) for prefix in prefixes)


def _looks_like_pseudo_tool_json(block: str) -> bool:
    """Return whether a fenced JSON block is an exposed internal tool payload."""
    return any(marker in block for marker in _PSEUDO_TOOL_JSON_MARKERS)


def _looks_like_internal_tool_line(line: str) -> bool:
    """Return whether a visible line is only leaking internal tool mechanics."""
    return any(marker in line for marker in _INTERNAL_TOOL_LINE_MARKERS)


class _InternalReminderFilter:
    """Remove internal-only blocks from streamed model-visible text."""

    def __init__(self, *, suppress_internal_tool_lines: bool = False) -> None:
        self._buffer = ""
        self._json_fence_buffer = ""
        self._line_buffer = ""
        self._internal_block_end = _INTERNAL_REMINDER_END
        self._suppress_internal_tool_lines = suppress_internal_tool_lines
        self._inside_internal_block = False
        self._inside_pseudo_tool_call = False
        self._inside_json_fence = False

    def feed(self, text: str) -> str:
        """Accept one streamed chunk and return only user-facing text."""
        if not text:
            return ""

        self._buffer += text
        visible_parts: list[str] = []

        while self._buffer:
            if self._inside_json_fence:
                end_index = self._buffer.find(_JSON_FENCE_END)
                if end_index == -1:
                    self._json_fence_buffer += self._buffer
                    self._buffer = ""
                    break

                json_body = self._json_fence_buffer + self._buffer[:end_index]
                self._buffer = self._buffer[end_index + len(_JSON_FENCE_END) :]
                self._json_fence_buffer = ""
                self._inside_json_fence = False
                if not _looks_like_pseudo_tool_json(json_body):
                    visible_parts.append(
                        f"{_JSON_FENCE_START}{json_body}{_JSON_FENCE_END}"
                    )
                continue

            if self._inside_internal_block:
                end_index = self._buffer.find(self._internal_block_end)
                if end_index == -1:
                    keep = _longest_suffix_prefix_match(
                        self._buffer,
                        self._internal_block_end,
                    )
                    self._buffer = self._buffer[-keep:] if keep else ""
                    break

                self._buffer = self._buffer[end_index + len(self._internal_block_end) :]
                self._inside_internal_block = False
                self._internal_block_end = _INTERNAL_REMINDER_END
                continue

            if self._inside_pseudo_tool_call:
                end_index = self._buffer.find(_PSEUDO_TOOL_CALL_END)
                if end_index == -1:
                    keep = _longest_suffix_prefix_match(
                        self._buffer,
                        _PSEUDO_TOOL_CALL_END,
                    )
                    self._buffer = self._buffer[-keep:] if keep else ""
                    break

                self._buffer = self._buffer[end_index + len(_PSEUDO_TOOL_CALL_END) :]
                self._inside_pseudo_tool_call = False
                continue

            start_index = self._buffer.find(_INTERNAL_REMINDER_START)
            commentary_index = self._buffer.find(_COMMENTARY_START)
            plan_check_index = self._buffer.find(_PLAN_CHECK_START)
            json_fence_index = self._buffer.find(_JSON_FENCE_START)
            starts = [
                (start_index, _INTERNAL_REMINDER_START, "internal"),
                (commentary_index, _COMMENTARY_START, "commentary"),
                (plan_check_index, _PLAN_CHECK_START, "plan_check"),
                (json_fence_index, _JSON_FENCE_START, "json_fence"),
                *(
                    (self._buffer.find(prefix), prefix, "tool_call")
                    for prefix in _PSEUDO_TOOL_CALL_STARTS
                ),
            ]
            starts = [(idx, prefix, kind) for idx, prefix, kind in starts if idx != -1]
            if starts:
                next_index, prefix, kind = min(starts, key=lambda item: item[0])
                visible_parts.append(self._buffer[:next_index])
                self._buffer = self._buffer[next_index + len(prefix) :]
                if kind in {"internal", "commentary", "plan_check"}:
                    self._inside_internal_block = True
                    self._internal_block_end = {
                        "commentary": _COMMENTARY_END,
                        "plan_check": _PLAN_CHECK_END,
                    }.get(kind, _INTERNAL_REMINDER_END)
                elif kind == "json_fence":
                    self._inside_json_fence = True
                else:
                    self._inside_pseudo_tool_call = True
                continue

            keep = _longest_suffix_prefix_match_any(
                self._buffer,
                (
                    _INTERNAL_REMINDER_START,
                    _COMMENTARY_START,
                    _PLAN_CHECK_START,
                    _JSON_FENCE_START,
                    *_PSEUDO_TOOL_CALL_STARTS,
                ),
            )
            emit_until = len(self._buffer) - keep
            visible_parts.append(self._buffer[:emit_until])
            self._buffer = self._buffer[emit_until:]
            break

        return self._filter_internal_tool_lines("".join(visible_parts))

    def flush(self) -> str:
        """Return any safe buffered text and discard unterminated internals."""
        if self._inside_internal_block or self._inside_pseudo_tool_call:
            self._buffer = ""
            self._json_fence_buffer = ""
            self._line_buffer = ""
            self._inside_internal_block = False
            self._inside_pseudo_tool_call = False
            self._internal_block_end = _INTERNAL_REMINDER_END
            return ""
        if self._inside_json_fence:
            text = self._json_fence_buffer + self._buffer
            self._buffer = ""
            self._json_fence_buffer = ""
            self._inside_json_fence = False
            if _looks_like_pseudo_tool_json(text):
                return ""
            return self._filter_internal_tool_lines(
                f"{_JSON_FENCE_START}{text}", final=True
            )

        text = self._buffer
        self._buffer = ""
        return self._filter_internal_tool_lines(text, final=True)

    def _filter_internal_tool_lines(self, text: str, *, final: bool = False) -> str:
        """Drop leaked internal operation lines for Brand Strategy chat only."""
        if not self._suppress_internal_tool_lines:
            return text

        self._line_buffer += text
        visible_lines: list[str] = []
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            line_with_newline = f"{line}\n"
            if not _looks_like_internal_tool_line(line):
                visible_lines.append(line_with_newline)

        if final and self._line_buffer:
            line = self._line_buffer
            self._line_buffer = ""
            if not _looks_like_internal_tool_line(line):
                visible_lines.append(line)

        return "".join(visible_lines)


class _AgentTurnTraceBuilder:
    """Accumulate the reasoning timeline for one agent turn.

    The web UI subscribes to live SSE events to draw the timeline while
    a turn is streaming. After page reload the same shape has to be
    reconstructable from disk — the live event queue is gone — so the
    bridge mirrors every thinking chunk and tool call into this builder
    and snapshots it into :class:`PersistedAgentTurn` when the stream
    closes.

    The merge rule for thinking blocks matches the client-side
    ``_append_thinking`` helper in ``web/brandmind_web/state.py``:
    consecutive thinking chunks roll up into the trailing entry until
    the producer flips ``done=True``; the next thinking event after
    that opens a new entry.
    """

    def __init__(self) -> None:
        self._entries: list[PersistedTimelineEntry] = []
        self._tool_entries: ToolCallMatcher[PersistedTimelineEntry] = ToolCallMatcher()
        self._thinking_open = False

    def on_thinking(self, token: str, done: bool) -> None:
        """Fold one streamed thinking chunk into the trailing entry.

        Consecutive thinking tokens with ``done=False`` collapse into a
        single timeline entry so the rehydrated bubble shows the same
        reasoning blocks the live stream rendered. A ``done=True`` flag
        closes the entry so the next thinking chunk opens a fresh one.

        Args:
            token (str): Visible thinking text just emitted upstream.
            done (bool): Whether this chunk closes the current thinking
                block.
        """
        if token:
            if self._thinking_open and self._entries:
                tail = self._entries[-1]
                if tail.kind == "thinking":
                    tail.thinking_text = f"{tail.thinking_text}{token}"
                else:
                    self._entries.append(
                        PersistedTimelineEntry(
                            kind="thinking",
                            thinking_text=token,
                        )
                    )
                    self._thinking_open = True
            else:
                self._entries.append(
                    PersistedTimelineEntry(
                        kind="thinking",
                        thinking_text=token,
                    )
                )
                self._thinking_open = True
        if done:
            self._thinking_open = False

    def on_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        tool_call_id: str = "",
    ) -> None:
        """Open a tool entry in the timeline with the args the agent sent.

        Tool calls always close any in-flight thinking block — the SSE
        stream interleaves the two in chronological order, and the
        client renders them as separate timeline nodes.

        Args:
            tool_name (str): Identifier of the dispatched tool.
            arguments (dict): JSON-serialisable invocation payload.
            tool_call_id (str): Provider id used to match out-of-order
                result events from concurrent calls of the same tool.
        """
        entry = PersistedTimelineEntry(
            kind="tool_call",
            tool_call=PersistedToolCall(
                tool_name=tool_name,
                arguments=dict(arguments),
            ),
        )
        self._entries.append(entry)
        self._tool_entries.add(tool_name, entry, tool_call_id)
        self._thinking_open = False

    def on_tool_result(
        self,
        tool_name: str,
        result: str,
        tool_call_id: str = "",
    ) -> None:
        """Settle the matching tool entry for one result event.

        Provider ids are the primary correlation key. FIFO by tool name
        remains as a compatibility fallback for older callback events
        that did not carry ids.

        Args:
            tool_name (str): Identifier of the tool whose result arrived.
            result (str): Stringified result body.
            tool_call_id (str): Provider id copied from the original
                tool-call request when available.
        """
        entry = self._tool_entries.pop(tool_name, tool_call_id)
        if entry is None or entry.tool_call is None:
            return
        entry.tool_call.result = result

    def finalize(self, duration_seconds: float) -> PersistedAgentTurn:
        """Snapshot the accumulated trace as a persisted-turn record.

        Fills the placeholder ``"(done)"`` result for any tool entry the
        backend never emitted a ``tool_result`` for (fire-and-forget
        tools such as ``write_todos`` are common) so the rehydrated UI
        does not render them as stuck on "running".

        Args:
            duration_seconds (float): Wall-clock duration of the turn,
                used to render the collapsed "Thought for …" cap.

        Returns:
            turn (PersistedAgentTurn): Frozen reasoning trace plus
            formatted duration label for storage on the session.
        """
        for entry in self._entries:
            if (
                entry.kind == "tool_call"
                and entry.tool_call is not None
                and entry.tool_call.result == ""
            ):
                entry.tool_call.result = "(done)"
        return PersistedAgentTurn(
            timeline=list(self._entries),
            duration_label=format_turn_duration(duration_seconds),
        )


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
        response_segment: list[str] = []
        hold_response_segments = session.mode is SessionMode.BRAND_STRATEGY
        suppress_internal_tool_lines = session.mode is SessionMode.BRAND_STRATEGY
        response_filter = _InternalReminderFilter(
            suppress_internal_tool_lines=suppress_internal_tool_lines
        )
        thinking_filter = _InternalReminderFilter(
            suppress_internal_tool_lines=suppress_internal_tool_lines
        )
        filters_flushed = False

        async def _emit_response_text(text: str) -> None:
            if hold_response_segments:
                response_segment.append(text)
                return

            accumulated_response.append(text)
            await event_queue.put(StreamingTokenEvent(token=text))

        async def _discard_response_segment() -> None:
            nonlocal response_filter
            response_segment.clear()
            response_filter = _InternalReminderFilter(
                suppress_internal_tool_lines=suppress_internal_tool_lines
            )

        async def _flush_visible_text() -> None:
            nonlocal filters_flushed
            if filters_flushed:
                return

            thinking_tail = thinking_filter.flush()
            if thinking_tail:
                await event_queue.put(StreamingThinkingEvent(token=thinking_tail))

            response_tail = response_filter.flush()
            if response_tail:
                await _emit_response_text(response_tail)

            if hold_response_segments:
                response_text = "".join(response_segment)
                if response_text:
                    accumulated_response.append(response_text)
                    await event_queue.put(StreamingTokenEvent(token=response_text))
                response_segment.clear()

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
                                    await _emit_response_text(visible_text)

                    elif isinstance(chunk.content, str) and chunk.content:
                        visible_text = response_filter.feed(chunk.content)
                        if visible_text:
                            if not thinking_done:
                                await event_queue.put(
                                    StreamingThinkingEvent(token="", done=True)
                                )
                                thinking_done = True
                            await _emit_response_text(visible_text)

                    if chunk.tool_calls:
                        if hold_response_segments:
                            await _discard_response_segment()
                        if not thinking_done:
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

        trace_builder = _AgentTurnTraceBuilder()
        turn_started_at = asyncio.get_event_loop().time()
        ai_messages_at_start = sum(
            1 for m in session.messages if isinstance(m, AIMessage)
        )

        # Consumer: yield events until stream end
        try:
            while True:
                event = await event_queue.get()
                if isinstance(event, _StreamEnd):
                    break
                if isinstance(event, StreamingThinkingEvent):
                    trace_builder.on_thinking(event.token, event.done)
                elif isinstance(event, ToolCallEvent):
                    trace_builder.on_tool_call(
                        event.tool_name,
                        event.arguments,
                        event.tool_call_id,
                    )
                elif isinstance(event, ToolResultEvent):
                    trace_builder.on_tool_result(
                        event.tool_name,
                        event.result,
                        event.tool_call_id,
                    )
                yield event
        finally:
            if not producer.done():
                producer.cancel()
            bs = session.brand_strategy_session
            if session.mode is SessionMode.BRAND_STRATEGY and bs is not None:
                ai_messages_now = sum(
                    1 for m in session.messages if isinstance(m, AIMessage)
                )
                if ai_messages_now > ai_messages_at_start:
                    duration = max(
                        0.0,
                        asyncio.get_event_loop().time() - turn_started_at,
                    )
                    bs.agent_traces.append(trace_builder.finalize(duration))
                    manager.persist_session(session)

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
    pending_tool_arguments: ToolCallMatcher[dict[str, Any]] = ToolCallMatcher()

    async for event in stream_agent_response(session, content, manager):
        if isinstance(event, StreamingTokenEvent):
            if event.token and not event.done:
                response_tokens.append(event.token)
        elif isinstance(event, ToolCallEvent):
            pending_tool_arguments.add(
                event.tool_name,
                dict(event.arguments),
                event.tool_call_id,
            )
        elif isinstance(event, ToolResultEvent):
            arguments = pending_tool_arguments.pop(
                event.tool_name,
                event.tool_call_id,
            )
            tool_calls.append(
                ToolCallInfo(
                    tool_name=event.tool_name,
                    arguments=arguments or {},
                    result=event.result,
                )
            )

    return MessageResponse(
        response="".join(response_tokens),
        metadata=session.to_session_info().metadata,
        tool_calls=tool_calls,
    )
