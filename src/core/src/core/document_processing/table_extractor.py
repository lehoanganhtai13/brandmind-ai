"""Table extraction supporting both HTML and markdown formats."""

import re
from typing import List

from loguru import logger

from core.document_processing.markdown_table_converter import MarkdownTableConverter
from core.document_processing.models import TableInfo


class TableExtractor:
    """
    Extracts both HTML and markdown tables from page markdown files.

    This extractor detects two table formats:
    1. HTML tables: <table>...</table>
    2. Markdown tables: pipe-separated format (| col1 | col2 |)

    The extractor maintains position information for all table types to enable
    chain detection and merging across page boundaries, including cases where
    a table spans pages with different formats (e.g., HTML on page N, markdown
    on page N+1).
    """

    def __init__(self):
        """Initialize the table extractor with detection patterns."""
        # HTML table pattern
        self.html_table_pattern = re.compile(
            r"<table[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE
        )

        # Markdown table converter for detection and position finding
        self.markdown_converter = MarkdownTableConverter()

    def detect_tables_in_files(self, page_files: List[str]) -> List[TableInfo]:
        """
        Detect all HTML and markdown tables in page markdown files.

        This method scans each file for both formats:
        1. HTML tables: Extracted with regex matching <table>...</table>
        2. Markdown tables: Detected with pipe-separator pattern validation

        All tables are tracked with position metadata to enable chain detection
        across pages and formats.

        Args:
            page_files (List[str]): Paths to page markdown files

        Returns:
            List[TableInfo]: All detected tables with format and position metadata
        """
        tables = []

        for page_file_path in page_files:
            try:
                with open(page_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_num_match = re.search(r"page_(\d+)", page_file_path)
                if not page_num_match:
                    logger.warning(
                        f"Could not extract page number from {page_file_path}"
                    )
                    continue
                page_num = int(page_num_match.group(1))

                # Detect HTML tables
                for match in self.html_table_pattern.finditer(content):
                    table_info = TableInfo(
                        html_content=match.group(0),
                        table_format="html",
                        start_pos=match.start(),
                        end_pos=match.end(),
                        page_number=page_num,
                        page_file=page_file_path,
                    )
                    tables.append(table_info)

                # Detect markdown tables
                markdown_positions = self.markdown_converter.detect_markdown_table_positions(
                    content
                )
                for start_pos, end_pos in markdown_positions:
                    markdown_content = content[start_pos:end_pos]
                    table_info = TableInfo(
                        html_content=markdown_content,  # Store raw markdown
                        table_format="markdown",
                        start_pos=start_pos,
                        end_pos=end_pos,
                        page_number=page_num,
                        page_file=page_file_path,
                    )
                    tables.append(table_info)

            except Exception as e:
                logger.warning(f"Failed to process tables in {page_file_path}: {e}")
                continue

        # Count by format
        html_count = sum(1 for t in tables if t.table_format == "html")
        markdown_count = sum(1 for t in tables if t.table_format == "markdown")

        logger.info(
            f"Detected {len(tables)} tables across {len(page_files)} page files "
            f"({html_count} HTML, {markdown_count} markdown)"
        )
        return tables
