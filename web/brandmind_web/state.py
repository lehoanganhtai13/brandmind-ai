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
import uuid

import httpx
import reflex as rx
from loguru import logger

from .api_client import (
    create_brand_strategy_session,
    extract_final_metadata,
    get_session,
    health_check,
    stream_message,
)
from .models import (
    BrandStrategyMetadata,
    ChatMessage,
    PhaseAdvancePayload,
    StreamingThinkingPayload,
    StreamingTokenPayload,
    ToolCallInfo,
    ToolCallPayload,
    ToolResultPayload,
)

_DEFAULT_API_URL = "http://localhost:8000"
_HEALTH_POLL_INTERVAL_SECONDS = 10
_SIDEBAR_COLLAPSED_BREAKPOINT_PX = 1280


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

    @rx.event(background=True)
    async def initialize_session(self) -> None:
        """Bootstrap the session on first navigation.

        Creates a new brand-strategy session via the backend and seeds
        the sidebar state with whatever scope-dependent metadata the
        backend reports. When the backend is unreachable, the error
        is logged and the UI falls back to the disconnected state.
        """
        api_url = _api_base_url()
        try:
            info = await create_brand_strategy_session(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: session bootstrap failed: {exc}")
            async with self:
                self.is_connected = False
                self.error_message = "Backend unreachable — start brandmind serve."
            return

        async with self:
            self.session_id = info.session_id
            self._apply_metadata(info.metadata)
            self.is_connected = True
            self.error_message = ""

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

        Reflex's two-way binding on text inputs requires a state setter;
        keeping this minimal so the InputComposer stays focused on
        layout in Phase 3.
        """
        self.pending_input = value

    @rx.event(background=True)
    async def send_message(self) -> None:
        """Stream a turn through ``stream_message`` and dispatch events.

        Flow per turn:
          1. Append a user :class:`ChatMessage` for the request text.
          2. Append a streaming agent :class:`ChatMessage` and mark
             ``is_streaming = True`` so the InputComposer disables.
          3. Iterate SSE events, mutating the in-flight agent message
             and sidebar state under ``async with self:`` so Reflex
             serialises against UI reads.
          4. On ``done`` settle the final response text and metadata,
             then mark ``is_streaming = False``.
        """
        async with self:
            content = self.pending_input.strip()
            if not content or self.is_streaming or not self.session_id:
                return
            self.pending_input = ""
            self.error_message = ""
            self.messages = [
                *self.messages,
                ChatMessage(role="user", content=content),
                ChatMessage(role="agent", content="", is_streaming=True),
            ]
            self.is_streaming = True
            session_id = self.session_id

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
                    "Mất kết nối khi đang gửi tin nhắn. Thử lại nhé."
                )
                self._finalize_agent_message()

    def _dispatch_event(self, event_name: str, payload: dict) -> None:
        """Route one SSE event to the matching state mutation."""
        if event_name == "streaming_token":
            chunk = StreamingTokenPayload.model_validate(payload)
            if chunk.token:
                self._append_agent_token(chunk.token)
        elif event_name == "streaming_thinking":
            chunk = StreamingThinkingPayload.model_validate(payload)
            if chunk.token:
                self._append_agent_thinking(chunk.token)
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

    def _append_agent_thinking(self, token: str) -> None:
        """Append a streaming thinking chunk to the active agent message."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target.thinking = f"{target.thinking}{token}"
        self.messages = [*self.messages[:-1], target]

    def _append_tool_call(self, call: ToolCallPayload) -> None:
        """Push a new in-progress tool entry under the active agent message."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target.tool_calls = [
            *target.tool_calls,
            ToolCallInfo(tool_name=call.tool_name, arguments=call.arguments),
        ]
        self.messages = [*self.messages[:-1], target]

    def _settle_tool_result(self, result: ToolResultPayload) -> None:
        """Attach a result string to the most recent matching tool call."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent" or not target.tool_calls:
            return
        for index in range(len(target.tool_calls) - 1, -1, -1):
            if target.tool_calls[index].tool_name == result.tool_name:
                target.tool_calls[index].result = result.result
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
        """Mark the trailing agent message as no longer streaming."""
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent" or not target.is_streaming:
            return
        target.is_streaming = False
        self.messages = [*self.messages[:-1], target]

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
