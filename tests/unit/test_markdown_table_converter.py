"""Unit tests for markdown table to HTML converter."""

import pytest

from core.document_processing.markdown_table_converter import MarkdownTableConverter


class TestMarkdownTableConverter:
    """Test suite for markdown table detection and conversion."""

    def setup_method(self):
        """Initialize converter for each test."""
        self.converter = MarkdownTableConverter()

    def test_is_markdown_table_valid(self):
        """Test detection of valid markdown table."""
        valid_table = """
| Column1 | Column2 | Column3 |
|---------|---------|---------|
| Value1  | Value2  | Value3  |
| Value4  | Value5  | Value6  |
"""
        assert self.converter.is_markdown_table(valid_table)

    def test_is_markdown_table_valid_no_separator(self):
        """Test that tables without separator row are valid (relaxed format)."""
        relaxed_table = """
| Column1 | Column2 |
| Value1  | Value2  |
"""
        # Relaxed format is now supported (separator is optional)
        assert self.converter.is_markdown_table(relaxed_table)

    def test_is_markdown_table_invalid_too_short(self):
        """Test rejection of content with insufficient rows."""
        invalid_table = """
| Column1 | Column2 |
"""
        assert not self.converter.is_markdown_table(invalid_table)

    def test_convert_to_html_basic(self):
        """Test basic markdown to HTML conversion."""
        markdown_table = """
| Name | Age | City |
|------|-----|------|
| John | 30  | NYC  |
| Jane | 25  | LA   |
"""
        html = self.converter.convert_to_html(markdown_table)

        # Verify HTML structure
        assert "<table>" in html
        assert "</table>" in html
        assert "<thead>" in html
        assert "</thead>" in html
        assert "<tbody>" in html
        assert "</tbody>" in html

        # Verify header content
        assert "<th>Name</th>" in html
        assert "<th>Age</th>" in html
        assert "<th>City</th>" in html

        # Verify body content
        assert "<td>John</td>" in html
        assert "<td>30</td>" in html
        assert "<td>NYC</td>" in html
        assert "<td>Jane</td>" in html
        assert "<td>25</td>" in html
        assert "<td>LA</td>" in html

    def test_convert_to_html_user_example(self):
        """Test conversion of user's cross-page example."""
        # In markdown, the row before separator is always treated as header
        # So we need to add a proper header row if data rows should be in <tbody>
        markdown_with_separator = """
| Category | Val1 | Val2 | Val3 | Val4 | Val5 | Val6 |
|----------|------|------|------|------|------|------|
| Cardholders | 37 | 63 | 15 | 32 | 52 | 1 |
| Non-cardholder customers | 42 | 58 | 12 | 34 | 53 | 1 |
"""
        html = self.converter.convert_to_html(markdown_with_separator)

        assert "<table>" in html
        # Header row
        assert "<th>Category</th>" in html
        assert "<th>Val1</th>" in html
        # Body rows
        assert "<td>Cardholders</td>" in html
        assert "<td>37</td>" in html
        assert "<td>Non-cardholder customers</td>" in html
        assert "<td>42</td>" in html

    def test_detect_markdown_table_positions_single_table(self):
        """Test position detection for single markdown table."""
        content = """
Some text before table.

| Header1 | Header2 |
|---------|---------|
| Data1   | Data2   |

Some text after table.
"""
        positions = self.converter.detect_markdown_table_positions(content)
        assert len(positions) == 1

        start_pos, end_pos = positions[0]
        extracted = content[start_pos:end_pos]
        assert "Header1" in extracted
        assert "Data1" in extracted

    def test_detect_markdown_table_positions_multiple_tables(self):
        """Test detection of multiple tables in same content."""
        content = """
First table:

| A | B |
|---|---|
| 1 | 2 |

Second table:

| X | Y | Z |
|---|---|---|
| 3 | 4 | 5 |
"""
        positions = self.converter.detect_markdown_table_positions(content)
        assert len(positions) == 2

    def test_detect_markdown_table_positions_no_tables(self):
        """Test that no positions are returned when no tables exist."""
        content = """
This is just regular text.
No tables here.
| This looks like a table but has no separator
"""
        positions = self.converter.detect_markdown_table_positions(content)
        assert len(positions) == 0

    def test_is_markdown_table_relaxed_no_trailing_pipes(self):
        """Test relaxed format without trailing pipes (like LlamaParse output)."""
        relaxed_table = """
Cardholders | 37 | 63 | 15 | 32 | 52 | 1
Non-cardholder customers | 42 | 58 | 12 | 34 | 53 | 1
"""
        assert self.converter.is_markdown_table(relaxed_table)
        
        # Test conversion
        html = self.converter.convert_to_html(relaxed_table)
        assert "<table>" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "<th>Cardholders</th>" in html
        assert "<td>Non-cardholder customers</td>" in html

    def test_convert_empty_content(self):
        """Test handling of empty or invalid content."""
        assert self.converter.convert_to_html("") == ""
        assert self.converter.convert_to_html("   ") == ""
        assert not self.converter.is_markdown_table("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
