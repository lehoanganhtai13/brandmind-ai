"""Dynamic tool loading middleware — inventory pattern for LangChain.

Implements a game-like tool inventory system using LangChain middleware:
- tool_search: Browse the warehouse catalog
- load_tools: Equip tools the agent needs
- unload_tools: Put tools back when done
- Blacklist approach: catalog tools are hidden until loaded, all other tools visible

Usage:
    from shared.agent_middlewares.tool_search import create_tool_search_middleware

    middleware = create_tool_search_middleware(
        all_tools=tools,
        tool_catalog=BRAND_STRATEGY_TOOL_CATALOG,
    )
"""

from .middleware import ToolSearchMiddleware, create_tool_search_middleware
from .registry import ToolMetadata, ToolRegistry

__all__ = [
    "ToolSearchMiddleware",
    "ToolRegistry",
    "ToolMetadata",
    "create_tool_search_middleware",
]
