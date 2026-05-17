"""Session-related Pydantic schemas for the API server.

Provides strongly-typed request/response models with discriminated
metadata based on session mode.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

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
    """

    current_phase: str
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = []
    phase_sequence: list[str] = []
    phase_display_labels: dict[str, str] = {}
    title: str = ""
    pinned: bool = False


class SessionInfo(BaseModel):
    """API response model for session state."""

    session_id: str
    mode: SessionMode
    created_at: datetime
    message_count: int
    metadata: AskSessionMetadata | BrandStrategyMetadata


class CreateSessionRequest(BaseModel):
    """Request body for creating a new session."""

    mode: SessionMode
    initial_message: str | None = None


class SessionMessage(BaseModel):
    """One user-or-agent turn from a session's chat history.

    Returned by ``GET /api/v1/sessions/{id}/messages`` so the web UI
    can repaint a chat scroll when the user switches between
    persistent sessions. Tool calls and the internal reasoning trace
    are intentionally not part of this shape — they are stream-only
    artefacts that do not survive across page reloads.
    """

    role: Literal["user", "agent"]
    content: str


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
