"""Content cleanup processor for normalizing parsed markdown files."""

import re
from pathlib import Path
from typing import List

from loguru import logger


class ContentCleanupProcessor:
    """
    Processes parsed markdown files to normalize whitespace and fix metadata separators.

    This processor handles two main cleanup tasks:
    1. Normalizing excessive blank lines (3+ consecutive) to exactly 2 blank lines
    2. Fixing missing blank line after metadata separator

    The cleanup ensures consistent formatting. Content extraction should use
    split("---", 1) to split only at the first separator, eliminating the need
    to escape additional --- in content.
    """

    def __init__(self):
        """Initialize the content cleanup processor with regex patterns."""
        # Regex to match 3 or more consecutive newlines
        self.excessive_newlines_pattern = re.compile(r"\n{3,}")

    def normalize_whitespace(self, content: str) -> str:
        """
        Normalize excessive blank lines in markdown content.

        Replaces 3 or more consecutive newlines with exactly 2 newlines,
        maintaining readability while removing excessive spacing.

        Args:
            content (str): Raw markdown content with potential excessive spacing

        Returns:
            normalized_content (str): Content with normalized whitespace
        """
        # Replace 3+ consecutive newlines with exactly 2
        normalized = self.excessive_newlines_pattern.sub("\n\n", content)
        return normalized

    def fix_metadata_separator_spacing(self, content: str) -> str:
        """
        Ensure there's a blank line after the metadata separator.

        Fixes cases where content is directly attached to --- separator:
        "--- Philip Kotler" → "---\\n\\nPhilip Kotler"

        Args:
            content (str): Markdown content with potential spacing issues

        Returns:
            fixed_content (str): Content with proper spacing after separator
        """
        lines = content.split("\n")

        # Find the metadata separator (should be around line 9)
        for i, line in enumerate(lines):
            if line.strip() == "---" and i < 15:
                # Check if next line exists and is not blank
                if i + 1 < len(lines) and lines[i + 1].strip() != "":
                    # Insert a blank line after separator
                    lines.insert(i + 1, "")
                    logger.debug(
                        f"Added blank line after metadata separator at line {i + 1}"
                    )
                break

            # Handle case where separator has content on same line
            if line.startswith("---") and line.strip() != "---" and i < 15:
                # Split "--- Philip Kotler" into "---" and "Philip Kotler"
                content_part = line[3:].strip()
                lines[i] = "---"
                lines.insert(i + 1, "")
                lines.insert(i + 2, content_part)
                logger.debug(
                    f"Fixed metadata separator with attached content at line {i + 1}"
                )
                break

        return "\n".join(lines)

    def process_file(self, file_path: str) -> bool:
        """
        Process a single markdown file to apply all cleanup operations.

        Args:
            file_path (str): Absolute path to the markdown file

        Returns:
            success (bool): True if file was processed successfully
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            # Read original content
            with open(path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # Apply cleanup operations in order
            cleaned_content = self.normalize_whitespace(original_content)
            cleaned_content = self.fix_metadata_separator_spacing(cleaned_content)

            # Write back if content changed
            if cleaned_content != original_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                logger.debug(f"Cleaned up content in: {path.name}")
                return True

            return True

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return False

    def process_pages(self, page_files: List[str]) -> List[str]:
        """
        Process multiple page files to apply content cleanup.

        Args:
            page_files (List[str]): List of absolute paths to page markdown files

        Returns:
            processed_files (List[str]): List of files that were successfully processed
        """
        processed = []

        for file_path in page_files:
            if self.process_file(file_path):
                processed.append(file_path)

        logger.info(
            f"Content cleanup completed for {len(processed)}/{len(page_files)} files"
        )
        return processed
