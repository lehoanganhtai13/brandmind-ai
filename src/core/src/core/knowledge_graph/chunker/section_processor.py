"""
Section Processor for extracting section content from merged pages.

Uses global_map.json to determine section boundaries and extract
content while respecting subsection hierarchy.
"""

from typing import List, Tuple

from loguru import logger

from core.knowledge_graph.chunker.page_merger import PageMerger
from core.knowledge_graph.models.global_map import SectionNode


class SectionProcessor:
    """
    Processes sections from global map to extract clean content.

    This class handles the recursive extraction of section content,
    ensuring that subsections are properly separated and no content
    is duplicated or lost at boundaries.
    """

    def __init__(self, page_merger: PageMerger):
        """
        Initialize SectionProcessor with PageMerger.

        Args:
            page_merger: PageMerger instance for merging pages
        """
        self.page_merger = page_merger

    def extract_section_content(
        self, section: SectionNode, next_section_start: Tuple[str, int] | None = None
    ) -> Tuple[str, dict[str, Tuple[int, int]]]:
        """
        Extract content for a section, stopping before next section.

        Args:
            section: SectionNode from global_map.json
            next_section_start: Optional tuple of (page_id, line_index) for next section

        Returns:
            Tuple of:
            - content (str): Section content
            - offset_map (dict): Character offset map for page tracking
        """
        # Build page list
        start_page_num = int(
            section.start_page_id.replace("page_", "").replace(".md", "")
        )
        end_page_num = int(section.end_page_id.replace("page_", "").replace(".md", ""))

        page_ids = [f"page_{i}.md" for i in range(start_page_num, end_page_num + 1)]

        # Determine start/end lines
        start_line = section.start_line_index - 10  # Adjust for metadata (10 lines)

        end_line = None
        if next_section_start:
            next_page_id, next_line_idx = next_section_start
            if next_page_id == section.end_page_id:
                end_line = next_line_idx - 10  # Same page, cut before next section

        # Merge pages
        content, offset_map = self.page_merger.merge_pages(
            page_ids=page_ids, start_line=start_line, end_line=end_line
        )

        logger.info(
            f"Extracted section '{section.title}': "
            f"{len(content)} chars, {len(page_ids)} pages"
        )

        return content, offset_map

    def extract_subsection_boundaries(
        self, section: SectionNode
    ) -> List[Tuple[int, SectionNode]]:
        """
        Get character positions where subsections start in merged content.

        Args:
            section: Parent section with children

        Returns:
            List of (char_position, subsection) tuples
        """
        # TODO: Implement subsection boundary detection
        # This requires merging parent content first, then finding
        # where each child's start_line_index maps to in merged content
        return []  # Placeholder for future implementation
