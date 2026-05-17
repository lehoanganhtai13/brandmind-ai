"""Session CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from server.dependencies import get_session_manager
from server.schemas.session import (
    CreateSessionRequest,
    GenerateTitleRequest,
    SessionInfo,
    SessionMessage,
    SessionMessages,
    UpdateSessionRequest,
)
from server.services.chat_title import generate_chat_title
from server.services.session_manager import SessionManager

router = APIRouter(tags=["sessions"])


def _extract_text_content(message: BaseMessage) -> str:
    """Flatten a LangChain message body to plain text for wire transport.

    AIMessage.content can be either a string or a list of content blocks
    (used when the model emits tool calls alongside text). The web UI
    only consumes user-visible prose, so this collapses block lists to
    their concatenated ``text`` fields and ignores tool-call blocks.
    """
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


@router.post("/sessions", status_code=201)
async def create_session(
    body: CreateSessionRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    """Create a new session with the specified mode."""
    return await manager.create_session(body.mode)


@router.get("/sessions")
async def list_sessions(
    manager: SessionManager = Depends(get_session_manager),
) -> list[SessionInfo]:
    """List all active sessions."""
    return await manager.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    """Get session info by ID."""
    try:
        return await manager.get_session_info(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionMessages:
    """Return the user/agent turn history for a persistent session.

    Powers the web client's "switch chat" affordance — when the user
    picks an older session from the sidebar, the web UI repaints its
    scroll from this payload. System messages and tool results are
    omitted because they belong to the live SSE stream, not the
    saved chat record.
    """
    try:
        session = await manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    history: list[SessionMessage] = []
    for raw in session.messages:
        if isinstance(raw, HumanMessage):
            history.append(
                SessionMessage(role="user", content=_extract_text_content(raw))
            )
        elif isinstance(raw, AIMessage):
            text = _extract_text_content(raw)
            if text:
                history.append(SessionMessage(role="agent", content=text))
    return SessionMessages(session_id=session_id, messages=history)


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    """Apply a partial update to a brand-strategy session's UX metadata.

    Powers manual rename + pin from the chat picker. ``None`` fields
    in the request are left untouched; explicit empty strings clear
    the title back to the placeholder.
    """
    try:
        session = await manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    bs = session.brand_strategy_session
    if bs is None:
        raise HTTPException(
            status_code=400,
            detail="Only brand-strategy sessions carry UX metadata",
        )
    if body.title is not None:
        bs.title = body.title.strip()
    if body.pinned is not None:
        bs.pinned = bool(body.pinned)
    return session.to_session_info()


@router.post("/sessions/{session_id}/title")
async def auto_generate_title(
    session_id: str,
    body: GenerateTitleRequest | None = None,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    """Generate and persist a 3–4 word title for the session.

    Falls back to the first persisted ``HumanMessage`` when the request
    body omits ``message``. When Gemini returns an empty response the
    session is left unchanged so the sidebar keeps its ``Untitled``
    placeholder rather than locking in a bad label.
    """
    try:
        session = await manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    bs = session.brand_strategy_session
    if bs is None:
        raise HTTPException(
            status_code=400,
            detail="Only brand-strategy sessions support auto-titling",
        )
    source: str | None = body.message if body and body.message else None
    if source is None:
        source = _first_user_text(session.messages)
    if not source:
        raise HTTPException(
            status_code=400,
            detail="No first user message available to title from",
        )
    new_title = await generate_chat_title(source)
    if new_title:
        bs.title = new_title
    return session.to_session_info()


def _first_user_text(messages: list[BaseMessage]) -> str | None:
    """Return the text content of the earliest ``HumanMessage`` if any."""
    for message in messages:
        if isinstance(message, HumanMessage):
            return _extract_text_content(message)
    return None


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """Delete a session and clean up resources."""
    try:
        await manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    await manager.delete_session(session_id)
