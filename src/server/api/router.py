"""API router aggregation — includes all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from server.api.artifacts import router as artifacts_router
from server.api.chat import router as chat_router
from server.api.health import router as health_router
from server.api.search import router as search_router
from server.api.sessions import router as sessions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(chat_router)
api_router.include_router(search_router)
api_router.include_router(artifacts_router)
