"""Unit tests for BrandMind API server.

Tests cover:
- SessionManager lifecycle (create, get, list, delete, TTL)
- EventRouter (set_queue, clear_queue, callback routing)
- Agent factory registry
- API routes (CRUD, health, validation)
- Pydantic schema validation
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from server.main import create_app
from server.schemas.chat import MessageResponse, ToolCallInfo
from server.schemas.enums import SessionMode, SSEEventType
from server.schemas.events import StreamDoneEvent
from server.schemas.session import (
    AskSessionMetadata,
    BrandStrategyMetadata,
    CreateSessionRequest,
    SessionInfo,
)
from server.services.agent_factory import (
    _AGENT_FACTORIES,
    create_agent_for_session,
)
from server.services.session_manager import (
    EventRouter,
    ManagedSession,
    SessionManager,
)
from shared.agent_middlewares.callback_types import (
    StreamingTokenEvent,
    ToolCallEvent,
)


# ── SessionMode Enum ─────────────────────────────────────────────────


class TestSessionModeEnum:
    """Verify SessionMode enum values and behavior."""

    def test_values(self):
        assert SessionMode.ASK.value == "ask"
        assert SessionMode.BRAND_STRATEGY.value == "brand-strategy"

    def test_from_string(self):
        assert SessionMode("ask") is SessionMode.ASK
        assert SessionMode("brand-strategy") is SessionMode.BRAND_STRATEGY

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            SessionMode("invalid")

    def test_is_str(self):
        assert isinstance(SessionMode.ASK, str)
        assert SessionMode.ASK == "ask"


class TestSSEEventTypeEnum:
    """Verify SSEEventType enum completeness."""

    def test_all_types_present(self):
        expected = {
            "model_loading",
            "thinking",
            "streaming_thinking",
            "tool_call",
            "tool_result",
            "todo_update",
            "streaming_token",
            "done",
        }
        actual = {e.value for e in SSEEventType}
        assert actual == expected


# ── EventRouter ──────────────────────────────────────────────────────


class TestEventRouter:
    """Verify EventRouter callback routing."""

    def test_routes_to_queue(self):
        router = EventRouter()
        queue: asyncio.Queue = asyncio.Queue()
        router.set_queue(queue)

        event = StreamingTokenEvent(token="hello")
        router(event)

        assert not queue.empty()
        received = queue.get_nowait()
        assert received.token == "hello"

    def test_no_queue_no_error(self):
        router = EventRouter()
        event = StreamingTokenEvent(token="hello")
        router(event)  # Should not raise

    def test_clear_queue(self):
        router = EventRouter()
        queue: asyncio.Queue = asyncio.Queue()
        router.set_queue(queue)
        router.clear_queue()

        event = StreamingTokenEvent(token="hello")
        router(event)

        assert queue.empty()

    def test_redirect_queue(self):
        router = EventRouter()
        q1: asyncio.Queue = asyncio.Queue()
        q2: asyncio.Queue = asyncio.Queue()

        router.set_queue(q1)
        router(StreamingTokenEvent(token="to_q1"))

        router.set_queue(q2)
        router(StreamingTokenEvent(token="to_q2"))

        assert q1.get_nowait().token == "to_q1"
        assert q2.get_nowait().token == "to_q2"
        assert q1.empty()
        assert q2.empty()


# ── SessionManager ───────────────────────────────────────────────────


class TestSessionManager:
    """Verify SessionManager CRUD operations."""

    @pytest.fixture
    def manager(self):
        return SessionManager(ttl_seconds=5)

    @pytest.mark.asyncio
    async def test_create_ask_session(self, manager):
        info = await manager.create_session(SessionMode.ASK)
        assert info.mode is SessionMode.ASK
        assert info.message_count == 0
        assert isinstance(info.metadata, AskSessionMetadata)

    @pytest.mark.asyncio
    async def test_create_brand_strategy_session(self, manager):
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        assert info.mode is SessionMode.BRAND_STRATEGY
        assert isinstance(info.metadata, BrandStrategyMetadata)
        assert info.metadata.current_phase == "phase_0"

    @pytest.mark.asyncio
    async def test_get_session(self, manager):
        info = await manager.create_session(SessionMode.ASK)
        session = await manager.get_session(info.session_id)
        assert session.session_id == info.session_id
        assert session.agent is None  # Not yet initialized

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, manager):
        with pytest.raises(KeyError):
            await manager.get_session("nonexistent")

    @pytest.mark.asyncio
    async def test_list_sessions(self, manager):
        await manager.create_session(SessionMode.ASK)
        await manager.create_session(SessionMode.BRAND_STRATEGY)
        sessions = await manager.list_sessions()
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_delete_session(self, manager):
        info = await manager.create_session(SessionMode.ASK)
        await manager.delete_session(info.session_id)
        with pytest.raises(KeyError):
            await manager.get_session(info.session_id)

    @pytest.mark.asyncio
    async def test_brand_strategy_lock_exists(self, manager):
        lock = manager.brand_strategy_lock
        assert isinstance(lock, asyncio.Lock)


# ── Agent Factory ────────────────────────────────────────────────────


class TestAgentFactory:
    """Verify agent factory registry."""

    def test_both_modes_registered(self):
        assert SessionMode.ASK in _AGENT_FACTORIES
        assert SessionMode.BRAND_STRATEGY in _AGENT_FACTORIES

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="No agent factory"):
            create_agent_for_session(mode="unknown")


# ── Pydantic Schemas ─────────────────────────────────────────────────


class TestSchemas:
    """Verify Pydantic schema validation."""

    def test_create_session_request_valid(self):
        req = CreateSessionRequest(mode=SessionMode.ASK)
        assert req.mode is SessionMode.ASK

    def test_create_session_request_invalid_mode(self):
        with pytest.raises(Exception):
            CreateSessionRequest(mode="invalid")

    def test_session_info_with_ask_metadata(self):
        info = SessionInfo(
            session_id="test",
            mode=SessionMode.ASK,
            created_at=datetime.now(),
            message_count=0,
            metadata=AskSessionMetadata(),
        )
        data = info.model_dump()
        assert data["mode"] == "ask"
        assert data["metadata"] == {}

    def test_session_info_with_bs_metadata(self):
        info = SessionInfo(
            session_id="test",
            mode=SessionMode.BRAND_STRATEGY,
            created_at=datetime.now(),
            message_count=5,
            metadata=BrandStrategyMetadata(
                current_phase="phase_1",
                scope="new_brand",
                brand_name="Test",
                completed_phases=["phase_0"],
            ),
        )
        data = info.model_dump()
        assert data["metadata"]["current_phase"] == "phase_1"
        assert data["metadata"]["scope"] == "new_brand"

    def test_message_response(self):
        resp = MessageResponse(
            response="Hello",
            metadata=AskSessionMetadata(),
            tool_calls=[
                ToolCallInfo(
                    tool_name="search",
                    arguments={"q": "test"},
                    result="found",
                )
            ],
        )
        assert resp.response == "Hello"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool_name == "search"

    def test_stream_done_event(self):
        done = StreamDoneEvent(
            response="Full text",
            metadata=BrandStrategyMetadata(
                current_phase="phase_2",
            ),
            tool_calls=[],
        )
        assert done.type == "done"
        data = done.model_dump_json()
        assert '"done"' in data


# ── API Routes ───────────────────────────────────────────────────────


class TestAPIRoutes:
    """Verify FastAPI route behavior."""

    @pytest.fixture
    def client(self):
        app = create_app()
        with TestClient(app) as c:
            yield c

    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_create_ask_session(self, client):
        resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        assert resp.status_code == 201
        assert resp.json()["mode"] == "ask"

    def test_create_brand_strategy_session(self, client):
        resp = client.post(
            "/api/v1/sessions", json={"mode": "brand-strategy"}
        )
        assert resp.status_code == 201
        assert resp.json()["metadata"]["current_phase"] == "phase_0"

    def test_create_invalid_mode(self, client):
        resp = client.post("/api/v1/sessions", json={"mode": "invalid"})
        assert resp.status_code == 422

    def test_list_sessions(self, client):
        client.post("/api/v1/sessions", json={"mode": "ask"})
        resp = client.get("/api/v1/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_session(self, client):
        create_resp = client.post(
            "/api/v1/sessions", json={"mode": "ask"}
        )
        sid = create_resp.json()["session_id"]
        resp = client.get(f"/api/v1/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == sid

    def test_get_session_not_found(self, client):
        resp = client.get("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404

    def test_delete_session(self, client):
        create_resp = client.post(
            "/api/v1/sessions", json={"mode": "ask"}
        )
        sid = create_resp.json()["session_id"]
        resp = client.delete(f"/api/v1/sessions/{sid}")
        assert resp.status_code == 204

    def test_delete_session_not_found(self, client):
        resp = client.delete("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404
