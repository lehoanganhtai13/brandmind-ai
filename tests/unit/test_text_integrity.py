"""Unit tests for TextIntegrityProcessor using pytest."""

import os
import shutil
import tempfile
from typing import Generator

import pytest
from core.document_processing.text_integrity_processor import TextIntegrityProcessor


@pytest.fixture
def processor() -> TextIntegrityProcessor:
    """Fixture to provide a TextIntegrityProcessor instance."""
    return TextIntegrityProcessor()


@pytest.fixture
def test_dir() -> Generator[str, None, None]:
    """Fixture to provide a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def create_page_file(directory: str, page_num: int, content: str) -> str:
    """Helper to create a page markdown file."""
    file_path = os.path.join(directory, f"page_{page_num}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def test_simple_sentence_split(processor: TextIntegrityProcessor, test_dir: str):
    """Test merging a simple sentence split across two pages."""
    page1_content = """# Page 1
---

The quick brown fox"""
    
    page2_content = """# Page 2
---

jumps over the dog. Next sentence."""

    p1 = create_page_file(test_dir, 1, page1_content)
    p2 = create_page_file(test_dir, 2, page2_content)

    processor.process_pages([p1, p2])

    with open(p1, "r") as f:
        new_p1 = f.read()
    with open(p2, "r") as f:
        new_p2 = f.read()

    assert "The quick brown fox jumps over the dog." in new_p1
    assert "Next sentence." in new_p2
    assert "jumps over the dog" not in new_p2


def test_paragraph_split(processor: TextIntegrityProcessor, test_dir: str):
    """Test merging when split happens inside a paragraph."""
    page1_content = """# Page 1
---

...foundation of the growth of every other"""
    
    page2_content = """# Page 2
---

arm of the Google we know today – a business with an incredibly diverse and profitable range of services. This has led..."""

    p1 = create_page_file(test_dir, 1, page1_content)
    p2 = create_page_file(test_dir, 2, page2_content)

    processor.process_pages([p1, p2])

    with open(p1, "r") as f:
        new_p1 = f.read()
    with open(p2, "r") as f:
        new_p2 = f.read()

    expected_merged = "foundation of the growth of every other arm of the Google we know today – a business with an incredibly diverse and profitable range of services."
    assert expected_merged in new_p1
    assert "This has led..." in new_p2
    assert "arm of the Google" not in new_p2


def test_no_merge_complete_sentence(processor: TextIntegrityProcessor, test_dir: str):
    """Test that complete sentences are NOT merged."""
    page1_content = """# Page 1
---

This is a complete sentence."""
    
    page2_content = """# Page 2
---

Next page starts here."""

    p1 = create_page_file(test_dir, 1, page1_content)
    p2 = create_page_file(test_dir, 2, page2_content)

    processor.process_pages([p1, p2])

    with open(p1, "r") as f:
        new_p1 = f.read()
    
    assert "This is a complete sentence." in new_p1
    assert "Next page starts here" not in new_p1


def test_no_merge_header(processor: TextIntegrityProcessor, test_dir: str):
    """Test that headers are NOT merged."""
    page1_content = """# Page 1
---

Some text without punctuation"""
    
    page2_content = """# Page 2
---

# Section Header
New section text."""

    p1 = create_page_file(test_dir, 1, page1_content)
    p2 = create_page_file(test_dir, 2, page2_content)

    processor.process_pages([p1, p2])

    with open(p1, "r") as f:
        new_p1 = f.read()
    
    assert "Section Header" not in new_p1


def test_intervening_content(processor: TextIntegrityProcessor, test_dir: str):
    """Test merging when there is intervening content (Header, Table, Note) on the next page."""
    page1_content = """# Page 1
---

The quick brown fox"""
    
    page2_content = """# Page 2
---

# Figure 1.2 Automotive perceptual map

<table>
  <thead>
    <tr>
      <th>Col1</th>
      <th>Col2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Val1</td>
      <td>Val2</td>
    </tr>
  </tbody>
</table>

> **NOTE** This is a note.

jumps over the dog. Next sentence."""

    p1 = create_page_file(test_dir, 1, page1_content)
    p2 = create_page_file(test_dir, 2, page2_content)

    processor.process_pages([p1, p2])

    with open(p1, "r") as f:
        new_p1 = f.read()
    with open(p2, "r") as f:
        new_p2 = f.read()

    # Verify merge happened
    assert "The quick brown fox jumps over the dog." in new_p1
    
    # Verify intervening content remains on Page 2
    assert "# Figure 1.2 Automotive perceptual map" in new_p2
    assert "<table>" in new_p2
    assert "<td>Val1</td>" in new_p2
    assert "> **NOTE** This is a note." in new_p2
    
    # Verify text was removed from Page 2
    assert "jumps over the dog" not in new_p2
    assert "Next sentence." in new_p2
