"""
SearXNG search provider implementation.

This provider uses a self-hosted SearXNG instance to perform meta-searches
across multiple search engines. It supports engine rotation within SearXNG
for better reliability.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import requests
from loguru import logger

from shared.agent_tools.search.exceptions import (
    SearchConnectionError,
    SearchResponseError,
    SearchTimeoutError,
)
from shared.agent_tools.search.models import ProviderResult
from shared.agent_tools.search.providers.base import BaseProvider
from shared.utils.base_class import SearchResult


class SearXNGProvider(BaseProvider):
    """
    Search provider using self-hosted SearXNG meta-search engine.

    This provider connects to a SearXNG instance which can query multiple
    upstream search engines (DuckDuckGo, Startpage, etc.). It supports
    engine rotation within SearXNG itself, allowing the orchestrator to
    try different backends when one fails.

    Attributes:
        name: Provider identifier used for logging and tracking.
        engines: List of SearXNG backend engines to use for rotation.
            The orchestrator will try each engine in order.

    Environment Variables:
        SEARXNG_HOST: Host address of SearXNG instance (default: "localhost").
        SEARXNG_PORT: Port of SearXNG instance (default: "8080").
    """

    name: str = "searxng"
    engines: List[Optional[str]] = ["duckduckgo", "startpage"]

    def __init__(self, language: str = "vi", response_format: str = "json") -> None:
        """
        Initialize the SearXNG provider with configuration.

        Args:
            language: Language code for search results (default: "vi").
            response_format: Response format from SearXNG (default: "json").
        """
        self.language = language
        self.response_format = response_format
        self._host = os.getenv("SEARXNG_HOST", "localhost")
        self._port = os.getenv("SEARXNG_PORT", "8080")
        self._base_url = f"http://{self._host}:{self._port}"

    def is_available(self) -> bool:
        """Check if SearXNG service is running and reachable."""
        try:
            response = requests.get(self._base_url, timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @property
    def requires_delay(self) -> bool:
        """SearXNG is self-hosted and needs delay to avoid overwhelming upstream."""
        return True

    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for multiple queries using specified SearXNG engine.

        Processes queries concurrently using ThreadPoolExecutor.

        Args:
            queries: List of search query strings to process.
            engine: SearXNG backend engine to use (e.g., "duckduckgo", "startpage").
            num_results: Maximum number of results per query.

        Returns:
            ProviderResult with successful results and any failed queries.
        """
        start_time = time.time()
        success_results = {}
        failed_queries = []

        # Process queries concurrently
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {
                executor.submit(self._search_single, query, engine, num_results): query
                for query in queries
            }

            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    if results:
                        success_results[query] = results
                    else:
                        failed_queries.append(query)
                except Exception as e:
                    logger.error(f"SearXNG search error for '{query}': {e}")
                    failed_queries.append(query)

        engine_key = f"{self.name}_{engine}" if engine else f"{self.name}_default"

        return ProviderResult(
            success_results=success_results,
            failed_queries=failed_queries,
            engine_used=engine_key,
            response_time=time.time() - start_time,
        )

    def _search_single(
        self,
        query: str,
        engine: Optional[str],
        num_results: int,
    ) -> List[SearchResult]:
        """
        Execute a single search query against SearXNG.

        Args:
            query: The search query string.
            engine: SearXNG backend engine to use.
            num_results: Maximum number of results to return.

        Returns:
            List of SearchResult objects, empty list if search fails.
        """
        params = {
            "q": query,
            "format": self.response_format,
            "language": self.language,
        }
        if engine:
            params["engines"] = engine

        try:
            response = requests.get(
                self._base_url,
                params=params,
                timeout=30,
            )

            if response.status_code != 200:
                logger.warning(
                    f"SearXNG engine {engine} returned status {response.status_code} "
                    f"for query '{query}'"
                )
                return []

            results = response.json().get("results", [])

            search_results: List[SearchResult] = []
            for result in results:
                content = result.get("content", "")
                if content:
                    search_results.append(
                        SearchResult(
                            title=result.get("title", "").capitalize(),
                            url=result.get("url", ""),
                            snippet=content,
                        )
                    )
                    if len(search_results) >= num_results:
                        break

            return search_results

        except requests.exceptions.Timeout:
            logger.error(SearchTimeoutError(provider="SearXNG", query=query))
            return []
        except requests.exceptions.RequestException as e:
            logger.error(SearchConnectionError(provider="SearXNG", error=str(e)))
            return []
        except Exception as e:
            logger.error(SearchResponseError(provider="SearXNG", error=str(e)))
            return []
