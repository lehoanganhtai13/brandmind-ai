"""search_places tool — Google Places API for local market research.

Plain function callable by the agent via create_agent(). Follows
codebase convention: search_web and scrape_web_content are both plain
functions, create_agent() accepts them directly.
"""

from __future__ import annotations

from loguru import logger

from config.system_config import SETTINGS
from shared.agent_tools.places.formatter import format_places_markdown
from shared.agent_tools.places.places_client import GooglePlacesClient


def search_places(
    query: str,
    location: str | None = None,
    radius_meters: int = 5000,
    max_results: int = 20,
) -> str:
    """Search for local businesses using Google Places API.

    Use this tool to find competitors, map the local F&B market,
    and understand the competitive landscape in a specific area.
    Returns business details including name, address, rating,
    reviews, pricing level, and opening hours.

    Best for: local competitor mapping, finding nearby businesses,
    getting review data for F&B establishments.

    Args:
        query: Search query (e.g., "specialty coffee shop",
            "quán cà phê đặc sản").
        location: Location center for search
            (e.g., "District 1, Ho Chi Minh City").
        radius_meters: Search radius in meters (default 5000 = 5km).
        max_results: Maximum number of results (default 20, max 20).

    Returns:
        Formatted markdown with business details: name, address,
        rating, review count, price level, reviews summary.
        Returns error message string if API call fails.
    """
    api_key = SETTINGS.GOOGLE_PLACES_API_KEY
    if not api_key:
        return (
            "Google Places API key not configured. "
            "Please add GOOGLE_PLACES_API_KEY to your .env file."
        )

    try:
        client = GooglePlacesClient(api_key=api_key)
        results = client.text_search(
            query=query,
            location=location,
            radius_meters=radius_meters,
            max_results=max_results,
        )

        if not results:
            return f"No results found for '{query}' in {location or 'any location'}."

        return format_places_markdown(results, query, location)

    except Exception as e:
        logger.error(f"search_places failed: {e}")
        return f"Places search failed: {e}"
