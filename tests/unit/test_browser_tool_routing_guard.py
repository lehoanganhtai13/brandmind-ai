"""Regression tests for browser research routing guardrails."""

from __future__ import annotations

import pytest

from shared.agent_tools.browser.browser_tool import (
    _LIVE_BROWSER_MARKER,
    create_browse_tool,
)


class _ExplodingBrowserManager:
    def get_browser(self):  # pragma: no cover - should never be reached
        raise AssertionError("Browser should not launch without live authorization")


@pytest.mark.asyncio
async def test_browse_tool_rejects_unauthorized_live_research() -> None:
    """Accidental social-audit calls should fail fast before opening Chrome."""
    browse_and_research = create_browse_tool(_ExplodingBrowserManager())

    result = await browse_and_research(
        "Audit CHAMEOW's social media presence on TikTok, Instagram, and Facebook."
    )

    assert "Live browser verification was not authorized" in result
    assert "search_web or scrape_web_content" in result
    assert _LIVE_BROWSER_MARKER in result
