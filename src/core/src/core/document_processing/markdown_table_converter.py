"""Utility for converting markdown tables to HTML format."""

import re
from typing import List


class MarkdownTableConverter:
    """
    Converts pipe-format markdown tables to HTML <table> structure.

    This converter handles standard markdown table syntax:
    - Header row with pipe separators: | Header1 | Header2 |
    - Separator row with dashes: |---------|---------|
    - Data rows: | Value1 | Value2 |

    The converter normalizes markdown tables to HTML so that the LLM can
    process all table fragments in a uniform format during assembly.
    """

    def __init__(self):
        """Initialize the converter with regex patterns for markdown tables."""
        # Pattern to detect markdown table rows (supports both formats):
        # Standard: | col1 | col2 | col3 |
        # Relaxed:  col1 | col2 | col3  (no trailing pipe)
        # Must have at least 2 cells (1 pipe separator minimum)
        self.table_row_pattern = re.compile(
            r"^\s*\|?\s*[^|]+(\s*\|\s*[^|]+)+\s*\|?\s*$", re.MULTILINE
        )

        # Pattern to detect separator row (|---|---|---| or |:---|:---|:---|)
        # Must contain only pipes, spaces, dashes, and colons
        self.separator_pattern = re.compile(r"^\s*\|[\s\-:|]+$", re.MULTILINE)

    def is_markdown_table(self, content: str) -> bool:
        """
        Check if content contains a markdown table.

        A valid markdown table must have:
        1. At least 2 consecutive lines starting with |
        2. A separator row with dashes

        Args:
            content (str): Text content to check

        Returns:
            bool: True if content contains a markdown table
        """
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]

        # Need at least 2 lines (header + data, separator is optional)
        if len(lines) < 2:
            return False

        # Check if we have pipe-separated rows (excluding separator)
        pipe_rows = [
            line
            for line in lines
            if self.table_row_pattern.match(line)
            and not self.separator_pattern.match(line)
        ]

        # Must have at least 2 pipe rows
        if len(pipe_rows) < 2:
            return False

        # If separator exists, it should be exactly 1
        separator_count = sum(1 for line in lines if self.separator_pattern.match(line))
        if separator_count > 1:
            return False

        return True

    def convert_to_html(self, markdown_table: str) -> str:
        """
        Convert a markdown table to HTML format.

        The conversion process:
        1. Parse rows into cells by splitting on |
        2. Identify separator row (indicates header/body boundary)
        3. Generate HTML <table> with <thead> and <tbody>

        Args:
            markdown_table (str): Markdown table string

        Returns:
            html_table (str): Converted HTML table string
        """
        lines = [
            line.strip() for line in markdown_table.strip().split("\n") if line.strip()
        ]

        # Parse rows and find separator
        header_rows = []
        body_rows = []
        separator_found = False

        for i, line in enumerate(lines):
            # Check separator first (separator also matches table_row_pattern)
            if self.separator_pattern.match(line):
                separator_found = True
                continue

            # Then check if it's a table row (after excluding separator)
            if self.table_row_pattern.match(line):
                # Extract cells by splitting on |
                cells = [cell.strip() for cell in line.split("|")]
                # Remove empty first/last elements from splitting
                cells = [cell for cell in cells if cell]

                # Classify as header or body based on separator position
                if not separator_found:
                    header_rows.append(cells)
                else:
                    body_rows.append(cells)

        # If no separator found, treat first row as header, rest as body
        if not separator_found and header_rows:
            if len(header_rows) > 1:
                body_rows = header_rows[1:]
                header_rows = [header_rows[0]]

        if not header_rows and not body_rows:
            return ""

        # Build HTML
        html_parts = ["<table>"]

        # Generate <thead>
        if header_rows:
            html_parts.append("  <thead>")
            for row in header_rows:
                html_parts.append("    <tr>")
                for cell in row:
                    html_parts.append(f"      <th>{cell}</th>")
                html_parts.append("    </tr>")
            html_parts.append("  </thead>")

        # Generate <tbody>
        if body_rows:
            html_parts.append("  <tbody>")
            for row in body_rows:
                html_parts.append("    <tr>")
                for cell in row:
                    html_parts.append(f"      <td>{cell}</td>")
                html_parts.append("    </tr>")
            html_parts.append("  </tbody>")

        html_parts.append("</table>")
        return "\n".join(html_parts)

    def detect_markdown_table_positions(self, content: str) -> List[tuple]:
        """
        Detect all markdown tables in content and return their positions.

        This method scans the content to find markdown table blocks and returns
        their start/end positions for extraction.

        Args:
            content (str): Text content to scan

        Returns:
            positions (List[tuple]): List of (start_pos, end_pos) tuples for each table
        """
        positions = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this line could start a table
            if self.table_row_pattern.match(line):
                # Look ahead to verify it's a table (find separator)
                table_start_line = i
                table_end_line = i

                # Collect consecutive table-like lines
                j = i
                has_separator = False
                data_row_count = 0
                while j < len(lines):
                    stripped_line = lines[j].strip()
                    if not stripped_line:
                        # Empty line ends the table
                        break

                    # Check separator first
                    if self.separator_pattern.match(stripped_line):
                        has_separator = True
                        table_end_line = j
                        j += 1
                        continue

                    # Then check for table row
                    if self.table_row_pattern.match(stripped_line):
                        data_row_count += 1
                        table_end_line = j
                        j += 1
                    else:
                        # Non-table line ends the table
                        break

                # Validate: must have at least 2 data rows (separator is optional)
                # If separator exists, total lines >= 3 (header + separator + data)
                # If no separator, total lines >= 2 (header + data)
                min_rows_needed = 3 if has_separator else 2
                if (
                    data_row_count >= 2
                    and (table_end_line - table_start_line + 1) >= min_rows_needed
                ):
                    # Calculate character positions
                    start_pos = sum(len(lines[k]) + 1 for k in range(table_start_line))
                    end_pos = sum(len(lines[k]) + 1 for k in range(table_end_line + 1))
                    positions.append((start_pos, end_pos))

                    # Skip past this table
                    i = table_end_line + 1
                    continue

            i += 1

        return positions
