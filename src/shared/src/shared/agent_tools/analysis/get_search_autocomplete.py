"""get_search_autocomplete tool — Google autocomplete suggestions.

Simple REST tool for keyword research. No API key required.
Fetches Google autocomplete suggestions to discover what people
are searching for related to a topic.
"""

from __future__ import annotations

import json

import httpx
from loguru import logger

GOOGLE_AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"


def _fetch_autocomplete(
    query: str,
    language: str = "vi",
    country: str = "vn",
) -> list[str]:
    """Fetch Google autocomplete suggestions.

    Args:
        query: Partial search query
        language: Language code (vi for Vietnamese)
        country: Country code (vn for Vietnam)

    Returns:
        List of autocomplete suggestion strings.
    """
    params = {
        "client": "firefox",
        "q": query,
        "hl": language,
        "gl": country,
    }
    try:
        response = httpx.get(
            GOOGLE_AUTOCOMPLETE_URL,
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        # Google returns Content-Type: charset=ISO-8859-1 but body is UTF-8
        data = json.loads(response.content.decode("utf-8"))
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            return [str(s) for s in data[1]]
        return []
    except Exception as e:
        logger.warning(f"Autocomplete request failed for '{query}': {e}")
        return []


def get_search_autocomplete(
    query: str,
    language: str = "vi",
    variants: list[str] | None = None,
) -> str:
    """Get Google autocomplete suggestions for keyword research.

    Reveals what people are actually searching for related to
    a topic. Useful for:
    - Discovering customer language and terminology
    - Finding popular search patterns in a category
    - Understanding what questions people ask about F&B topics

    Args:
        query: Base search query (e.g., "quán café specialty")
        language: Language — "vi" (Vietnamese, default), "en" (English)
        variants: Additional query prefixes to try
            (e.g., ["how to", "best", "why"]). Each generates
            separate autocomplete results.

    Returns:
        Autocomplete suggestions grouped by query variant.
    """
    all_suggestions: dict[str, list[str]] = {}

    # Step 1: Fetch for base query
    base_results = _fetch_autocomplete(query, language=language)
    all_suggestions[query] = base_results

    # Step 2: Fetch for each variant prefix
    if variants:
        for variant in variants:
            variant_query = f"{variant} {query}"
            results = _fetch_autocomplete(variant_query, language=language)
            all_suggestions[variant_query] = results

    # Step 3: Format output
    if not any(all_suggestions.values()):
        return f"No autocomplete suggestions found for '{query}'."

    lines = [f"## Autocomplete Suggestions for: {query}\n"]

    for variant_query, suggestions in all_suggestions.items():
        if variant_query == query:
            lines.append(f"### Base query: `{query}`")
        else:
            lines.append(f"### Variant: `{variant_query}`")

        if suggestions:
            for s in suggestions:
                lines.append(f"- {s}")
        else:
            lines.append("- _(no suggestions)_")
        lines.append("")

    total = sum(len(s) for s in all_suggestions.values())
    lines.append(f"**Total suggestions**: {total}")
    return "\n".join(lines)
