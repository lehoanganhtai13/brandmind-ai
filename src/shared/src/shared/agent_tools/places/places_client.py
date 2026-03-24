"""Google Places API (New) REST client.

Implements Text Search and Place Details endpoints optimized for
F&B competitive landscape mapping. Uses sync httpx client to match
codebase tool convention (search_web, scrape_web_content are sync).

FieldMask includes places.reviews (Pro SKU, $0.035/req) — a single
Pro request is cheaper than Basic + N x Place Details calls.
"""

from __future__ import annotations

import unicodedata

import httpx
from loguru import logger
from pydantic import BaseModel, Field


class PlaceReview(BaseModel):
    """A single user review for a place."""

    author: str = ""
    rating: int = 0
    text: str = ""
    relative_time: str = ""


class PlaceResult(BaseModel):
    """Structured result for a single place from Google Places API."""

    place_id: str
    name: str
    address: str = ""
    rating: float | None = None
    review_count: int = 0
    price_level: str | None = None
    website: str | None = None
    phone: str | None = None
    opening_hours: list[str] = Field(default_factory=list)
    dine_in: bool | None = None
    delivery: bool | None = None
    takeout: bool | None = None
    reviews: list[PlaceReview] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)
    google_maps_url: str | None = None


# Major Vietnamese city coordinates for locationBias optimization.
# City-level only — districts/wards are NOT hardcoded here.
# When location is a district (e.g., "Quận 1"), _resolve_location
# returns None → text_search appends location to query text instead.
# Google Places API understands "coffee Quận 1 HCMC" natively.
#
# Keys: normalized lowercase, no diacritics. Multiple aliases per city.
VIETNAM_CITIES: dict[str, tuple[float, float]] = {
    # Ho Chi Minh City
    "ho chi minh": (10.7769, 106.7009),
    "hcmc": (10.7769, 106.7009),
    "tp hcm": (10.7769, 106.7009),
    "sai gon": (10.7769, 106.7009),
    # Hanoi
    "hanoi": (21.0285, 105.8542),
    "ha noi": (21.0285, 105.8542),
    # Major cities
    "da nang": (16.0544, 108.2022),
    "hai phong": (20.8449, 106.6881),
    "can tho": (10.0452, 105.7469),
    "nha trang": (12.2451, 109.1943),
    "hue": (16.4637, 107.5909),
    "vung tau": (10.3460, 107.0843),
    "da lat": (11.9465, 108.4419),
    "quy nhon": (13.7830, 109.2197),
    "buon ma thuot": (12.6680, 108.0378),
    "phu quoc": (10.2899, 103.9840),
    "bien hoa": (10.9574, 106.8426),
    "thu dau mot": (11.0036, 106.6520),
    "long xuyen": (10.3860, 105.4350),
    "rach gia": (10.0125, 105.0809),
    "ha long": (20.9517, 107.0845),
}


class GooglePlacesClient:
    """Sync REST client for Google Places API (New).

    Implements Text Search endpoint to find local businesses by query
    and location. Optimized for F&B competitive landscape mapping
    with FieldMask to minimize cost per request.

    Attributes:
        _api_key: Google Cloud API key with Places API enabled.
        _client: Sync httpx client instance.
    """

    FIELD_MASK = ",".join(
        [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.rating",
            "places.userRatingCount",
            "places.priceLevel",
            "places.reviews",
            "places.regularOpeningHours",
            "places.websiteUri",
            "places.nationalPhoneNumber",
            "places.delivery",
            "places.dineIn",
            "places.takeout",
            "places.types",
            "places.googleMapsUri",
        ]
    )

    def __init__(self, api_key: str) -> None:
        """Initialize with Google Cloud API key.

        Args:
            api_key: Google Cloud API key with Places API enabled.
        """
        self._api_key = api_key
        self._client = httpx.Client(timeout=30.0)

    def text_search(
        self,
        query: str,
        location: str | None = None,
        radius_meters: int = 5000,
        max_results: int = 20,
        language: str = "vi",
    ) -> list[PlaceResult]:
        """Search for places via Google Places Text Search API.

        If location resolves to coordinates, uses locationBias.
        Otherwise appends location text to query for natural matching.

        Args:
            query: Search text (e.g., "specialty coffee shop").
            location: Location name (e.g., "Da Nang", "Quận 1 HCMC").
            radius_meters: Search radius in meters (default 5km).
            max_results: Maximum results (max 20).
            language: Language code (default "vi").

        Returns:
            List of PlaceResult with business details.

        Raises:
            httpx.HTTPStatusError: If API returns non-2xx status.
        """
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": self.FIELD_MASK,
        }

        body: dict = {
            "textQuery": query,
            "maxResultCount": max(1, min(max_results, 20)),
            "languageCode": language,
        }

        if location:
            coords = self._resolve_location(location)
            if coords:
                body["locationBias"] = {
                    "circle": {
                        "center": {
                            "latitude": coords[0],
                            "longitude": coords[1],
                        },
                        "radius": float(radius_meters),
                    }
                }
            else:
                body["textQuery"] = f"{query} {location}"

        response = self._client.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()
        places_raw = data.get("places", [])
        return [self._parse_place(p) for p in places_raw]

    def get_place_details(
        self,
        place_id: str,
        language: str = "vi",
    ) -> PlaceResult:
        """Fetch full details for a single place by place_id.

        Use for on-demand enrichment when you need complete data for
        a specific business (e.g., analyze_reviews for one competitor).
        NOT needed for general search — text_search() already includes
        reviews in its FIELD_MASK.

        Args:
            place_id: Google Place ID (from text_search results).
            language: Language code (default "vi").

        Returns:
            PlaceResult with full detail data.

        Raises:
            httpx.HTTPStatusError: If API returns non-2xx status.
        """
        detail_mask = ",".join(
            [
                "id",
                "displayName",
                "formattedAddress",
                "rating",
                "userRatingCount",
                "priceLevel",
                "reviews",
                "currentOpeningHours",
                "websiteUri",
                "nationalPhoneNumber",
                "delivery",
                "dineIn",
                "takeout",
                "types",
                "googleMapsUri",
            ]
        )
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": detail_mask,
        }
        params = {"languageCode": language}

        response = self._client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return self._parse_place(response.json())

    def _resolve_location(self, location: str) -> tuple[float, float] | None:
        """Resolve location name to lat/lng via VIETNAM_CITIES lookup.

        Normalizes input (lowercase, strip diacritics) then checks dict.
        Returns None if not found — caller appends location to query text.

        Args:
            location: Location name (e.g., "Da Nang", "HCMC").

        Returns:
            (lat, lng) tuple or None if not in VIETNAM_CITIES.
        """
        normalized = location.lower().strip()
        nfkd = unicodedata.normalize("NFKD", normalized)
        ascii_key = "".join(c for c in nfkd if not unicodedata.combining(c))

        if ascii_key in VIETNAM_CITIES:
            return VIETNAM_CITIES[ascii_key]

        for prefix in ("thanh pho ", "tp ", "city of "):
            stripped = ascii_key.removeprefix(prefix)
            if stripped in VIETNAM_CITIES:
                return VIETNAM_CITIES[stripped]

        for suffix in (" city", " province"):
            stripped = ascii_key.removesuffix(suffix)
            if stripped in VIETNAM_CITIES:
                return VIETNAM_CITIES[stripped]

        if "," in ascii_key:
            for segment in ascii_key.split(","):
                segment = segment.strip()
                if segment in VIETNAM_CITIES:
                    return VIETNAM_CITIES[segment]

        return None

    def _parse_place(self, raw: dict) -> PlaceResult:
        """Parse a single place from API response JSON.

        Args:
            raw: Raw place dict from Google Places API response.

        Returns:
            Parsed PlaceResult model.
        """
        reviews = []
        for r in raw.get("reviews", []):
            reviews.append(
                PlaceReview(
                    author=r.get("authorAttribution", {}).get("displayName", ""),
                    rating=r.get("rating", 0),
                    text=r.get("text", {}).get("text", ""),
                    relative_time=r.get("relativePublishTimeDescription", ""),
                )
            )

        hours_data = (
            raw.get("regularOpeningHours") or raw.get("currentOpeningHours") or {}
        )
        hours: list[str] = hours_data.get("weekdayDescriptions", [])

        return PlaceResult(
            place_id=raw.get("id", ""),
            name=raw.get("displayName", {}).get("text", ""),
            address=raw.get("formattedAddress", ""),
            rating=raw.get("rating"),
            review_count=raw.get("userRatingCount", 0),
            price_level=raw.get("priceLevel"),
            website=raw.get("websiteUri"),
            phone=raw.get("nationalPhoneNumber"),
            opening_hours=hours,
            dine_in=raw.get("dineIn"),
            delivery=raw.get("delivery"),
            takeout=raw.get("takeout"),
            reviews=reviews,
            types=raw.get("types", []),
            google_maps_url=raw.get("googleMapsUri"),
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
        logger.debug("GooglePlacesClient closed")
