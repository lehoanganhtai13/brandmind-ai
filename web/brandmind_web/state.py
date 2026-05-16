"""Reflex state layer for the BrandMind Web UI.

Centralises session lifecycle (create / restore brand-strategy session
on first navigation), SSE stream consumption (dispatches each agent
event to the right state mutation), and UI preferences (sidebar
collapse) so the page-level component can stay focused on rendering.

The state subscribes to the design contract locked in
``docs/web_design.md`` § 9.2: the sidebar reads ``phase_sequence`` and
``phase_display_labels`` from the backend rather than hard-coding the
canonical phase taxonomy on the client side.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid

import httpx
import reflex as rx
from loguru import logger

from .api_client import (
    create_brand_strategy_session,
    extract_final_metadata,
    get_session,
    get_session_messages,
    health_check,
    list_brand_strategy_sessions,
    stream_message,
)
from .models import (
    BrandStrategyMetadata,
    ChatMessage,
    PhaseAdvancePayload,
    SessionInfo,
    StreamingThinkingPayload,
    StreamingTokenPayload,
    TimelineEntry,
    ToolCallInfo,
    ToolCallPayload,
    ToolResultPayload,
)

_DEFAULT_API_URL = "http://localhost:8000"
_HEALTH_POLL_INTERVAL_SECONDS = 10


def _format_duration(seconds: float) -> str:
    """Format a positive elapsed seconds value as a short human label.

    Returns ``"<1s"`` for sub-second turns, ``"Ns"`` for under a minute,
    and ``"MmSs"`` once the duration crosses one minute so the collapsed
    timeline summary stays compact ("Thought for 1m04s").
    """
    if seconds < 1.0:
        return "<1s"
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    return f"{minutes}m{secs:02d}s"


def _api_base_url() -> str:
    """Return the FastAPI backend base URL the web UI should reach.

    Reads ``BRANDMIND_API_URL`` so a Docker deployment can swap the
    host without rebuilding the image. Falls back to a local default
    matching a default ``brandmind serve`` install.
    """
    return os.getenv("BRANDMIND_API_URL", _DEFAULT_API_URL).rstrip("/")


class BrandMindState(rx.State):
    """Application state for the BrandMind Web UI v1.

    Reactive vars on this class drive every component in the page. The
    state owns three concerns: connectivity (``is_connected``), session
    metadata (``session_id`` / ``current_phase`` / ``phase_sequence`` /
    ...), and the chat scroll (``messages`` + streaming buffers). UI
    preferences (sidebar collapsed state) live alongside because they
    are also reactive and persisted via ``rx.LocalStorage``.
    """

    is_connected: bool = False
    session_id: str = ""
    scope: str = ""
    brand_name: str = ""
    current_phase: str = "phase_0"
    completed_phases: list[str] = []
    phase_sequence: list[str] = []
    phase_display_labels: dict[str, str] = {}
    messages: list[ChatMessage] = []
    sessions: list[SessionInfo] = []
    is_streaming: bool = False
    pending_input: str = ""
    error_message: str = ""
    sidebar_collapsed: str = rx.LocalStorage(
        "",
        name="bm.web.sidebar.collapsed",
    )

    @rx.var
    def sidebar_is_collapsed(self) -> bool:
        """Resolve the sidebar collapsed flag from persisted preference.

        Empty string means the user has not toggled yet; in that case the
        page-level layout decides default via responsive breakpoint. A
        non-empty value (``"1"`` or ``"0"``) overrides the default.
        """
        return self.sidebar_collapsed == "1"

    @rx.event
    def toggle_sidebar(self) -> None:
        """Flip the persisted sidebar preference and re-render dependents."""
        current = self.sidebar_collapsed == "1"
        self.sidebar_collapsed = "0" if current else "1"

    def _filter_chats(self, sessions: list[SessionInfo]) -> list[SessionInfo]:
        """Keep brand-strategy chats with at least one message, plus the active one.

        Lazy session creation guarantees every newly minted chat will
        accumulate a message; this filter hides legacy empty bootstraps
        left over before the lazy refactor. The active session is
        whitelisted so that the instant after lazy-create — when the
        backend still reports zero messages — the sidebar entry does
        not flicker out.
        """
        return [
            s
            for s in sessions
            if s.mode == "brand-strategy"
            and (s.message_count > 0 or s.session_id == self.session_id)
        ]

    @rx.event(background=True)
    async def initialize_app(self) -> None:
        """Pull the chat list on first navigation; do NOT create a session.

        Earlier revisions eagerly POSTed a fresh session at page mount,
        which polluted the backend with empty drafts every reload. The
        page now boots into "no chat selected" — the user picks an
        existing chat from the sidebar or starts a new one by sending
        a first message.
        """
        api_url = _api_base_url()
        try:
            sessions = await list_brand_strategy_sessions(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: chat list fetch failed: {exc}")
            async with self:
                self.is_connected = False
                self.error_message = (
                    "Backend unreachable — start `brandmind serve` and retry."
                )
            return
        async with self:
            self.sessions = self._filter_chats(sessions)
            self.is_connected = True
            self.error_message = ""

    @rx.event(background=True)
    async def refresh_sessions(self) -> None:
        """Re-pull the chat list from the backend.

        Called after creating or deleting a chat so the sidebar list
        stays in sync without forcing the user to reload.
        """
        api_url = _api_base_url()
        try:
            sessions = await list_brand_strategy_sessions(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: chat list refresh failed: {exc}")
            return
        async with self:
            self.sessions = self._filter_chats(sessions)

    @rx.event(background=True)
    async def start_new_chat(self) -> None:
        """Reset the workspace to an empty draft, ready for the first message.

        Does NOT hit the backend — the session is lazily created when
        the user actually sends the first message (see
        :meth:`_ensure_session`). This keeps the picker free of empty
        rows when the user just wants a clean slate.
        """
        async with self:
            if self.is_streaming:
                return
            self.session_id = ""
            self.messages = []
            self.scope = ""
            self.brand_name = ""
            self.current_phase = "phase_0"
            self.completed_phases = []
            self.phase_sequence = []
            self.phase_display_labels = {}
            self.error_message = ""

    @rx.event(background=True)
    async def switch_chat(self, session_id: str) -> None:
        """Load metadata and message history for an existing chat.

        Repaints the chat scroll plus the phase sidebar from server
        truth. Refuses to switch while a turn is mid-stream so the
        SSE consumer cannot land events on a swapped-out target.
        """
        if not session_id:
            return
        async with self:
            if self.is_streaming or session_id == self.session_id:
                return
        api_url = _api_base_url()
        try:
            info = await get_session(api_url, session_id)
            history = await get_session_messages(api_url, session_id)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: chat switch failed: {exc}")
            async with self:
                self.error_message = (
                    "Could not load that chat — please try again."
                )
            return
        async with self:
            self.session_id = info.session_id
            self._apply_metadata(info.metadata)
            self.messages = [
                ChatMessage(role=m.role, content=m.content)
                for m in history.messages
            ]
            self.error_message = ""

    async def _ensure_session(self) -> str | None:
        """Create a brand-strategy session if one is not bound yet.

        Returns the session id to send against, or ``None`` when the
        backend is unreachable. Called by :meth:`send_message` and
        :meth:`send_message_with` so the first user message is what
        materialises the chat on the backend — empty drafts never
        leak into the picker.
        """
        if self.session_id:
            return self.session_id
        api_url = _api_base_url()
        try:
            info = await create_brand_strategy_session(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: lazy session create failed: {exc}")
            self.error_message = (
                "Backend unreachable — start `brandmind serve` and retry."
            )
            return None
        self.session_id = info.session_id
        self._apply_metadata(info.metadata)
        self.sessions = [info, *self.sessions]
        return info.session_id

    @rx.event(background=True)
    async def poll_health(self) -> None:
        """Mirror backend health into ``is_connected`` on a fixed cadence.

        Lives for the lifetime of the page-mount. The poll cadence is
        intentionally coarse — the SSE stream is the primary signal of
        backend availability during an active turn, and the poll only
        needs to recover state after idle periods.
        """
        api_url = _api_base_url()
        while True:
            connected = await health_check(api_url)
            async with self:
                self.is_connected = connected
            await asyncio.sleep(_HEALTH_POLL_INTERVAL_SECONDS)

    @rx.event
    def set_pending_input(self, value: str) -> None:
        """Mirror the InputComposer value into state for the send action.

        Drops writes that arrive while a turn is streaming: browsers fire a
        trailing ``onChange`` with the textarea body (often plus a stray
        ``\\n``) right after the Enter keydown that triggered the send. If
        that write were honoured it would re-paint the just-sent message
        into the now-empty composer and confuse the user.
        """
        if self.is_streaming:
            return
        self.pending_input = value

    @rx.event
    def on_composer_key_down(self, key: str, info: dict):
        """Send on Enter (no modifier), let Shift+Enter fall through to newline.

        Reflex's :func:`key_event` arg-spec passes the key name plus a
        ``KeyInputInfo`` dict (``shift_key`` / ``ctrl_key`` / ``alt_key`` /
        ``meta_key``). Sending only triggers when the user pressed a bare
        Enter while connected, with non-empty content, and not mid-stream;
        any modifier (incl. composing Vietnamese accents via IME) falls
        through to the textarea's native behaviour. The handler flips
        ``is_streaming`` synchronously so any trailing ``set_pending_input``
        from the same Enter is dropped by the guard above.
        """
        if key != "Enter":
            return None
        if (
            info.get("shift_key")
            or info.get("ctrl_key")
            or info.get("alt_key")
            or info.get("meta_key")
        ):
            return None
        content = self.pending_input.strip()
        if not self.is_connected or self.is_streaming or not content:
            return None
        self.pending_input = ""
        self.is_streaming = True
        return BrandMindState.send_message_with(content)

    @rx.event(background=True)
    async def send_message(self) -> None:
        """Send the current ``pending_input`` as a chat turn.

        Triggered by the Send button click. Snapshots ``pending_input``,
        clears it, lazily creates the backend session if none is bound,
        then delegates to :meth:`_stream_turn`.
        """
        async with self:
            content = self.pending_input.strip()
            if not content or self.is_streaming:
                return
            session_id = await self._ensure_session()
            if session_id is None:
                return
            self.pending_input = ""
            self._begin_turn(content)
        await self._stream_turn(session_id, content)

    @rx.event(background=True)
    async def send_message_with(self, content: str) -> None:
        """Send a pre-snapshotted message body as a chat turn.

        Called by :meth:`on_composer_key_down` after it has already
        cleared ``pending_input`` and flipped ``is_streaming`` to ``True``
        synchronously, so the caller already owns the turn. Lazily
        creates the backend session if none is bound yet so the chat
        only materialises on the first real message.
        """
        async with self:
            body = content.strip()
            if not body:
                return
            session_id = await self._ensure_session()
            if session_id is None:
                self.is_streaming = False
                return
            self._begin_turn(body)
        await self._stream_turn(session_id, body)

    def _begin_turn(self, content: str) -> None:
        """Seed the chat scroll with a user turn + streaming agent placeholder.

        Must run inside ``async with self`` so the user bubble and the
        streaming agent bubble appear in the same render tick.
        """
        self.error_message = ""
        self.messages = [
            *self.messages,
            ChatMessage(role="user", content=content),
            ChatMessage(
                role="agent",
                content="",
                is_streaming=True,
                timeline_expanded=True,
                turn_started_at=time.monotonic(),
            ),
        ]
        self.is_streaming = True

    async def _stream_turn(self, session_id: str, content: str) -> None:
        """Consume the SSE stream for one turn and dispatch each event.

        On ``done`` or ``error`` the agent bubble is finalised and the
        composer is re-enabled. ``httpx.HTTPError`` surfaces as the
        in-line error banner without raising.
        """
        api_url = _api_base_url()
        try:
            async for event in stream_message(api_url, session_id, content):
                async with self:
                    self._dispatch_event(event.event, event.data)
                    if event.event in {"done", "error"}:
                        self.is_streaming = False
                        self._finalize_agent_message()
                        break
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: stream failed: {exc}")
            async with self:
                self.is_streaming = False
                self.error_message = (
                    "Connection lost mid-send. Please try again."
                )
                self._finalize_agent_message()
        try:
            refreshed = await list_brand_strategy_sessions(api_url)
        except httpx.HTTPError as exc:
            logger.debug(f"BrandMind web: post-turn refresh skipped: {exc}")
            return
        async with self:
            self.sessions = self._filter_chats(refreshed)

    def _dispatch_event(self, event_name: str, payload: dict) -> None:
        """Route one SSE event to the matching state mutation."""
        if event_name == "streaming_token":
            chunk = StreamingTokenPayload.model_validate(payload)
            if chunk.token:
                self._append_agent_token(chunk.token)
        elif event_name == "streaming_thinking":
            chunk = StreamingThinkingPayload.model_validate(payload)
            self._append_thinking(chunk.token, chunk.done)
        elif event_name == "tool_call":
            call = ToolCallPayload.model_validate(payload)
            self._append_tool_call(call)
        elif event_name == "tool_result":
            result = ToolResultPayload.model_validate(payload)
            self._settle_tool_result(result)
        elif event_name == "phase_advance":
            advance = PhaseAdvancePayload.model_validate(payload)
            self._apply_phase_advance(advance)
        elif event_name == "done":
            final = extract_final_metadata(payload)
            self._apply_metadata(final.metadata)
        elif event_name == "error":
            self.error_message = str(payload.get("error", "Stream error"))

    def _append_agent_token(self, token: str) -> None:
        """Append a streaming chunk to the active agent message body."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target.content = f"{target.content}{token}"
        self.messages = [*self.messages[:-1], target]

    def _append_thinking(self, token: str, finalised: bool) -> None:
        """Append a streaming thinking chunk to the chronological timeline.

        Consecutive thinking chunks merge into the trailing thinking entry
        until the backend signals ``done`` for that block; the next thinking
        event after that opens a new entry. This keeps every distinct
        reasoning block visible as its own timeline node.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        timeline = list(target.timeline)
        tail = timeline[-1] if timeline else None
        if tail is not None and tail.kind == "thinking" and not tail.thinking_done:
            if token:
                tail.thinking_text = f"{tail.thinking_text}{token}"
            if finalised:
                tail.thinking_done = True
        elif token:
            timeline.append(
                TimelineEntry(
                    kind="thinking",
                    thinking_text=token,
                    thinking_done=finalised,
                )
            )
        target.timeline = timeline
        self.messages = [*self.messages[:-1], target]

    def _append_tool_call(self, call: ToolCallPayload) -> None:
        """Push a new in-progress tool entry into the reasoning timeline."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target.timeline = [
            *target.timeline,
            TimelineEntry(
                kind="tool_call",
                tool_call=ToolCallInfo(
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                ),
            ),
        ]
        self.messages = [*self.messages[:-1], target]

    def _settle_tool_result(self, result: ToolResultPayload) -> None:
        """Settle the earliest still-running tool entry of the same tool.

        When the agent calls the same tool more than once, each result
        settles the oldest unresolved invocation — otherwise a later
        result overwrites an already-completed call and earlier entries
        stay stuck on "running" forever in the timeline.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent" or not target.timeline:
            return
        for entry in target.timeline:
            if entry.kind != "tool_call" or entry.tool_call is None:
                continue
            if (
                entry.tool_call.tool_name == result.tool_name
                and entry.tool_call.result == ""
            ):
                entry.tool_call.result = result.result
                break
        self.messages = [*self.messages[:-1], target]

    def _apply_phase_advance(self, advance: PhaseAdvancePayload) -> None:
        """Mirror a phase-advance event into the sidebar state."""
        self.current_phase = advance.to_phase
        self.completed_phases = list(advance.completed_phases)
        if advance.scope:
            self.scope = advance.scope

    def _apply_metadata(self, metadata: BrandStrategyMetadata) -> None:
        """Refresh sidebar + identity state from a full metadata payload."""
        self.current_phase = metadata.current_phase
        self.completed_phases = list(metadata.completed_phases)
        self.scope = metadata.scope or ""
        self.brand_name = metadata.brand_name or ""
        self.phase_sequence = list(metadata.phase_sequence)
        self.phase_display_labels = dict(metadata.phase_display_labels)

    def _finalize_agent_message(self) -> None:
        """Close the trailing agent message and tidy its reasoning timeline.

        On stream close: force-settle any tool entries the backend never
        emitted a ``tool_result`` for (fire-and-forget tools like
        ``write_todos`` are common), mark any open thinking blocks done,
        compute the turn duration, and collapse the timeline by default
        so the chat scroll reads as the final response.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        for entry in target.timeline:
            if entry.kind == "tool_call" and entry.tool_call is not None:
                if entry.tool_call.result == "":
                    entry.tool_call.result = "(done)"
            elif entry.kind == "thinking" and not entry.thinking_done:
                entry.thinking_done = True
        if target.is_streaming:
            target.is_streaming = False
        if target.turn_started_at > 0.0 and target.turn_duration_label == "":
            elapsed = max(0.0, time.monotonic() - target.turn_started_at)
            target.turn_duration_label = _format_duration(elapsed)
        target.timeline_expanded = False
        self.messages = [*self.messages[:-1], target]

    @rx.event
    def toggle_timeline(self, message_index: int) -> None:
        """Toggle the collapsed/expanded state of a turn's reasoning timeline."""
        if message_index < 0 or message_index >= len(self.messages):
            return
        target = self.messages[message_index]
        if target.role != "agent" or not target.timeline:
            return
        target.timeline_expanded = not target.timeline_expanded
        self.messages = [
            *self.messages[:message_index],
            target,
            *self.messages[message_index + 1:],
        ]

    @rx.event(background=True)
    async def restore_session(self, session_id: str) -> None:
        """Rehydrate sidebar state from an existing session id.

        Reserved for future use when the page picks up a session id
        from URL params or local storage; not wired by the v1 page yet.
        """
        if not session_id:
            return
        api_url = _api_base_url()
        try:
            info = await get_session(api_url, session_id)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: session restore failed: {exc}")
            return
        async with self:
            self.session_id = info.session_id
            self._apply_metadata(info.metadata)

    @staticmethod
    def fresh_client_token() -> str:
        """Return a random short token for client-side correlation ids.

        Used by the future tool-call timeline + future telemetry to
        de-duplicate retry waves. Kept here so the helper survives
        when the page-level component is rewritten in Phase 3.
        """
        return uuid.uuid4().hex[:8]
