"""Unit tests for deep_research tool — pure functions and config only.

Tests cover DEPTH_CONFIG validation, URL ranking/deduplication,
search snippet formatting, and crawled content formatting.
No external API calls are made.
"""

from __future__ import annotations

import pytest

from shared.agent_tools.research.deep_research import (
    DEPTH_CONFIG,
    _format_crawled_content,
    _format_search_snippets,
    _rank_and_deduplicate_urls,
)


# =========================================================================
# Helpers
# =========================================================================


def _make_search_results(
    results_by_query: dict[str, list[dict[str, str]]],
) -> dict[str, dict]:
    """Build a search_results dict matching search_web() output shape."""
    queries = {}
    for query_key, results in results_by_query.items():
        queries[query_key] = {"results": results}
    return {"queries": queries}


# =========================================================================
# DEPTH_CONFIG
# =========================================================================


class TestDepthConfig:
    """Validate the three depth profiles exist and have sensible values."""

    EXPECTED_PROFILES = ("quick", "standard", "comprehensive")
    REQUIRED_KEYS = ("num_queries", "crawl_top_n", "max_chars_per_page")

    def test_three_profiles_exist(self):
        for profile in self.EXPECTED_PROFILES:
            assert profile in DEPTH_CONFIG, f"Missing profile: {profile}"
        assert len(DEPTH_CONFIG) == 3

    @pytest.mark.parametrize("profile", EXPECTED_PROFILES)
    def test_required_keys_present(self, profile: str):
        cfg = DEPTH_CONFIG[profile]
        for key in self.REQUIRED_KEYS:
            assert key in cfg, f"{profile} missing key: {key}"

    @pytest.mark.parametrize("profile", EXPECTED_PROFILES)
    def test_values_are_positive_ints(self, profile: str):
        cfg = DEPTH_CONFIG[profile]
        for key in self.REQUIRED_KEYS:
            val = cfg[key]
            assert isinstance(val, int), f"{profile}.{key} is not int"
            assert val > 0, f"{profile}.{key} must be positive"

    def test_num_queries_at_most_5(self):
        """search_web enforces MAX_QUERIES=5; comprehensive must not exceed it."""
        for profile, cfg in DEPTH_CONFIG.items():
            assert cfg["num_queries"] <= 5, (
                f"{profile}.num_queries={cfg['num_queries']} exceeds MAX_QUERIES=5"
            )

    def test_profiles_are_ordered_by_intensity(self):
        """quick < standard < comprehensive for every numeric parameter."""
        q = DEPTH_CONFIG["quick"]
        s = DEPTH_CONFIG["standard"]
        c = DEPTH_CONFIG["comprehensive"]
        for key in self.REQUIRED_KEYS:
            assert q[key] < s[key] < c[key], (
                f"Expected quick < standard < comprehensive for {key}, "
                f"got {q[key]}, {s[key]}, {c[key]}"
            )

    def test_max_chars_per_page_reasonable_range(self):
        for profile, cfg in DEPTH_CONFIG.items():
            chars = cfg["max_chars_per_page"]
            assert 1000 <= chars <= 20000, (
                f"{profile}.max_chars_per_page={chars} outside [1000, 20000]"
            )


# =========================================================================
# _rank_and_deduplicate_urls
# =========================================================================


class TestRankAndDeduplicateUrls:
    """Tests for URL deduplication and keyword-based ranking."""

    def test_deduplicates_by_domain(self):
        """Second URL from the same domain should be dropped."""
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://example.com/page1",
                        "title": "Page 1",
                        "snippet": "first",
                    },
                    {
                        "url": "https://example.com/page2",
                        "title": "Page 2",
                        "snippet": "second from same domain",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=10)
        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/page1"

    def test_different_domains_kept(self):
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://alpha.com/a",
                        "title": "Alpha",
                        "snippet": "alpha content",
                    },
                    {
                        "url": "https://beta.com/b",
                        "title": "Beta",
                        "snippet": "beta content",
                    },
                    {
                        "url": "https://gamma.com/c",
                        "title": "Gamma",
                        "snippet": "gamma content",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=10)
        assert len(result) == 3

    def test_ranking_by_keyword_match(self):
        """URLs whose snippets contain more topic keywords rank higher."""
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://low.com/page",
                        "title": "Low",
                        "snippet": "unrelated content here",
                    },
                    {
                        "url": "https://high.com/page",
                        "title": "High",
                        "snippet": "coffee market trends in Vietnam 2026",
                    },
                    {
                        "url": "https://mid.com/page",
                        "title": "Mid",
                        "snippet": "coffee beans roasting tips",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(
            search_results, topic="coffee market Vietnam", top_n=10
        )
        # "high" snippet matches "coffee", "market", "vietnam" (3 words >3 chars)
        # "mid" snippet matches "coffee" (1 word)
        # "low" snippet matches nothing
        assert result[0]["url"] == "https://high.com/page"
        assert result[-1]["url"] == "https://low.com/page"

    def test_top_n_limits_output(self):
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": f"https://site{i}.com/page",
                        "title": f"Site {i}",
                        "snippet": "content",
                    }
                    for i in range(10)
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=3)
        assert len(result) == 3

    def test_empty_search_results(self):
        search_results: dict = {"queries": {}}
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=5)
        assert result == []

    def test_skips_results_without_url(self):
        search_results = _make_search_results(
            {
                "q1": [
                    {"url": "", "title": "No URL", "snippet": "content"},
                    {
                        "url": "https://valid.com/page",
                        "title": "Valid",
                        "snippet": "content",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=10)
        assert len(result) == 1
        assert result[0]["url"] == "https://valid.com/page"

    def test_output_keys(self):
        """Each result dict should contain exactly url, title, snippet (no score)."""
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://example.com/page",
                        "title": "Example",
                        "snippet": "content",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=10)
        assert len(result) == 1
        assert set(result[0].keys()) == {"url", "title", "snippet"}

    def test_short_topic_words_ignored(self):
        """Words with 3 or fewer characters should not count for scoring."""
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://a.com/page",
                        "title": "A",
                        "snippet": "the and for but not matching",
                    },
                    {
                        "url": "https://b.com/page",
                        "title": "B",
                        "snippet": "branding strategy overview",
                    },
                ],
            }
        )
        # Topic has only short words (<=3 chars) plus "branding"
        result = _rank_and_deduplicate_urls(
            search_results, topic="the art of branding", top_n=10
        )
        # "branding" (8 chars) matches snippet B; "art" (3 chars) is filtered out
        assert result[0]["url"] == "https://b.com/page"

    def test_dedup_across_multiple_queries(self):
        """Same domain appearing in different queries should still be deduped."""
        search_results = _make_search_results(
            {
                "q1": [
                    {
                        "url": "https://example.com/page1",
                        "title": "Page 1",
                        "snippet": "first query",
                    },
                ],
                "q2": [
                    {
                        "url": "https://example.com/page2",
                        "title": "Page 2",
                        "snippet": "second query",
                    },
                ],
            }
        )
        result = _rank_and_deduplicate_urls(search_results, topic="test", top_n=10)
        assert len(result) == 1


# =========================================================================
# _format_search_snippets
# =========================================================================


class TestFormatSearchSnippets:
    """Tests for markdown formatting of search results."""

    def test_single_query_single_result(self):
        search_results = _make_search_results(
            {
                "coffee trends": [
                    {
                        "url": "https://example.com",
                        "title": "Coffee Trends",
                        "snippet": "Vietnam coffee is growing",
                    },
                ],
            }
        )
        output = _format_search_snippets(search_results)
        assert "### Query: coffee trends" in output
        assert "[Coffee Trends](https://example.com)" in output
        assert "Vietnam coffee is growing" in output

    def test_multiple_queries(self):
        search_results = _make_search_results(
            {
                "query alpha": [
                    {
                        "url": "https://a.com",
                        "title": "A",
                        "snippet": "alpha snippet",
                    },
                ],
                "query beta": [
                    {
                        "url": "https://b.com",
                        "title": "B",
                        "snippet": "beta snippet",
                    },
                ],
            }
        )
        output = _format_search_snippets(search_results)
        assert "### Query: query alpha" in output
        assert "### Query: query beta" in output

    def test_empty_results(self):
        search_results: dict = {"queries": {}}
        output = _format_search_snippets(search_results)
        assert output == ""

    def test_result_format_is_markdown_list(self):
        search_results = _make_search_results(
            {
                "q": [
                    {
                        "url": "https://x.com",
                        "title": "Title",
                        "snippet": "Snippet",
                    },
                ],
            }
        )
        output = _format_search_snippets(search_results)
        assert "- [Title](https://x.com): Snippet" in output

    def test_multiple_results_under_one_query(self):
        search_results = _make_search_results(
            {
                "q": [
                    {
                        "url": "https://a.com",
                        "title": "A",
                        "snippet": "snap A",
                    },
                    {
                        "url": "https://b.com",
                        "title": "B",
                        "snippet": "snap B",
                    },
                ],
            }
        )
        output = _format_search_snippets(search_results)
        assert "- [A](https://a.com): snap A" in output
        assert "- [B](https://b.com): snap B" in output


# =========================================================================
# _format_crawled_content
# =========================================================================


class TestFormatCrawledContent:
    """Tests for formatting crawled pages with source labels."""

    def test_empty_pages_returns_fallback(self):
        output = _format_crawled_content([])
        assert output == "(No pages were crawled successfully)"

    def test_single_page_formatting(self):
        pages = [
            {
                "url": "https://example.com/article",
                "title": "Great Article",
                "content": "This is the article content.",
            }
        ]
        output = _format_crawled_content(pages)
        assert "--- Source [1]: Great Article ---" in output
        assert "URL: https://example.com/article" in output
        assert "This is the article content." in output

    def test_multiple_pages_numbered(self):
        pages = [
            {"url": "https://a.com", "title": "First", "content": "Content A"},
            {"url": "https://b.com", "title": "Second", "content": "Content B"},
            {"url": "https://c.com", "title": "Third", "content": "Content C"},
        ]
        output = _format_crawled_content(pages)
        assert "--- Source [1]: First ---" in output
        assert "--- Source [2]: Second ---" in output
        assert "--- Source [3]: Third ---" in output

    def test_source_numbering_starts_at_1(self):
        pages = [
            {"url": "https://x.com", "title": "Only", "content": "Body"},
        ]
        output = _format_crawled_content(pages)
        assert "[1]" in output
        assert "[0]" not in output

    def test_content_preserved_verbatim(self):
        content_text = "Line one\nLine two\n\nParagraph two."
        pages = [
            {"url": "https://x.com", "title": "T", "content": content_text},
        ]
        output = _format_crawled_content(pages)
        assert content_text in output

    def test_each_section_contains_url(self):
        pages = [
            {"url": "https://alpha.com/p", "title": "A", "content": "body a"},
            {"url": "https://beta.com/p", "title": "B", "content": "body b"},
        ]
        output = _format_crawled_content(pages)
        assert "URL: https://alpha.com/p" in output
        assert "URL: https://beta.com/p" in output
