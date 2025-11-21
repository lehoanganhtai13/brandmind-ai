"""Table chain collector for detecting consecutive table fragments."""

import re
from pathlib import Path
from typing import Dict, List

from loguru import logger

from core.document_processing.models import TableChain, TableInfo


class TableChainCollector:
    """
    Detects and groups consecutive table fragments within page markdown files.

    This collector analyzes the spacing and content between HTML tables to identify
    potential table fragmentation patterns. Tables are considered consecutive if
    they appear one after another with only whitespace/newlines between them,
    suggesting they may be fragments of a single logical table.

    The collector builds transitive chains: if table_1 → table_2 and table_2 → table_3
    are consecutive, they form a single chain [table_1, table_2, table_3].
    """

    def __init__(self):
        """Initialize the chain collector with regex patterns for detection."""
        # Pattern to detect table followed by optional whitespace and another table
        self.consecutive_pattern = re.compile(
            r"</table>\s*<table", re.DOTALL | re.IGNORECASE
        )

        # Pattern to check for non-whitespace content between tables
        self.content_between_pattern = re.compile(
            r"</table>(.*?)<table", re.DOTALL | re.IGNORECASE
        )

    def collect_chains_from_page(
        self, page_file_path: str, tables: List[TableInfo]
    ) -> List[TableChain]:
        """
        Identify chains of consecutive tables within a single page file.

        This method analyzes the content between tables to determine which ones
        are consecutive (no intervening text). It builds transitive chains where
        if A→B and B→C are consecutive, the result is chain [A, B, C].

        Args:
            page_file_path (str): Path to the page markdown file
            tables (List[TableInfo]): All tables detected in this page file

        Returns:
            chains (List[TableChain]): List of table chains found in the page
        """
        if not tables:
            return []

        try:
            with open(page_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read page file {page_file_path}: {e}")
            return []

        # Sort tables by position in file
        sorted_tables = sorted(tables, key=lambda t: t.start_pos)

        # Build adjacency map: table_index → is_consecutive_with_next
        adjacency = {}
        for i in range(len(sorted_tables) - 1):
            current_table = sorted_tables[i]
            next_table = sorted_tables[i + 1]

            # Extract content between current table end and next table start
            gap_content = content[current_table.end_pos : next_table.start_pos]

            # Check if gap contains only whitespace
            is_consecutive = gap_content.strip() == ""
            adjacency[i] = is_consecutive

        # Build chains using transitive closure
        chains = []
        visited = set()

        for i in range(len(sorted_tables)):
            if i in visited:
                continue

            # Start a new chain
            chain_tables = [sorted_tables[i]]
            visited.add(i)

            # Extend chain while consecutive
            current_idx = i
            while current_idx in adjacency and adjacency[current_idx]:
                current_idx += 1
                chain_tables.append(sorted_tables[current_idx])
                visited.add(current_idx)

            # Only create a chain if it has 2+ tables
            if len(chain_tables) >= 2:
                page_number = sorted_tables[i].page_number
                chain_id = f"page_{page_number}_chain_{len(chains) + 1}"

                chain = TableChain(
                    chain_id=chain_id,
                    page_number=page_number,
                    tables=chain_tables,
                    has_gap_content=False,  # Already filtered by whitespace check
                )
                chains.append(chain)

                logger.debug(
                    f"Detected chain {chain_id} with {len(chain_tables)} tables "
                    f"on page {page_number}"
                )

        return chains

    def collect_all_chains(
        self, page_files: List[str], all_tables: List[TableInfo]
    ) -> Dict[int, List[TableChain]]:
        """
        Collect table chains across all page files, including cross-page chains.

        This method first processes each page to find within-page consecutive patterns,
        then extends chains across page boundaries by checking if the last table of
        page N connects to the first table of page N+1 (with no text content between).

        Cross-page chain example:
        - Page 1 ends with table_A
        - Page 2 starts with table_B (no text before it)
        - If A→B are consecutive, they form a cross-page chain
        - If page 2 also has table_B→table_C consecutive, the chain extends to [A,B,C]

        Args:
            page_files (List[str]): List of all page markdown file paths (sorted)
            all_tables (List[TableInfo]): All detected tables across all pages

        Returns:
            chains_by_page (Dict[int, List[TableChain]]): Chains organized by page
        """
        # Group tables by page file
        tables_by_file = {}
        for table in all_tables:
            if table.page_file not in tables_by_file:
                tables_by_file[table.page_file] = []
            tables_by_file[table.page_file].append(table)

        # Step 1: Collect within-page chains
        intra_page_chains = {}
        for page_file in page_files:
            page_tables = tables_by_file.get(page_file, [])
            if not page_tables:
                continue

            chains = self.collect_chains_from_page(page_file, page_tables)

            if chains:
                page_number = chains[0].page_number
                intra_page_chains[page_number] = chains
                logger.debug(
                    f"Page {page_number}: Found {len(chains)} intra-page chain(s)"
                )

        # Step 2: Detect cross-page connections
        cross_page_links = self._detect_cross_page_connections(
            page_files, tables_by_file
        )

        # Step 3: Merge chains using cross-page links
        if cross_page_links:
            chains_by_page = self._merge_cross_page_chains(
                intra_page_chains, all_tables, cross_page_links
            )
        else:
            chains_by_page = intra_page_chains

        total_chains = sum(len(chains) for chains in chains_by_page.values())
        logger.info(
            f"Total chains detected across document: {total_chains} "
            f"(including {len(cross_page_links)} cross-page connections)"
        )

        return chains_by_page

    def _detect_cross_page_connections(
        self, page_files: List[str], tables_by_file: Dict[str, List[TableInfo]]
    ) -> List[tuple]:
        """
        Detect if last table of page N connects to first table of page N+1.

        Two tables are connected if:
        1. Table A is at/near the end of page N
        2. Table B is at/near the start of page N+1
        3. No text content exists between A's end and page boundary
        4. No text content exists between page boundary and B's start

        Args:
            page_files (List[str]): Sorted list of page file paths
            tables_by_file (Dict[str, List[TableInfo]]): Tables grouped by page

        Returns:
            connections (List[tuple]): List of (table_A, table_B) cross-page pairs
        """
        connections = []

        for i in range(len(page_files) - 1):
            current_page_file = page_files[i]
            next_page_file = page_files[i + 1]

            current_tables = tables_by_file.get(current_page_file, [])
            next_tables = tables_by_file.get(next_page_file, [])

            if not current_tables or not next_tables:
                continue

            try:
                # Read both page contents
                with open(current_page_file, "r", encoding="utf-8") as f:
                    current_content = f.read()
                with open(next_page_file, "r", encoding="utf-8") as f:
                    next_content = f.read()

                # Get last table of current page
                last_table = max(current_tables, key=lambda t: t.end_pos)

                # Get first table of next page
                first_table = min(next_tables, key=lambda t: t.start_pos)

                # Check if content after last table (until page end) is only whitespace
                content_after_last = current_content[last_table.end_pos :]
                # Remove page metadata/footer patterns if any
                content_after_last = re.sub(
                    r"\n---\n.*$", "", content_after_last, flags=re.DOTALL
                ).strip()

                # Check if content before first table (after page header) is only whitespace
                # Extract content after metadata header
                header_match = re.search(
                    r"^#\s+Page\s+\d+.*?\n---\s*\n", next_content, flags=re.DOTALL
                )
                if header_match:
                    content_before_first = next_content[
                        header_match.end() : first_table.start_pos
                    ].strip()
                else:
                    content_before_first = next_content[
                        : first_table.start_pos
                    ].strip()

                # If both gaps are empty (only whitespace), tables are connected
                if content_after_last == "" and content_before_first == "":
                    connections.append((last_table, first_table))
                    logger.debug(
                        f"Cross-page connection: "
                        f"page {last_table.page_number} (last table) → "
                        f"page {first_table.page_number} (first table)"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to check cross-page connection between "
                    f"{current_page_file} and {next_page_file}: {e}"
                )
                continue

        return connections

    def _merge_cross_page_chains(
        self,
        intra_page_chains: Dict[int, List[TableChain]],
        all_tables: List[TableInfo],
        cross_page_links: List[tuple],
    ) -> Dict[int, List[TableChain]]:
        """
        Merge intra-page chains with cross-page connections into complete chains.

        This method rebuilds chains by considering both within-page chains and
        cross-page table connections. The result maintains transitive closure:
        if page 1 chain ends with table A, and page 2 starts with table B,
        and A→B are connected, the chains merge into one spanning both pages.

        Args:
            intra_page_chains (Dict[int, List[TableChain]]): Chains within each page
            all_tables (List[TableInfo]): All tables for lookup
            cross_page_links (List[tuple]): Cross-page (table_A, table_B) connections

        Returns:
            merged_chains (Dict[int, List[TableChain]]): Final chains organized by page
        """
        # Build a global table graph: table_id → [connected_table_ids]
        table_graph: Dict[int, List[int]] = {}

        # Add intra-page chain connections
        for chains in intra_page_chains.values():
            for chain in chains:
                for i in range(len(chain.tables) - 1):
                    current_id = id(chain.tables[i])
                    next_id = id(chain.tables[i + 1])
                    if current_id not in table_graph:
                        table_graph[current_id] = []
                    table_graph[current_id].append(next_id)

        # Add cross-page connections
        for table_a, table_b in cross_page_links:
            id_a = id(table_a)
            id_b = id(table_b)
            if id_a not in table_graph:
                table_graph[id_a] = []
            table_graph[id_a].append(id_b)

        # Build table lookup: table_id → TableInfo
        table_lookup = {id(t): t for t in all_tables}

        # Find connected components (complete chains) using DFS
        visited: set = set()
        final_chains = []

        for table_id in table_graph:
            if table_id in visited:
                continue

            # Build chain starting from this table
            chain_tables = self._dfs_build_chain(
                table_id, table_graph, table_lookup, visited
            )

            if len(chain_tables) >= 2:
                # Use first table's page as chain reference
                first_page = chain_tables[0].page_number
                chain_id = f"page_{first_page}_chain_{len(final_chains) + 1}_cross"

                chain = TableChain(
                    chain_id=chain_id,
                    page_number=first_page,
                    tables=chain_tables,
                    has_gap_content=False,
                )
                final_chains.append(chain)

                logger.debug(
                    f"Built cross-page chain {chain_id} with {len(chain_tables)} "
                    f"tables spanning pages {chain_tables[0].page_number} to "
                    f"{chain_tables[-1].page_number}"
                )

        # Organize by page number (use first table's page as key)
        chains_by_page = {}
        for chain in final_chains:
            page_num = chain.page_number
            if page_num not in chains_by_page:
                chains_by_page[page_num] = []
            chains_by_page[page_num].append(chain)

        return chains_by_page

    def _dfs_build_chain(
        self,
        start_table_id: int,
        graph: Dict[int, List[int]],
        table_lookup: Dict[int, TableInfo],
        visited: set,
    ) -> List[TableInfo]:
        """
        Build a chain of tables using depth-first traversal.

        Args:
            start_table_id (int): Starting table ID
            graph (Dict[int, List[int]]): Adjacency graph of table connections
            table_lookup (Dict[int, TableInfo]): Lookup map for table objects
            visited (set): Set of already visited table IDs

        Returns:
            chain (List[TableInfo]): Ordered list of connected tables
        """
        chain = []
        stack = [start_table_id]
        local_visited: set = set()

        while stack:
            current_id = stack.pop()
            if current_id in local_visited:
                continue

            local_visited.add(current_id)
            visited.add(current_id)
            chain.append(table_lookup[current_id])

            # Add connected tables to stack
            if current_id in graph:
                for next_id in graph[current_id]:
                    if next_id not in local_visited:
                        stack.append(next_id)

        # Sort by position to maintain document order
        chain.sort(key=lambda t: (t.page_number, t.start_pos))

        return chain
