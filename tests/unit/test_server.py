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
from langchain_core.messages import AIMessage, HumanMessage

from core.brand_strategy import session as brand_strategy_session_store
from core.brand_strategy.session import BrandStrategySession
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
    SessionManager,
)
from shared.agent_middlewares.callback_types import StreamingTokenEvent

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
    async def test_brand_strategy_metadata_carries_phase_sequence_for_scope(
        self, manager
    ):
        """SessionInfo must expose scope-specific phase sequence and labels."""
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        session.brand_strategy_session.scope = "refresh"

        refreshed = session.to_session_info()
        assert isinstance(refreshed.metadata, BrandStrategyMetadata)
        assert refreshed.metadata.phase_sequence == [
            "phase_0",
            "phase_0_5",
            "phase_1",
            "phase_3",
            "phase_4",
            "phase_5",
        ]
        assert (
            refreshed.metadata.phase_display_labels["phase_0_5"]
            == "Audit thương hiệu hiện có"
        )
        assert "phase_2" not in refreshed.metadata.phase_display_labels

    @pytest.mark.asyncio
    async def test_brand_strategy_metadata_unset_scope_returns_empty_phase_lists(
        self, manager
    ):
        """Until a scope is classified, the web UI must see empty sequence/labels."""
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)

        snapshot = session.to_session_info()
        assert isinstance(snapshot.metadata, BrandStrategyMetadata)
        assert snapshot.metadata.scope is None
        assert snapshot.metadata.phase_sequence == []
        assert snapshot.metadata.phase_display_labels == {}

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
    async def test_start_hydrates_persisted_brand_strategy_sessions(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Server start should restore saved brand-strategy chats into the sidebar."""
        monkeypatch.setattr(
            brand_strategy_session_store,
            "BRANDMIND_HOME",
            tmp_path / "home.brandmind",
        )
        saved = BrandStrategySession(
            session_id="persist1",
            brand_name="Chuyện Ba Bữa Signature",
            title="Signature strategy",
        )
        saved.messages = [
            HumanMessage(content="Tôi muốn làm brand strategy."),
            AIMessage(content="Mình bắt đầu từ chẩn đoán nhé."),
        ]
        brand_strategy_session_store.save_session(saved)

        fresh_manager = SessionManager(ttl_seconds=5)
        await fresh_manager.start()
        try:
            sessions = await fresh_manager.list_sessions()
            restored_info = next(
                info for info in sessions if info.session_id == "persist1"
            )
            assert restored_info.message_count == 2
            assert isinstance(restored_info.metadata, BrandStrategyMetadata)
            assert restored_info.metadata.brand_name == "Chuyện Ba Bữa Signature"

            restored = await fresh_manager.get_session("persist1")
            assert [message.type for message in restored.messages] == ["human", "ai"]
        finally:
            await fresh_manager.stop()

    @pytest.mark.asyncio
    async def test_get_session_lazily_hydrates_persisted_brand_strategy_session(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Direct session URLs should recover even before list hydration runs."""
        monkeypatch.setattr(
            brand_strategy_session_store,
            "BRANDMIND_HOME",
            tmp_path / "home.brandmind",
        )
        saved = BrandStrategySession(session_id="lazy1234", brand_name="Lazy Cafe")
        saved.messages = [HumanMessage(content="Xin chào")]
        brand_strategy_session_store.save_session(saved)

        fresh_manager = SessionManager(ttl_seconds=5)

        restored = await fresh_manager.get_session("lazy1234")

        assert restored.brand_strategy_session is not None
        assert restored.brand_strategy_session.brand_name == "Lazy Cafe"
        assert restored.messages[0].content == "Xin chào"

    @pytest.mark.asyncio
    async def test_delete_session(self, manager):
        info = await manager.create_session(SessionMode.ASK)
        await manager.delete_session(info.session_id)
        with pytest.raises(KeyError):
            await manager.get_session(info.session_id)

    @pytest.mark.asyncio
    async def test_delete_session_removes_persisted_brand_strategy_record(
        self,
        manager,
        tmp_path,
        monkeypatch,
    ):
        """Deleted chats should not reappear after the next server start."""
        monkeypatch.setattr(
            brand_strategy_session_store,
            "BRANDMIND_HOME",
            tmp_path / "home.brandmind",
        )
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        session.messages.append(HumanMessage(content="keep until delete"))
        manager.persist_session(session)
        assert brand_strategy_session_store.get_session_file(info.session_id).exists()

        await manager.delete_session(info.session_id, delete_workspace=False)

        assert not brand_strategy_session_store.get_session_file(
            info.session_id,
        ).exists()

    @pytest.mark.asyncio
    async def test_brand_strategy_lock_exists(self, manager):
        lock = manager.brand_strategy_lock
        assert isinstance(lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_brand_strategy_session_id_matches_api_id(self, manager):
        """API session_id is forwarded so disk paths share the URL id."""
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        assert session.brand_strategy_session.session_id == info.session_id

    @pytest.mark.asyncio
    async def test_delete_session_clears_workspace_when_flag_on(
        self, manager, tmp_path, monkeypatch
    ):
        """Cleanup runs only with the flag enabled and stays inside projects."""
        from server.services import session_manager as sm_module

        monkeypatch.setattr(sm_module, "BRANDMIND_HOME", tmp_path)
        monkeypatch.setattr(
            sm_module.SETTINGS,
            "BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE",
            True,
        )
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        bs_id = session.brand_strategy_session.session_id

        workspace = tmp_path / "projects" / bs_id / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text("scratch")

        await manager.delete_session(info.session_id)
        assert not (tmp_path / "projects" / bs_id).exists()

    @pytest.mark.asyncio
    async def test_delete_session_keeps_workspace_when_flag_off(
        self, manager, tmp_path, monkeypatch
    ):
        """Default off path leaves disk untouched for eval-pipeline safety."""
        from server.services import session_manager as sm_module

        monkeypatch.setattr(sm_module, "BRANDMIND_HOME", tmp_path)
        monkeypatch.setattr(
            sm_module.SETTINGS,
            "BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE",
            False,
        )
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        bs_id = session.brand_strategy_session.session_id

        workspace = tmp_path / "projects" / bs_id / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text("scratch")

        await manager.delete_session(info.session_id)
        assert workspace.exists()

    @pytest.mark.asyncio
    async def test_delete_workspace_explicit_true_overrides_flag_off(
        self, manager, tmp_path, monkeypatch
    ):
        """Per-request ``delete_workspace=True`` removes the dir."""
        from server.services import session_manager as sm_module

        monkeypatch.setattr(sm_module, "BRANDMIND_HOME", tmp_path)
        monkeypatch.setattr(
            sm_module.SETTINGS,
            "BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE",
            False,
        )
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        bs_id = session.brand_strategy_session.session_id

        workspace = tmp_path / "projects" / bs_id / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text("scratch")

        await manager.delete_session(info.session_id, delete_workspace=True)
        assert not (tmp_path / "projects" / bs_id).exists()

    @pytest.mark.asyncio
    async def test_delete_workspace_explicit_false_overrides_flag_on(
        self, manager, tmp_path, monkeypatch
    ):
        """Per-request ``delete_workspace=False`` keeps the dir."""
        from server.services import session_manager as sm_module

        monkeypatch.setattr(sm_module, "BRANDMIND_HOME", tmp_path)
        monkeypatch.setattr(
            sm_module.SETTINGS,
            "BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE",
            True,
        )
        info = await manager.create_session(SessionMode.BRAND_STRATEGY)
        session = await manager.get_session(info.session_id)
        assert session.brand_strategy_session is not None
        bs_id = session.brand_strategy_session.session_id

        workspace = tmp_path / "projects" / bs_id / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "brand_brief.md").write_text("scratch")

        await manager.delete_session(info.session_id, delete_workspace=False)
        assert workspace.exists()


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
    def client(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            brand_strategy_session_store,
            "BRANDMIND_HOME",
            tmp_path / "home.brandmind",
        )
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
        resp = client.post("/api/v1/sessions", json={"mode": "brand-strategy"})
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
        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        resp = client.get(f"/api/v1/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == sid

    def test_get_session_not_found(self, client):
        resp = client.get("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404

    def test_delete_session(self, client):
        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        resp = client.delete(f"/api/v1/sessions/{sid}")
        assert resp.status_code == 204

    def test_delete_session_not_found(self, client):
        resp = client.delete("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404

    def test_get_session_messages_empty(self, client):
        """Brand new session returns empty message history."""
        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        resp = client.get(f"/api/v1/sessions/{sid}/messages")
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == sid
        assert body["messages"] == []

    def test_get_session_messages_not_found(self, client):
        resp = client.get("/api/v1/sessions/nonexistent/messages")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_messages_after_turns(self, client):
        """Populating a session's message log surfaces through the endpoint."""
        from langchain_core.messages import AIMessage, HumanMessage

        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        manager = client.app.state.session_manager
        session = await manager.get_session(sid)
        session.messages.extend(
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
                HumanMessage(content="Tell me a joke"),
                AIMessage(
                    content=[
                        {"type": "text", "text": "Why did the chicken cross the road?"},
                        {"type": "tool_use", "name": "noop", "input": {}},
                    ]
                ),
            ]
        )
        resp = client.get(f"/api/v1/sessions/{sid}/messages")
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == sid
        history = body["messages"]
        assert [m["role"] for m in history] == ["user", "agent", "user", "agent"]
        assert history[0]["content"] == "Hello"
        assert history[3]["content"] == "Why did the chicken cross the road?"

    def test_patch_session_renames_and_pins(self, client):
        """PATCH updates title and pinned independently on brand-strategy sessions."""
        create_resp = client.post("/api/v1/sessions", json={"mode": "brand-strategy"})
        sid = create_resp.json()["session_id"]
        resp = client.patch(
            f"/api/v1/sessions/{sid}",
            json={"title": "Cafe Da Lat launch", "pinned": True},
        )
        assert resp.status_code == 200
        meta = resp.json()["metadata"]
        assert meta["title"] == "Cafe Da Lat launch"
        assert meta["pinned"] is True
        # Partial: send only pinned=False; title must survive.
        resp = client.patch(f"/api/v1/sessions/{sid}", json={"pinned": False})
        assert resp.status_code == 200
        meta = resp.json()["metadata"]
        assert meta["title"] == "Cafe Da Lat launch"
        assert meta["pinned"] is False

    def test_patch_session_not_found(self, client):
        resp = client.patch("/api/v1/sessions/nonexistent", json={"title": "X"})
        assert resp.status_code == 404

    def test_patch_session_rejects_ask_mode(self, client):
        """Ask sessions have no UX metadata target, so PATCH returns 400."""
        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        resp = client.patch(f"/api/v1/sessions/{sid}", json={"title": "X"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_auto_title_uses_persisted_first_user_message(
        self, client, monkeypatch
    ):
        """When no body is sent, the endpoint titles from the first HumanMessage."""
        from langchain_core.messages import HumanMessage

        from server.api import sessions as sessions_module

        async def fake_titler(text: str) -> str:
            assert text == "Tôi muốn mở một quán cà phê specialty ở Đà Lạt."
            return "Specialty cafe Da Lat"

        monkeypatch.setattr(sessions_module, "generate_chat_title", fake_titler)
        create_resp = client.post("/api/v1/sessions", json={"mode": "brand-strategy"})
        sid = create_resp.json()["session_id"]
        manager = client.app.state.session_manager
        session = await manager.get_session(sid)
        session.messages.append(
            HumanMessage(content="Tôi muốn mở một quán cà phê specialty ở Đà Lạt.")
        )
        resp = client.post(f"/api/v1/sessions/{sid}/title")
        assert resp.status_code == 200
        assert resp.json()["metadata"]["title"] == "Specialty cafe Da Lat"

    def test_auto_title_with_explicit_message(self, client, monkeypatch):
        """An explicit `message` in the body overrides the persisted lookup."""
        from server.api import sessions as sessions_module

        async def fake_titler(text: str) -> str:
            return text.split()[0] + " brief"

        monkeypatch.setattr(sessions_module, "generate_chat_title", fake_titler)
        create_resp = client.post("/api/v1/sessions", json={"mode": "brand-strategy"})
        sid = create_resp.json()["session_id"]
        resp = client.post(
            f"/api/v1/sessions/{sid}/title",
            json={"message": "Repositioning a heritage F&B brand"},
        )
        assert resp.status_code == 200
        assert resp.json()["metadata"]["title"] == "Repositioning brief"

    def test_auto_title_rejects_ask_mode(self, client):
        create_resp = client.post("/api/v1/sessions", json={"mode": "ask"})
        sid = create_resp.json()["session_id"]
        resp = client.post(f"/api/v1/sessions/{sid}/title")
        assert resp.status_code == 400

    def test_auto_title_no_source_message(self, client):
        """Brand-strategy session with no first user message + no body 400s."""
        create_resp = client.post("/api/v1/sessions", json={"mode": "brand-strategy"})
        sid = create_resp.json()["session_id"]
        resp = client.post(f"/api/v1/sessions/{sid}/title")
        assert resp.status_code == 400

    def test_list_sessions_orders_pinned_first(self, client):
        """list_sessions surfaces pinned chats before unpinned ones."""
        ids = []
        for _ in range(3):
            ids.append(
                client.post("/api/v1/sessions", json={"mode": "brand-strategy"}).json()[
                    "session_id"
                ]
            )
        # Pin only the middle one.
        client.patch(f"/api/v1/sessions/{ids[1]}", json={"pinned": True})
        resp = client.get("/api/v1/sessions")
        assert resp.status_code == 200
        # Filter to just the ones we created so concurrent tests don't pollute.
        ours = [s for s in resp.json() if s["session_id"] in ids]
        assert ours[0]["session_id"] == ids[1]
        assert ours[0]["metadata"]["pinned"] is True
