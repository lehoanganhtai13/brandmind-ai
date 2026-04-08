"""Chat-related Pydantic schemas for the API server.

Provides strongly-typed request/response models for the message endpoint.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from server.schemas.session import AskSessionMetadata, BrandStrategyMetadata


class MessageRequest(BaseModel):
    """Request body for sending a message to a session."""

    content: str


class ToolCallInfo(BaseModel):
    """Record of a single tool invocation during a turn."""

    tool_name: str
    arguments: dict[str, Any]
    result: str


class MessageResponse(BaseModel):
    """Non-streaming response from agent.

    Returned when stream=false. Contains the complete agent response
    along with updated session metadata and tool usage information.
    """

    response: str
    metadata: AskSessionMetadata | BrandStrategyMetadata
    tool_calls: list[ToolCallInfo] = []
