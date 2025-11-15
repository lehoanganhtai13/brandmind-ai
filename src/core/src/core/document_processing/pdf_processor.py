"""Unified PDF processing pipeline."""

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from core.document_processing.llama_parser import LlamaPDFProcessor
from core.document_processing.models import PDFParseResult, TableInfo, TableSummary
from core.document_processing.table_extractor import HTMLTableExtractor
from core.document_processing.table_summarizer import TableSummarizer


class PDFProcessor:
    """
    A simplified PDF processing pipeline that focuses on parsing,
    table summarization, and file-based storage.
    """

    def __init__(self, llama_config: Dict[str, Any]):
        """
        Initializes all processing components.

        Args:
            llama_config (Dict[str, Any]): Configuration for the LlamaPDFProcessor.
        """
        self.llama_processor = LlamaPDFProcessor(**llama_config)
        self.table_extractor = HTMLTableExtractor()
        self.table_summarizer = TableSummarizer()

    async def process_pdf(self, file_path: str) -> PDFParseResult:
        """
        Processes a single PDF through a multi-step pipeline:
        1. Parse PDF to individual page files.
        2. Detect tables within those page files.
        3. Summarize the detected tables using an LLM.
        4. Update the page files by replacing HTML tables with their summaries.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            PDFParseResult: The result object from the initial parsing step,
                            containing metadata about the processed document.

        Raises:
            Exception: Propagates exceptions from underlying processing steps.
        """
        try:
            logger.info(f"Step 1: Parsing PDF to page files: {file_path}")
            parse_result = await self.llama_processor.parse_pdf(file_path)

            logger.info(
                f"Step 2: Detecting tables in {len(parse_result.page_files)} page files"
            )
            tables = self.table_extractor.detect_tables_in_files(
                parse_result.page_files
            )

            if tables:
                logger.info(f"Step 3: Summarizing {len(tables)} detected tables")
                table_summaries = await self.table_summarizer.summarize_tables_batch(
                    tables
                )

                if table_summaries:
                    logger.info("Step 4: Updating page files with table summaries")
                    await self._update_files_with_summaries(tables, table_summaries)

            logger.info(
                f"PDF processing completed: {len(parse_result.page_files)} "
                "page files created"
            )
            return parse_result

        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            raise

    async def _update_files_with_summaries(
        self, tables: List[TableInfo], summaries: List[TableSummary]
    ):
        """
        Updates page files by replacing HTML tables with their generated summaries.

        Args:
            tables (List[TableInfo]): The list of detected tables with their locations.
            summaries (List[TableSummary]): The list of generated summaries.
        """
        summary_map = {summary.original_table_html: summary for summary in summaries}

        for table in tables:
            summary = summary_map.get(table.html_content)
            if summary and table.page_file and Path(table.page_file).exists():
                try:
                    with open(table.page_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    updated_content = content.replace(
                        table.html_content, f"\n\n{summary.summary_markdown}\n\n"
                    )

                    with open(table.page_file, "w", encoding="utf-8") as f:
                        f.write(updated_content)

                    logger.debug(f"Updated table in {table.page_file}")
                except Exception as e:
                    logger.error(f"Failed to update file {table.page_file}: {e}")

    async def process_pdf_batch(self, file_paths: List[str]) -> List[PDFParseResult]:
        """
        Processes multiple PDF files sequentially with a progress bar.

        Args:
            file_paths (List[str]): A list of paths to the PDF files.

        Returns:
            List[PDFParseResult]: A list of results for each successfully processed PDF.
        """
        from tqdm import tqdm

        logger.info(f"Starting batch PDF processing: {len(file_paths)} files")
        results = []

        with tqdm(total=len(file_paths), desc="Processing PDFs") as pbar:
            for file_path in file_paths:
                try:
                    result = await self.process_pdf(file_path)
                    results.append(result)
                    pbar.set_description(f"Processed: {Path(file_path).name}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    pbar.update(1)
                    continue

        logger.info(f"Completed batch processing: {len(results)} successful")
        return results
