"""Report generation service for table processing pipeline traceability."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from core.document_processing.models import (
    TableChain,
    TableMergeDecision,
    TableMergeReport,
    TableSummarizationReport,
    TableSummary,
)


class ReportGenerator:
    """
    Generates structured processing reports for table merging and summarization.

    This service creates detailed JSON reports that provide complete traceability
    for debugging and analysis of the document processing pipeline. Reports are
    organized in a dedicated folder structure within each document's output directory.
    """

    def __init__(self):
        """Initialize the report generator."""
        pass

    def create_report_structure(self, output_directory: str) -> Dict[str, Path]:
        """
        Create report folder structure in the output directory.

        Structure:
            output_directory/
                reports/
                    merge/       # Table merge operation reports
                    summarize/   # Table summarization reports

        Args:
            output_directory (str): Base output directory for the document

        Returns:
            paths (Dict[str, Path]): Dictionary with 'merge' and 'summarize' paths
        """
        base_path = Path(output_directory)
        reports_path = base_path / "reports"
        merge_path = reports_path / "merge"
        summarize_path = reports_path / "summarize"

        merge_path.mkdir(parents=True, exist_ok=True)
        summarize_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created report structure in {reports_path}")

        return {
            "merge": merge_path,
            "summarize": summarize_path,
        }

    async def generate_assembly_reports(
        self,
        chains: List[TableChain],
        decisions: List[TableMergeDecision],
        report_dir: Path,
    ):
        """
        Generate individual reports for each table chain assembly operation.

        Each report file corresponds to one chain and contains:
        - Chain identification and metadata
        - List of all fragments with positions and page numbers
        - LLM assembly decision with analysis (status, reasoning, fragments merged)
        - Final merged table HTML if status=SUCCESS

        Args:
            chains (List[TableChain]): All table chains that were analyzed
            decisions (List[TableMergeDecision]): Assembly decisions for each chain
            report_dir (Path): Directory to save assembly reports
        """
        decision_map = {d.chain_id: d for d in decisions}

        for chain in chains:
            decision = decision_map.get(chain.chain_id)
            if not decision:
                continue

            # Build fragments info
            fragments_info = [
                {
                    "fragment_index": i + 1,
                    "page_number": table.page_number,
                    "start_pos": table.start_pos,
                    "end_pos": table.end_pos,
                    "html_size": len(table.html_content),
                    "page_file": table.page_file,
                }
                for i, table in enumerate(chain.tables)
            ]

            # Determine if cross-page and page range
            page_numbers = [t.page_number for t in chain.tables]
            is_cross_page = len(set(page_numbers)) > 1
            page_range = (
                f"{min(page_numbers)}-{max(page_numbers)}"
                if is_cross_page
                else str(chain.page_number)
            )

            # Create report
            report = TableMergeReport(
                chain_id=chain.chain_id,
                page_number=chain.page_number,
                fragment_count=len(chain.tables),
                fragments_info=fragments_info,
                is_cross_page=is_cross_page,
                page_range=page_range,
                merge_decision=decision,
                timestamp=datetime.now().isoformat(),
            )

            # Save to file
            report_file = report_dir / f"{chain.chain_id}_assembly_report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Generated assembly report: {report_file.name}")

        logger.info(f"Generated {len(chains)} assembly report(s) in {report_dir}")

    async def generate_summarization_reports(
        self,
        summaries: List[TableSummary],
        chains_by_page: Dict[int, List[TableChain]],
        decisions: List[TableMergeDecision],
        report_dir: Path,
    ):
        """
        Generate individual reports for each table summarization operation.

        Each report file corresponds to one table and contains:
        - Table identification and page location
        - Original HTML table content
        - Generated summary markdown
        - Processing metadata (time, merge status)

        Args:
            summaries (List[TableSummary]): All generated table summaries
            chains_by_page (Dict[int, List[TableChain]]): Chains by page for lookup
            decisions (List[TableMergeDecision]): Merge decisions for chain tracking
            report_dir (Path): Directory to save summarization reports
        """
        # Build chain lookup: table HTML -> chain_id (if successfully assembled)
        decision_map = {d.chain_id: d for d in decisions if d.status == "SUCCESS"}
        table_to_chain = {}

        for page_num, chains in chains_by_page.items():
            for chain in chains:
                decision = decision_map.get(chain.chain_id)
                if decision and decision.final_merged_html:
                    table_to_chain[decision.final_merged_html] = chain.chain_id

        # Generate report for each summary
        for i, summary in enumerate(summaries):
            # Check if this summary resulted from a merge
            source_chain_id = table_to_chain.get(summary.original_table_html)
            was_merged = source_chain_id is not None

            table_id = f"page_{summary.page_number}_table_{i + 1}"

            report = TableSummarizationReport(
                table_id=table_id,
                page_number=summary.page_number,
                original_table_html=summary.original_table_html,
                summary_markdown=summary.summary_markdown,
                processing_time=summary.processing_time or 0.0,
                was_merged=was_merged,
                source_chain_id=source_chain_id,
                timestamp=datetime.now().isoformat(),
            )

            # Save to file
            report_file = report_dir / f"{table_id}_summary_report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Generated summarization report: {report_file.name}")

        logger.info(
            f"Generated {len(summaries)} summarization report(s) in {report_dir}"
        )
