"""
Agent browser tool for social media research.

This module exposes ``create_browse_tool()``, a factory function that binds a
pre-configured ``BrowserManager`` to a closure and returns an async function
``browse_and_research(task)`` that the LangChain/DeepAgents framework can
register as an agent tool.

**Design rationale — factory + closure pattern**:
Agent tools must have a clean, LLM-facing signature containing *only* the
arguments the agent provides (e.g., the task description). Infrastructure
dependencies like ``BrowserManager`` must not appear in the tool signature —
the LLM cannot provide them, and exposing them would confuse the tool schema.

The factory pattern solves this by capturing ``browser_manager`` in a closure
at agent initialization time, while the inner ``browse_and_research()`` function
presents only ``task: str`` to the agent.

**LLM configuration**:
The browser agent always uses ``gemini-flash-latest`` via ``ChatGoogle`` from
``browser-use``. The model is fixed (not overridable) to ensure consistent cost
and latency characteristics. ``GEMINI_API_KEY`` from ``SETTINGS`` is bridged to
the ``GOOGLE_API_KEY`` environment variable required by ``ChatGoogle``.

Usage::

    from shared.agent_tools.browser import BrowserManager, create_browse_tool

    manager = BrowserManager()
    browse_tool = create_browse_tool(manager)

    # Agent calls:
    result = await browse_tool(
        "Go to facebook.com and summarize the top 3 posts on my news feed"
    )
"""

import os
from typing import Callable, Coroutine, Literal

from browser_use import Agent as BrowserAgent
from browser_use import ChatGoogle

from config.system_config import SETTINGS

from .browser_manager import BrowserManager

_DEFAULT_MODEL = "gemini-3-flash-preview"
_DEFAULT_THINKING_LEVEL: Literal["minimal", "low", "medium", "high"] = "medium"
_DEFAULT_MAX_STEPS = 30  # Cap browser actions per task to prevent runaway sessions


def _create_browser_llm() -> ChatGoogle:
    """
    Create and return a ``ChatGoogle`` LLM instance for the browser agent.

    Reads the Google API key from ``SETTINGS.GEMINI_API_KEY`` and bridges it
    to the ``GOOGLE_API_KEY`` environment variable expected by ``browser-use``'s
    ``ChatGoogle`` class.

    Returns:
        A configured ``ChatGoogle`` instance using ``gemini-flash-latest`` with
        ``"low"`` thinking level.

    Raises:
        ValueError: If ``SETTINGS.GEMINI_API_KEY`` is not set. The user must
            configure it via ``make setup-env``.
    """
    if not SETTINGS.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured. Run 'make setup-env' to set it up."
        )

    # browser-use's ChatGoogle reads the API key from the GOOGLE_API_KEY
    # environment variable. Our project stores it as GEMINI_API_KEY in SETTINGS,
    # so we bridge the two here before constructing the model.
    os.environ["GOOGLE_API_KEY"] = SETTINGS.GEMINI_API_KEY

    return ChatGoogle(
        model=_DEFAULT_MODEL,
        thinking_level=_DEFAULT_THINKING_LEVEL,
    )


def create_browse_tool(
    browser_manager: BrowserManager,
) -> Callable[[str], Coroutine]:
    """
    Factory function that creates a ready-to-use ``browse_and_research`` tool
    with ``browser_manager`` pre-bound via closure.

    This is called **once** during agent initialization, binding the
    infrastructure dependency (``browser_manager``) before the agent starts
    processing user requests. The returned ``browse_and_research`` function
    exposes only ``task: str`` — the single argument the LLM must provide.

    The returned function's docstring serves as the tool description that the
    LLM reads to decide when and how to invoke the tool.

    Args:
        browser_manager: A pre-configured ``BrowserManager`` instance with the
            desired sandbox directory and stealth settings. Callers are
            responsible for ensuring ``setup_login()`` has been run at least
            once before the agent starts browsing.

    Returns:
        An async callable ``browse_and_research(task: str) -> str`` suitable
        for registration as a LangChain / DeepAgents tool.

    Example::

        manager = BrowserManager()
        browse_tool = create_browse_tool(manager)

        # Register as tool (exact API depends on agent framework):
        agent = create_agent(tools=[browse_tool, search_web, ...])
    """

    async def browse_and_research(task: str) -> str:
        """
        Research social media platforms using a real browser with a
        logged-in clone account session.

        Use this tool ONLY when you need to access content that requires
        user authentication or JavaScript rendering on social media platforms
        (Facebook, Instagram, etc.). For general web search, use
        ``search_web()`` instead. For reading public articles or documents,
        use the crawl tools instead.

        This tool opens a visible Chrome window that the user can watch.
        An AI browser agent (powered by ``browser-use``) autonomously navigates
        pages, reads posts, scrolls feeds, and extracts the requested
        information. Interactive elements are highlighted on screen.

        When to use:
        - Research competitor social media posts and engagement metrics
        - Analyze trending content on Facebook / Instagram feeds
        - Gather audience feedback from social media comments or replies
        - Browse social media profiles for brand research
        - Access authenticated content (e.g., private group posts)

        When NOT to use:
        - Simple web search queries → use ``search_web()``
        - Reading public articles, blogs, or documentation → use crawl tools
        - Querying marketing knowledge → use ``search_knowledge_graph()``
        - Searching document library → use ``search_document_library()``

        Args:
            task: Natural language description of what to research.
                Be specific: name the platform, what content to find,
                and what information to extract.

                Good examples:
                - "Go to facebook.com and summarize the latest 3 posts
                  from the page 'Competitor Brand'. Include the post text
                  and estimated engagement (likes, comments)."
                - "Navigate to instagram.com/explore and list the top 5
                  trending hashtags visible on the Explore page."

                Poor examples (too vague):
                - "Check social media"
                - "Find competitor info"

        Returns:
            Research findings as structured text. The browser agent will
            format its findings as a readable summary of what it observed,
            extracted, and concluded from the browsing session.

        Raises:
            RuntimeError: If no valid login session exists. The user must
                run ``setup_login()`` (or ``brandmind browser setup``) first.
            ValueError: If ``GEMINI_API_KEY`` is not configured. Run
                ``make setup-env`` to set it up.
        """
        llm = _create_browser_llm()
        browser = browser_manager.get_browser()

        # Inject guardrails into the task description so the browser
        # agent knows when to STOP instead of endlessly retrying.
        task_with_guardrails = (
            task + "\n\n---\n"
            "**CRITICAL RULES:**\n"
            "- If you encounter a login wall, paywall, or authentication "
            "requirement, try **AT MOST ONE** alternative approach. "
            "If that also fails, **STOP IMMEDIATELY**.\n"
            "- Do **NOT** try multiple proxy/viewer services to bypass "
            "login walls. This wastes time with no result.\n"
            "- When you cannot access content, report clearly: "
            "(1) what you **could** observe before being blocked, "
            "(2) which URL was inaccessible, "
            "(3) the reason (login required, content blocked, etc.).\n"
            "- **Partial information is valuable.** Reporting 'profile has "
            "~6K followers but content is login-gated' is far better than "
            "spending 20 steps trying to bypass the wall.\n"
        )

        agent: BrowserAgent = BrowserAgent(
            task=task_with_guardrails,
            llm=llm,
            browser=browser,
        )

        # agent.run() returns AgentHistoryList; final_result() extracts
        # the last response. max_steps is a safety net in case guardrails
        # don't fully prevent runaway sessions.
        history = await agent.run(max_steps=_DEFAULT_MAX_STEPS)
        final: str = history.final_result() or str(history)
        return final

    return browse_and_research
