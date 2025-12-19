"""
Context variable for tracking current tool execution.

Uses Python's contextvars to automatically track which tool is currently
executing. This context propagates through all async calls, allowing
loguru logs to be automatically grouped by their originating tool.

How it works:
1. Middleware sets current_tool when tool starts
2. All nested async calls inherit this context
3. Custom loguru sink reads current_tool to route logs
4. Middleware resets context when tool finishes
"""

from contextvars import ContextVar
from typing import Optional

# Context variable to track which tool is currently executing
# None means no tool is active (logs go to "Other" category)
current_tool: ContextVar[Optional[str]] = ContextVar(
    "current_tool",
    default=None,
)


def get_current_tool() -> Optional[str]:
    """Get the name of the currently executing tool, if any."""
    return current_tool.get()


def set_current_tool(tool_name: str) -> object:
    """
    Set the current tool context.

    Returns a token that must be used to reset the context.

    Args:
        tool_name: Name of the tool being executed

    Returns:
        Token for resetting context via current_tool.reset(token)
    """
    return current_tool.set(tool_name)


def reset_current_tool(token: object) -> None:
    """Reset the tool context using the token from set_current_tool."""
    current_tool.reset(token)  # type: ignore
