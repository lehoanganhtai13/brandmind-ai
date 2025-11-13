"""HTML table extraction from markdown content."""

import re
from typing import List
from core.document_processing.models import TableInfo
from loguru import logger


class HTMLTableExtractor:
    """
    Extracts HTML tables from individual page markdown files for LLM summarization.
    This class uses regular expressions to find table structures within text.
    """

    def __init__(self):
        """Initializes the HTMLTableExtractor with a compiled regex pattern."""
        self.table_pattern = re.compile(
            r"<table[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE
        )

    def detect_tables_in_files(self, page_files: List[str]) -> List[TableInfo]:
        """
        Detects all HTML tables in a list of individual page markdown files.

        This method reads each file, searches for table patterns, and extracts
        relevant metadata for each table found.

        Args:
            page_files (List[str]): A list of paths to page markdown files.

        Returns:
            List[TableInfo]: A list of objects, each containing information
                             about a detected table.
        """
        tables = []
        for page_file_path in page_files:
            try:
                with open(page_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                page_num_match = re.search(r"page_(\d+)", page_file_path)
                if not page_num_match:
                    logger.warning(f"Could not extract page number from {page_file_path}")
                    continue
                page_num = int(page_num_match.group(1))

                for match in self.table_pattern.finditer(content):
                    table_info = TableInfo(
                        html_content=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        page_number=page_num,
                        page_file=page_file_path,
                    )
                    tables.append(table_info)
            except Exception as e:
                logger.warning(f"Failed to process tables in {page_file_path}: {e}")
                continue

        logger.info(f"Detected {len(tables)} tables across {len(page_files)} page files")
        return tables
