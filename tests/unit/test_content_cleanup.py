"""Unit tests for ContentCleanupProcessor."""

import tempfile
from pathlib import Path

import pytest

from core.document_processing.content_cleanup_processor import (
    ContentCleanupProcessor,
)


@pytest.fixture
def processor():
    """Create a ContentCleanupProcessor instance for testing."""
    return ContentCleanupProcessor()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_normalize_whitespace_excessive_blank_lines(processor):
    """Test that 3+ consecutive blank lines are reduced to 2."""
    content = "Line 1\n\n\n\nLine 2"
    result = processor.normalize_whitespace(content)
    assert result == "Line 1\n\nLine 2"


def test_normalize_whitespace_five_blank_lines(processor):
    """Test that 5 consecutive blank lines are reduced to 2."""
    content = "Line 1\n\n\n\n\n\nLine 2"
    result = processor.normalize_whitespace(content)
    assert result == "Line 1\n\nLine 2"


def test_normalize_whitespace_preserves_single_blank_line(processor):
    """Test that single blank lines are preserved."""
    content = "Line 1\n\nLine 2"
    result = processor.normalize_whitespace(content)
    assert result == "Line 1\n\nLine 2"


def test_normalize_whitespace_preserves_double_blank_line(processor):
    """Test that double blank lines are preserved."""
    content = "Line 1\n\n\nLine 2"
    result = processor.normalize_whitespace(content)
    assert result == "Line 1\n\nLine 2"


def test_fix_metadata_separator_spacing_missing_blank_line(processor):
    """Test adding blank line after metadata separator."""
    content = """# Page 1

**Title**: Test
**Author**: Test Author

---
Content starts here"""
    
    result = processor.fix_metadata_separator_spacing(content)
    lines = result.split("\n")
    
    # Find --- separator
    sep_index = lines.index("---")
    # Check that next line is blank
    assert lines[sep_index + 1] == ""
    # Check that content is after blank line
    assert lines[sep_index + 2] == "Content starts here"


def test_fix_metadata_separator_spacing_attached_content(processor):
    """Test fixing content attached to separator (--- Philip Kotler)."""
    content = """# Page 3

**Title**: Test
**Author**: Test Author

--- Philip Kotler"""
    
    result = processor.fix_metadata_separator_spacing(content)
    lines = result.split("\n")
    
    # Find --- separator
    sep_index = lines.index("---")
    # Check that next line is blank
    assert lines[sep_index + 1] == ""
    # Check that content is after blank line
    assert lines[sep_index + 2] == "Philip Kotler"


def test_fix_metadata_separator_preserves_existing_blank_line(processor):
    """Test that existing blank line after separator is preserved."""
    content = """# Page 1

---

Content here"""
    
    result = processor.fix_metadata_separator_spacing(content)
    lines = result.split("\n")
    
    # Find --- separator
    sep_index = lines.index("---")
    # Should still have blank line
    assert lines[sep_index + 1] == ""
    assert lines[sep_index + 2] == "Content here"


def test_process_file_creates_cleaned_content(processor, temp_dir):
    """Test that process_file correctly cleans a file."""
    # Create test file
    test_file = Path(temp_dir) / "test_page.md"
    content = """# Page 1

**Title**: Test

--- Philip Kotler


Content here"""
    
    test_file.write_text(content, encoding="utf-8")
    
    # Process file
    result = processor.process_file(str(test_file))
    assert result is True
    
    # Read cleaned content
    cleaned = test_file.read_text(encoding="utf-8")
    lines = cleaned.split("\n")
    
    # Check separator is fixed
    sep_index = lines.index("---")
    assert lines[sep_index + 1] == ""
    assert lines[sep_index + 2] == "Philip Kotler"
    
    # Check excessive blank lines are normalized
    assert "\n\n\n" not in cleaned


def test_process_file_nonexistent(processor):
    """Test that process_file handles nonexistent files gracefully."""
    result = processor.process_file("/nonexistent/file.md")
    assert result is False


def test_process_pages_multiple_files(processor, temp_dir):
    """Test processing multiple page files."""
    # Create test files
    files = []
    for i in range(3):
        test_file = Path(temp_dir) / f"page_{i}.md"
        content = f"""# Page {i}

---

Content {i}"""
        test_file.write_text(content, encoding="utf-8")
        files.append(str(test_file))
    
    # Process files
    processed = processor.process_pages(files)
    
    # All files should be processed
    assert len(processed) == 3


def test_edge_case_no_metadata_separator(processor):
    """Test file without metadata separator."""
    content = """# Page 1

Just content here"""
    
    result = processor.fix_metadata_separator_spacing(content)
    # Should return unchanged
    assert result == content


def test_edge_case_empty_file(processor):
    """Test empty file."""
    content = ""
    result = processor.normalize_whitespace(content)
    assert result == ""


def test_edge_case_only_whitespace(processor):
    """Test file with only whitespace."""
    content = "\n\n\n\n\n"
    result = processor.normalize_whitespace(content)
    assert result == "\n\n"


def test_complex_scenario_all_operations(processor, temp_dir):
    """Test all cleanup operations together."""
    test_file = Path(temp_dir) / "complex_page.md"
    content = """# Page 55

**Title**: Test Document

--- Author Name



## Section 1

Content here


More content"""
    
    test_file.write_text(content, encoding="utf-8")
    processor.process_file(str(test_file))
    
    cleaned = test_file.read_text(encoding="utf-8")
    lines = cleaned.split("\n")
    
    # Check metadata separator is fixed
    first_sep = lines.index("---")
    assert lines[first_sep + 1] == ""
    assert lines[first_sep + 2] == "Author Name"
    
    # Check excessive blank lines normalized
    assert "\n\n\n" not in cleaned


def test_content_with_horizontal_rules_preserved(processor):
    """Test that horizontal rules in content are preserved (not escaped)."""
    content = """# Page 10

---

Chapter 1

---

Chapter 2"""
    
    # Apply cleanup
    result = processor.normalize_whitespace(content)
    result = processor.fix_metadata_separator_spacing(result)
    
    # All --- should be preserved (not escaped)
    assert "\\---" not in result
    assert result.count("---") == 2
