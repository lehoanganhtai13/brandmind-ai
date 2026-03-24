"""Unit tests for analysis tools (Task 40).

Pure function tests — no real HTTP calls to Google autocomplete.
Tests _fetch_autocomplete parsing/error handling and
get_search_autocomplete variant generation/formatting.
"""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest

# Force-import the MODULE (not the re-exported function) via sys.modules
from shared.agent_tools.analysis import get_search_autocomplete as _fn  # noqa: F401
_mod = sys.modules["shared.agent_tools.analysis.get_search_autocomplete"]


# ===== _fetch_autocomplete =====


class TestFetchAutocomplete:
    """Test _fetch_autocomplete with mocked httpx.get."""

    def _make_resp(self, json_data):
        resp = MagicMock()
        resp.content = json.dumps(json_data).encode("utf-8")
        resp.raise_for_status = MagicMock()
        return resp

    def test_successful_response(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(
            ["cafe da nang", ["cafe da nang ngon", "cafe da nang view dep"]]
        ))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)

        result = _mod._fetch_autocomplete("cafe da nang")
        assert result == ["cafe da nang ngon", "cafe da nang view dep"]
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == "cafe da nang"
        assert params["client"] == "firefox"

    def test_custom_language_and_country(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(["q", ["r1"]]))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)

        _mod._fetch_autocomplete("coffee", language="en", country="us")
        params = mock_get.call_args.kwargs["params"]
        assert params["hl"] == "en"
        assert params["gl"] == "us"

    def test_empty_suggestions(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(["xyz", []]))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("xyz") == []

    def test_malformed_response_no_list(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp("unexpected"))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("anything") == []

    def test_malformed_response_short_list(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(["only_one"]))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("anything") == []

    def test_malformed_second_element_not_list(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(["q", "str"]))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("anything") == []

    def test_http_error_returns_empty(self, monkeypatch):
        mock_get = MagicMock(side_effect=Exception("Connection refused"))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("cafe") == []

    def test_timeout_returns_empty(self, monkeypatch):
        mock_get = MagicMock(side_effect=httpx.TimeoutException("Timed out"))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("cafe") == []

    def test_suggestions_cast_to_strings(self, monkeypatch):
        mock_get = MagicMock(return_value=self._make_resp(
            ["q", [123, True, "normal"]]
        ))
        monkeypatch.setattr(_mod.httpx, "get", mock_get)
        assert _mod._fetch_autocomplete("q") == ["123", "True", "normal"]


# ===== get_search_autocomplete =====


class TestGetSearchAutocomplete:
    """Test get_search_autocomplete with mocked _fetch_autocomplete."""

    def test_base_query_only(self, monkeypatch):
        monkeypatch.setattr(
            _mod, "_fetch_autocomplete",
            lambda q, language="vi", country="vn": ["ngon", "dep"],
        )
        result = _mod.get_search_autocomplete("cafe da nang")
        assert "## Autocomplete Suggestions for: cafe da nang" in result
        assert "ngon" in result
        assert "**Total suggestions**: 2" in result

    def test_with_variants(self, monkeypatch):
        calls = []

        def mock(q, language="vi", country="vn"):
            calls.append(q)
            return {"cafe": ["ngon", "dep"], "best cafe": ["hcmc"], "top cafe": ["sg", "hn"]}.get(q, [])

        monkeypatch.setattr(_mod, "_fetch_autocomplete", mock)
        result = _mod.get_search_autocomplete("cafe", variants=["best", "top"])
        assert len(calls) == 3
        assert "ngon" in result
        assert "hcmc" in result
        assert "sg" in result
        assert "**Total suggestions**: 5" in result

    def test_no_suggestions_at_all(self, monkeypatch):
        monkeypatch.setattr(
            _mod, "_fetch_autocomplete",
            lambda q, language="vi", country="vn": [],
        )
        result = _mod.get_search_autocomplete("xyz", variants=["best"])
        assert "No autocomplete suggestions found" in result

    def test_partial_suggestions(self, monkeypatch):
        def mock(q, language="vi", country="vn"):
            return ["shop", "beans"] if q == "coffee" else []

        monkeypatch.setattr(_mod, "_fetch_autocomplete", mock)
        result = _mod.get_search_autocomplete("coffee", variants=["why"])
        assert "No autocomplete suggestions found" not in result
        assert "shop" in result
        assert "_(no suggestions)_" in result
        assert "**Total suggestions**: 2" in result

    def test_markdown_structure(self, monkeypatch):
        def mock(q, language="vi", country="vn"):
            return {"tea": ["tea shop"], "best tea": ["best tea brand"]}.get(q, [])

        monkeypatch.setattr(_mod, "_fetch_autocomplete", mock)
        result = _mod.get_search_autocomplete("tea", variants=["best"])
        assert "### Base query: `tea`" in result
        assert "### Variant: `best tea`" in result

    def test_language_passed_through(self, monkeypatch):
        langs = []

        def mock(q, language="vi", country="vn"):
            langs.append(language)
            return ["r"]

        monkeypatch.setattr(_mod, "_fetch_autocomplete", mock)
        _mod.get_search_autocomplete("coffee", language="en")
        assert all(l == "en" for l in langs)

    def test_empty_variants_list(self, monkeypatch):
        calls = []

        def mock(q, language="vi", country="vn"):
            calls.append(q)
            return ["sug"]

        monkeypatch.setattr(_mod, "_fetch_autocomplete", mock)
        result = _mod.get_search_autocomplete("cafe", variants=[])
        assert len(calls) == 1
        assert "**Total suggestions**: 1" in result
