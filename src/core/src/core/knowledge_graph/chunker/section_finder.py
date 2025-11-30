"""
Section Finder for determining the most specific section a chunk belongs to.

Given a chunk's page range, finds the deepest (most specific) section
in the global_map hierarchy that contains those pages.
"""

from typing import List, Optional, Tuple

from loguru import logger

from core.knowledge_graph.models.global_map import SectionNode


class SectionFinder:
    """
    Finds the most specific section for a given page range.

    This class traverses the global_map hierarchy to find the deepest
    section that contains a given set of pages, ensuring accurate
    metadata assignment for chunks.
    """

    def __init__(self, global_map_sections: List[SectionNode]):
        """
        Initialize SectionFinder with global_map structure.

        Args:
            global_map_sections: Top-level sections from global_map.json
        """
        self.sections = global_map_sections
        logger.info("SectionFinder initialized")

    def find_section_for_pages(self, pages: List[str]) -> Optional[Tuple[str, str]]:
        """
        Find the most specific section containing the given pages.

        Traverses the section hierarchy depth-first to find the deepest
        section whose page range contains all the given pages, then builds
        the full hierarchy path.

        Args:
            pages: List of page IDs (e.g., ["page_17.md", "page_18.md"])

        Returns:
            Tuple of (hierarchy_path, section_summary) where hierarchy_path
            is the full path from root to leaf (e.g., "Part 1 > Chapter 1"),
            or None if no section contains these pages
        """
        if not pages:
            return None

        # Extract page numbers for comparison
        page_numbers = [self._extract_page_number(p) for p in pages]
        min_page = min(page_numbers)
        max_page = max(page_numbers)

        # Find the deepest section containing this page range
        result = self._find_deepest_section_with_path(
            self.sections, min_page, max_page, []
        )

        if result is None:
            return None

        section, path = result

        # Build hierarchy path string
        hierarchy_path = " > ".join(path)

        return (hierarchy_path, section.summary_context)

    def _find_deepest_section_with_path(
        self,
        sections: List[SectionNode],
        min_page: int,
        max_page: int,
        current_path: List[str],
        current_best: Optional[Tuple[SectionNode, List[str]]] = None,
    ) -> Optional[Tuple[SectionNode, List[str]]]:
        """
        Recursively find the deepest section with its full path.

        Args:
            sections: List of sections to search
            min_page: Minimum page number in chunk
            max_page: Maximum page number in chunk
            current_path: Path from root to current level
            current_best: Current best match (deepest section, path)

        Returns:
            Tuple of (section, path) where path is list of section titles
            from root to this section
        """
        for section in sections:
            # Extract section's page range
            section_start = self._extract_page_number(section.start_page_id)
            section_end = self._extract_page_number(section.end_page_id)

            # Check if chunk is within this section's range
            if section_start <= min_page and max_page <= section_end:
                # This section contains the chunk
                # Build path including this section
                new_path = current_path + [section.title]

                # Update current_best if this is deeper (higher level number)
                if current_best is None or section.level > current_best[0].level:
                    current_best = (section, new_path)

                # Recurse into children to find even deeper match
                if section.children:
                    deeper_match = self._find_deepest_section_with_path(
                        section.children, min_page, max_page, new_path, current_best
                    )
                    if deeper_match:
                        current_best = deeper_match

        return current_best

    def _extract_page_number(self, page_id: str) -> int:
        """
        Extract numeric page number from page ID.

        Args:
            page_id: Page ID like "page_17.md"

        Returns:
            Page number as integer
        """
        # Remove "page_" prefix and ".md" suffix
        return int(page_id.replace("page_", "").replace(".md", ""))
