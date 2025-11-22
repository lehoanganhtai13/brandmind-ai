"""Text integrity processor for restoring cross-page text fragmentation."""

import re
from pathlib import Path
from typing import List, Set, Tuple

from loguru import logger


class TextIntegrityProcessor:
    """
    Handles the restoration of cross-page text fragmentation.

    This processor scans pages for sentences that are split across page boundaries
    (e.g., ending without terminal punctuation on page N and continuing on page N+1).
    It merges the fragmented text back to the previous page to ensure semantic continuity.
    """

    def __init__(self):
        """Initialize the text integrity processor."""
        # Terminal punctuation marks that indicate a complete sentence end
        self.terminal_punctuation = {".", "!", "?", ":", ";"}
        
        # Pattern to detect headers (lines starting with #)
        self.header_pattern = re.compile(r"^#+\s+.*")
        
        # Pattern to detect page metadata headers
        self.metadata_pattern = re.compile(r"^#\s+Page\s+\d+.*?\n---\s*\n", re.DOTALL)

    def process_pages(self, page_files: List[str]) -> Set[int]:
        """
        Iterate through pages and fix text fragmentation.

        Args:
            page_files (List[str]): List of paths to page markdown files (sorted)

        Returns:
            modified_pages (Set[int]): Set of page numbers that were modified
        """
        modified_pages = set()
        
        # Process pairs of consecutive pages
        for i in range(len(page_files) - 1):
            current_page_file = page_files[i]
            next_page_file = page_files[i + 1]
            
            try:
                # Read content
                with open(current_page_file, "r", encoding="utf-8") as f:
                    current_content = f.read()
                
                with open(next_page_file, "r", encoding="utf-8") as f:
                    next_content = f.read()
                
                # Check for fragmentation
                if self._should_merge_text(current_content, next_content):
                    # Perform merge
                    new_current, new_next = self._merge_text(
                        current_content, next_content
                    )
                    
                    # Write updates
                    with open(current_page_file, "w", encoding="utf-8") as f:
                        f.write(new_current)
                    
                    with open(next_page_file, "w", encoding="utf-8") as f:
                        f.write(new_next)
                    
                    # Track modified pages
                    current_page_num = self._extract_page_number(current_page_file)
                    next_page_num = self._extract_page_number(next_page_file)
                    modified_pages.add(current_page_num)
                    modified_pages.add(next_page_num)
                    
                    logger.info(
                        f"Restored text fragmentation between page {current_page_num} "
                        f"and {next_page_num}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to process text integrity between {current_page_file} "
                    f"and {next_page_file}: {e}"
                )
                continue
                
        return modified_pages

    def _should_merge_text(self, current_content: str, next_content: str) -> bool:
        """
        Check if text should be merged between pages.
        
        Criteria:
        1. Current page ends with incomplete sentence (no terminal punctuation)
        2. Next page has a valid continuation paragraph (skipping headers/tables/notes)
        3. Not merging headers or distinct sections
        """
        # Clean content to ignore metadata/footers for analysis
        current_text = self._get_clean_text_end(current_content)
        
        # Find the first candidate paragraph in next page
        next_text_start, _ = self._find_continuation_candidate(next_content)
        
        if not current_text or not next_text_start:
            return False
            
        # Check 1: Current text ends without terminal punctuation
        last_char = current_text.strip()[-1] if current_text.strip() else ""
        if not last_char or last_char in self.terminal_punctuation:
            return False
            
        # Check 2: Next text looks like a continuation
        # (starts with lowercase or is part of a sentence)
        first_word = next_text_start.split()[0] if next_text_start else ""
        if not first_word:
            return False
            
        # Heuristic: If it's a header, definitely don't merge (double check)
        if self.header_pattern.match(next_text_start):
            return False
            
        return True

    def _find_continuation_candidate(self, content: str) -> Tuple[str, int]:
        """
        Find the first valid text paragraph in content, skipping headers, tables, etc.
        
        Returns:
            (candidate_text, start_index_in_content)
            candidate_text is empty if no valid candidate found.
        """
        # Remove metadata header first to get the content body
        header_match = self.metadata_pattern.match(content)
        start_offset = header_match.end() if header_match else 0
        body_content = content[start_offset:]
        
        lines = body_content.split('\n')
        current_offset = 0
        
        for line in lines:
            line_len = len(line) + 1 # +1 for newline
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                current_offset += line_len
                continue
                
            # Skip Headers (#)
            if stripped_line.startswith('#'):
                current_offset += line_len
                continue
                
            # Skip Tables (| ... |)
            if stripped_line.startswith('|') and stripped_line.endswith('|'):
                current_offset += line_len
                continue
                
            # Skip Blockquotes (>) - often used for Notes
            if stripped_line.startswith('>'):
                current_offset += line_len
                continue
                
            # Skip Figure/Table Captions (heuristic)
            # e.g. "Figure 1.2", "Table 3:"
            if re.match(r"^(Figure|Table)\s+\d+", stripped_line, re.IGNORECASE):
                current_offset += line_len
                continue

            # Skip HTML tags (e.g. <table>, <thead>, <tr>, </div>)
            # We assume these are block-level elements starting the line
            if stripped_line.startswith('<'):
                current_offset += line_len
                continue
                
            # If we reach here, it's likely a text paragraph
            return stripped_line, start_offset + current_offset
            
        return "", -1

    def _merge_text(self, current_content: str, next_content: str) -> Tuple[str, str]:
        """
        Merge the fragmented text from next page to current page.
        
        Returns:
            (new_current_content, new_next_content)
        """
        # Find the candidate fragment again
        next_clean_start, start_index = self._find_continuation_candidate(next_content)
        
        if not next_clean_start:
            return current_content, next_content
        
        # Find the end of the first sentence/clause in the candidate paragraph
        match = re.search(r"[\.\!\?](?:\s|$)", next_clean_start)
        
        if match:
            split_index = match.end()
            fragment = next_clean_start[:split_index]
        else:
            # If no punctuation, take the whole line/paragraph
            fragment = next_clean_start
            
        # Construct new contents
        # 1. Remove trailing newlines/whitespace from current text
        current_stripped = current_content.rstrip()
        
        # 2. Append fragment (add space if needed)
        new_current = f"{current_stripped} {fragment.strip()}\n"
        
        # 3. Remove fragment from next content
        # We know exactly where the candidate paragraph starts (start_index)
        # We need to remove 'fragment' from that position
        
        # Reconstruct next_content:
        # prefix (metadata + skipped content) + remaining_paragraph + suffix
        
        prefix = next_content[:start_index]
        paragraph_part = next_content[start_index:]
        
        # We need to match the fragment in paragraph_part carefully
        # fragment comes from stripped_line, so we might need to handle leading whitespace in paragraph_part
        
        # Let's find the fragment in the paragraph_part
        # It should be at the start (ignoring whitespace)
        match_fragment = re.search(re.escape(fragment.strip()), paragraph_part)
        
        if match_fragment:
            # Remove the matched fragment
            new_paragraph_part = paragraph_part[:match_fragment.start()] + paragraph_part[match_fragment.end():]
            # Clean up potential double spaces or leading punctuation if any (simple lstrip)
            new_paragraph_part = new_paragraph_part.lstrip()
            
            new_next = prefix + new_paragraph_part
        else:
            # Fallback: simple replace if exact match fails (shouldn't happen if logic is correct)
            new_next = next_content.replace(fragment, "", 1)
            
        return new_current, new_next

    def _get_clean_text_end(self, content: str) -> str:
        """Get the last meaningful text line from content (ignoring footers)."""
        lines = content.strip().split('\n')
        # Filter out empty lines
        lines = [l for l in lines if l.strip()]
        if not lines:
            return ""
        return lines[-1]

    def _get_clean_text_start(self, content: str) -> str:
        """Get the first meaningful text from content (ignoring metadata header)."""
        # Remove metadata header
        content_no_header = self.metadata_pattern.sub("", content)
        return content_no_header.strip()

    def _extract_page_number(self, file_path: str) -> int:
        """Extract page number from filename (page_X.md)."""
        try:
            return int(Path(file_path).stem.split('_')[-1])
        except (ValueError, IndexError):
            return 0
