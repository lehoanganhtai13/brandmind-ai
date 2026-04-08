"""Session-related Pydantic schemas for the API server.

Provides strongly-typed request/response models with discriminated
metadata based on session mode.
"""

from __future__ import annotations

from datetime import datetime

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
    internal implementation details.
    """

    current_phase: str
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = []


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
