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
    truth.
    """

    current_phase: str
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = []
    phase_sequence: list[str] = []
    phase_display_labels: dict[str, str] = {}


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
