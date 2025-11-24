"""Unified PDF processing pipeline."""

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from core.document_processing.content_cleanup_processor import (
    ContentCleanupProcessor,
)
from core.document_processing.llama_parser import LlamaPDFProcessor
from core.document_processing.models import PDFParseResult, TableInfo, TableSummary
from core.document_processing.page_file_updater import PageFileUpdater
from core.document_processing.report_generator import ReportGenerator
from core.document_processing.table_assembler import TableAssembler
from core.document_processing.table_chain_collector import TableChainCollector
from core.document_processing.table_extractor import TableExtractor
from core.document_processing.table_summarizer import TableSummarizer
from core.document_processing.text_integrity_processor import TextIntegrityProcessor


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
        self.table_extractor = TableExtractor()
        self.table_chain_collector = TableChainCollector()
        self.table_assembler = TableAssembler()
        self.page_file_updater = PageFileUpdater()
        self.table_summarizer = TableSummarizer()
        self.report_generator = ReportGenerator()
        self.text_integrity_processor = TextIntegrityProcessor()
        self.content_cleanup_processor = ContentCleanupProcessor()

    async def process_pdf(
        self,
        file_path: str,
        skip_table_merge: bool = False,
        skip_text_merge: bool = False,
        skip_table_summarization: bool = False,
        skip_content_cleanup: bool = False,
    ) -> PDFParseResult:
        """
        Process PDF: parsing → table detection → merging → summarization → reports.

        Enhanced pipeline with table fragmentation resolution:
        1. Parse PDF to individual page files
        2. Detect all tables in page files
        3. Collect consecutive table chains (Optional)
        4. Use LLM to decide which chains to merge (Optional)
        5. Apply merge decisions and cleanup empty pages (Optional)
        6. Restore cross-page text integrity (Optional)
        7. Re-detect tables after assembly
        8. Summarize final tables (merged or original) (Optional)
        9. Update page files with summaries
        10. Generate processing reports for traceability
        11. Clean up content formatting (Optional)

        Args:
            file_path (str): Path to PDF file
            skip_table_merge (bool): If True, skip table fragmentation
                merging (Steps 3-5)
            skip_text_merge (bool): If True, skip text integrity
                restoration (Step 6)
            skip_table_summarization (bool): If True, skip table
                summarization (Step 8)
            skip_content_cleanup (bool): If True, skip content formatting
                cleanup (Step 11)

        Returns:
            PDFParseResult: Result with file-based storage and processing metadata

        Raises:
            Exception: Propagates exceptions from underlying processing steps.
        """
        try:
            # Step 1: Parse PDF to individual page files
            logger.info(f"Step 1: Parsing PDF to page files: {file_path}")
            parse_result = await self.llama_processor.parse_pdf(file_path)

            # Step 2: Detect tables in page files
            logger.info(
                f"Step 2: Detecting tables in {len(parse_result.page_files)} page files"
            )
            tables = self.table_extractor.detect_tables_in_files(
                parse_result.page_files
            )

            # Step 3: Collect consecutive table chains
            chains_by_page = {}
            merge_decisions = []

            if not skip_table_merge:
                if tables:
                    logger.info("Step 3: Collecting consecutive table chains")
                    chains_by_page = self.table_chain_collector.collect_all_chains(
                        parse_result.page_files, tables
                    )

                    # Step 4: Assemble table chains using LLM
                    if chains_by_page:
                        all_chains = [
                            chain
                            for chains in chains_by_page.values()
                            for chain in chains
                        ]
                        logger.info(
                            f"Step 4: Assembling {len(all_chains)} "
                            "table chain(s) with LLM"
                        )
                        merge_decisions = (
                            await self.table_assembler.analyze_chains_batch(all_chains)
                        )

                        # Step 5: Apply assembly decisions and cleanup
                        if merge_decisions:
                            logger.info(
                                "Step 5: Applying assembly decisions to page files"
                            )
                            modified_pages = (
                                await self.page_file_updater.apply_merge_decisions(
                                    chains_by_page, merge_decisions
                                )
                            )

                            # Cleanup empty pages
                            removed_pages = (
                                await self.page_file_updater.cleanup_empty_pages(
                                    parse_result.output_directory, modified_pages
                                )
                            )

                            if removed_pages:
                                # Update page_files list to remove deleted pages
                                parse_result.page_files = [
                                    pf
                                    for pf in parse_result.page_files
                                    if not any(
                                        f"page_{rp}.md" in pf for rp in removed_pages
                                    )
                                ]
            else:
                logger.info("Skipping table merging (Steps 3-5) as requested")

            # Step 6: Restore text integrity (cross-page fragmentation)
            if not skip_text_merge:
                logger.info("Step 6: Restoring cross-page text integrity")
                modified_text_pages = self.text_integrity_processor.process_pages(
                    parse_result.page_files
                )

                if modified_text_pages:
                    logger.info(
                        f"Restored text integrity on {len(modified_text_pages)} pages"
                    )
            else:
                logger.info("Skipping text integrity restoration (Step 6) as requested")

            # Step 7: Re-detect tables after assembly (some may have been merged)
            logger.info("Step 7: Re-detecting tables after assembly")
            final_tables = self.table_extractor.detect_tables_in_files(
                parse_result.page_files
            )
            logger.info(
                f"Detected {len(final_tables)} tables across "
                f"{len(parse_result.page_files)} page files"
            )

            # Step 8: Summarizing final table(s)
            table_summaries = []
            if not skip_table_summarization:
                if final_tables:
                    logger.info(
                        f"Step 8: Summarizing {len(final_tables)} final table(s)"
                    )
                    table_summaries = (
                        await self.table_summarizer.summarize_tables_batch(
                            tables=final_tables
                        )
                    )
            else:
                logger.info("Skipping table summarization (Step 8) as requested")

            # Step 9: Update page files with table summaries
            if table_summaries:
                logger.info("Step 9: Updating page files with table summaries")
                await self._update_files_with_summaries(final_tables, table_summaries)

            # Step 10: Generating processing reports
            logger.info("Step 10: Generating processing reports")
            report_paths = self.report_generator.create_report_structure(
                output_directory=parse_result.output_directory
            )

            if chains_by_page and merge_decisions:
                all_chains = [
                    chain for chains in chains_by_page.values() for chain in chains
                ]
                await self.report_generator.generate_assembly_reports(
                    all_chains, merge_decisions, report_paths["merge"]
                )

            if table_summaries:
                await self.report_generator.generate_summarization_reports(
                    table_summaries,
                    chains_by_page,
                    merge_decisions,
                    report_paths["summarize"],
                )

            # Step 11: Clean up content formatting
            if not skip_content_cleanup:
                logger.info("Step 11: Cleaning up content formatting")
                cleaned_files = self.content_cleanup_processor.process_pages(
                    parse_result.page_files
                )
                logger.info(f"Cleaned up {len(cleaned_files)} page files")
            else:
                logger.info("Skipping content cleanup (Step 11) as requested")

            logger.info(
                f"PDF processing completed: {len(parse_result.page_files)} page(s), "
                f"{len(table_summaries)} table(s) summarized"
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
                        table.html_content, f"{summary.summary_markdown}"
                    )

                    with open(table.page_file, "w", encoding="utf-8") as f:
                        f.write(updated_content)

                    logger.debug(f"Updated table in {table.page_file}")
                except Exception as e:
                    logger.error(f"Failed to update file {table.page_file}: {e}")

    async def process_pdf_batch(
        self,
        file_paths: List[str],
        skip_table_merge: bool = False,
        skip_text_merge: bool = False,
        skip_table_summarization: bool = False,
        skip_content_cleanup: bool = False,
    ) -> List[PDFParseResult]:
        """
        Processes multiple PDF files sequentially with a progress bar.

        Args:
            file_paths (List[str]): List of PDF file paths
            skip_table_merge (bool): If True, skip table
                fragmentation merging (Steps 3-5)
            skip_text_merge (bool): If True, skip text integrity
                restoration (Step 6)
            skip_table_summarization (bool): If True, skip table
                summarization (Step 8)
            skip_content_cleanup (bool): If True, skip content formatting
                cleanup (Step 11)

        Returns:
            List[PDFParseResult]: A list of results for each successfully processed PDF.
        """
        from tqdm import tqdm

        logger.info(f"Starting batch PDF processing: {len(file_paths)} files")
        results = []

        with tqdm(total=len(file_paths), desc="Processing PDFs") as pbar:
            for file_path in file_paths:
                try:
                    result = await self.process_pdf(
                        file_path,
                        skip_table_merge=skip_table_merge,
                        skip_text_merge=skip_text_merge,
                        skip_table_summarization=skip_table_summarization,
                        skip_content_cleanup=skip_content_cleanup,
                    )
                    results.append(result)
                    pbar.set_description(f"Processed: {Path(file_path).name}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    pbar.update(1)
                    continue

        logger.info(
            f"Completed batch processing: {len(results)} successful, "
            f"{len(file_paths) - len(results)} failed"
        )
        return results
