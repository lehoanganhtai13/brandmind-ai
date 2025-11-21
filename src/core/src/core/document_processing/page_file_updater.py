"""Page file updater for safe table merging operations and empty page cleanup."""

import re
from pathlib import Path
from typing import Dict, List, Set

from loguru import logger

from core.document_processing.models import TableChain, TableMergeDecision


class PageFileUpdater:
    """
    Manages page file updates for table merging and empty page cleanup.

    This service handles the critical operation of updating page markdown files
    after table merge decisions. It replaces the first table in a chain with the
    merged result, removes subsequent fragment positions, and detects/removes pages
    that become empty after merging operations.
    """

    def __init__(self):
        """Initialize the page file updater."""
        # Pattern to detect if page has only metadata header (no content)
        self.metadata_only_pattern = re.compile(
            r"^#\s+Page\s+\d+\s*\n\*\*.*?\*\*.*?\n---\s*$", re.DOTALL
        )

    async def apply_merge_decisions(
        self,
        chains_by_page: Dict[int, List[TableChain]],
        decisions: List[TableMergeDecision],
    ) -> Set[int]:
        """
        Apply assembly decisions to page files and track modified pages.

        This method iterates through all assembly decisions, updating page files where
        status=SUCCESS. It replaces the first table position with the merged result
        and removes subsequent fragment positions by replacing with empty string.
        For cross-page chains, it tracks all affected page numbers.

        Args:
            chains_by_page (Dict[int, List[TableChain]]): Chains organized by page
            decisions (List[TableMergeDecision]): Assembly decisions for all chains

        Returns:
            modified_pages (Set[int]): Set of page numbers that were modified
        """
        # Build decision lookup map
        decision_map = {d.chain_id: d for d in decisions}

        modified_pages: Set[int] = set()

        for page_number, chains in chains_by_page.items():
            for chain in chains:
                decision = decision_map.get(chain.chain_id)
                if not decision or decision.status != "SUCCESS":
                    continue

                # Apply merge to this chain
                try:
                    await self._apply_single_merge(chain, decision)
                    
                    # Track all page numbers affected by this chain (including cross-page)
                    affected_pages = set(table.page_number for table in chain.tables)
                    modified_pages.update(affected_pages)
                    
                    logger.info(
                        f"Applied merge for chain {chain.chain_id}, "
                        f"affected pages: {sorted(affected_pages)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to apply merge for chain {chain.chain_id}: {e}"
                    )

        logger.info(f"Applied merges across {len(modified_pages)} page(s)")
        return modified_pages

    async def _apply_single_merge(
        self,
        chain: TableChain,
        decision: TableMergeDecision,
    ):
        """
        Apply a single assembly decision to page files (handles cross-page chains).

        This method performs the actual file update for chains that may span multiple
        pages. It replaces the first table fragment with the assembled/merged table,
        and removes all subsequent fragments from their respective page files.

        Handles both HTML and markdown table formats by using exact content matching.

        Args:
            chain (TableChain): The table chain being merged
            decision (TableMergeDecision): The assembly decision with final_merged_html
        """
        # Group tables by their page file
        tables_by_file = {}
        for table in chain.tables:
            if table.page_file not in tables_by_file:
                tables_by_file[table.page_file] = []
            tables_by_file[table.page_file].append(table)

        # Process each affected page file
        first_table_processed = False
        for page_file, tables in tables_by_file.items():
            if not page_file or not Path(page_file).exists():
                logger.warning(f"Page file not found: {page_file}")
                continue

            # Read current content
            with open(page_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Process tables in this file (sorted by position to handle overlaps)
            sorted_tables = sorted(tables, key=lambda t: t.start_pos)
            
            for table in sorted_tables:
                # Use exact content matching (works for both HTML and markdown)
                original_content = table.html_content.strip()
                
                if not first_table_processed:
                    # Replace first table with assembled result (always HTML)
                    content = content.replace(
                        original_content,
                        f"\n\n{decision.final_merged_html}\n\n",
                        1,  # Replace only first occurrence
                    )
                    first_table_processed = True
                    logger.debug(
                        f"Replaced {table.table_format} table at position "
                        f"{table.start_pos} with merged HTML"
                    )
                else:
                    # Remove subsequent fragments (both HTML and markdown)
                    content = content.replace(original_content, "", 1)
                    logger.debug(
                        f"Removed {table.table_format} table at position "
                        f"{table.start_pos}"
                    )

            # Write updated content back to this page file
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(content)

    async def cleanup_empty_pages(
        self,
        output_directory: str,
        modified_pages: Set[int],
    ) -> List[int]:
        """
        Detect and remove pages that became empty after table merging.

        A page is considered empty if it contains only the metadata header with no
        actual content. This can happen when a page contained only table fragments
        that were all merged into a previous page's table.

        Args:
            output_directory (str): Directory containing page markdown files
            modified_pages (Set[int]): Pages that were modified by merging

        Returns:
            removed_pages (List[int]): List of page numbers that were removed
        """
        output_path = Path(output_directory)
        if not output_path.exists():
            logger.warning(f"Output directory not found: {output_directory}")
            return []

        removed_pages = []

        # Check each modified page for emptiness
        for page_number in modified_pages:
            page_file = output_path / f"page_{page_number}.md"

            if not page_file.exists():
                continue

            try:
                with open(page_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Remove metadata header and check if any content remains
                content_without_metadata = re.sub(
                    r"^#\s+Page\s+\d+.*?\n---\s*\n",
                    "",
                    content,
                    flags=re.DOTALL,
                )

                # If only whitespace remains, page is empty
                if content_without_metadata.strip() == "":
                    page_file.unlink()  # Delete the file
                    removed_pages.append(page_number)
                    logger.info(f"Removed empty page: page_{page_number}.md")

            except Exception as e:
                logger.error(f"Failed to process page {page_number}: {e}")

        if removed_pages:
            logger.info(
                f"Removed {len(removed_pages)} empty page(s): {removed_pages}"
            )

        return removed_pages
