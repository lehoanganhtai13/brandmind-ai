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
    """Completed tool call surfaced inline in the chat timeline."""

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: str = ""


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
        thinking_done (bool): Whether the thinking block has finalised so
            subsequent ``streaming_thinking`` events should open a new
            entry instead of appending here.
        tool_call (ToolCallInfo | None): Tool-call payload. ``None`` when
            ``kind == "thinking"``.
    """

    kind: Literal["thinking", "tool_call"]
    thinking_text: str = ""
    thinking_done: bool = False
    tool_call: ToolCallInfo | None = None


class BrandStrategyMetadata(BaseModel):
    """Metadata payload mirroring ``server.schemas.session.BrandStrategyMetadata``.

    The web UI reads ``phase_sequence`` and ``phase_display_labels`` to
    render the scope-dependent sidebar without hard-coding the canonical
    phase taxonomy on the client side. ``title`` and ``pinned`` drive
    the chat-picker row label and pin badge.
    """

    current_phase: str = "phase_0"
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    phase_sequence: list[str] = Field(default_factory=list)
    phase_display_labels: dict[str, str] = Field(default_factory=dict)
    title: str = ""
    pinned: bool = False


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


class SessionMessage(BaseModel):
    """One persisted turn from a session's chat history.

    Agent turns carry the reasoning ``timeline`` and short
    ``duration_label`` so the rehydrated bubble can show the "Thought
    for …" summary the user saw live. User turns leave both empty.
    """

    role: Literal["user", "agent"]
    content: str
    timeline: list[PersistedTimelineEntryWire] = Field(default_factory=list)
    duration_label: str = ""


class SessionMessages(BaseModel):
    """Response body of ``GET /api/v1/sessions/{id}/messages``."""

    session_id: str
    messages: list[SessionMessage] = Field(default_factory=list)


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
    """

    role: Literal["user", "agent"]
    content: str = ""
    is_streaming: bool = False
    timeline: list[TimelineEntry] = Field(default_factory=list)
    turn_started_at: float = 0.0
    turn_duration_label: str = ""
    timeline_expanded: bool = True


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


class ToolResultPayload(BaseModel):
    """SSE ``tool_result`` event body — emitted when a tool finishes."""

    tool_name: str
    result: str = ""


class StreamDonePayload(BaseModel):
    """SSE ``done`` event body — final accumulated state for the turn."""

    response: str = ""
    metadata: BrandStrategyMetadata = Field(default_factory=BrandStrategyMetadata)
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
