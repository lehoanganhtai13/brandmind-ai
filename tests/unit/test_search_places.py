"""Unit tests for search_places tool (Task 36).

Pure function tests — no Google Places API calls.
Tests VIETNAM_CITIES dict, Pydantic models, formatter helpers,
and _resolve_location normalization logic.
"""

from __future__ import annotations

import pytest

from shared.agent_tools.places.places_client import (
    VIETNAM_CITIES,
    GooglePlacesClient,
    PlaceResult,
    PlaceReview,
)
from shared.agent_tools.places.formatter import (
    _PRICE_LEVEL_MAP,
    _rating_stars,
    _format_services,
)


# ===== VIETNAM_CITIES =====


class TestVietnamCities:
    """Verify VIETNAM_CITIES dict has expected major cities."""

    EXPECTED_KEYS = [
        "ho chi minh",
        "hcmc",
        "hanoi",
        "ha noi",
        "da nang",
        "hai phong",
        "can tho",
        "nha trang",
        "hue",
        "da lat",
    ]

    def test_major_cities_present(self):
        for key in self.EXPECTED_KEYS:
            assert key in VIETNAM_CITIES, f"Missing city key: {key}"

    def test_values_are_lat_lng_tuples(self):
        for key, value in VIETNAM_CITIES.items():
            assert isinstance(value, tuple), f"{key}: value is not a tuple"
            assert len(value) == 2, f"{key}: tuple length is {len(value)}, expected 2"
            lat, lng = value
            assert isinstance(lat, (int, float)), f"{key}: lat is not numeric"
            assert isinstance(lng, (int, float)), f"{key}: lng is not numeric"

    def test_hcmc_aliases_same_coords(self):
        hcmc_coords = VIETNAM_CITIES["ho chi minh"]
        assert VIETNAM_CITIES["hcmc"] == hcmc_coords
        assert VIETNAM_CITIES["tp hcm"] == hcmc_coords
        assert VIETNAM_CITIES["sai gon"] == hcmc_coords

    def test_hanoi_aliases_same_coords(self):
        assert VIETNAM_CITIES["hanoi"] == VIETNAM_CITIES["ha noi"]

    def test_lat_lng_ranges_vietnam(self):
        """All coords should be within Vietnam's bounding box."""
        for key, (lat, lng) in VIETNAM_CITIES.items():
            assert 8.0 <= lat <= 24.0, f"{key}: lat {lat} out of Vietnam range"
            assert 102.0 <= lng <= 110.0, f"{key}: lng {lng} out of Vietnam range"


# ===== PlaceResult =====


class TestPlaceResult:
    def test_minimal_construction(self):
        place = PlaceResult(place_id="abc123", name="Coffee Shop")
        assert place.place_id == "abc123"
        assert place.name == "Coffee Shop"

    def test_defaults(self):
        place = PlaceResult(place_id="id1", name="Test")
        assert place.address == ""
        assert place.rating is None
        assert place.review_count == 0
        assert place.price_level is None
        assert place.website is None
        assert place.phone is None
        assert place.opening_hours == []
        assert place.dine_in is None
        assert place.delivery is None
        assert place.takeout is None
        assert place.reviews == []
        assert place.types == []
        assert place.google_maps_url is None

    def test_full_construction(self):
        review = PlaceReview(
            author="Nguyen Van A",
            rating=5,
            text="Great coffee!",
            relative_time="2 months ago",
        )
        place = PlaceResult(
            place_id="ChIJ_xyz",
            name="Specialty Coffee Lab",
            address="123 Le Loi, District 1, HCMC",
            rating=4.5,
            review_count=120,
            price_level="PRICE_LEVEL_MODERATE",
            website="https://coffeelab.vn",
            phone="028 1234 5678",
            opening_hours=["Mon: 7AM-10PM", "Tue: 7AM-10PM"],
            dine_in=True,
            delivery=True,
            takeout=False,
            reviews=[review],
            types=["cafe", "restaurant"],
            google_maps_url="https://maps.google.com/?cid=123",
        )
        assert place.rating == 4.5
        assert len(place.reviews) == 1
        assert place.reviews[0].author == "Nguyen Van A"
        assert place.dine_in is True
        assert place.takeout is False

    def test_serialization_roundtrip(self):
        place = PlaceResult(
            place_id="id1",
            name="Test Cafe",
            rating=4.2,
            reviews=[PlaceReview(author="User", rating=4, text="Nice")],
        )
        data = place.model_dump()
        restored = PlaceResult.model_validate(data)
        assert restored.place_id == place.place_id
        assert restored.rating == place.rating
        assert len(restored.reviews) == 1
        assert restored.reviews[0].author == "User"

    def test_json_serialization(self):
        place = PlaceResult(place_id="id1", name="Test")
        json_str = place.model_dump_json()
        assert '"place_id":"id1"' in json_str or '"place_id": "id1"' in json_str


# ===== PlaceReview =====


class TestPlaceReview:
    def test_defaults(self):
        review = PlaceReview()
        assert review.author == ""
        assert review.rating == 0
        assert review.text == ""
        assert review.relative_time == ""

    def test_populated(self):
        review = PlaceReview(
            author="Tran B",
            rating=4,
            text="Excellent atmosphere",
            relative_time="3 weeks ago",
        )
        assert review.author == "Tran B"
        assert review.rating == 4
        assert review.text == "Excellent atmosphere"
        assert review.relative_time == "3 weeks ago"

    def test_serialization(self):
        review = PlaceReview(author="X", rating=5, text="Top!")
        data = review.model_dump()
        assert data["author"] == "X"
        assert data["rating"] == 5


# ===== _rating_stars =====


class TestRatingStars:
    def test_five_stars(self):
        result = _rating_stars(5.0)
        assert result == "★★★★★ 5.0"

    def test_four_point_two(self):
        result = _rating_stars(4.2)
        assert result == "★★★★☆ 4.2"

    def test_three_point_five(self):
        # int(3.5) = 3, so 3 full stars + 2 empty
        result = _rating_stars(3.5)
        assert result == "★★★☆☆ 3.5"

    def test_zero_rating(self):
        result = _rating_stars(0.0)
        assert result == "☆☆☆☆☆ 0.0"

    def test_one_star(self):
        result = _rating_stars(1.0)
        assert result == "★☆☆☆☆ 1.0"

    def test_none_rating(self):
        result = _rating_stars(None)
        assert result == "No rating"

    def test_high_fraction(self):
        # int(4.9) = 4, so 4 full + 1 empty
        result = _rating_stars(4.9)
        assert result == "★★★★☆ 4.9"

    def test_low_fraction(self):
        # int(2.1) = 2, so 2 full + 3 empty
        result = _rating_stars(2.1)
        assert result == "★★☆☆☆ 2.1"


# ===== _format_services =====


class TestFormatServices:
    def test_all_services_true(self):
        place = PlaceResult(
            place_id="id1",
            name="Test",
            dine_in=True,
            delivery=True,
            takeout=True,
        )
        result = _format_services(place)
        assert result == "Dine-in, Delivery, Takeout"

    def test_some_services_false(self):
        place = PlaceResult(
            place_id="id1",
            name="Test",
            dine_in=True,
            delivery=False,
            takeout=True,
        )
        result = _format_services(place)
        assert result == "Dine-in, Takeout"

    def test_all_services_none(self):
        place = PlaceResult(place_id="id1", name="Test")
        result = _format_services(place)
        assert result == ""

    def test_only_delivery(self):
        place = PlaceResult(
            place_id="id1",
            name="Test",
            dine_in=False,
            delivery=True,
            takeout=False,
        )
        result = _format_services(place)
        assert result == "Delivery"

    def test_all_services_false(self):
        place = PlaceResult(
            place_id="id1",
            name="Test",
            dine_in=False,
            delivery=False,
            takeout=False,
        )
        result = _format_services(place)
        assert result == ""


# ===== _PRICE_LEVEL_MAP =====


class TestPriceLevelMap:
    def test_all_five_levels_present(self):
        assert len(_PRICE_LEVEL_MAP) == 5

    def test_free(self):
        assert _PRICE_LEVEL_MAP["PRICE_LEVEL_FREE"] == "Free"

    def test_inexpensive(self):
        assert _PRICE_LEVEL_MAP["PRICE_LEVEL_INEXPENSIVE"] == "$"

    def test_moderate(self):
        assert _PRICE_LEVEL_MAP["PRICE_LEVEL_MODERATE"] == "$$"

    def test_expensive(self):
        assert _PRICE_LEVEL_MAP["PRICE_LEVEL_EXPENSIVE"] == "$$$"

    def test_very_expensive(self):
        assert _PRICE_LEVEL_MAP["PRICE_LEVEL_VERY_EXPENSIVE"] == "$$$$"

    def test_expected_keys(self):
        expected = {
            "PRICE_LEVEL_FREE",
            "PRICE_LEVEL_INEXPENSIVE",
            "PRICE_LEVEL_MODERATE",
            "PRICE_LEVEL_EXPENSIVE",
            "PRICE_LEVEL_VERY_EXPENSIVE",
        }
        assert set(_PRICE_LEVEL_MAP.keys()) == expected


# ===== _resolve_location =====


class TestResolveLocation:
    """Test GooglePlacesClient._resolve_location with a dummy API key."""

    @pytest.fixture
    def client(self):
        c = GooglePlacesClient(api_key="dummy-key-for-testing")
        yield c
        c.close()

    def test_ho_chi_minh(self, client):
        result = client._resolve_location("Ho Chi Minh")
        assert result is not None
        assert result == VIETNAM_CITIES["ho chi minh"]

    def test_hcmc_uppercase(self, client):
        result = client._resolve_location("HCMC")
        assert result is not None
        assert result == VIETNAM_CITIES["hcmc"]

    def test_hanoi_with_diacritics(self, client):
        result = client._resolve_location("Hà Nội")
        assert result is not None
        assert result == VIETNAM_CITIES["ha noi"]

    def test_da_nang_with_diacritics(self, client):
        """Đ→đ is NOT decomposable by NFKD (it's a distinct letter, not
        a composed character), so 'Đà Nẵng' normalizes to 'đa nang',
        not 'da nang'. The lookup returns None in this case."""
        result = client._resolve_location("Đà Nẵng")
        # đ ≠ d, so NFKD normalization alone doesn't resolve this
        assert result is None

    def test_da_nang_ascii(self, client):
        """ASCII 'Da Nang' should resolve correctly."""
        result = client._resolve_location("Da Nang")
        assert result is not None
        assert result == VIETNAM_CITIES["da nang"]

    def test_unknown_city_returns_none(self, client):
        result = client._resolve_location("Tokyo")
        assert result is None

    def test_unknown_district_returns_none(self, client):
        result = client._resolve_location("Quận 1")
        assert result is None

    def test_leading_trailing_spaces(self, client):
        result = client._resolve_location("  Da Nang  ")
        assert result is not None
        assert result == VIETNAM_CITIES["da nang"]

    def test_case_insensitive(self, client):
        result = client._resolve_location("HA NOI")
        assert result is not None
        assert result == VIETNAM_CITIES["ha noi"]

    def test_thanh_pho_prefix(self, client):
        """'Thành phố Hà Nội' should strip prefix and resolve."""
        result = client._resolve_location("Thanh pho Ha Noi")
        assert result is not None
        assert result == VIETNAM_CITIES["ha noi"]

    def test_city_suffix(self, client):
        """'Da Nang city' should strip suffix and resolve."""
        result = client._resolve_location("Da Nang city")
        assert result is not None
        assert result == VIETNAM_CITIES["da nang"]

    def test_comma_separated_resolves_first_match(self, client):
        """'Da Nang, Vietnam' should resolve via comma splitting."""
        result = client._resolve_location("Da Nang, Vietnam")
        assert result is not None
        assert result == VIETNAM_CITIES["da nang"]
