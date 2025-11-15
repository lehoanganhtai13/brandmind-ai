"""Integration tests for the full PDF processing pipeline."""

import os
import shutil
from pathlib import Path

import pytest

from config.system_config import SETTINGS
from core.document_processing.pdf_processor import PDFProcessor

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

TEST_PDF_PATH = (
    "data/raw_documents/Kotler_and_Armstrong_Principles_of_Marketing_test.pdf"
)


@pytest.fixture(scope="module")
def processor():
    """Fixture to create a PDFProcessor instance."""
    llama_config = {
        "api_key": SETTINGS.LLAMA_PARSE_API_KEY,
    }
    return PDFProcessor(llama_config=llama_config)


async def test_pdf_processing_pipeline(processor: PDFProcessor):
    """
    Tests the end-to-end PDF processing pipeline.
    It processes a sample PDF and verifies the output structure and content.
    """
    assert os.path.exists(TEST_PDF_PATH), f"Test PDF not found at {TEST_PDF_PATH}"

    # --- Setup: Load expected author from metadata ---
    import json

    expected_author = "Unknown"
    metadata_path = "data/raw_documents/document_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)

        test_pdf_filename = Path(TEST_PDF_PATH).name
        for item in metadata_list:
            if item.get("document_name") == test_pdf_filename:
                expected_author = item.get("author", "Unknown")
                break

    # --- Execution ---
    parse_result = await processor.process_pdf(TEST_PDF_PATH)

    # --- Verification ---
    # 1. Check if the result object is valid
    assert parse_result is not None
    assert parse_result.file_path == TEST_PDF_PATH
    assert parse_result.pages > 0
    assert len(parse_result.page_files) == parse_result.pages
    assert parse_result.metadata.get("author") == expected_author

    # 2. Check if the output directory and files were created
    output_dir = Path(parse_result.output_directory)
    assert output_dir.exists()
    assert output_dir.is_dir()

    # 3. Check if the number of page files matches the metadata
    found_files = list(output_dir.glob("page_*.md"))
    assert len(found_files) == parse_result.pages

    # 4. Check the content of the first page file
    if parse_result.pages > 0:
        first_page_path = output_dir / "page_1.md"
        assert first_page_path.exists()
        with open(first_page_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Page 1" in content
            assert f"**Document**: {Path(TEST_PDF_PATH).stem}" in content
            assert f"**Author**: {expected_author}" in content
            assert f"**Original File**: {TEST_PDF_PATH}" in content
            assert f"**Page Number**: 1/{parse_result.pages}" in content

    # 5. Check if tables were summarized (if any)
    if parse_result.tables_extracted > 0:
        print(f"Found and processed {parse_result.tables_extracted} tables.")
        # Verify that the HTML tables have been replaced by summaries.
        # We do this by checking that the '<table>' tag no longer exists in the
        # final files.
        for page_file_path in parse_result.page_files:
            with open(page_file_path, "r", encoding="utf-8") as f:
                final_content = f.read()
                assert "<table" not in final_content.lower(), (
                    f"Found an unprocessed <table> tag in the final output file: "
                    f"{page_file_path}"
                )

    # --- Cleanup ---
    # Clean up the created directory and its contents
    # Comment this out if you want to inspect the files after a test run
    shutil.rmtree(output_dir)
    assert not output_dir.exists()
