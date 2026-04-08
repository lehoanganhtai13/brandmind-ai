"""FastAPI application for BrandMind API server.

Entry point: create_app() returns a configured FastAPI instance.
The SessionManager is initialized during lifespan and stored in app.state.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.config import ServerConfig
from server.services.session_manager import SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage server lifecycle — init and cleanup SessionManager."""
    config = ServerConfig()
    manager = SessionManager(ttl_seconds=config.session_ttl)
    await manager.start()
    app.state.session_manager = manager
    yield
    await manager.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app with all routes and lifespan.
    """
    app = FastAPI(
        title="BrandMind API Server",
        version="0.1.0",
        description=(
            "HTTP/SSE API for BrandMind's agent capabilities. "
            "Manages sessions, streams events, and enables "
            "programmatic access for evaluation and clients."
        ),
        lifespan=lifespan,
    )

    from server.api.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    return app
