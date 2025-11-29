"""Line Search Tool for finding exact line numbers of patterns in files.

This tool uses fuzzy string matching to find the exact line number where
a specific pattern (e.g., section header) appears in a markdown file.
Critical for precise section boundary detection in Document Mapping.
"""

from pathlib import Path
from typing import Any

from loguru import logger
from rapidfuzz import fuzz


def line_search(
    file_path: str,
    pattern: str,
    fuzzy_threshold: float = 85.0,
) -> dict[str, Any]:
    """Search for a text pattern in a file and return its exact line number.

    Uses fuzzy string matching to handle OCR errors and formatting variations.
    Returns the line with highest similarity score above threshold.

    Args:
        file_path: Absolute path to file to search
        pattern: Text pattern to find (e.g., section header)
        fuzzy_threshold: Minimum similarity score (0-100) to consider a match

    Returns:
        Dictionary with keys:
        - found (bool): Whether any matches were found
        - matches (list): List of up to 5 matching lines, sorted by relevance.
           Each match is a dict with:
            - line_number (int): 1-indexed line number (matching IDE)
            - matched_text (str): Actual text that matched
            - similarity_score (float): Similarity percentage (0-100)
            - header_level (int): Markdown header level
                (1=H1, 2=H2, etc., 10=non-header)
            - match_type (str): "fuzzy" or "ngram"
        - total_lines (int): Total lines in file
        - error (str | None): Error message if any
        - message (str | None): Info message if no match found

    Example:
        ```python
        result = line_search("/page_20.md", "Chapter 1: Finance")
        if result["found"]:
            # Get the best match (first in list)
            best_match = result["matches"][0]
            line_num = best_match["line_number"]
            text = best_match["matched_text"]
            score = best_match["similarity_score"]

            # For multi-line headers, check if H1 exists
            h1_matches = [m for m in result["matches"] if m["header_level"] == 1]
            if h1_matches:
                # Prefer H1 (chapter start) over H2 (subtitle)
                line_num = h1_matches[0]["line_number"]
        ```
    """
    try:
        logger.info("🛠️ Line search tool called")

        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return {
                "found": False,
                "matches": [],
                "total_lines": 0,
                "error": f"File not found: {file_path}",
            }

        with open(path, encoding="utf-8") as f:
            lines = f.readlines()

        # Collect all matches (no threshold filtering)
        matches: list[dict[str, Any]] = []

        # Phase 1: Calculate fuzzy match scores for all lines
        for i, line in enumerate(lines):
            score = fuzz.ratio(pattern.strip(), line.strip())

            if score > 0:  # Any match at all
                # Detect markdown header level
                header_level = 10  # Default for non-headers
                stripped = line.strip()
                if stripped.startswith("#"):
                    header_level = len(stripped) - len(stripped.lstrip("#"))

                matches.append(
                    {
                        "line_number": i + 1,
                        "matched_text": line.strip(),
                        "similarity_score": score,
                        "header_level": header_level,
                        "match_type": "fuzzy",
                    }
                )

        # Phase 2: Also calculate word-based matching scores
        # Use n-gram matching to find consecutive word sequences
        pattern_words = set(pattern.lower().split())
        stop_words = {"and", "the", "a", "an", "of", "to", "in", "for", "on", "with"}
        pattern_words = pattern_words - stop_words

        if pattern_words:
            # Create n-grams from pattern (sequences of 2-4 consecutive words)
            pattern_lower = pattern.lower()
            pattern_tokens = pattern_lower.split()

            for i, line in enumerate(lines):
                line_lower = line.lower()

                # Check for consecutive word sequences (n-grams)
                max_ngram_score = 0.0

                # Try different n-gram sizes (from longest to shortest)
                for n in range(min(len(pattern_tokens), 4), 1, -1):
                    for j in range(len(pattern_tokens) - n + 1):
                        ngram = " ".join(pattern_tokens[j : j + n])
                        if ngram in line_lower:
                            # Found consecutive sequence
                            ngram_score = (n / len(pattern_tokens)) * 100
                            max_ngram_score = max(max_ngram_score, ngram_score)

                if max_ngram_score > 0:
                    # Check if this line already has a match
                    existing = next(
                        (m for m in matches if m["line_number"] == i + 1), None
                    )
                    if existing:
                        # Update with better score
                        if max_ngram_score > existing["similarity_score"]:
                            existing["similarity_score"] = max_ngram_score
                            existing["match_type"] = "ngram"
                    else:
                        # Add new n-gram match
                        header_level = 10
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            header_level = len(stripped) - len(stripped.lstrip("#"))

                        matches.append(
                            {
                                "line_number": i + 1,
                                "matched_text": line.strip(),
                                "similarity_score": max_ngram_score,
                                "header_level": header_level,
                                "match_type": "ngram",
                            }
                        )

        # Sort matches by: 1) header level (lower is better),
        # 2) score (higher is better)
        matches.sort(key=lambda x: (x["header_level"], -x["similarity_score"]))

        # Filter to only keep matches above a minimal threshold (e.g., 20%)
        # to avoid returning every single line
        matches = [m for m in matches if m["similarity_score"] >= 20]

        # Limit to top 5 matches
        matches = matches[:5]

        if matches:
            logger.info(
                f"Found {len(matches)} match(es) for pattern '{pattern}' "
                f"in file '{file_path}'"
            )
            for match in matches:
                h_level = match["header_level"]
                level_str = f"H{h_level}" if h_level < 10 else "none"
                logger.info(
                    f"  - Line {match['line_number']}: "
                    f"{match['matched_text'][:60]}... "
                    f"(score: {match['similarity_score']:.1f}%, "
                    f"level: {level_str})"
                )
            return {
                "found": True,
                "matches": matches,
                "total_lines": len(lines),
            }
        else:
            logger.info(
                f"No line matched pattern '{pattern}' in file '{file_path}' "
                f"with threshold {fuzzy_threshold}%"
            )
            return {
                "found": False,
                "matches": [],
                "total_lines": len(lines),
                "message": f"No line matched pattern with threshold {fuzzy_threshold}%",
            }

    except Exception as e:
        return {
            "found": False,
            "matches": [],
            "total_lines": 0,
            "error": str(e),
        }
