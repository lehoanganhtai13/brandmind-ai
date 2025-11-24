"""Command-line interface for running the document processing pipeline."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from core.document_processing.pdf_processor import PDFProcessor


async def async_main():
    """
    Main asynchronous function to run the document processing CLI.

    This script serves as the entry point for parsing PDF documents or cleaning
    up existing parsed documents. It supports three modes:
    1. Batch mode: Process all documents from metadata
    2. Single-file mode: Process a specific PDF file (--file)
    3. Cleanup-only mode: Apply content cleanup to existing parsed folder
       (--cleanup-folder)
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run the document processing pipeline or cleanup existing "
            "parsed documents."
        )
    )

    # Create mutually exclusive group for processing modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--file",
        type=str,
        help="Process a specific PDF file from document_metadata.json",
        required=False,
    )
    mode_group.add_argument(
        "--cleanup-folder",
        type=str,
        metavar="FOLDER_NAME",
        help=(
            "Apply content cleanup to an existing parsed document folder. "
            "Provide folder name only (e.g., "
            "'Kotler_and_Armstrong_Principles_of_Marketing_20251123_193123'). "
            "The folder must exist in data/parsed_documents/."
        ),
        required=False,
    )
    parser.add_argument(
        "--skip-table-merge",
        action="store_true",
        help="Skip table fragmentation merging step",
    )
    parser.add_argument(
        "--skip-text-merge",
        action="store_true",
        help="Skip cross-page text integrity restoration step",
    )
    parser.add_argument(
        "--skip-table-summarization",
        action="store_true",
        help="Skip table summarization step",
    )
    parser.add_argument(
        "--skip-content-cleanup",
        action="store_true",
        help="Skip content formatting cleanup step",
    )
    args = parser.parse_args()

    # Handle cleanup-only mode
    if args.cleanup_folder:
        await run_cleanup_mode(args.cleanup_folder)
        return

    # Load document metadata
    metadata_path = Path("data/raw_documents/document_metadata.json")
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            all_docs_metadata = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {metadata_path}")
        return

    # Determine which documents to process
    target_docs: List[Dict[str, Any]] = []
    if args.file:
        # Single file mode: find the specified document in the metadata
        found = False
        for doc in all_docs_metadata:
            if doc.get("document_name") == args.file:
                target_docs.append(doc)
                found = True
                break
        if not found:
            logger.error(f"File '{args.file}' not found in metadata file. Aborting.")
            return
    else:
        # Batch mode: process all documents from metadata
        target_docs = all_docs_metadata

    file_paths_to_process = [
        str(Path("data/raw_documents") / doc["document_name"]) for doc in target_docs
    ]

    if not file_paths_to_process:
        logger.warning("No documents to process.")
        return

    # Initialize and run the processor
    # API keys are handled by the SETTINGS object within the processor's constructor
    processor = PDFProcessor(llama_config={})
    logger.info(f"Starting processing for {len(file_paths_to_process)} document(s)...")
    await processor.process_pdf_batch(
        file_paths_to_process,
        skip_table_merge=args.skip_table_merge,
        skip_text_merge=args.skip_text_merge,
        skip_table_summarization=args.skip_table_summarization,
        skip_content_cleanup=args.skip_content_cleanup,
    )
    logger.info("All processing tasks completed.")


async def run_cleanup_mode(folder_name: str):
    """
    Execute cleanup-only mode on an existing parsed document folder.

    This mode applies ContentCleanupProcessor to all page_*.md files in the
    specified folder without re-parsing the PDF or running other processing steps.
    It normalizes whitespace (reduces 3+ blank lines to 2) and fixes metadata
    separator spacing.

    Args:
        folder_name (str): Name of the folder in data/parsed_documents/ to clean

    Returns:
        None
    """
    from pathlib import Path

    from tqdm import tqdm

    from core.document_processing.content_cleanup_processor import (
        ContentCleanupProcessor,
    )

    # Construct full folder path
    base_dir = Path("data/parsed_documents")
    folder_path = base_dir / folder_name

    # Validate folder exists
    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        logger.info(f"Available folders in {base_dir}:")
        for f in sorted(base_dir.iterdir()):
            if f.is_dir():
                logger.info(f"  - {f.name}")
        return

    # Find all page files
    page_files = sorted(folder_path.glob("page_*.md"))

    if not page_files:
        logger.error(f"No page_*.md files found in {folder_path}")
        return

    logger.info(f"Found {len(page_files)} page files in {folder_name}")
    logger.info("Starting content cleanup...")

    # Initialize processor
    processor = ContentCleanupProcessor()

    # Process files with progress bar
    page_file_paths = [str(f) for f in page_files]
    cleaned_files = []

    with tqdm(total=len(page_file_paths), desc="Cleaning pages") as pbar:
        for file_path in page_file_paths:
            try:
                if processor.process_file(file_path):
                    cleaned_files.append(file_path)
                pbar.update(1)
            except Exception as e:
                logger.error(f"Failed to process {Path(file_path).name}: {e}")
                pbar.update(1)
                continue

    # Report summary
    logger.info(
        f"Cleanup completed: {len(cleaned_files)}/{len(page_file_paths)} "
        f"files processed successfully"
    )


def main():
    """Synchronous entry point for the CLI."""
    asyncio.run(async_main())


if __name__ == "__main__":
    # Entry point when running the script directly: python parse_documents.py
    main()
