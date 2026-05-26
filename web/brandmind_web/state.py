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
import re
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
    get_user_profile_settings,
    health_check,
    list_brand_strategy_sessions,
    list_main_agent_models,
    list_session_artifacts,
    save_user_profile_settings,
    stream_message,
    update_session,
)
from .models import (
    ArtifactRef,
    BrandStrategyMetadata,
    ChatMessage,
    ContentBlock,
    DocxTocEntry,
    MainAgentModelOption,
    PhaseAdvancePayload,
    SessionInfo,
    SessionMessage,
    StreamingThinkingPayload,
    StreamingTokenPayload,
    ThinkingSegment,
    TimelineEntry,
    ToolCallInfo,
    ToolCallPayload,
    ToolResultPayload,
    UserProfileSettings,
    UserProfileSettingsOptions,
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
_HEALTH_POLL_DEGRADED_INTERVAL_SECONDS = 3
_STREAM_RECONNECT_BACKOFFS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


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


_BOLD_MARKER_PATTERN = re.compile(r"\*\*([^*]+?)\*\*")


def _compact_thinking_text(text: str) -> str:
    """Normalize whitespace inside a streamed thinking block.

    Stale persisted reasoning state carries Windows newlines, runs of
    blank lines, and trailing spaces that explode into large visual
    gaps once the timeline expands. Collapsing those keeps the raw
    string a clean source of truth for both segmentation and any
    plain-text fallback. ``**bold**`` markers are intentionally
    preserved here so :func:`_segment_thinking_text` can find the
    header / body boundary; the markers are stripped per-segment by
    the segmentation step, never on the raw text.
    """
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    stripped_lines = "\n".join(
        line.rstrip() for line in normalized_newlines.split("\n")
    )
    without_extra_spaces = re.sub(r"[ \t]{2,}", " ", stripped_lines)
    paragraph_collapsed = re.sub(r"\n{3,}", "\n\n", without_extra_spaces)
    return paragraph_collapsed.strip()


def _segment_thinking_text(text: str) -> list[ThinkingSegment]:
    """Split a normalized thinking block into header / body segments.

    The agent emits each reasoning step as ``**Header**\\nBody...`` and
    the same row may carry several such sections back-to-back. The web
    timeline renders this list with ``rx.foreach`` so each segment can
    use the matching weight and palette without mounting a heavier
    component (rx.markdown is intentionally avoided to keep the React
    hook order stable across thinking and tool-call rows). When the
    raw text has no markers the whole string falls into a single body
    segment so legacy persisted entries still render correctly.

    Args:
        text (str): The normalized thinking block.

    Returns:
        segments (list[ThinkingSegment]): Alternating header / body
            slices in document order. Empty when ``text`` is empty.
    """
    if not text:
        return []
    segments: list[ThinkingSegment] = []
    cursor = 0
    for match in _BOLD_MARKER_PATTERN.finditer(text):
        if match.start() > cursor:
            body = text[cursor : match.start()].strip()
            if body:
                segments.append(ThinkingSegment(kind="body", text=body))
        header = match.group(1).strip()
        if header:
            segments.append(ThinkingSegment(kind="header", text=header))
        cursor = match.end()
    if cursor < len(text):
        tail = text[cursor:].strip()
        if tail:
            segments.append(ThinkingSegment(kind="body", text=tail))
    return segments


def _compact_timeline_entries(timeline: list[TimelineEntry]) -> list[TimelineEntry]:
    """Return timeline entries with display-ready thinking text and segments."""
    compacted: list[TimelineEntry] = []
    for entry in timeline:
        if entry.kind == "thinking" and entry.thinking_text:
            normalized = _compact_thinking_text(entry.thinking_text)
            entry = entry.model_copy(
                update={
                    "thinking_text": normalized,
                    "thinking_segments": _segment_thinking_text(normalized),
                }
            )
        compacted.append(entry)
    return compacted


def _compact_chat_message_timeline(message: ChatMessage) -> ChatMessage:
    """Return a chat message whose reasoning timeline is display-ready."""
    if not message.timeline:
        return message
    return message.model_copy(
        update={"timeline": _compact_timeline_entries(message.timeline)}
    )


def _compact_chat_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Return chat messages with normalized reasoning snippets."""
    return [_compact_chat_message_timeline(message) for message in messages]


def _append_token_to_blocks(
    blocks: list[ContentBlock], token: str
) -> list[ContentBlock]:
    """Mirror a streaming-token chunk into the ordered live blocks.

    Appends to the trailing ``assistant_text`` block when it is still
    the active block; otherwise opens a fresh ``assistant_text`` block
    (the Codex Phase 1 rule that turns a token-after-thinking into a
    new paragraph instead of merging it with an earlier reasoning
    block).

    Args:
        blocks (list[ContentBlock]): The turn's current block list, by
            value (the caller passes a shallow copy so this helper can
            mutate in-place without surprising Reflex's diff tracker).
        token (str): The incremental assistant-text chunk; an empty
            string is a no-op so a stray empty SSE token does not open
            a phantom block.

    Returns:
        blocks (list[ContentBlock]): The updated list ready to assign
            back onto the message.
    """
    if not token:
        return blocks
    tail = blocks[-1] if blocks else None
    if tail is not None and tail.kind == "assistant_text" and not tail.is_done:
        tail.text = f"{tail.text}{token}"
        return blocks
    blocks.append(ContentBlock(kind="assistant_text", text=token))
    return blocks


def _append_thinking_to_blocks(
    blocks: list[ContentBlock], token: str, finalised: bool
) -> list[ContentBlock]:
    """Mirror a streaming-thinking chunk into the ordered live blocks.

    Routes the chunk through the trailing ``reasoning_timeline`` block,
    appending to its trailing thinking entry while still open or
    starting a fresh entry otherwise. When the trailing block is an
    ``assistant_text`` (or no block exists yet), a new
    ``reasoning_timeline`` block is opened first so the thinking trace
    sits below the prior text paragraph.

    Args:
        blocks (list[ContentBlock]): The turn's current block list.
        token (str): The incremental thinking-text chunk.
        finalised (bool): Whether the ``streaming_thinking`` event
            marks the current thinking entry done.

    Returns:
        blocks (list[ContentBlock]): The updated list.
    """
    tail = blocks[-1] if blocks else None
    if tail is None or tail.kind != "reasoning_timeline" or tail.is_done:
        blocks.append(ContentBlock(kind="reasoning_timeline"))
        tail = blocks[-1]
    timeline = list(tail.timeline)
    last_entry = timeline[-1] if timeline else None
    if (
        last_entry is not None
        and last_entry.kind == "thinking"
        and not last_entry.thinking_done
    ):
        if token:
            last_entry.thinking_text = _compact_thinking_text(
                f"{last_entry.thinking_text}{token}"
            )
            last_entry.thinking_segments = _segment_thinking_text(
                last_entry.thinking_text
            )
        if finalised:
            last_entry.thinking_done = True
    elif token:
        normalized = _compact_thinking_text(token)
        timeline.append(
            TimelineEntry(
                kind="thinking",
                thinking_text=normalized,
                thinking_segments=_segment_thinking_text(normalized),
                thinking_done=finalised,
            )
        )
    tail.timeline = timeline
    return blocks


def _append_timeline_entry_to_blocks(
    blocks: list[ContentBlock], entry: TimelineEntry
) -> list[ContentBlock]:
    """Mirror a new tool-call entry into the trailing reasoning block.

    Opens a fresh ``reasoning_timeline`` block when the trailing block
    is an ``assistant_text`` so tool runs after a paragraph cleanly
    start their own trace rather than appending to a stale text block.

    Args:
        blocks (list[ContentBlock]): The turn's current block list.
        entry (TimelineEntry): The tool-call entry to append.

    Returns:
        blocks (list[ContentBlock]): The updated list.
    """
    tail = blocks[-1] if blocks else None
    if tail is None or tail.kind != "reasoning_timeline" or tail.is_done:
        blocks.append(ContentBlock(kind="reasoning_timeline"))
        tail = blocks[-1]
    tail.timeline = [*tail.timeline, entry]
    return blocks


def _settle_tool_result_in_blocks(
    blocks: list[ContentBlock],
    tool_call_id: str,
    tool_name: str,
    result_text: str,
) -> list[ContentBlock]:
    """Settle the matching in-progress tool entry within the blocks view.

    Mirrors :meth:`BrandMindState._settle_tool_result` so the live
    blocks renderer flips a running tool row to its completed icon as
    soon as the backend confirms the result. Prefers ``tool_call_id``
    pairing and falls back to the first unresolved entry with the same
    ``tool_name`` when no id is provided.

    Args:
        blocks (list[ContentBlock]): The turn's current block list.
        tool_call_id (str): Provider id from the tool-result payload.
        tool_name (str): Tool name used for the FIFO fallback.
        result_text (str): The settled result body.

    Returns:
        blocks (list[ContentBlock]): The updated list.
    """
    for block in blocks:
        if block.kind != "reasoning_timeline":
            continue
        if tool_call_id:
            for entry in block.timeline:
                if entry.kind != "tool_call" or entry.tool_call is None:
                    continue
                if (
                    entry.tool_call.tool_call_id == tool_call_id
                    and entry.tool_call.result == ""
                ):
                    entry.tool_call.result = result_text
                    return blocks
    for block in blocks:
        if block.kind != "reasoning_timeline":
            continue
        for entry in block.timeline:
            if entry.kind != "tool_call" or entry.tool_call is None:
                continue
            if entry.tool_call.tool_name == tool_name and entry.tool_call.result == "":
                entry.tool_call.result = result_text
                return blocks
    return blocks


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
    streaming_session_id: str = ""
    pending_input: str = ""
    error_message: str = ""

    available_models: list[MainAgentModelOption] = []
    selected_model_id: str = ""
    locked_model_id: str = ""
    model_picker_open: bool = False

    rename_target: str = ""
    rename_draft: str = ""
    delete_target: str = ""
    delete_workspace_too: bool = False

    profile_settings: UserProfileSettings = UserProfileSettings()
    profile_settings_options: UserProfileSettingsOptions = UserProfileSettingsOptions()
    profile_settings_draft: UserProfileSettings = UserProfileSettings()
    profile_settings_saving: bool = False
    profile_settings_error: str = ""
    settings_dialog_open: bool = False
    settings_dialog_section: str = "personalization"
    onboarding_open: bool = False
    onboarding_has_auto_opened: str = rx.LocalStorage(
        "",
        name="bm.web.onboarding.auto_opened",
    )

    artifacts: list[ArtifactRef] = []
    canvas_open: bool = False
    active_artifact_filename: str = ""
    docx_html: str = ""
    docx_toc: list[DocxTocEntry] = []
    docx_loading: bool = False
    docx_error: str = ""
    docx_toc_open: bool = False
    artifacts_seen_count: int = 0
    artifacts_refresh_pending: bool = False

    health_retry_in_flight: bool = False
    stream_error_active: bool = False
    last_failed_turn_content: str = ""

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
    def has_unseen_artifacts(self) -> bool:
        """Whether the canvas has files the user has not acknowledged yet.

        Drives the notification badge on the canvas-toggle button. The
        count is snapshotted to ``artifacts_seen_count`` each time the
        user CLOSES the canvas (see :meth:`toggle_canvas`) — so once
        they have looked at the file list, the badge stays off until a
        new artifact arrives, instead of pinging every time the canvas
        is dismissed.

        Returns:
            unseen (bool): ``True`` when the artifact manifest has grown
            beyond what the user has acknowledged, ``False`` otherwise.
        """
        return self.artifacts_seen_count < len(self.artifacts)

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

    @rx.var
    def recent_sessions(self) -> list[SessionInfo]:
        """The 10 most-recent chats shown in the collapsed-rail Recents popover.

        Bounds the master ``sessions`` list server-side so the popover
        body stays at a constant height regardless of how many chats
        the user has accumulated. Falls back to all sessions when
        fewer than 10 exist.

        Returns:
            sessions (list[SessionInfo]): At most 10 sessions, in the
                same ordering as :attr:`sessions`.
        """
        return self.sessions[:10]

    @rx.var
    def banner_variant(self) -> str:
        """Resolve the connectivity banner variant from raw state.

        Keeps the dispatch logic in one place so the component tree
        stays branch-free. Recovery is silent by design (see
        ``degraded_banner.py`` module docstring).

        Returns:
            variant (str): ``"error"`` when the backend is unreachable,
                ``"warning"`` when a recent SSE turn failed but the
                backend itself is healthy, otherwise the empty string
                (meaning "no banner").
        """
        if not self.is_connected:
            return "error"
        if self.stream_error_active:
            return "warning"
        return ""

    @rx.var
    def connectivity_message(self) -> str:
        """Human-readable description for the error variant of the banner.

        Distinguishes between a manual retry in flight and the steady
        offline state so the user sees the loop is working when they
        click "Try again".
        """
        if self.health_retry_in_flight:
            return "Retrying connection to BrandMind…"
        return (
            "Cannot reach BrandMind backend — start `brandmind serve` or "
            "wait for the next health check."
        )

    @rx.var
    def picker_is_locked(self) -> bool:
        """Whether the model picker should refuse selection changes.

        Locked once the active chat has committed a model — either by
        sending the first user message (``locked_model_id`` set by
        :meth:`_apply_metadata`) or while a turn is streaming so the
        user cannot swap mid-flight.
        """
        return bool(self.locked_model_id) or self.is_streaming

    @rx.var
    def picker_active_model_id(self) -> str:
        """Model id the picker pill should render as the current choice.

        Prefers the locked profile so a rehydrated chat shows the model
        that is actually driving it; falls back to the user's pending
        selection for a fresh draft chat.
        """
        return self.locked_model_id or self.selected_model_id

    @rx.var
    def picker_active_model_label(self) -> str:
        """Display label matching :attr:`picker_active_model_id`."""
        active_id = self.locked_model_id or self.selected_model_id
        for option in self.available_models:
            if option.model_id == active_id:
                return option.display_name
        return active_id

    @rx.event
    def toggle_sidebar(self) -> None:
        """Flip the persisted sidebar preference and re-render dependents."""
        current = self.sidebar_collapsed == "1"
        self.sidebar_collapsed = "0" if current else "1"

    @rx.event
    def normalize_timeline_text(self) -> None:
        """Compact existing reasoning snippets already present in browser state."""
        if not self.messages:
            return
        self.messages = _compact_chat_messages(self.messages)

    @rx.event
    def toggle_model_picker(self) -> None:
        """Open or close the model-picker popover.

        Refuses to open when the picker is locked so the disabled-pill
        affordance does not surface a list the user cannot act on.
        """
        if self.picker_is_locked and not self.model_picker_open:
            return
        self.model_picker_open = not self.model_picker_open

    @rx.event
    def close_model_picker(self) -> None:
        """Close the popover without changing the selection."""
        self.model_picker_open = False

    @rx.event
    def select_model(self, model_id: str) -> None:
        """Set the user's intent for the next-new-chat model and close.

        Silently ignored when the picker is locked or when the model id
        is not present in :attr:`available_models` — these branches
        would otherwise let the picker drift away from a server-known
        profile.
        """
        if self.picker_is_locked:
            return
        if not any(option.model_id == model_id for option in self.available_models):
            return
        self.selected_model_id = model_id
        self.model_picker_open = False

    @rx.event
    def open_canvas(self) -> None:
        """Reveal the canvas drawer; no-ops when already open."""
        self.canvas_open = True

    @rx.event
    def close_canvas(self) -> None:
        """Slide the canvas drawer out without dropping the artifact list.

        Snapshots ``artifacts_seen_count`` to the current list length
        so the notification badge on the header toggle treats every
        file the user just had open as acknowledged. Mirrors the
        close branch of :meth:`toggle_canvas` — both the header X and
        the in-canvas X reach this handler, and either path must
        update the seen count or the badge would falsely re-ping on
        the very next render.
        """
        self.canvas_open = False
        self.artifacts_seen_count = len(self.artifacts)

    @rx.event
    def back_to_artifact_list(self) -> None:
        """Return from the artifact viewer to the file-list mode.

        The Claude-Cowork workspace pattern keeps the canvas open and
        only swaps the inner pane between list and viewer. Clearing
        ``active_artifact_filename`` flips the conditional render in
        ``canvas_pane`` so the file list takes the full canvas width
        again. The chat layout next to the canvas is unaffected.
        """
        self.active_artifact_filename = ""

    @rx.event
    def toggle_docx_toc(self) -> None:
        """Show or hide the DOCX outline sidebar inside the viewer.

        The outline defaults closed so the document body claims the
        full canvas width on open. The user opens it via the "Outline"
        chip in the body's top-left and dismisses it via the close
        button inside the sidebar header. Selecting a different
        artifact resets the flag (see ``_select_artifact_internal``).
        """
        self.docx_toc_open = not self.docx_toc_open

    @rx.event(background=True)
    async def toggle_canvas(self) -> None:
        """Flip the canvas drawer open / closed and refresh artifacts on open.

        When the user opens the canvas from the header button while the
        chat already has artifacts in flight, we pull the latest
        manifest so the panel reflects every file the agent has emitted
        so far — not just what the SSE stream surfaced this turn.

        Closing the canvas snapshots ``artifacts_seen_count`` to the
        current list length so the notification badge on the toggle
        treats every file the user just looked at as acknowledged. The
        badge re-appears only when a new artifact arrives later — see
        :attr:`has_unseen_artifacts`.
        """
        async with self:
            opening = not self.canvas_open
            self.canvas_open = opening
            session_id = self.session_id
            if not opening:
                self.artifacts_seen_count = len(self.artifacts)
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
        a first message. Also fetches the supported model profile list
        so the picker reflects what the backend will accept; failure
        is non-fatal because the picker is allowed to degrade to a
        single-option read-only badge.
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
        try:
            options = await list_main_agent_models(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: model list fetch failed: {exc}")
            options = []
        default_model_id = next(
            (option.model_id for option in options if option.is_default),
            options[0].model_id if options else "",
        )
        try:
            profile_payload = await get_user_profile_settings(api_url)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: profile settings fetch failed: {exc}")
            profile_payload = None
        async with self:
            self.sessions = self._filter_chats(sessions)
            if self.messages:
                self.messages = _compact_chat_messages(self.messages)
            self.available_models = options
            if not self.selected_model_id:
                self.selected_model_id = default_model_id
            if profile_payload is not None:
                self.profile_settings = profile_payload.settings
                self.profile_settings_options = profile_payload.options
                self.profile_settings_draft = profile_payload.settings.model_copy()
                force_param = (
                    self.router.page.params.get("force_onboarding", "")
                    if hasattr(self, "router")
                    else ""
                )
                if force_param in {"1", "true", "yes"}:
                    self.onboarding_has_auto_opened = ""
                if (
                    not profile_payload.settings.onboarding_completed
                    and not self.onboarding_has_auto_opened
                ):
                    self.onboarding_open = True
                    self.onboarding_has_auto_opened = "1"
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
            self.locked_model_id = ""
            self.model_picker_open = False
            self._reset_canvas_state()

    @rx.event(background=True)
    async def switch_chat(self, session_id: str) -> None:
        """Load metadata and message history for an existing chat.

        Repaints the chat scroll plus the phase sidebar from server
        truth. Switching is allowed while another chat is streaming:
        the in-flight stream keeps running server-side, the dispatch
        layer drops paint while its target is not in view, and the
        composer stays globally disabled until the stream completes.
        """
        if not session_id:
            return
        async with self:
            if session_id == self.session_id:
                return
        api_url = _api_base_url()
        try:
            info = await get_session(api_url, session_id)
            history = await get_session_messages(api_url, session_id)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: chat switch failed: {exc}")
            async with self:
                self.error_message = "Could not load that chat — please try again."
            return
        async with self:
            self.session_id = info.session_id
            self._apply_metadata(info.metadata)
            self.messages = [self._chat_message_from_wire(m) for m in history.messages]
            self.error_message = ""
            self._reset_canvas_state()
        await self._refresh_artifacts(info.session_id)

    async def _ensure_session(self) -> str | None:
        """Create a brand-strategy session if one is not bound yet.

        Returns the session id to send against, or ``None`` when the
        backend is unreachable. Called by :meth:`send_message` and
        :meth:`send_message_with` so the first user message is what
        materialises the chat on the backend — empty drafts never
        leak into the picker. The model picker's current
        ``selected_model_id`` is forwarded to the backend so the chat
        is pinned to that profile from the first send.
        """
        if self.session_id:
            return self.session_id
        api_url = _api_base_url()
        try:
            info = await create_brand_strategy_session(
                api_url,
                model_id=self.selected_model_id or None,
            )
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
    async def open_rename_dialog(self, session_id: str, current_title: str) -> None:
        """Pre-fill the rename dialog with the current title."""
        async with self:
            self.rename_target = session_id
            self.rename_draft = current_title

    @rx.event
    def set_rename_draft(self, value: str) -> None:
        """Mirror the rename input value into state."""
        self.rename_draft = value

    @rx.event
    def on_rename_key_down(self, key: str, info: dict):
        """Submit the rename dialog when the user hits a bare Enter.

        Mirrors the composer's Enter-to-send convention so the rename
        dialog feels native: bare Enter saves, Shift/Ctrl/Alt/Meta+Enter
        falls through to the input's default (allowing IME composition
        and platform-specific newline behaviour).
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
        if not self.rename_target:
            return None
        return BrandMindState.confirm_rename

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
            info = await update_session(api_url, session_id, pinned=not current)
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
            self.delete_workspace_too = False

    @rx.event
    def cancel_delete(self) -> None:
        """Dismiss the delete dialog without removing the chat."""
        self.delete_target = ""
        self.delete_workspace_too = False

    @rx.event
    def toggle_delete_workspace_too(self, value: bool) -> None:
        """Update the dialog's workspace-deletion checkbox."""
        self.delete_workspace_too = value

    @rx.event(background=True)
    async def confirm_delete(self) -> None:
        """DELETE the targeted chat and rebuild local state.

        Resets the workspace when the deleted chat is the currently
        active one so the user does not end up streaming into a tombstone.
        The ``delete_workspace`` flag travels with the API call so the
        backend can drop the matching workspace directory when the user
        opted in via the dialog checkbox.
        """
        async with self:
            target = self.delete_target
            also_delete_workspace = self.delete_workspace_too
        if not target:
            return
        api_url = _api_base_url()
        try:
            await delete_session(
                api_url,
                target,
                delete_workspace=also_delete_workspace,
            )
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: delete failed: {exc}")
            async with self:
                self.error_message = "Could not delete that chat."
                self.delete_target = ""
                self.delete_workspace_too = False
            return
        async with self:
            self.sessions = [s for s in self.sessions if s.session_id != target]
            self.delete_target = ""
            self.delete_workspace_too = False
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

    @rx.event
    def open_settings(self) -> None:
        """Open the Settings dialog seeded with the saved snapshot.

        Clones the saved settings into the draft so an in-progress edit
        can be cancelled without mutating the persisted state.
        """
        self.profile_settings_draft = self.profile_settings.model_copy()
        self.profile_settings_error = ""
        self.settings_dialog_open = True

    @rx.event
    def close_settings(self) -> None:
        """Dismiss the Settings dialog and discard any unsaved edits."""
        self.settings_dialog_open = False
        self.profile_settings_draft = self.profile_settings.model_copy()
        self.profile_settings_error = ""

    @rx.event
    def close_onboarding(self) -> None:
        """Dismiss the onboarding modal without saving.

        The local ``onboarding_has_auto_opened`` flag stays set so the
        modal does not auto-reappear; the user can still revisit the
        form via Settings.
        """
        self.onboarding_open = False
        self.profile_settings_draft = self.profile_settings.model_copy()
        self.profile_settings_error = ""

    @rx.event
    def set_settings_dialog_section(self, section: str) -> None:
        """Switch the visible content panel inside the Settings dialog."""
        self.settings_dialog_section = section

    @rx.event
    def update_setting_field(self, field: str, value: str) -> None:
        """Patch one field on the in-flight settings draft.

        The dialog dropdowns call this on every change so the draft
        accumulates edits without touching the saved snapshot until the
        user explicitly saves.
        """
        allowed = {
            "job_domain",
            "role",
            "experience_years",
            "brand_strategy_familiarity",
            "mentoring_style",
            "stakeholder_context",
        }
        if field not in allowed:
            return
        self.profile_settings_draft = self.profile_settings_draft.model_copy(
            update={field: value}
        )

    @rx.event(background=True)
    async def save_profile_settings(self) -> None:
        """Persist the draft, replace the saved snapshot, and close dialogs.

        ``onboarding_completed`` is forced to true on save so the user
        does not see the first-run modal again after explicitly setting
        their preferences. On HTTP failure the draft is preserved and
        an inline error message is surfaced.
        """
        async with self:
            if self.profile_settings_saving:
                return
            self.profile_settings_saving = True
            self.profile_settings_error = ""
            payload = self.profile_settings_draft.model_copy(
                update={"onboarding_completed": True}
            )
        api_url = _api_base_url()
        try:
            result = await save_user_profile_settings(api_url, payload)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: profile settings save failed: {exc}")
            async with self:
                self.profile_settings_saving = False
                self.profile_settings_error = (
                    "Could not save — backend unreachable. Try again in a moment."
                )
            return
        async with self:
            self.profile_settings = result.settings
            self.profile_settings_options = result.options
            self.profile_settings_draft = result.settings.model_copy()
            self.profile_settings_saving = False
            self.settings_dialog_open = False
            self.onboarding_open = False
            self.onboarding_has_auto_opened = "1"

    @rx.event(background=True)
    async def skip_onboarding(self) -> None:
        """Close the onboarding modal and persist defaults as accepted.

        Saves the current draft (or pristine defaults if untouched) with
        ``onboarding_completed=true`` so future loads no longer auto-open
        the modal. The user can still revisit and refine values later
        via the Settings entry in the sidebar.
        """
        async with self:
            if self.profile_settings_saving:
                return
            self.profile_settings_saving = True
            self.profile_settings_error = ""
            payload = self.profile_settings_draft.model_copy(
                update={"onboarding_completed": True}
            )
        api_url = _api_base_url()
        try:
            result = await save_user_profile_settings(api_url, payload)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: skip onboarding save failed: {exc}")
            async with self:
                self.profile_settings_saving = False
                self.onboarding_open = False
                self.onboarding_has_auto_opened = "1"
                self.profile_settings_error = ""
            return
        async with self:
            self.profile_settings = result.settings
            self.profile_settings_options = result.options
            self.profile_settings_draft = result.settings.model_copy()
            self.profile_settings_saving = False
            self.onboarding_open = False
            self.onboarding_has_auto_opened = "1"

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
        self.docx_toc_open = False
        self.artifacts_seen_count = 0
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
            normalized_thinking = _compact_thinking_text(entry.thinking_text)
            timeline.append(
                TimelineEntry(
                    kind=entry.kind,
                    thinking_text=normalized_thinking,
                    thinking_segments=_segment_thinking_text(normalized_thinking),
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

    def _reorder_sessions(self, sessions: list[SessionInfo]) -> list[SessionInfo]:
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
        """Mirror backend health into ``is_connected`` on a dynamic cadence.

        Polls every :data:`_HEALTH_POLL_INTERVAL_SECONDS` while healthy
        and every :data:`_HEALTH_POLL_DEGRADED_INTERVAL_SECONDS` while
        degraded so the banner recovers quickly when ``brandmind
        serve`` comes back online. Recovery is silent — the offline
        banner disappears as soon as ``is_connected`` flips back to
        True, without surfacing a "Back online" announcement.
        """
        api_url = _api_base_url()
        while True:
            connected = await health_check(api_url)
            await self._apply_health_result(connected)
            interval = (
                _HEALTH_POLL_INTERVAL_SECONDS
                if connected
                else _HEALTH_POLL_DEGRADED_INTERVAL_SECONDS
            )
            await asyncio.sleep(interval)

    async def _apply_health_result(self, connected: bool) -> None:
        """Apply the latest connectivity probe to ``is_connected``.

        Called by :meth:`poll_health` and :meth:`retry_connection`.
        Recovery is silent: the banner hides itself as soon as
        ``is_connected`` flips back to True (see ``banner_variant``).

        Args:
            connected (bool): Result of the most recent health probe.
        """
        async with self:
            self.is_connected = connected

    @rx.event(background=True)
    async def retry_connection(self) -> None:
        """Ping the backend immediately, ignoring the polling interval.

        Wired to the "Try again" button in :mod:`degraded_banner`. When
        the last failing surface was a stream (``stream_error_active``)
        and the backend is healthy, also clears the stream error flag
        so the warning variant disappears after the manual retry.
        """
        async with self:
            if self.health_retry_in_flight:
                return
            self.health_retry_in_flight = True
        api_url = _api_base_url()
        connected = await health_check(api_url)
        await self._apply_health_result(connected)
        async with self:
            self.health_retry_in_flight = False
            if connected and self.stream_error_active:
                self.stream_error_active = False
                self.error_message = ""
        if connected and self.last_failed_turn_content:
            async with self:
                session_id = self.session_id
                content = self.last_failed_turn_content
                self.last_failed_turn_content = ""
            if session_id and content:
                await self._stream_turn(session_id, content)

    @rx.event(background=True)
    async def dismiss_stream_error(self) -> None:
        """Manually clear the stream error flag (e.g. when user types again)."""
        async with self:
            self.stream_error_active = False
            self.error_message = ""
            self.last_failed_turn_content = ""

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
            self._begin_turn(content, session_id)
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
            self._begin_turn(body, session_id)
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
            info = await generate_session_title(api_url, session_id, message=message)
        except httpx.HTTPError as exc:
            logger.warning(f"BrandMind web: parallel title gen failed: {exc}")
            return
        if not info.metadata.title:
            return
        async with self:
            self.sessions = self._replace_session_in_list(info)

    def _begin_turn(self, content: str, session_id: str) -> None:
        """Seed the chat scroll with a user turn + streaming agent placeholder.

        Must run inside ``async with self`` so the user bubble and the
        streaming agent bubble appear in the same render tick. Records
        ``streaming_session_id`` so SSE events that arrive after the
        user has switched the view to another chat can be dropped at
        the dispatch layer instead of corrupting the visible chat.
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
        self.streaming_session_id = session_id

    async def _stream_turn(self, session_id: str, content: str) -> None:
        """Consume the SSE stream for one turn with exponential-backoff retry.

        Reconnect strategy: if :func:`stream_message` raises
        ``httpx.HTTPError`` before yielding the first event, the
        connection is treated as transient — sleep, retry, and try
        again with the same content. Backoff schedule lives in
        :data:`_STREAM_RECONNECT_BACKOFFS_SECONDS`. Once any event has
        been received the partial turn is left in place — retrying
        after partial delivery would create a duplicate turn on the
        server, so the user is offered the manual retry button instead.

        After every attempt either succeeds (``done`` / ``error`` event)
        or exhausts the backoff schedule, the agent bubble is finalised
        and the composer is re-enabled. On final failure the warning
        banner offers a manual retry that re-runs the same turn after
        the user confirms.
        """
        api_url = _api_base_url()
        async with self:
            self.stream_error_active = False
            self.last_failed_turn_content = ""

        success = False
        for attempt_index, backoff in enumerate(
            (0.0, *_STREAM_RECONNECT_BACKOFFS_SECONDS)
        ):
            if backoff:
                logger.info(
                    f"BrandMind web: SSE reconnect attempt {attempt_index} "
                    f"after {backoff}s"
                )
                await asyncio.sleep(backoff)
            received_any = False
            try:
                async for event in stream_message(api_url, session_id, content):
                    received_any = True
                    async with self:
                        self._dispatch_event(event.event, event.data)
                        if event.event in {"done", "error"}:
                            self.is_streaming = False
                            self._finalize_agent_message()
                            break
            except httpx.HTTPError as exc:
                logger.warning(
                    f"BrandMind web: stream failed (attempt {attempt_index}): {exc}"
                )
                if received_any:
                    await self._mark_stream_failed(content, mid_stream=True)
                    break
                if attempt_index == len(_STREAM_RECONNECT_BACKOFFS_SECONDS):
                    await self._mark_stream_failed(content, mid_stream=False)
                    break
                continue
            else:
                async with self:
                    self.stream_error_active = False
                    self.last_failed_turn_content = ""
                success = True
                break

        await self._run_post_turn_followups(session_id, success=success)

    async def _mark_stream_failed(self, content: str, *, mid_stream: bool) -> None:
        """Surface a stream failure to the user with retry context.

        Args:
            content (str): The user-message body that failed to stream
                so the retry path can resend it.
            mid_stream (bool): ``True`` when at least one event was
                received before the drop — the user message is already
                on the server, so retry would duplicate it; the banner
                wording reflects that.
        """
        async with self:
            self.is_streaming = False
            self._finalize_agent_message()
            self.stream_error_active = True
            self.last_failed_turn_content = content
            if mid_stream:
                self.error_message = (
                    "Connection lost mid-response. The agent may have "
                    "kept working — refresh the chat to see its final "
                    "answer."
                )
            else:
                self.error_message = (
                    "Could not reach the agent. Click try again to resend this message."
                )

    async def _run_post_turn_followups(self, session_id: str, *, success: bool) -> None:
        """Refresh sidebar + auto-title + canvas after a turn settles.

        Runs whether the stream succeeded or failed mid-flight so the
        sidebar's message count still updates when the server already
        recorded the user turn. ``success`` gates the artifact reveal —
        a failed stream cannot trust the ``artifacts_refresh_pending``
        flag because the failing dispatch may have only produced a
        partial manifest entry.
        """
        api_url = _api_base_url()
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
        if success and artifacts_pending:
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

    async def _select_artifact_internal(self, filename: str, category: str) -> None:
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
            self.docx_toc_open = False
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
        """Route one SSE event to the matching state mutation.

        When the user has switched the view to a different chat while
        this stream is mid-flight, drop paint for everything except
        the stream's own terminal markers. The agent's response keeps
        being persisted server-side; the user sees it next time they
        navigate back and the chat is re-fetched from the server.
        """
        if self.streaming_session_id and self.streaming_session_id != self.session_id:
            return
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
        """Append a streaming chunk to the active agent message body.

        Mirrors the token into two places:

        - ``target.content`` — concatenated text used by the persisted-
          history fallback renderer.
        - ``target.blocks`` — the ordered live-block view: append to the
          trailing ``assistant_text`` block when it is still open, or
          push a fresh ``assistant_text`` block when the trailing block
          is a ``reasoning_timeline`` (Codex Phase 1 Rule 3) or when no
          block has been opened yet.

        Args:
            token (str): Incremental assistant-text chunk from the
                ``streaming_token`` SSE event.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target.content = f"{target.content}{token}"
        target.blocks = _append_token_to_blocks(list(target.blocks), token)
        self.messages = [*self.messages[:-1], target]

    def _append_thinking(self, token: str, finalised: bool) -> None:
        """Append a streaming thinking chunk to the reasoning timeline.

        Consecutive thinking chunks merge into the trailing thinking entry
        until the backend signals ``done`` for that block; the next
        thinking event after that opens a new entry. Mirrors into both
        the legacy ``target.timeline`` (fallback for persisted history)
        AND the trailing ``reasoning_timeline`` block on ``target.blocks``
        (Phase 1 live-block view), opening a new reasoning_timeline
        block when the trailing block is an ``assistant_text`` so a
        progress note above the timeline stays in its own paragraph.

        Args:
            token (str): Incremental thinking-text chunk.
            finalised (bool): Whether the ``streaming_thinking`` event
                marks this block as done.
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
                tail.thinking_text = _compact_thinking_text(
                    f"{tail.thinking_text}{token}"
                )
                tail.thinking_segments = _segment_thinking_text(tail.thinking_text)
            if finalised:
                tail.thinking_done = True
        elif token:
            normalized_thinking = _compact_thinking_text(token)
            timeline.append(
                TimelineEntry(
                    kind="thinking",
                    thinking_text=normalized_thinking,
                    thinking_segments=_segment_thinking_text(normalized_thinking),
                    thinking_done=finalised,
                )
            )
        target.timeline = timeline
        target.blocks = _append_thinking_to_blocks(
            list(target.blocks), token, finalised
        )
        self.messages = [*self.messages[:-1], target]

    def _append_tool_call(self, call: ToolCallPayload) -> None:
        """Push a new in-progress tool entry into the reasoning timeline.

        Mirrors the entry into both ``target.timeline`` (legacy fallback)
        and the trailing ``reasoning_timeline`` block on ``target.blocks``
        (Phase 1 live view), opening a new reasoning_timeline block when
        the trailing block is an ``assistant_text``.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        entry = TimelineEntry(
            kind="tool_call",
            tool_call=ToolCallInfo(
                tool_name=call.tool_name,
                arguments=call.arguments,
                tool_call_id=call.tool_call_id,
            ),
        )
        target.timeline = [*target.timeline, entry]
        target.blocks = _append_timeline_entry_to_blocks(list(target.blocks), entry)
        self.messages = [*self.messages[:-1], target]

    def _settle_tool_result(self, result: ToolResultPayload) -> None:
        """Settle the matching in-progress tool entry with the result text.

        Prefers ``tool_call_id`` pairing so concurrent invocations of the
        same tool always settle the exact originating call. When the id
        is missing (older sessions or providers that do not emit one)
        the search falls back to the earliest still-running entry with
        the same ``tool_name`` so a single in-flight invocation still
        resolves correctly. Mirrors the settlement into both the
        legacy ``target.timeline`` and the ordered ``target.blocks``
        view (Phase 1) so either renderer flips the row to its
        completed icon.
        """
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent" or not target.timeline:
            return
        settled = False
        if result.tool_call_id and self._settle_by_tool_call_id(
            target, result.tool_call_id, result.result
        ):
            settled = True
        if not settled:
            for entry in target.timeline:
                if entry.kind != "tool_call" or entry.tool_call is None:
                    continue
                if (
                    entry.tool_call.tool_name == result.tool_name
                    and entry.tool_call.result == ""
                ):
                    entry.tool_call.result = result.result
                    break
        target.blocks = _settle_tool_result_in_blocks(
            list(target.blocks),
            result.tool_call_id,
            result.tool_name,
            result.result,
        )
        self.messages = [*self.messages[:-1], target]

    def _settle_by_tool_call_id(
        self,
        target: ChatMessage,
        tool_call_id: str,
        result_text: str,
    ) -> bool:
        """Settle the timeline entry whose ``tool_call_id`` matches the result.

        Returns ``True`` when a matching unresolved entry was found and
        updated so the caller can skip the FIFO fallback.
        """
        for entry in target.timeline:
            if entry.kind != "tool_call" or entry.tool_call is None:
                continue
            if (
                entry.tool_call.tool_call_id == tool_call_id
                and entry.tool_call.result == ""
            ):
                entry.tool_call.result = result_text
                return True
        return False

    def _apply_phase_advance(self, advance: PhaseAdvancePayload) -> None:
        """Mirror a phase-advance event into the sidebar state."""
        self.current_phase = advance.to_phase
        self.completed_phases = list(advance.completed_phases)
        if advance.scope:
            self.scope = advance.scope

    def _apply_metadata(self, metadata: BrandStrategyMetadata) -> None:
        """Refresh sidebar + identity state from a full metadata payload.

        ``main_agent_model`` is treated as the locked profile when the
        server returns a non-empty value — switching chats then
        reflects the picker as read-only on the locked option without
        clobbering ``selected_model_id`` (which represents the user's
        intent for the next new chat).
        """
        self.current_phase = metadata.current_phase
        self.completed_phases = list(metadata.completed_phases)
        self.scope = metadata.scope or ""
        self.brand_name = metadata.brand_name or ""
        self.phase_sequence = list(metadata.phase_sequence)
        self.phase_display_labels = dict(metadata.phase_display_labels)
        self.locked_model_id = metadata.main_agent_model or ""
        if self.locked_model_id and not self.selected_model_id:
            self.selected_model_id = self.locked_model_id

    def _finalize_agent_message(self) -> None:
        """Close the trailing agent message and tidy its reasoning timeline.

        On stream close: force-settle any tool entries the backend never
        emitted a ``tool_result`` for (fire-and-forget tools like
        ``write_todos`` are common), mark any open thinking blocks done,
        compute the turn duration, and collapse the timeline by default
        so the chat scroll reads as the final response. The
        ``streaming_session_id`` is always cleared so the global
        ``is_streaming`` lock can release; if the user has switched the
        view to a different chat, the message-list mutation is skipped
        (the visible chat is not the stream target).
        """
        streamed_id = self.streaming_session_id
        self.streaming_session_id = ""
        if streamed_id and streamed_id != self.session_id:
            return
        if not self.messages:
            return
        target = self.messages[-1]
        if target.role != "agent":
            return
        target = _compact_chat_message_timeline(target)
        for entry in target.timeline:
            if entry.kind == "tool_call" and entry.tool_call is not None:
                if entry.tool_call.result == "":
                    entry.tool_call.result = "(done)"
            elif entry.kind == "thinking" and not entry.thinking_done:
                entry.thinking_done = True
        for block in target.blocks:
            if block.kind == "reasoning_timeline":
                for entry in block.timeline:
                    if entry.kind == "tool_call" and entry.tool_call is not None:
                        if entry.tool_call.result == "":
                            entry.tool_call.result = "(done)"
                    elif entry.kind == "thinking" and not entry.thinking_done:
                        entry.thinking_done = True
            block.is_done = True
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
        target = _compact_chat_message_timeline(target)
        target.timeline_expanded = not target.timeline_expanded
        self.messages = [
            *self.messages[:message_index],
            target,
            *self.messages[message_index + 1 :],
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
