"""
Page Merger for combining markdown pages into section content.

Handles metadata stripping and character offset tracking for
reverse page mapping during chunking.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger


class PageMerger:
    """
    Merges multiple markdown page files into a single content string.

    This class handles the complexities of combining parsed document pages
    while preserving the ability to map chunks back to their source pages.
    It strips metadata headers and builds a character offset map for
    reverse lookup.
    """

    # Metadata pattern: Everything from start to second "---" line
    METADATA_PATTERN = r"^# Page \d+\n\n\*\*Document Title\*\*:.*?\n---\n\n"

    def __init__(self, document_folder: str):
        """
        Initialize PageMerger with document folder path.

        Args:
            document_folder: Absolute path to parsed document folder
        """
        self.document_folder = Path(document_folder)
        self._document_metadata: Dict[str, str] | None = None  # Cache metadata
        logger.info(f"PageMerger initialized for: {document_folder}")

    def get_document_metadata(self) -> Dict[str, str]:
        """
        Extract document metadata from any page file.

        Reads the first available page file to extract document title
        and author from the metadata header.

        Returns:
            Dictionary with 'title' and 'author' keys
        """
        if self._document_metadata:
            return self._document_metadata

        # Find first page file
        page_files = sorted(self.document_folder.glob("page_*.md"))
        if not page_files:
            logger.warning("No page files found")
            return {"title": "Unknown", "author": "Unknown"}

        # Read first page
        first_page = page_files[0]
        with open(first_page, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata using regex
        title_match = re.search(r"\*\*Document Title\*\*:\s*(.+)", content)
        author_match = re.search(r"\*\*Author\*\*:\s*(.+)", content)

        metadata = {
            "title": title_match.group(1).strip() if title_match else "Unknown",
            "author": author_match.group(1).strip() if author_match else "Unknown",
        }

        # Cache for future calls
        self._document_metadata = metadata
        logger.info(f"Extracted metadata: {metadata}")

        return metadata

    def merge_pages(
        self,
        page_ids: List[str],
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> Tuple[str, Dict[str, Tuple[int, int]]]:
        """
        Merge multiple page files into single content string.

        Args:
            page_ids: List of page file names
                (e.g., ["page_5.md", "page_6.md"])
            start_line: Optional line number to start from in first page
                (0-indexed, after metadata removal)
            end_line: Optional line number to end at in last page
                (0-indexed, after metadata removal)

        Returns:
            Tuple of:
            - merged_content (str): Combined content from all pages
            - offset_map (Dict[str, Tuple[int, int]]): Maps page_id to
              (start_char, end_char) in merged content
        """
        merged_content = []
        offset_map = {}
        current_offset = 0

        for i, page_id in enumerate(page_ids):
            page_path = self.document_folder / page_id

            if not page_path.exists():
                logger.warning(f"Page not found: {page_id}, skipping")
                continue

            # Read page content
            with open(page_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            # Strip metadata header
            clean_content = re.sub(
                self.METADATA_PATTERN, "", raw_content, count=1, flags=re.DOTALL
            )

            # Handle start_line for first page
            if i == 0 and start_line is not None:
                lines = clean_content.split("\n")
                clean_content = "\n".join(lines[start_line:])

            # Handle end_line for last page
            if i == len(page_ids) - 1 and end_line is not None:
                lines = clean_content.split("\n")
                clean_content = "\n".join(lines[:end_line])

            # Track offset
            start_char = current_offset
            end_char = current_offset + len(clean_content)
            offset_map[page_id] = (start_char, end_char)

            merged_content.append(clean_content)
            current_offset = end_char + 2  # +2 for "\n\n" separator

        final_content = "\n\n".join(merged_content)

        logger.info(
            f"Merged {len(page_ids)} pages: "
            f"{page_ids[0]} to {page_ids[-1]} "
            f"({len(final_content)} chars)"
        )

        return final_content, offset_map

    def get_pages_for_chunk(
        self, chunk_start: int, chunk_end: int, offset_map: Dict[str, Tuple[int, int]]
    ) -> List[str]:
        """
        Determine which pages a chunk spans based on character offsets.

        Args:
            chunk_start: Start character index of chunk in merged content
            chunk_end: End character index of chunk in merged content
            offset_map: Map of page_id to (start_char, end_char)

        Returns:
            List of page IDs that the chunk spans
        """
        pages = []

        for page_id, (start, end) in offset_map.items():
            # Check if chunk overlaps with this page
            if not (chunk_end <= start or chunk_start >= end):
                pages.append(page_id)

        # Sort by page number
        pages.sort(key=lambda p: int(p.replace("page_", "").replace(".md", "")))

        return pages
