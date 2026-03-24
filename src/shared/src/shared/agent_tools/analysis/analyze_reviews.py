"""analyze_reviews tool — Customer review sentiment analysis.

Aggregates reviews from Google Maps via search_places and analyzes
them using Gemini LLM for themes, sentiment, and unmet needs.
"""

from __future__ import annotations

import json

from loguru import logger

from config.system_config import SETTINGS
from prompts.brand_strategy.analyze_reviews import REVIEW_ANALYSIS_PROMPT
from shared.agent_tools.places.places_client import GooglePlacesClient
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)


def analyze_reviews(
    business_name: str | None = None,
    query: str | None = None,
    location: str | None = None,
    max_businesses: int = 5,
) -> str:
    """Analyze customer reviews to find sentiment patterns and insights.

    Aggregates reviews from Google Maps (via search_places) and
    analyzes them using LLM for themes, sentiment, and unmet needs.

    Use this tool during Phase 1 to understand:
    - What customers love/hate about competitors
    - Unmet needs in the market (opportunity areas)
    - Service quality patterns in the area

    Args:
        business_name: Specific business to analyze (exact name).
            If None, analyzes top businesses matching query.
        query: Search query for businesses (e.g., "specialty coffee").
            Required if business_name is None.
        location: Area to search (e.g., "District 1, HCMC")
        max_businesses: Max businesses to analyze (default 5)

    Returns:
        Structured review analysis with themes, sentiment, and insights.
        Error message string if analysis fails.
    """
    if not business_name and not query:
        return "Either business_name or query must be provided."

    api_key = SETTINGS.GOOGLE_PLACES_API_KEY
    if not api_key:
        return (
            "Google Places API key not configured. "
            "Please add GOOGLE_PLACES_API_KEY to your .env file."
        )

    # Step 1: Search businesses and collect reviews
    search_query = business_name or query or ""
    client = GooglePlacesClient(api_key=api_key)
    try:
        results = client.text_search(
            query=search_query,
            location=location,
            max_results=max_businesses,
        )
    except Exception as e:
        logger.error(f"Places search failed: {e}")
        return f"Failed to search places: {e}"

    if not results:
        return f"No results found for '{search_query}' in {location or 'any location'}."

    # Step 2: Fetch full reviews for each business
    all_reviews: list[dict[str, object]] = []
    for place in results:
        if place.place_id:
            try:
                detailed = client.get_place_details(place.place_id)
                for review in detailed.reviews:
                    all_reviews.append(
                        {
                            "business": detailed.name,
                            "rating": review.rating,
                            "text": review.text,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to get details for {place.name}: {e}")

    if not all_reviews:
        return f"No reviews found for '{search_query}' in {location or 'any location'}."

    # Step 3: LLM analysis
    def _stars(rating: object) -> str:
        return "★" * int(rating or 0)  # type: ignore[call-overload]

    reviews_text = "\n".join(
        f"[{r['business']}] ({_stars(r.get('rating'))}) {r['text']}"
        for r in all_reviews
    )

    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash-lite",
            api_key=SETTINGS.GEMINI_API_KEY,
            response_mime_type="application/json",
        )
    )

    prompt = REVIEW_ANALYSIS_PROMPT.replace("{{business_name}}", search_query).replace(
        "{{reviews_text}}", reviews_text[:15000]
    )

    try:
        result = llm.complete(prompt, temperature=0.2).text
        analysis = json.loads(result.strip())
    except Exception as e:
        logger.error(f"Review analysis LLM call failed: {e}")
        return f"Review analysis failed: {e}"

    # Step 4: Format output
    lines = [
        f"## Review Analysis: {search_query}",
        f"**Reviews analyzed**: {len(all_reviews)} from {len(results)} businesses",
        f"**Overall sentiment**: {analysis.get('overall_sentiment', 'N/A')}\n",
    ]

    if analysis.get("positive_themes"):
        lines.append("### Positive Themes")
        for theme in analysis["positive_themes"]:
            if isinstance(theme, dict):
                lines.append(
                    f"- **{theme.get('theme', '')}**: {theme.get('frequency', '')}"
                )
            else:
                lines.append(f"- {theme}")

    if analysis.get("negative_themes"):
        lines.append("\n### Negative Themes")
        for theme in analysis["negative_themes"]:
            if isinstance(theme, dict):
                lines.append(
                    f"- **{theme.get('theme', '')}**: {theme.get('frequency', '')}"
                )
            else:
                lines.append(f"- {theme}")

    if analysis.get("unmet_needs"):
        lines.append("\n### Unmet Needs (Opportunities)")
        for need in analysis["unmet_needs"]:
            lines.append(f"- {need}")

    if analysis.get("key_quotes"):
        lines.append("\n### Key Quotes")
        for quote in analysis["key_quotes"][:5]:
            lines.append(f"> {quote}")

    return "\n".join(lines)
