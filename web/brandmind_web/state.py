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
    delete_session,
    extract_final_metadata,
    fetch_artifact_html,
    generate_session_title,
    get_session,
    get_session_messages,
    health_check,
    list_brand_strategy_sessions,
    list_session_artifacts,
    stream_message,
    update_session,
)
from .models import (
    ArtifactRef,
    BrandStrategyMetadata,
    ChatMessage,
    DocxTocEntry,
    PhaseAdvancePayload,
    SessionInfo,
    SessionMessage,
    StreamingThinkingPayload,
    StreamingTokenPayload,
    TimelineEntry,
    ToolCallInfo,
    ToolCallPayload,
    ToolResultPayload,
)

_GENERATE_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "generate_brand_key",
        "generate_document",
        "generate_presentation",
        "generate_spreadsheet",
    }
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

    rename_target: str = ""
    rename_draft: str = ""
    delete_target: str = ""

    artifacts: list[ArtifactRef] = []
    canvas_open: bool = False
    active_artifact_filename: str = ""
    docx_html: str = ""
    docx_toc: list[DocxTocEntry] = []
    docx_loading: bool = False
    docx_error: str = ""
    artifacts_refresh_pending: bool = False

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

    @rx.var
    def has_artifacts(self) -> bool:
        """Whether the active session has produced any artifact yet."""
        return len(self.artifacts) > 0

    @rx.var
    def active_artifact_url(self) -> str:
        """Backend download URL of the currently-selected artifact.

        Returns an empty string when no artifact is selected so the
        viewers can branch on truthiness without unwrapping ``None``.
        Reflex Var rules forbid returning ``None`` from a typed computed
        var.
        """
        for artifact in self.artifacts:
            if artifact.filename == self.active_artifact_filename:
                return f"{_api_base_url()}{artifact.download_url}"
        return ""

    @rx.var
    def active_artifact_category(self) -> str:
        """Category string of the active artifact, or empty when none."""
        for artifact in self.artifacts:
            if artifact.filename == self.active_artifact_filename:
                return artifact.category
        return ""

    @rx.event
    def toggle_sidebar(self) -> None:
        """Flip the persisted sidebar preference and re-render dependents."""
        current = self.sidebar_collapsed == "1"
        self.sidebar_collapsed = "0" if current else "1"

    @rx.event
    def open_canvas(self) -> None:
        """Reveal the canvas drawer; no-ops when already open."""
        self.canvas_open = True

    @rx.event
    def close_canvas(self) -> None:
        """Slide the canvas drawer out without dropping the artifact list."""
        self.canvas_open = False

    @rx.event(background=True)
    async def toggle_canvas(self) -> None:
        """Flip the canvas drawer open / closed and refresh artifacts on open.

        When the user opens the canvas from the header button while the
        chat already has artifacts in flight, we pull the latest
        manifest so the panel reflects every file the agent has emitted
        so far — not just what the SSE stream surfaced this turn.
        """
        async with self:
            opening = not self.canvas_open
            self.canvas_open = opening
            session_id = self.session_id
        if opening and session_id:
            await self._refresh_artifacts(session_id)

    @rx.event(background=True)
    async def select_artifact(self, filename: str) -> None:
        """Switch the canvas viewer to ``filename`` and load its body if needed.

        For document artifacts the call also fetches the mammoth-rendered
        HTML so the DocxView can paint without a separate trigger. Other
        categories render directly from the manifest reference plus the
        backend download URL.

        Args:
            filename (str): Basename of the artifact to display.
        """
        async with self:
            target_category = ""
            for artifact in self.artifacts:
                if artifact.filename == filename:
                    target_category = artifact.category
                    break
        await self._select_artifact_internal(filename, target_category)

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
            self._reset_canvas_state()

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
                self._chat_message_from_wire(m) for m in history.messages
            ]
            self.error_message = ""
            self._reset_canvas_state()
        await self._refresh_artifacts(info.session_id)

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
    async def open_rename_dialog(
        self, session_id: str, current_title: str
    ) -> None:
        """Pre-fill the rename dialog with the current title."""
        async with self:
            self.rename_target = session_id
            self.rename_draft = current_title

    @rx.event
    def set_rename_draft(self, value: str) -> None:
        """Mirror the rename input value into state."""
        self.rename_draft = value

    @rx.event
    def cancel_rename(self) -> None:
        """Dismiss the rename dialog without applying changes."""
        self.rename_target = ""
        self.rename_draft = ""

    @rx.event(background=True)
    async def confirm_rename(self) -> None:
        """Persist the drafted title to the targeted chat."""
        async with self:
            target = self.rename_target
            draft = self.rename_draft.strip()
        if not target:
            return
        api_url = _api_base_url()
        try:
            info = await update_session(api_url, target, title=draft)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: rename failed: {exc}")
            async with self:
                self.error_message = "Could not rename that chat."
            return
        async with self:
            self.sessions = self._replace_session_in_list(info)
            self.rename_target = ""
            self.rename_draft = ""

    @rx.event(background=True)
    async def toggle_pin(self, session_id: str) -> None:
        """Flip the pinned flag on a chat and re-sort the sidebar list."""
        if not session_id:
            return
        async with self:
            current = next(
                (
                    s.metadata.pinned
                    for s in self.sessions
                    if s.session_id == session_id
                ),
                False,
            )
        api_url = _api_base_url()
        try:
            info = await update_session(
                api_url, session_id, pinned=not current
            )
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: pin toggle failed: {exc}")
            return
        async with self:
            self.sessions = self._replace_session_in_list(info)
            self.sessions = self._reorder_sessions(self.sessions)

    @rx.event(background=True)
    async def open_delete_dialog(self, session_id: str) -> None:
        """Surface the delete-confirm modal for the targeted chat."""
        async with self:
            self.delete_target = session_id

    @rx.event
    def cancel_delete(self) -> None:
        """Dismiss the delete dialog without removing the chat."""
        self.delete_target = ""

    @rx.event(background=True)
    async def confirm_delete(self) -> None:
        """DELETE the targeted chat and rebuild local state.

        Resets the workspace when the deleted chat is the currently
        active one so the user does not end up streaming into a tombstone.
        """
        async with self:
            target = self.delete_target
        if not target:
            return
        api_url = _api_base_url()
        try:
            await delete_session(api_url, target)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: delete failed: {exc}")
            async with self:
                self.error_message = "Could not delete that chat."
                self.delete_target = ""
            return
        async with self:
            self.sessions = [
                s for s in self.sessions if s.session_id != target
            ]
            self.delete_target = ""
            if self.session_id == target:
                self.session_id = ""
                self.messages = []
                self.scope = ""
                self.brand_name = ""
                self.current_phase = "phase_0"
                self.completed_phases = []
                self.phase_sequence = []
                self.phase_display_labels = {}
                self._reset_canvas_state()

    def _reset_canvas_state(self) -> None:
        """Drop every canvas-related reactive var to its initial value.

        Called whenever the workspace pivots to a different chat —
        chat-switch, start-new-chat, or delete-the-active-chat — so the
        canvas does not carry artifacts from the previous session into
        the next one.
        """
        self.artifacts = []
        self.canvas_open = False
        self.active_artifact_filename = ""
        self.docx_html = ""
        self.docx_toc = []
        self.docx_loading = False
        self.docx_error = ""
        self.artifacts_refresh_pending = False

    async def _refresh_artifacts(self, session_id: str) -> None:
        """Pull the artifact manifest for ``session_id`` and update state.

        Wraps the HTTP error path so the canvas can keep its previous
        list visible if the refresh fails — better UX than blanking the
        panel because of a transient network blip.

        Args:
            session_id (str): Session whose artifacts to refresh.
        """
        api_url = _api_base_url()
        try:
            artifacts = await list_session_artifacts(api_url, session_id)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: artifact refresh failed: {exc}")
            return
        async with self:
            self.artifacts = artifacts

    def _chat_message_from_wire(self, message: SessionMessage) -> ChatMessage:
        """Rebuild a :class:`ChatMessage` from a server-side persisted turn.

        Agent turns rehydrate with their full reasoning timeline plus the
        recorded ``duration_label`` and the ``timeline_expanded=False``
        flag so the bubble matches the collapsed state a live turn ends
        in. User turns get an empty timeline and no duration label.

        Args:
            message (SessionMessage): Persisted turn payload as returned
                by ``GET /api/v1/sessions/{id}/messages``.

        Returns:
            chat_message (ChatMessage): Frontend-state-ready bubble
            wired with content, timeline, and duration metadata.
        """
        timeline: list[TimelineEntry] = []
        for entry in message.timeline:
            tool_call: ToolCallInfo | None = None
            if entry.tool_call is not None:
                tool_call = ToolCallInfo(
                    tool_name=entry.tool_call.tool_name,
                    arguments=dict(entry.tool_call.arguments),
                    result=entry.tool_call.result,
                )
            timeline.append(
                TimelineEntry(
                    kind=entry.kind,
                    thinking_text=entry.thinking_text,
                    thinking_done=True,
                    tool_call=tool_call,
                )
            )
        return ChatMessage(
            role=message.role,
            content=message.content,
            is_streaming=False,
            timeline=timeline,
            turn_duration_label=message.duration_label,
            timeline_expanded=False,
        )

    def _replace_session_in_list(self, info: SessionInfo) -> list[SessionInfo]:
        """Swap ``info`` in for any existing entry with the same id."""
        replaced = False
        result: list[SessionInfo] = []
        for s in self.sessions:
            if s.session_id == info.session_id:
                result.append(info)
                replaced = True
            else:
                result.append(s)
        if not replaced:
            result.append(info)
        return result

    def _reorder_sessions(
        self, sessions: list[SessionInfo]
    ) -> list[SessionInfo]:
        """Apply the backend's pinned-first ordering locally for snappier UX."""
        return sorted(
            sessions,
            key=lambda s: (not s.metadata.pinned, sessions.index(s)),
        )

    async def _auto_title_if_needed(self, session_id: str) -> None:
        """Trigger Gemini titling after the first turn if the chat is still untitled.

        Called from :meth:`_stream_turn` once the post-turn refresh has
        landed. Only fires when the picker still shows the chat as
        title-less so subsequent turns do not re-summarise.
        """
        if not session_id:
            return
        active = next(
            (s for s in self.sessions if s.session_id == session_id),
            None,
        )
        if active is None or active.metadata.title:
            return
        api_url = _api_base_url()
        try:
            info = await generate_session_title(api_url, session_id)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: auto-title failed: {exc}")
            return
        async with self:
            self.sessions = self._replace_session_in_list(info)

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
        then delegates to :meth:`_stream_turn` while a title-generation
        task runs in parallel.
        """
        async with self:
            content = self.pending_input.strip()
            if not content or self.is_streaming:
                return
            session_id = await self._ensure_session()
            if session_id is None:
                return
            self.pending_input = ""
            needs_title = self._chat_is_untitled(session_id)
            self._begin_turn(content)
        if needs_title:
            asyncio.create_task(self._title_task(session_id, content))
        await self._stream_turn(session_id, content)

    @rx.event(background=True)
    async def send_message_with(self, content: str) -> None:
        """Send a pre-snapshotted message body as a chat turn.

        Called by :meth:`on_composer_key_down` after it has already
        cleared ``pending_input`` and flipped ``is_streaming`` to ``True``
        synchronously, so the caller already owns the turn. Lazily
        creates the backend session if none is bound yet so the chat
        only materialises on the first real message. Fires the
        Gemini titler in parallel so the sidebar label can settle
        before the agent finishes streaming.
        """
        async with self:
            body = content.strip()
            if not body:
                return
            session_id = await self._ensure_session()
            if session_id is None:
                self.is_streaming = False
                return
            needs_title = self._chat_is_untitled(session_id)
            self._begin_turn(body)
        if needs_title:
            asyncio.create_task(self._title_task(session_id, body))
        await self._stream_turn(session_id, body)

    def _chat_is_untitled(self, session_id: str) -> bool:
        """Whether the matching chat row currently lacks a title."""
        for info in self.sessions:
            if info.session_id == session_id:
                return not info.metadata.title
        return True

    async def _title_task(self, session_id: str, message: str) -> None:
        """Fire the Gemini titler off the request thread.

        Runs concurrently with :meth:`_stream_turn` so the sidebar
        label is replaced as soon as Gemini comes back — usually well
        before the agent finishes its first turn.
        """
        api_url = _api_base_url()
        try:
            info = await generate_session_title(
                api_url, session_id, message=message
            )
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: parallel title gen failed: {exc}")
            return
        if not info.metadata.title:
            return
        async with self:
            self.sessions = self._replace_session_in_list(info)

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
        else:
            async with self:
                self.sessions = self._filter_chats(refreshed)
        await self._auto_title_if_needed(session_id)
        async with self:
            artifacts_pending = self.artifacts_refresh_pending
            self.artifacts_refresh_pending = False
        if artifacts_pending:
            await self._refresh_artifacts_and_reveal(session_id)

    async def _refresh_artifacts_and_reveal(self, session_id: str) -> None:
        """Pull the manifest, open the canvas, focus the newest artifact.

        Fires after a turn that produced at least one ``generate_*``
        ``tool_result`` so the user sees the just-emitted file without
        clicking the header button. The list is sorted oldest-first on
        the wire, so the last entry is the freshest; that becomes the
        active artifact and, for documents, the DOCX HTML pre-loads.

        Args:
            session_id (str): Session whose artifacts to surface.
        """
        await self._refresh_artifacts(session_id)
        async with self:
            if not self.artifacts:
                return
            newest = self.artifacts[-1]
            self.canvas_open = True
            target_filename = newest.filename
            target_category = newest.category
        await self._select_artifact_internal(target_filename, target_category)

    async def _select_artifact_internal(
        self, filename: str, category: str
    ) -> None:
        """Apply artifact selection from a non-event-handler caller.

        Mirrors :meth:`select_artifact` but written as a plain async
        method so internal helpers can reuse the logic without going
        through Reflex's event dispatch.
        """
        async with self:
            self.active_artifact_filename = filename
            self.docx_html = ""
            self.docx_toc = []
            self.docx_error = ""
            session_id = self.session_id
        if category != "documents" or not session_id:
            return
        async with self:
            self.docx_loading = True
        api_url = _api_base_url()
        try:
            rendered = await fetch_artifact_html(api_url, session_id, filename)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: DOCX render fetch failed: {exc}")
            async with self:
                self.docx_loading = False
                self.docx_error = (
                    "Could not render this document — try downloading instead."
                )
            return
        async with self:
            self.docx_html = rendered.html
            self.docx_toc = list(rendered.toc)
            self.docx_loading = False

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
            if result.tool_name in _GENERATE_TOOL_NAMES:
                self.artifacts_refresh_pending = True
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
