"""Client-side Pydantic models for the BrandMind Web UI.

The web sub-project stays self-contained per Task #89 Decision 4 — it does
not import from ``src/server/schemas`` or ``src/shared/agent_middlewares``
because the web container is intentionally decoupled from the backend
deployment. These models mirror the server-side schemas as they appear
on the SSE wire, so any change to the wire format must be reflected on
both sides. See ``src/server/schemas/session.py`` and
``src/shared/src/shared/agent_middlewares/callback_types.py`` for the
backend originals.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ToolCallInfo(BaseModel):
    """Completed tool call surfaced inline in the chat timeline.

    ``tool_call_id`` carries the provider id used to pair the result
    back to the originating call so the live timeline does not rely on
    FIFO-by-tool-name matching when the agent fires the same tool more
    than once before any of them returns.
    """

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: str = ""
    tool_call_id: str = ""


class ThinkingSegment(BaseModel):
    """One typed slice of a thinking block.

    The agent's reasoning stream interleaves short ``**bold headers**``
    with body paragraphs. Splitting that into typed segments lets the
    timeline render the headers with the brand's primary palette and a
    heavier weight while keeping the bodies italic-secondary, so the
    expanded "Thought for Ns" panel reads as a stack of headed
    paragraphs rather than one italic wall.

    Attributes:
        kind (Literal["header", "body"]): Header lines were wrapped in
            ``**...**`` markers in the raw stream; body lines were the
            paragraphs between them.
        text (str): The segment's visible text, stripped of the
            ``**`` markers.
    """

    kind: Literal["header", "body"]
    text: str


class TimelineEntry(BaseModel):
    """One chronological entry in an agent turn's reasoning timeline.

    The chat timeline merges streaming-thinking blocks and tool-call cards
    into a single ordered list so the UI can render the agent's reasoning
    trace as one connected vertical thread (Claude / ChatGPT pattern).
    Exactly one of ``thinking_text`` or ``tool_call`` is populated per
    entry; the discriminator is ``kind``.

    Attributes:
        kind (Literal["thinking", "tool_call"]): Which payload field holds
            this entry's content.
        thinking_text (str): Accumulated thinking-block text. Empty when
            ``kind == "tool_call"``.
        thinking_segments (list[ThinkingSegment]): Parsed view of
            ``thinking_text`` as alternating header / body slices,
            derived client-side from the raw ``**bold**`` markers. The
            timeline renders this list with ``rx.foreach`` so the React
            tree shape stays stable across thinking and tool-call rows
            (which is the React hook-order constraint that
            ``rx.markdown`` violates).
        thinking_done (bool): Whether the thinking block has finalised so
            subsequent ``streaming_thinking`` events should open a new
            entry instead of appending here.
        tool_call (ToolCallInfo | None): Tool-call payload. ``None`` when
            ``kind == "thinking"``.
    """

    kind: Literal["thinking", "tool_call"]
    thinking_text: str = ""
    thinking_segments: list[ThinkingSegment] = Field(default_factory=list)
    thinking_done: bool = False
    tool_call: ToolCallInfo | None = None


class BrandStrategyMetadata(BaseModel):
    """Metadata payload mirroring ``server.schemas.session.BrandStrategyMetadata``.

    The web UI reads ``phase_sequence`` and ``phase_display_labels`` to
    render the scope-dependent sidebar without hard-coding the canonical
    phase taxonomy on the client side. ``title`` and ``pinned`` drive
    the chat-picker row label and pin badge. ``main_agent_model`` lets
    the picker reflect the locked profile when the chat already started.
    """

    current_phase: str = "phase_0"
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    phase_sequence: list[str] = Field(default_factory=list)
    phase_display_labels: dict[str, str] = Field(default_factory=dict)
    title: str = ""
    pinned: bool = False
    main_agent_model: str = ""


class MainAgentModelOption(BaseModel):
    """One supported main-agent profile surfaced by the discovery endpoint.

    Mirrors ``server.api.brand_strategy.MainModelOption`` so the picker
    can render an option list without depending on the server package.
    ``description`` is the short trade-off blurb the picker shows
    underneath the display name.
    """

    model_id: str
    display_name: str
    description: str = ""
    is_default: bool = False


class SessionInfo(BaseModel):
    """Session-level state returned by ``GET /api/v1/sessions/{id}``."""

    session_id: str
    mode: str
    message_count: int = 0
    metadata: BrandStrategyMetadata = Field(default_factory=BrandStrategyMetadata)


class PersistedToolCallWire(BaseModel):
    """Tool call carried inside a persisted agent turn.

    Receives the same shape the backend ships in its message-history
    response so the rehydrated timeline can re-render the tool's name,
    arguments preview, and stringified result without re-running the
    agent.
    """

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: str = ""


class PersistedTimelineEntryWire(BaseModel):
    """One chronological reasoning-trace entry on the wire.

    Mirrors the server-side persisted shape so a rehydrated chat scroll
    renders the same collapsible thinking + tool-call timeline as the
    live SSE stream produced at send time.
    """

    kind: Literal["thinking", "tool_call"]
    thinking_text: str = ""
    tool_call: PersistedToolCallWire | None = None


class PersistedContentBlockWire(BaseModel):
    """One ordered assistant-turn block carried in persisted history.

    Mirrors :class:`server.schemas.session.PersistedContentBlockWire`.
    The backend serializes the insertion-ordered block list captured
    while the turn streamed so the client can restore the
    text → Thought → text layout after a refresh. ``duration_label``
    carries each reasoning block's own "Thought for Ns" timing; it is
    empty for ``assistant_text`` blocks and for turns persisted before
    per-block timings were recorded, where the client falls back to the
    turn-level label.
    """

    kind: Literal["assistant_text", "reasoning_timeline"]
    text: str = ""
    timeline: list[PersistedTimelineEntryWire] = Field(default_factory=list)
    duration_label: str = ""


class SessionMessage(BaseModel):
    """One persisted turn from a session's chat history.

    Agent turns carry the reasoning ``timeline`` and short
    ``duration_label`` so the rehydrated bubble can show the "Thought
    for …" summary the user saw live. ``blocks`` is the additive
    ordered-block payload clients hydrate from to restore the
    text → Thought → text layout; it is absent for turns persisted
    before blocks existed. User turns leave the timeline and block list
    empty.
    """

    role: Literal["user", "agent"]
    content: str
    timeline: list[PersistedTimelineEntryWire] = Field(default_factory=list)
    duration_label: str = ""
    blocks: list[PersistedContentBlockWire] = Field(default_factory=list)


class SessionMessages(BaseModel):
    """Response body of ``GET /api/v1/sessions/{id}/messages``."""

    session_id: str
    messages: list[SessionMessage] = Field(default_factory=list)


class ArtifactRef(BaseModel):
    """One artifact recorded in the backend manifest.

    Mirrors :class:`server.api.artifacts.ArtifactRef` so the canvas
    pane can list artifacts without depending on the server package.
    ``category`` drives which inline viewer is mounted; ``download_url``
    is the only handle the client needs to fetch the bytes. ``size_label``
    is a pre-formatted human-readable size (``"38 KB"`` etc.) the UI
    renders directly so the client does not own the unit logic.
    """

    session_id: str
    brand_name: str = ""
    category: Literal["documents", "presentations", "spreadsheets", "images"]
    tool: str = ""
    filename: str
    size_bytes: int = 0
    size_label: str = ""
    generated_at: str = ""
    download_url: str


class DocxTocEntry(BaseModel):
    """One heading in the auto-extracted DOCX outline."""

    level: int = 1
    text: str = ""
    anchor: str = ""


class DocxHtmlResponse(BaseModel):
    """Response body of ``GET /api/v1/artifacts/{id}/{filename}/html``.

    Carries the mammoth-rendered HTML body and the heading outline the
    canvas pane uses to paint a sticky TOC alongside the document.
    ``warnings`` is surfaced for diagnostics but the v1 UI does not
    render it inline.
    """

    html: str = ""
    toc: list[DocxTocEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UserProfileOption(BaseModel):
    """One option for a profile-settings dropdown.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileOption`
    so the settings + onboarding forms can render dropdowns without
    duplicating the canonical option list on the client.
    """

    value: str
    label: str
    description: str = ""


class UserProfileSettings(BaseModel):
    """Onboarding personalization settings synced with the backend.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileSettings`.
    Each field carries the public enum value (e.g. ``"fb"``,
    ``"comfortable"``) rather than the enum itself so the wire shape
    stays string-only. Defaults match the backend's safe fallback
    (``BALANCED`` mentoring density + ``UNKNOWN`` for the rest) so the
    dialog can render before the backend round-trip completes.
    """

    job_domain: str = "unknown"
    role: str = "unknown"
    experience_years: str = "unknown"
    brand_strategy_familiarity: str = "unknown"
    mentoring_style: str = "balanced"
    stakeholder_context: str = "unknown"
    onboarding_completed: bool = False
    updated_at: str | None = None


class UserProfileSettingsOptions(BaseModel):
    """Option lists for the six profile-settings dropdowns.

    Mirrors :class:`shared.workspace.profile_settings.UserProfileSettingsOptions`
    so the dialog projects the backend-owned label and description for
    each option without re-stating the copy on the client side.
    """

    job_domain: list[UserProfileOption] = Field(default_factory=list)
    role: list[UserProfileOption] = Field(default_factory=list)
    experience_years: list[UserProfileOption] = Field(default_factory=list)
    brand_strategy_familiarity: list[UserProfileOption] = Field(default_factory=list)
    mentoring_style: list[UserProfileOption] = Field(default_factory=list)
    stakeholder_context: list[UserProfileOption] = Field(default_factory=list)


class UserProfileSettingsPayload(BaseModel):
    """Response envelope for the user-profile settings endpoints.

    Both ``GET`` and ``PUT /api/v1/brand-strategy/user-profile/settings``
    return this shape. ``profile_markdown`` is the prompt-facing managed
    block the agent will read and is shown in the dialog as a read-only
    preview for users who want to verify what context is being persisted.
    """

    settings: UserProfileSettings = Field(default_factory=UserProfileSettings)
    options: UserProfileSettingsOptions = Field(
        default_factory=UserProfileSettingsOptions,
    )
    profile_markdown: str = ""


class ContentBlock(BaseModel):
    """One ordered slice of an agent turn — either prose text or a reasoning trace.

    The web UI renders an agent turn as a vertical sequence of blocks
    so a working note that arrives BEFORE the thinking can appear as
    its own paragraph above the timeline, instead of being merged with
    the final answer at the bottom (ChatGPT / Claude live-stream
    pattern). Block order is insertion order; the dispatch layer pushes
    a new block whenever the SSE event kind switches between text and
    reasoning, so the trailing block is always the active one.

    Each ``reasoning_timeline`` block carries its OWN expand state,
    started-at timestamp, and duration label so a turn that produces
    multiple thought blocks can collapse the earlier ones as soon as
    the next assistant text starts, give each block its own "Thought
    for Ns" badge, and be toggled independently from the others. The
    legacy single-toggle ``ChatMessage.timeline_expanded`` is only used
    by the persisted-history fallback renderer.

    Attributes:
        kind (Literal["assistant_text", "reasoning_timeline"]): Which
            payload field of this block holds content.
        text (str): Accumulated streaming-token text. Empty when
            ``kind == "reasoning_timeline"``.
        timeline (list[TimelineEntry]): Interleaved thinking + tool-call
            entries for this reasoning block. Empty when
            ``kind == "assistant_text"``.
        is_done (bool): True once the block has closed — either because
            a later block superseded it, or because the turn's ``done``
            event fired while this was the trailing block.
        expanded (bool): Whether the reasoning panel is open. Set to
            ``True`` while the block is live so the user sees the trace
            stream in; flipped to ``False`` once the block closes so the
            chat scroll lands on the final answer. Ignored for
            ``assistant_text`` blocks.
        started_at (float): ``time.monotonic()`` value captured when the
            block first opened. Used only client-side to compute
            ``duration_label`` when the block closes.
        duration_label (str): Pre-formatted ``"Ns"`` / ``"MmSs"`` label
            for the block's wall-clock duration, set when the block
            closes. An empty value renders the generic "Reasoning"
            header instead of "Thought for Ns".
        block_id (str): Stable per-block identifier (UUID hex) stamped
            at creation. The expand-toggle event locates the block by
            this id rather than by position so it stays correct inside
            the nested message/block render loops.
    """

    kind: Literal["assistant_text", "reasoning_timeline"]
    text: str = ""
    timeline: list[TimelineEntry] = Field(default_factory=list)
    is_done: bool = False
    expanded: bool = True
    started_at: float = 0.0
    duration_label: str = ""
    block_id: str = ""


class ChatMessage(BaseModel):
    """One row in the chat scroll — either a user turn or an agent turn.

    Agent messages accumulate streaming-token chunks into ``content``
    while in flight; ``is_streaming`` flips to ``False`` once the SSE
    ``done`` event fires for the turn. ``timeline`` carries the
    chronologically-ordered reasoning trace (thinking blocks + tool calls
    interleaved as they arrive on the wire) so the web UI can render a
    single connected collapsible thread (Claude / ChatGPT pattern).
    ``turn_started_at`` and ``turn_duration_s`` capture wall-clock
    duration so the collapsed state can read "Thought for Ns".
    ``timeline_expanded`` lets the user toggle the collapsed timeline
    open again after the turn closes.

    ``blocks`` is the ordered-blocks view of the same turn: the dispatch
    layer mirrors every streaming-token / thinking / tool event into
    both the legacy ``content`` + ``timeline`` fields AND the ordered
    ``blocks`` list, so a live stream renders the trace as
    text → Thought → text in arrival order. A turn re-loaded from a
    server that does not supply ``blocks`` keeps an empty list and
    falls back to the legacy single-content + single-timeline layout.

    Attributes:
        role (Literal["user", "agent"]): Speaker for this row.
        content (str): Concatenated assistant text (legacy mirror used
            for the persisted-history fallback renderer).
        is_streaming (bool): True while the agent turn is in flight.
        timeline (list[TimelineEntry]): Legacy single timeline mirror
            used for the persisted-history fallback renderer.
        turn_started_at (float): Wall-clock seconds at first token.
        turn_duration_label (str): Pre-formatted "Ns" label, set on
            ``done``.
        timeline_expanded (bool): Whether the user has the reasoning
            trace expanded.
        blocks (list[ContentBlock]): Ordered live blocks. Empty for
            persisted turns and during user rows.
    """

    role: Literal["user", "agent"]
    content: str = ""
    is_streaming: bool = False
    timeline: list[TimelineEntry] = Field(default_factory=list)
    turn_started_at: float = 0.0
    turn_duration_label: str = ""
    timeline_expanded: bool = True
    blocks: list[ContentBlock] = Field(default_factory=list)


class PhaseAdvancePayload(BaseModel):
    """SSE ``phase_advance`` event body.

    Sidebar consumes this to flip the current phase indicator without
    polling. Mirror of ``PhaseAdvanceEvent`` in callback_types.py.
    """

    from_phase: str
    to_phase: str
    completed_phases: list[str] = Field(default_factory=list)
    scope: str = ""


class StreamingTokenPayload(BaseModel):
    """SSE ``streaming_token`` event body."""

    token: str = ""
    done: bool = False


class StreamingThinkingPayload(BaseModel):
    """SSE ``streaming_thinking`` event body."""

    token: str = ""
    done: bool = False
    title: str = ""


class ToolCallPayload(BaseModel):
    """SSE ``tool_call`` event body — emitted when a tool starts."""

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    tool_call_id: str = ""


class ToolResultPayload(BaseModel):
    """SSE ``tool_result`` event body — emitted when a tool finishes."""

    tool_name: str
    result: str = ""
    tool_call_id: str = ""


class StreamDonePayload(BaseModel):
    """SSE ``done`` event body — final accumulated state for the turn."""

    response: str = ""
    metadata: BrandStrategyMetadata = Field(default_factory=BrandStrategyMetadata)
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
