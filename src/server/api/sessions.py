"""Session CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from server.dependencies import get_session_manager
from server.schemas.session import CreateSessionRequest, SessionInfo
from server.services.session_manager import SessionManager

router = APIRouter(tags=["sessions"])


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
