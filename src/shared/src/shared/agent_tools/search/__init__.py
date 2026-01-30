"""
Search module for web search operations.

This module provides a unified interface for web search across multiple
providers (SearXNG, Bing, Tavily, Perplexity, Scrapeless) with automatic
fallback, batch processing, and rate limiting.

Main Entry Point:
    search_web: Orchestrates search across all providers with batch processing.

Legacy Functions (for backward compatibility):
    deep_serp_search: Scrapeless Google SERP search.
    perplexity_search: Perplexity AI search.
    tavily_search: Tavily web search.
    bing_web_search: Direct Bing web scraping.

Example:
    >>> from shared.agent_tools.search import search_web
    >>> results = search_web(["Python tutorial", "Flask framework"])
    >>> for query, data in results["queries"].items():
    ...     print(f"{query}: {data['result_count']} results")
"""

from shared.agent_tools.search.search_web import (
    bing_web_search,
    deep_serp_search,
    perplexity_search,
    search_web,
    tavily_search,
)

__all__ = [
    "search_web",
    "deep_serp_search",
    "perplexity_search",
    "tavily_search",
    "bing_web_search",
]
