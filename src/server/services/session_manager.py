"""Session management for BrandMind API server.

Holds agent instances in memory across turns, manages session lifecycle,
and provides concurrency control for the _active_session global.
"""

from __future__ import annotations

import asyncio
import shutil
import uuid
from asyncio import Queue
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from config.system_config import SETTINGS
from core.brand_strategy.session import (
    BrandStrategySession,
    get_phase_display_labels,
    get_phase_sequence,
    save_session,
)
from server.schemas.enums import SessionMode
from server.schemas.session import (
    AskSessionMetadata,
    BrandStrategyMetadata,
    SessionInfo,
)
from server.services.agent_factory import create_agent_for_session
from shared.agent_middlewares.callback_types import BaseAgentEvent
from shared.workspace import BRANDMIND_HOME


def _is_pinned(info: SessionInfo) -> bool:
    """Return whether a session's metadata flags it as pinned."""
    metadata = info.metadata
    return bool(getattr(metadata, "pinned", False))


def _sort_timestamp(info: SessionInfo) -> float:
    """Return ``-epoch(created_at)`` so newer sessions sort first."""
    try:
        return -info.created_at.timestamp()
    except (AttributeError, OSError, ValueError):
        return 0.0


def _delete_workspace_dir(bs_session_id: str) -> None:
    """Remove ``~/.brandmind/projects/{bs_session_id}/`` if it is safe to.

    The path-containment guard refuses to follow symlinks or escape
    the projects root so a corrupted session id cannot delete data
    outside the BrandMind home directory.
    """
    projects_root = (BRANDMIND_HOME / "projects").resolve()
    target = (projects_root / bs_session_id).resolve()
    if not target.exists() or not target.is_dir():
        return
    try:
        target.relative_to(projects_root)
    except ValueError:
        logger.warning(f"Refusing to delete workspace outside projects root: {target}")
        return
    if target == projects_root:
        logger.warning("Refusing to delete projects root itself")
        return
    shutil.rmtree(target)
    logger.info(f"Removed workspace dir: {target}")


class EventRouter:
    """Mutable callback that routes middleware events to the current queue.

    Problem: Agent is created ONCE per session with a fixed callback.
    But each message creates a new streaming bridge with a new Queue.
    The callback must route events to the CURRENT message's queue.

    Solution: Agent receives this router as its callback. Before each
    message, call set_queue(new_queue) to redirect events. After the
    message, call clear_queue() to prevent stale references.
    """

    def __init__(self) -> None:
        self._queue: Queue[BaseAgentEvent] | None = None

    def set_queue(self, queue: Queue[BaseAgentEvent]) -> None:
        """Redirect middleware events to the given queue."""
        self._queue = queue

    def clear_queue(self) -> None:
        """Stop routing events (prevents stale references)."""
        self._queue = None

    def __call__(self, event: BaseAgentEvent) -> None:
        """Callback invoked by LogModelMessageMiddleware."""
        if self._queue is not None:
            self._queue.put_nowait(event)


@dataclass
class ManagedSession:
    """Internal session state held in memory.

    Each session holds:
    - An agent instance (lazy-initialized on first message)
    - An EventRouter (mutable callback for middleware events)
    - Message history (LangChain messages)
    - Mode-specific state (BrandStrategySession for brand-strategy)
    - A per-session Lock for serializing concurrent requests
    """

    session_id: str
    mode: SessionMode
    created_at: datetime
    last_active: float

    agent: CompiledStateGraph | None = None
    event_router: EventRouter = field(default_factory=EventRouter)
    messages: list[BaseMessage] = field(default_factory=list)
    brand_strategy_session: BrandStrategySession | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def message_count(self) -> int:
        """Count user-visible messages (those with content)."""
        return sum(1 for m in self.messages if hasattr(m, "content"))

    def to_session_info(self) -> SessionInfo:
        """Convert to API response model with typed metadata."""
        if (
            self.mode is SessionMode.BRAND_STRATEGY
            and self.brand_strategy_session is not None
        ):
            bs = self.brand_strategy_session
            metadata: AskSessionMetadata | BrandStrategyMetadata = (
                BrandStrategyMetadata(
                    current_phase=bs.current_phase,
                    scope=bs.scope,
                    brand_name=bs.brand_name,
                    completed_phases=list(bs.completed_phases),
                    phase_sequence=get_phase_sequence(bs.scope),
                    phase_display_labels=get_phase_display_labels(bs.scope),
                    title=bs.title,
                    pinned=bs.pinned,
                )
            )
        else:
            metadata = AskSessionMetadata()

        return SessionInfo(
            session_id=self.session_id,
            mode=self.mode,
            created_at=self.created_at,
            message_count=self.message_count,
            metadata=metadata,
        )

    def ensure_agent(self) -> CompiledStateGraph:
        """Lazy-create agent on first use.

        The agent's middleware callback is the EventRouter — a mutable
        wrapper. Before each message, the streaming bridge calls
        event_router.set_queue() to redirect events to that message's
        Queue.

        For brand-strategy mode: the CALLER (streaming bridge) must
        acquire brand_strategy_lock and call set_active_session()
        BEFORE calling this method.
        """
        if self.agent is None:
            from cli.tool_context import (
                reset_current_tool,
                set_current_tool,
            )

            self.agent = create_agent_for_session(
                mode=self.mode,
                callback=self.event_router,
                on_tool_start=set_current_tool,
                on_tool_end=reset_current_tool,
            )
        return self.agent


class SessionManager:
    """Manages agent sessions in memory with TTL-based eviction.

    Concurrency model:
    - _registry_lock: protects the _sessions dict (create/delete/list)
    - ManagedSession.lock: serializes messages within a single session
    - _brand_strategy_lock: serializes ALL brand-strategy invocations
      globally (required because set_active_session() is module-level)
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: dict[str, ManagedSession] = {}
        self._registry_lock = asyncio.Lock()
        self._brand_strategy_lock = asyncio.Lock()
        self._ttl = ttl_seconds
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop cleanup task and persist brand-strategy sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        for session in self._sessions.values():
            if session.brand_strategy_session is not None:
                save_session(session.brand_strategy_session)
        self._sessions.clear()

    async def create_session(self, mode: SessionMode) -> SessionInfo:
        """Create a new session with the given mode.

        For brand-strategy mode, BrandStrategySession is initialized
        eagerly so session info has metadata immediately. The API
        ``session_id`` is forwarded as the brand-strategy session id
        so the workspace directory and persisted JSON share the
        identifier the web URL already exposes.
        """
        session_id = str(uuid.uuid4())[:8]
        now = asyncio.get_event_loop().time()
        managed = ManagedSession(
            session_id=session_id,
            mode=mode,
            created_at=datetime.now(),
            last_active=now,
        )
        if mode is SessionMode.BRAND_STRATEGY:
            managed.brand_strategy_session = BrandStrategySession(
                session_id=session_id,
            )

        async with self._registry_lock:
            self._sessions[session_id] = managed
        return managed.to_session_info()

    async def get_session(self, session_id: str) -> ManagedSession:
        """Get a managed session by ID.

        Raises:
            KeyError: If the session does not exist.
        """
        async with self._registry_lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")
        return session

    async def get_session_info(self, session_id: str) -> SessionInfo:
        """Get session info (API response model) by ID."""
        session = await self.get_session(session_id)
        return session.to_session_info()

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions, pinned chats first then newest-first.

        The web sidebar reads this directly; sorting on the server keeps
        every client (CLI, web, future mobile) consistent without each
        re-implementing the order.
        """
        async with self._registry_lock:
            infos = [s.to_session_info() for s in self._sessions.values()]
        infos.sort(
            key=lambda info: (
                not _is_pinned(info),
                _sort_timestamp(info),
            ),
        )
        return infos

    async def delete_session(
        self,
        session_id: str,
        delete_workspace: bool | None = None,
    ) -> None:
        """Delete a session, persisting state and optionally clearing disk.

        Brand-strategy state is always saved before eviction so the
        agent's prior work survives. The workspace directory is removed
        when ``delete_workspace`` is explicitly ``True``; an explicit
        ``False`` keeps it on disk regardless of the install default;
        ``None`` falls back to
        :data:`SETTINGS.BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE`.
        """
        async with self._registry_lock:
            session = self._sessions.pop(session_id, None)
        if session is None or session.brand_strategy_session is None:
            return
        bs = session.brand_strategy_session
        save_session(bs)
        if delete_workspace is None:
            should_delete = SETTINGS.BRANDMIND_DELETE_WORKSPACE_ON_CHAT_DELETE
        else:
            should_delete = delete_workspace
        if should_delete:
            _delete_workspace_dir(bs.session_id)

    @property
    def brand_strategy_lock(self) -> asyncio.Lock:
        """Global lock for brand-strategy invocations.

        The streaming bridge acquires this before calling
        set_active_session() + agent invocation. This ensures
        the module-level _active_session global is not corrupted
        by concurrent brand-strategy sessions.
        """
        return self._brand_strategy_lock

    async def _cleanup_loop(self) -> None:
        """Periodically evict sessions idle longer than TTL."""
        while True:
            await asyncio.sleep(60)
            now = asyncio.get_event_loop().time()
            async with self._registry_lock:
                expired = [
                    sid
                    for sid, s in self._sessions.items()
                    if now - s.last_active > self._ttl
                ]
                for sid in expired:
                    session = self._sessions.pop(sid)
                    if session.brand_strategy_session is not None:
                        save_session(session.brand_strategy_session)
