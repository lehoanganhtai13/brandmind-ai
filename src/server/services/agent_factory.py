"""Agent factory with registry pattern for session modes.

Follows Open/Closed principle: new modes register via decorator
without modifying existing factory code.

Both create_qa_agent() and create_brand_strategy_agent() accept
the same callback signature (callback, on_tool_start, on_tool_end).
Verified from:
- src/cli/inference.py:31-35
- src/core/src/core/brand_strategy/agent_config.py:16-20
"""

from __future__ import annotations

from typing import Callable

from langgraph.graph.state import CompiledStateGraph

from server.schemas.enums import SessionMode
from shared.agent_middlewares.callback_types import AgentCallback

AgentFactoryFn = Callable[
    [
        AgentCallback | None,
        Callable[[str], object] | None,
        Callable[[object], None] | None,
    ],
    CompiledStateGraph,
]

_AGENT_FACTORIES: dict[SessionMode, AgentFactoryFn] = {}


def register_agent_factory(
    mode: SessionMode,
) -> Callable[[AgentFactoryFn], AgentFactoryFn]:
    """Decorator to register an agent factory for a session mode.

    Usage:
        @register_agent_factory(SessionMode.ASK)
        def _create_ask_agent(callback, on_tool_start, on_tool_end):
            ...
    """

    def decorator(fn: AgentFactoryFn) -> AgentFactoryFn:
        _AGENT_FACTORIES[mode] = fn
        return fn

    return decorator


def create_agent_for_session(
    mode: SessionMode,
    callback: AgentCallback | None = None,
    on_tool_start: Callable[[str], object] | None = None,
    on_tool_end: Callable[[object], None] | None = None,
) -> CompiledStateGraph:
    """Create the appropriate agent for the session mode.

    Args:
        mode: Session mode determining which agent to create.
        callback: Event callback for middleware (LogModelMessageMiddleware).
        on_tool_start: Hook called when a tool starts execution.
        on_tool_end: Hook called when a tool finishes execution.

    Returns:
        Compiled LangGraph agent ready for ainvoke/astream.

    Raises:
        ValueError: If no factory is registered for the given mode.
    """
    factory = _AGENT_FACTORIES.get(mode)
    if factory is None:
        raise ValueError(f"No agent factory registered for {mode}")
    return factory(callback, on_tool_start, on_tool_end)


# ── Registered Factories ─────────────────────────────────────────────


@register_agent_factory(SessionMode.ASK)
def _create_ask_agent(
    callback: AgentCallback | None,
    on_tool_start: Callable[[str], object] | None,
    on_tool_end: Callable[[object], None] | None,
) -> CompiledStateGraph:
    """Create Q&A agent for ask-mode sessions."""
    from cli.inference import create_qa_agent

    return create_qa_agent(
        callback=callback,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
    )


@register_agent_factory(SessionMode.BRAND_STRATEGY)
def _create_brand_strategy_agent(
    callback: AgentCallback | None,
    on_tool_start: Callable[[str], object] | None,
    on_tool_end: Callable[[object], None] | None,
) -> CompiledStateGraph:
    """Create brand strategy agent for brand-strategy sessions.

    Note: The caller (SessionManager) must call set_active_session()
    BEFORE invoking this factory — the agent reads get_active_session()
    internally during creation (agent_config.py lines 129, 326).
    """
    from core.brand_strategy.agent_config import (
        create_brand_strategy_agent,
    )

    return create_brand_strategy_agent(
        callback=callback,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
    )
