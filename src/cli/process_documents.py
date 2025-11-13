"""Command-line interface for running the document processing pipeline."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from core.document_processing.pdf_processor import PDFProcessor


async def main():
    """
    Main asynchronous function to run the document processing CLI.

    This script serves as the entry point for parsing PDF documents. It handles
    command-line arguments to determine which documents to process, loads the
    necessary metadata, and then invokes the PDFProcessor pipeline. It supports
    both a batch mode to process all documents listed in the metadata and a
    single-file mode.
    """
    parser = argparse.ArgumentParser(
        description="Run the document processing pipeline."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="The specific filename of a document to process. Must be listed in document_metadata.json.",
        required=False,
    )
    args = parser.parse_args()

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
            logger.error(
                f"File '{args.file}' not found in metadata file. Aborting."
            )
            return
    else:
        # Batch mode: process all documents from metadata
        target_docs = all_docs_metadata

    file_paths_to_process = [
        str(Path("data/raw_documents") / doc["document_name"])
        for doc in target_docs
    ]

    if not file_paths_to_process:
        logger.warning("No documents to process.")
        return

    # Initialize and run the processor
    # API keys are handled by the SETTINGS object within the processor's constructor
    processor = PDFProcessor(llama_config={})
    logger.info(
        f"Starting processing for {len(file_paths_to_process)} document(s)..."
    )
    await processor.process_pdf_batch(file_paths_to_process)
    logger.info("All processing tasks completed.")


if __name__ == "__main__":
    # This allows the async main function to be run from the command line
    asyncio.run(main())
