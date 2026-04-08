"""FastAPI dependency injection factories."""

from __future__ import annotations

from fastapi import Request

from server.services.session_manager import SessionManager


def get_session_manager(request: Request) -> SessionManager:
    """Get the SessionManager singleton from app state.

    Injected via FastAPI's Depends() mechanism.
    The SessionManager is initialized during app lifespan.
    """
    return request.app.state.session_manager
