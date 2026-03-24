"""Integration tests for ToolSearch Middleware (Task 47).

Tests create_tool_search_middleware factory and ToolSearchMiddleware
initialization with the brand strategy tool catalog.
"""

from __future__ import annotations

import pytest

from shared.agent_middlewares.tool_search import (
    ToolMetadata,
    ToolRegistry,
    ToolSearchMiddleware,
    create_tool_search_middleware,
)
from shared.agent_middlewares.tool_search.middleware import (
    BRAND_STRATEGY_TOOL_CATALOG,
    tool_search,
)


class TestBrandStrategyToolCatalog:
    """Test the built-in tool catalog."""

    def test_catalog_has_10_tools(self):
        assert len(BRAND_STRATEGY_TOOL_CATALOG) == 10

    def test_catalog_tool_names(self):
        names = {m.name for m in BRAND_STRATEGY_TOOL_CATALOG}
        expected = {
            "browse_and_research",
            "analyze_social_profile",
            "get_search_autocomplete",
            "generate_image",
            "edit_image",
            "generate_brand_key",
            "generate_document",
            "generate_presentation",
            "generate_spreadsheet",
            "export_to_markdown",
        }
        assert names == expected

    def test_catalog_categories(self):
        categories = {m.category for m in BRAND_STRATEGY_TOOL_CATALOG}
        expected = {
            "social_media",
            "customer_analysis",
            "image_generation",
            "document_export",
        }
        assert categories == expected



class TestCreateToolSearchMiddleware:
    """Test factory function."""

    def test_creates_middleware(self):
        middleware = create_tool_search_middleware()
        assert isinstance(middleware, ToolSearchMiddleware)

    def test_catalog_names_match_catalog(self):
        middleware = create_tool_search_middleware()
        expected = {m.name for m in BRAND_STRATEGY_TOOL_CATALOG}
        assert middleware._catalog_names == expected

    def test_non_catalog_tools_not_in_blacklist(self):
        middleware = create_tool_search_middleware()
        # Core tools should NOT be in the catalog blacklist
        assert "search_knowledge_graph" not in middleware._catalog_names
        assert "search_web" not in middleware._catalog_names

    def test_middleware_has_3_inventory_tools(self):
        """Middleware should expose tool_search, load_tools, unload_tools."""
        assert len(ToolSearchMiddleware.tools) == 3
        tool_names = {t.name for t in ToolSearchMiddleware.tools}
        assert tool_names == {"tool_search", "load_tools", "unload_tools"}


class TestToolSearchFunction:
    """Test the tool_search function with registry."""

    def test_search_image_tools(self):
        create_tool_search_middleware()  # Initialize _registry
        result = tool_search.invoke({"query": "generate image"})
        assert "generate_image" in result

    def test_search_document_tools(self):
        create_tool_search_middleware()
        result = tool_search.invoke({"query": "create PDF"})
        assert "generate_document" in result

    def test_search_no_match(self):
        create_tool_search_middleware()
        result = tool_search.invoke({"query": "xyz_nonexistent"})
        assert "No matching tools" in result

    def test_search_social_tools(self):
        create_tool_search_middleware()
        result = tool_search.invoke({"query": "browse social media profile"})
        assert "browse_and_research" in result

    def test_search_social_media(self):
        create_tool_search_middleware()
        result = tool_search.invoke({"query": "instagram social media"})
        assert "browse_and_research" in result or "analyze_social_profile" in result
