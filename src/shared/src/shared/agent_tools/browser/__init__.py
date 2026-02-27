"""
Agent browser tools for social media research.

This package provides an isolated, persistent browser sandbox that allows
the AI agent to browse social media platforms (Facebook, Instagram, etc.)
using a logged-in clone account.

Public API:
    - ``BrowserManager``: Manages browser lifecycle, login setup, and session
      persistence. Use ``setup_login()`` once to save a session, then
      ``get_browser()`` for subsequent agent browsing.
    - ``StealthConfig``: Pydantic model for anti-detection browser settings.
      Configures stealth layers (automation flag removal, human-like delays,
      headed mode) to avoid bot detection on social media platforms.
    - ``create_browse_tool(browser_manager)``: Factory function that returns
      an async ``browse_and_research(task)`` function suitable for registration
      as an agent tool. The ``browser_manager`` dependency is pre-bound via
      closure so the agent only sees ``task: str``.

Typical usage::

    from shared.agent_tools.browser import BrowserManager, create_browse_tool

    # One-time login setup (run interactively):
    manager = BrowserManager()
    await manager.setup_login("https://www.facebook.com")

    # Agent tool creation (at agent initialization):
    browse_tool = create_browse_tool(manager)

    # Agent browses (called autonomously by the agent):
    result = await browse_tool(
        "Go to facebook.com and summarize the latest 3 posts on my feed"
    )
"""

from .browser_manager import BrowserManager
from .browser_tool import create_browse_tool
from .stealth_config import StealthConfig

__all__ = [
    "BrowserManager",
    "StealthConfig",
    "create_browse_tool",
]
