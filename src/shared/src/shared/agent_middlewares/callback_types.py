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


class StreamingTokenEvent(BaseAgentEvent):
    """Event emitted for each streamed token from the model's final response.

    Used to enable real-time token-by-token display of the agent's answer
    in both CLI and TUI renderers. This event is emitted during the streaming
    phase of the agent's response, allowing progressive rendering of the final
    answer as tokens arrive.

    Attributes:
        token: The text chunk from the model's streaming output. Can be a single
            character, word, or phrase depending on the model's streaming behavior.
        done: Whether this is the final token (stream complete). When True, this
            signals that the streaming phase has ended and no more tokens will
            be received for the current response.
    """

    type: Literal["streaming_token"] = "streaming_token"
    token: str = Field(..., description="Text chunk from model streaming output")
    done: bool = Field(
        default=False, description="True if this is the final token (stream ended)"
    )


class StreamingThinkingEvent(BaseAgentEvent):
    """Event emitted for each streamed thinking token from the model.

    Enables real-time progressive display of the model's reasoning process
    as thinking tokens arrive from the stream, rather than showing the full
    thinking block all at once after completion. This provides better user
    experience by allowing users to observe the model's thought process in
    real-time as it generates.

    Attributes:
        token: Thinking text chunk from the model's streaming output. Can be
            a word, phrase, or sentence depending on streaming granularity.
        done: Whether this is the final thinking token for the current step.
            When True, signals the end of the thinking phase and that the
            model is transitioning to generating the final answer.
        title: Optional title summarizing the thinking block. Some models
            emit a brief title as the first part of thinking content.
    """

    type: Literal["streaming_thinking"] = "streaming_thinking"
    token: str = Field(
        ..., description="Thinking text chunk from model streaming output"
    )
    done: bool = Field(
        default=False,
        description="True if thinking is complete for this step",
    )
    title: str = Field(
        default="",
        description="Optional title for thinking block",
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
