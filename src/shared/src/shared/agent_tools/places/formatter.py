"""Markdown formatter for Google Places search results.

Converts PlaceResult list into agent-readable markdown with
structured sections per place: name, rating, address, price,
reviews summary, and service options.
"""

from __future__ import annotations

from .places_client import PlaceResult

# Price level mapping from Google Places API enum to display text
_PRICE_LEVEL_MAP: dict[str, str] = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}

# Maximum review text length before truncation
_MAX_REVIEW_LENGTH = 200

# Maximum reviews to show per place
_MAX_REVIEWS_PER_PLACE = 3


def _rating_stars(rating: float | None) -> str:
    """Convert numeric rating to star display.

    Args:
        rating: Rating value (0-5) or None.

    Returns:
        Star string like "★★★★☆ 4.2" or "No rating".
    """
    if rating is None:
        return "No rating"
    full = int(rating)
    empty = 5 - full
    return f"{'★' * full}{'☆' * empty} {rating:.1f}"


def _format_services(place: PlaceResult) -> str:
    """Format service options (dine-in, delivery, takeout).

    Args:
        place: PlaceResult with service flags.

    Returns:
        Comma-separated service string or empty string.
    """
    services = []
    if place.dine_in:
        services.append("Dine-in")
    if place.delivery:
        services.append("Delivery")
    if place.takeout:
        services.append("Takeout")
    return ", ".join(services)


def _format_single_place(place: PlaceResult, index: int) -> str:
    """Format a single PlaceResult into markdown.

    Args:
        place: PlaceResult to format.
        index: 1-based index for numbering.

    Returns:
        Markdown-formatted string for one place.
    """
    lines: list[str] = []

    # Header with name and rating
    stars = _rating_stars(place.rating)
    lines.append(f"### {index}. {place.name}")
    lines.append(f"**Rating**: {stars} ({place.review_count} reviews)")

    # Address
    if place.address:
        lines.append(f"**Address**: {place.address}")

    # Price level
    if place.price_level:
        display = _PRICE_LEVEL_MAP.get(place.price_level, place.price_level)
        lines.append(f"**Price**: {display}")

    # Services
    services = _format_services(place)
    if services:
        lines.append(f"**Services**: {services}")

    # Website and phone
    if place.website:
        lines.append(f"**Website**: {place.website}")
    if place.phone:
        lines.append(f"**Phone**: {place.phone}")

    # Google Maps link
    if place.google_maps_url:
        lines.append(f"**Google Maps**: {place.google_maps_url}")

    # Types/categories
    if place.types:
        display_types = [t.replace("_", " ") for t in place.types[:5]]
        lines.append(f"**Categories**: {', '.join(display_types)}")

    # Reviews
    if place.reviews:
        lines.append("")
        lines.append("**Top Reviews**:")
        for review in place.reviews[:_MAX_REVIEWS_PER_PLACE]:
            text = review.text
            if len(text) > _MAX_REVIEW_LENGTH:
                text = text[:_MAX_REVIEW_LENGTH] + "..."
            rating_str = f"{'★' * review.rating}" if review.rating else ""
            author = review.author or "Anonymous"
            time_str = f" ({review.relative_time})" if review.relative_time else ""
            lines.append(f"- {rating_str} **{author}**{time_str}: {text}")

    return "\n".join(lines)


def format_places_markdown(
    results: list[PlaceResult],
    query: str,
    location: str | None = None,
) -> str:
    """Format PlaceResult list into agent-readable markdown.

    Args:
        results: List of PlaceResult from Google Places API.
        query: Original search query.
        location: Location used for the search.

    Returns:
        Complete markdown document with all results.
    """
    loc_str = f" in {location}" if location else ""
    lines: list[str] = [
        f'## Local Business Search: "{query}"{loc_str}',
        f"Found **{len(results)}** result(s).",
        "",
    ]

    for i, place in enumerate(results, 1):
        lines.append(_format_single_place(place, i))
        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary statistics
    rated = [p for p in results if p.rating is not None]
    if rated:
        avg_rating = sum(p.rating for p in rated if p.rating) / len(rated)
        total_reviews = sum(p.review_count for p in results)
        lines.append(
            f"**Summary**: {len(results)} places found, "
            f"average rating {avg_rating:.1f}/5, "
            f"{total_reviews} total reviews"
        )

    return "\n".join(lines)
