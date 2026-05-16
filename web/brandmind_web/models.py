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


class BrandStrategyMetadata(BaseModel):
    """Metadata payload mirroring ``server.schemas.session.BrandStrategyMetadata``.

    The web UI reads ``phase_sequence`` and ``phase_display_labels`` to
    render the scope-dependent sidebar without hard-coding the canonical
    phase taxonomy on the client side.
    """

    current_phase: str = "phase_0"
    scope: str | None = None
    brand_name: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    phase_sequence: list[str] = Field(default_factory=list)
    phase_display_labels: dict[str, str] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    """Session-level state returned by ``GET /api/v1/sessions/{id}``."""

    session_id: str
    mode: str
    message_count: int = 0
    metadata: BrandStrategyMetadata = Field(default_factory=BrandStrategyMetadata)


class ChatMessage(BaseModel):
    """One row in the chat scroll — either a user turn or an agent turn.

    Agent messages accumulate streaming-token chunks into ``content``
    while in flight; ``is_streaming`` flips to ``False`` once the SSE
    ``done`` event fires for the turn. ``tool_calls`` carries the
    inline tool-call timeline cards captured for the same turn so the
    web UI can interleave them above the message body.
    """

    role: Literal["user", "agent"]
    content: str = ""
    thinking: str = ""
    is_streaming: bool = False
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)


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
