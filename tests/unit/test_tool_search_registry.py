"""Unit tests for ToolSearch Registry (Task 47).

Tests ToolMetadata, ToolRegistry search and categorization.
"""

from __future__ import annotations

import pytest

from shared.agent_middlewares.tool_search.registry import (
    ToolMetadata,
    ToolRegistry,
)


@pytest.fixture
def sample_registry() -> ToolRegistry:
    """Create a registry with sample tools."""
    registry = ToolRegistry()
    registry.register_many(
        [
            ToolMetadata(
                name="generate_image",
                description="Generate visual brand assets",
                category="image_generation",
                keywords=("image", "visual", "mood board"),
                phases=("3", "5"),
            ),
            ToolMetadata(
                name="generate_brand_key",
                description="Generate Brand Key one-pager visual",
                category="image_generation",
                keywords=("brand key", "one-pager", "infographic"),
                phases=("5",),
            ),
            ToolMetadata(
                name="generate_document",
                description="Generate brand strategy documents PDF DOCX",
                category="document_export",
                keywords=("document", "PDF", "DOCX"),
                phases=("5",),
            ),
            ToolMetadata(
                name="search_places",
                description="Search local businesses Google Places",
                category="local_market",
                keywords=("google places", "local", "competitors"),
                phases=("1",),
            ),
            ToolMetadata(
                name="analyze_reviews",
                description="Aggregate customer reviews sentiment",
                category="customer_analysis",
                keywords=("reviews", "sentiment", "customer"),
                phases=("0.5", "1"),
            ),
        ]
    )
    return registry


class TestToolMetadata:
    def test_immutable(self):
        meta = ToolMetadata(
            name="test",
            description="Test tool",
            category="test_cat",
        )
        with pytest.raises(AttributeError):
            meta.name = "changed"  # type: ignore

    def test_list_to_tuple_coercion(self):
        meta = ToolMetadata(
            name="test",
            description="Test",
            category="test",
            keywords=["a", "b"],  # type: ignore
            phases=["1", "2"],  # type: ignore
        )
        assert isinstance(meta.keywords, tuple)
        assert isinstance(meta.phases, tuple)


class TestToolRegistry:
    def test_register_and_has_tool(self, sample_registry):
        assert sample_registry.has_tool("generate_image")
        assert sample_registry.has_tool("search_places")
        assert not sample_registry.has_tool("nonexistent")

    def test_duplicate_raises(self, sample_registry):
        with pytest.raises(ValueError, match="already registered"):
            sample_registry.register(
                ToolMetadata(
                    name="generate_image",
                    description="Dup",
                    category="dup",
                )
            )

    def test_search_by_name(self, sample_registry):
        results = sample_registry.search("generate_image")
        assert len(results) >= 1
        assert results[0].name == "generate_image"

    def test_search_by_keyword(self, sample_registry):
        results = sample_registry.search("mood board")
        names = [r.name for r in results]
        assert "generate_image" in names

    def test_search_by_category(self, sample_registry):
        results = sample_registry.search("image")
        names = [r.name for r in results]
        assert "generate_image" in names
        assert "generate_brand_key" in names

    def test_search_by_description_word(self, sample_registry):
        results = sample_registry.search("sentiment")
        names = [r.name for r in results]
        assert "analyze_reviews" in names

    def test_search_empty_query(self, sample_registry):
        results = sample_registry.search("")
        assert results == []

    def test_search_no_match(self, sample_registry):
        results = sample_registry.search("xyz_nonexistent_term")
        assert results == []

    def test_search_top_k_limit(self, sample_registry):
        results = sample_registry.search("generate", top_k=2)
        assert len(results) <= 2

    def test_get_tools_in_category(self, sample_registry):
        tools = sample_registry.get_tools_in_category("image_generation")
        names = [t.name for t in tools]
        assert "generate_image" in names
        assert "generate_brand_key" in names
        assert "search_places" not in names

    def test_get_category_for_tool(self, sample_registry):
        cat = sample_registry.get_category_for_tool("search_places")
        assert cat == "local_market"

    def test_get_category_for_unknown(self, sample_registry):
        cat = sample_registry.get_category_for_tool("unknown")
        assert cat is None

    def test_get_category_names(self, sample_registry):
        names = sample_registry.get_category_names()
        assert "image_generation" in names
        assert "document_export" in names
        assert "local_market" in names
        assert "customer_analysis" in names
        assert names == sorted(names)

    def test_get_summary(self, sample_registry):
        summary = sample_registry.get_summary()
        assert "Image Generation" in summary
        assert "generate_image" in summary
        assert "Document Export" in summary

    def test_get_all_tool_names_in_category(self, sample_registry):
        names = sample_registry.get_all_tool_names_in_category("image_generation")
        assert names == {"generate_image", "generate_brand_key"}
