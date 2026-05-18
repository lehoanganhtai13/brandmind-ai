"""Message endpoint — send message to session (JSON or SSE stream)."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse

from server.dependencies import get_session_manager
from server.schemas.chat import MessageRequest, MessageResponse, ToolCallInfo
from server.schemas.events import StreamDoneEvent
from server.services.session_manager import ManagedSession, SessionManager
from server.streaming.bridge import (
    collect_agent_response,
    stream_agent_response,
)
from server.streaming.tool_call_matching import ToolCallMatcher
from shared.agent_middlewares.callback_types import (
    StreamingTokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)

router = APIRouter(tags=["chat"])


@router.post("/sessions/{session_id}/message", response_model=None)
async def send_message(
    session_id: str,
    body: MessageRequest,
    request: Request,
    stream: bool = False,
    manager: SessionManager = Depends(get_session_manager),
) -> MessageResponse | EventSourceResponse:
    """Send a message to a session.

    Args:
        session_id: Target session ID.
        body: Message content.
        stream: If true, return SSE stream. If false, return JSON.
        manager: SessionManager dependency.

    Returns:
        MessageResponse (JSON) or EventSourceResponse (SSE).
    """
    try:
        session = await manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if session is busy (Lock already held)
    if session.lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Session is busy processing another message",
        )

    if stream:
        return EventSourceResponse(
            _sse_event_generator(session, body.content, manager, request),
            ping=15,
        )
    else:
        return await collect_agent_response(session, body.content, manager)


async def _sse_event_generator(
    session: ManagedSession,
    content: str,
    manager: SessionManager,
    request: Request,
) -> AsyncGenerator[dict[str, str], None]:
    """Convert BaseAgentEvent stream to SSE-formatted dicts.

    Yields dicts with 'event' and 'data' keys that sse-starlette
    serializes into SSE wire format.

    After all agent events, yields a 'done' event with the full
    response text and updated session metadata.
    """
    response_tokens: list[str] = []
    tool_calls: list[ToolCallInfo] = []
    pending_tool_arguments: ToolCallMatcher[dict[str, Any]] = ToolCallMatcher()

    try:
        async for event in stream_agent_response(session, content, manager):
            # Check client disconnect
            if await request.is_disconnected():
                break

            # Track response tokens for the done event
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

            # Yield SSE event
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }

        # Final done event with accumulated data
        done = StreamDoneEvent(
            response="".join(response_tokens),
            metadata=session.to_session_info().metadata,
            tool_calls=tool_calls,
        )
        yield {
            "event": "done",
            "data": done.model_dump_json(),
        }

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}),
        }
