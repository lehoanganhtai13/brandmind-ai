"""
Callback type definitions for agent middleware output integration.

Uses Pydantic BaseModel inheritance for type-safe, extensible event types.
All events inherit from BaseAgentEvent for consistent type annotation.
"""

from typing import Any, Callable, Literal

from pydantic import BaseModel, Field


class BaseAgentEvent(BaseModel):
    """
    Base class for all agent events.

    All specific event types inherit from this class, enabling
    consistent type annotation: `def handle(event: BaseAgentEvent)`
    """

    type: str = Field(..., description="Event type discriminator")

    class Config:
        """Pydantic config."""

        frozen = True  # Immutable events


class ThinkingEvent(BaseAgentEvent):
    """Event emitted when model produces thinking content."""

    type: Literal["thinking"] = "thinking"
    content: str = Field(..., description="Model thinking content")


class ToolCallEvent(BaseAgentEvent):
    """Event emitted when tool is called."""

    type: Literal["tool_call"] = "tool_call"
    tool_name: str = Field(..., description="Name of the tool being called")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Tool call arguments"
    )


class ToolResultEvent(BaseAgentEvent):
    """Event emitted when tool returns result."""

    type: Literal["tool_result"] = "tool_result"
    tool_name: str = Field(..., description="Name of the tool")
    result: str = Field(..., description="Tool execution result")


class TodoUpdateEvent(BaseAgentEvent):
    """Event emitted when todo list changes."""

    type: Literal["todo_update"] = "todo_update"
    todos: list[dict[str, Any]] = Field(
        default_factory=list, description="Current todo list state"
    )


class ModelLoadingEvent(BaseAgentEvent):
    """Event emitted when model is busy/loading."""

    type: Literal["model_loading"] = "model_loading"
    loading: bool = Field(
        ..., description="True if model started loading, False if finished"
    )


# Type alias for callback function
# Uses base class for polymorphism - can receive any event type
AgentCallback = Callable[[BaseAgentEvent], None]
