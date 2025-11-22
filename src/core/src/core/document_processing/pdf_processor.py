"""Unified PDF processing pipeline."""

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

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

    async def process_pdf(self, file_path: str) -> PDFParseResult:
        """
        Process PDF: parsing → table detection → merging → summarization → reports.

        Enhanced pipeline with table fragmentation resolution:
        1. Parse PDF to individual page files
        2. Detect all tables in page files
        3. Collect consecutive table chains
        4. Use LLM to decide which chains to merge
        5. Apply merge decisions and cleanup empty pages
        6. Summarize final tables (merged or original)
        7. Generate processing reports for traceability

        Args:
            file_path (str): Path to PDF file

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

            if tables:
                logger.info("Step 3: Collecting consecutive table chains")
                chains_by_page = self.table_chain_collector.collect_all_chains(
                    parse_result.page_files, tables
                )

                # Step 4: Assemble table chains using LLM
                if chains_by_page:
                    all_chains = [
                        chain for chains in chains_by_page.values() for chain in chains
                    ]
                    logger.info(
                        f"Step 4: Assembling {len(all_chains)} table chain(s) with LLM"
                    )
                    merge_decisions = await self.table_assembler.analyze_chains_batch(
                        all_chains
                    )

                    # Step 5: Apply assembly decisions and cleanup
                    if merge_decisions:
                        logger.info("Step 5: Applying assembly decisions to page files")
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

                # Step 5.5: Restore text integrity (cross-page fragmentation)
                logger.info("Step 5.5: Restoring cross-page text integrity")
                modified_text_pages = self.text_integrity_processor.process_pages(
                    parse_result.page_files
                )
                if modified_text_pages:
                    logger.info(
                        f"Restored text integrity on {len(modified_text_pages)} pages"
                    )

                # Step 6: Re-detect tables after assembly (some may have been merged)
                logger.info("Step 6: Re-detecting tables after assembly")
                tables = self.table_extractor.detect_tables_in_files(
                    parse_result.page_files
                )

            # Step 7: Summarize final tables
            table_summaries = []
            if tables:
                logger.info(f"Step 7: Summarizing {len(tables)} final table(s)")
                table_summaries = await self.table_summarizer.summarize_tables_batch(
                    tables
                )

                # Step 8: Update page files with summaries
                if table_summaries:
                    logger.info("Step 8: Updating page files with table summaries")
                    await self._update_files_with_summaries(tables, table_summaries)

            # NEW Step 9: Generate processing reports
            logger.info("Step 9: Generating processing reports")
            report_paths = self.report_generator.create_report_structure(
                parse_result.output_directory
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
