"""SSE event schemas for the API server.

Defines server-only events that complement the agent event types
from shared.agent_middlewares.callback_types.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from server.schemas.chat import ToolCallInfo
from server.schemas.session import AskSessionMetadata, BrandStrategyMetadata


class StreamDoneEvent(BaseModel):
    """Final SSE event signaling stream completion.

    Constructed by the SSE serialization layer after
    stream_agent_response() completes. Carries the full accumulated
    response text and updated session metadata so the client can
    finalize in one shot.

    This is NOT a BaseAgentEvent — it's a server-only construct.
    """

    type: Literal["done"] = "done"
    response: str
    metadata: AskSessionMetadata | BrandStrategyMetadata
    tool_calls: list[ToolCallInfo] = []
