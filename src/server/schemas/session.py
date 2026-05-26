"""Session-related Pydantic schemas for the API server.

Provides strongly-typed request/response models with discriminated
metadata based on session mode.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from server.schemas.enums import SessionMode


class AskSessionMetadata(BaseModel):
    """Metadata for ask-mode sessions.

    Currently minimal — may be extended with topic tracking,
    conversation summary, etc.
    """

    pass


class BrandStrategyMetadata(BaseModel):
    """Metadata for brand-strategy sessions.

    Reflects the state of BrandStrategySession without exposing
    internal implementation details. The web UI consumes the
    ``phase_sequence`` and ``phase_display_labels`` fields to render
    the scope-dependent progress sidebar without hard-coding the phase
    taxonomy on the client; backend stays the canonical source of
    truth. ``title`` and ``pinned`` carry UX state — the sidebar shows
    the title on each chat row and pins-to-top when ``pinned`` is set.
    ``main_agent_model`` exposes the picker selection so the web can
    show which profile is driving the session and lock the picker on
    rehydration.
    """

    current_phase: str
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = []
    phase_sequence: list[str] = []
    phase_display_labels: dict[str, str] = {}
    title: str = ""
    pinned: bool = False
    main_agent_model: str = ""


class SessionInfo(BaseModel):
    """API response model for session state."""

    session_id: str
    mode: SessionMode
    created_at: datetime
    message_count: int
    metadata: AskSessionMetadata | BrandStrategyMetadata


class CreateSessionRequest(BaseModel):
    """Request body for creating a new session.

    ``model_id`` optionally pins a brand-strategy session to a
    specific main-agent profile from
    :func:`core.brand_strategy.model_profiles.list_supported_brand_strategy_main_models`.
    Leave it unset to fall back to the server's configured default.
    The field is ignored for non brand-strategy modes.
    """

    mode: SessionMode
    initial_message: str | None = None
    model_id: str | None = None


class PersistedToolCallWire(BaseModel):
    """Tool call captured for one agent turn, in wire format.

    Mirrors :class:`core.brand_strategy.session.PersistedToolCall` over
    the API surface so the web UI can deserialise tool invocations from
    a session's history payload without depending on the core package.
    """

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: str = ""


class PersistedTimelineEntryWire(BaseModel):
    """One chronological reasoning-trace entry, in wire format.

    Mirrors :class:`core.brand_strategy.session.PersistedTimelineEntry`
    so the web UI can deserialise without depending on the core package.
    """

    kind: Literal["thinking", "tool_call"]
    thinking_text: str = ""
    tool_call: PersistedToolCallWire | None = None


class PersistedContentBlockWire(BaseModel):
    """One ordered assistant-turn block, in wire format.

    Added alongside the legacy ``content`` + ``timeline`` fields so
    newer clients can restore text → Thought → text ordering after a
    page reload while older clients keep ignoring the extra field.
    """

    kind: Literal["assistant_text", "reasoning_timeline"]
    text: str = ""
    timeline: list[PersistedTimelineEntryWire] = Field(default_factory=list)
    duration_label: str = ""


class SessionMessage(BaseModel):
    """One user-or-agent turn from a session's chat history.

    Returned by ``GET /api/v1/sessions/{id}/messages`` so the web UI
    can repaint a chat scroll when the user switches between persistent
    sessions. Agent turns carry their reasoning trace (thinking blocks
    plus completed tool calls) and the wall-clock ``duration_label`` so
    the rehydrated bubble can render the same collapsed "Thought for …"
    summary the live stream produced. User turns leave both fields
    empty since they have no reasoning trace of their own.
    """

    role: Literal["user", "agent"]
    content: str
    timeline: list[PersistedTimelineEntryWire] = Field(default_factory=list)
    duration_label: str = ""
    blocks: list[PersistedContentBlockWire] = Field(default_factory=list)


class SessionMessages(BaseModel):
    """Wire-format payload for a session's chat history."""

    session_id: str
    messages: list[SessionMessage]


class UpdateSessionRequest(BaseModel):
    """Partial update for a session's UX-side metadata.

    Both fields are optional so callers can rename, pin, or both in a
    single PATCH. Server-side default is "leave unchanged" — the
    handler ignores ``None`` rather than clearing the field.
    """

    title: str | None = None
    pinned: bool | None = None


class GenerateTitleRequest(BaseModel):
    """Optional body for the auto-title endpoint.

    ``message`` overrides the persisted first-user-message lookup,
    useful when the caller wants to title a chat from a draft that
    has not been streamed yet. When omitted the server reads the
    first ``HumanMessage`` from the session's stored history.
    """

    message: str | None = None
