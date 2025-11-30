"""
Unit tests for SectionFinder.

Tests the logic for finding the most specific section
for a given chunk based on its page range.
"""

import pytest

from core.knowledge_graph.chunker.section_finder import SectionFinder
from core.knowledge_graph.models.global_map import SectionNode


def test_find_section_simple_hierarchy():
    """Test finding section in simple 2-level hierarchy."""
    # Create test hierarchy: Part 1 > Chapter 1
    chapter1 = SectionNode(
        title="Chapter 1",
        level=2,
        start_page_id="page_10.md",
        end_page_id="page_20.md",
        start_line_index=11,
        summary_context="Chapter 1 summary",
        children=[],
    )

    part1 = SectionNode(
        title="Part 1",
        level=1,
        start_page_id="page_10.md",
        end_page_id="page_50.md",
        start_line_index=11,
        summary_context="Part 1 summary",
        children=[chapter1],
    )

    finder = SectionFinder([part1])

    # Chunk in pages 15-16 should belong to Chapter 1 (most specific)
    result = finder.find_section_for_pages(["page_15.md", "page_16.md"])

    assert result is not None
    hierarchy_path, summary = result
    assert hierarchy_path == "Part 1 > Chapter 1"
    assert summary == "Chapter 1 summary"


def test_find_section_nested_hierarchy():
    """Test finding section in 3-level hierarchy."""
    # Create test hierarchy: Part 1 > Chapter 1 > Section 1.1
    section_1_1 = SectionNode(
        title="Section 1.1",
        level=3,
        start_page_id="page_15.md",
        end_page_id="page_20.md",
        start_line_index=11,
        summary_context="Section 1.1 summary",
        children=[],
    )

    chapter1 = SectionNode(
        title="Chapter 1",
        level=2,
        start_page_id="page_10.md",
        end_page_id="page_30.md",
        start_line_index=11,
        summary_context="Chapter 1 summary",
        children=[section_1_1],
    )

    part1 = SectionNode(
        title="Part 1",
        level=1,
        start_page_id="page_10.md",
        end_page_id="page_50.md",
        start_line_index=11,
        summary_context="Part 1 summary",
        children=[chapter1],
    )

    finder = SectionFinder([part1])

    # Test case 1: Chunk in pages 12-13 (before section 1.1 starts)
    # Should belong to Chapter 1, not Section 1.1
    result = finder.find_section_for_pages(["page_12.md", "page_13.md"])
    assert result is not None
    hierarchy_path, summary = result
    assert hierarchy_path == "Part 1 > Chapter 1"
    assert summary == "Chapter 1 summary"

    # Test case 2: Chunk in pages 17-18 (within section 1.1)
    # Should belong to Section 1.1 (most specific)
    result = finder.find_section_for_pages(["page_17.md", "page_18.md"])
    assert result is not None
    hierarchy_path, summary = result
    assert hierarchy_path == "Part 1 > Chapter 1 > Section 1.1"
    assert summary == "Section 1.1 summary"

    # Test case 3: Chunk in pages 25-26 (after section 1.1 ends)
    # Should belong to Chapter 1, not Section 1.1
    result = finder.find_section_for_pages(["page_25.md", "page_26.md"])
    assert result is not None
    hierarchy_path, summary = result
    assert hierarchy_path == "Part 1 > Chapter 1"
    assert summary == "Chapter 1 summary"


def test_find_section_multiple_children():
    """Test finding section with multiple children."""
    # Create hierarchy with multiple chapters
    chapter1 = SectionNode(
        title="Chapter 1",
        level=2,
        start_page_id="page_10.md",
        end_page_id="page_20.md",
        start_line_index=11,
        summary_context="Chapter 1 summary",
        children=[],
    )

    chapter2 = SectionNode(
        title="Chapter 2",
        level=2,
        start_page_id="page_21.md",
        end_page_id="page_30.md",
        start_line_index=11,
        summary_context="Chapter 2 summary",
        children=[],
    )

    part1 = SectionNode(
        title="Part 1",
        level=1,
        start_page_id="page_10.md",
        end_page_id="page_50.md",
        start_line_index=11,
        summary_context="Part 1 summary",
        children=[chapter1, chapter2],
    )

    finder = SectionFinder([part1])

    # Chunk in Chapter 1 range
    result = finder.find_section_for_pages(["page_15.md"])
    assert result is not None
    hierarchy_path, _ = result
    assert hierarchy_path == "Part 1 > Chapter 1"

    # Chunk in Chapter 2 range
    result = finder.find_section_for_pages(["page_25.md"])
    assert result is not None
    hierarchy_path, _ = result
    assert hierarchy_path == "Part 1 > Chapter 2"

    # Chunk spanning both chapters should belong to Part 1
    result = finder.find_section_for_pages(["page_19.md", "page_22.md"])
    assert result is not None
    hierarchy_path, summary = result
    assert hierarchy_path == "Part 1"
    assert summary == "Part 1 summary"


def test_find_section_no_match():
    """Test when chunk pages don't match any section."""
    chapter1 = SectionNode(
        title="Chapter 1",
        level=2,
        start_page_id="page_10.md",
        end_page_id="page_20.md",
        start_line_index=11,
        summary_context="Chapter 1 summary",
        children=[],
    )

    finder = SectionFinder([chapter1])

    # Pages outside section range
    result = finder.find_section_for_pages(["page_50.md"])
    assert result is None


def test_find_section_empty_pages():
    """Test with empty page list."""
    chapter1 = SectionNode(
        title="Chapter 1",
        level=2,
        start_page_id="page_10.md",
        end_page_id="page_20.md",
        start_line_index=11,
        summary_context="Chapter 1 summary",
        children=[],
    )

    finder = SectionFinder([chapter1])

    result = finder.find_section_for_pages([])
    assert result is None
