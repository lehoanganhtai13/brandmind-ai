"""Enum definitions for BrandMind API server.

Provides strong typing for session modes and SSE event types.
Follows the same (str, Enum) pattern used by BrandScope and Phase
in core.brand_strategy.orchestrator.phase_state.
"""

from enum import Enum


class SessionMode(str, Enum):
    """Available session modes for the API server.

    Each mode creates a different agent type:
    - ASK: Q&A agent with KG + document library tools
    - BRAND_STRATEGY: Full brand strategy agent with 6-phase workflow
    """

    ASK = "ask"
    BRAND_STRATEGY = "brand-strategy"


class SSEEventType(str, Enum):
    """SSE event types sent from server to client.

    Core events (from callback_types.py):
    - MODEL_LOADING through STREAMING_TOKEN map 1:1 to BaseAgentEvent subclasses

    Server-only events:
    - DONE signals stream completion with final response + metadata
    """

    MODEL_LOADING = "model_loading"
    THINKING = "thinking"
    STREAMING_THINKING = "streaming_thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TODO_UPDATE = "todo_update"
    STREAMING_TOKEN = "streaming_token"
    DONE = "done"
