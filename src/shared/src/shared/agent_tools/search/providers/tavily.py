"""
Tavily search provider implementation.

This provider uses the Tavily API to perform high-quality web searches
with configurable search depth for balancing speed and comprehensiveness.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import requests
from loguru import logger

from shared.agent_tools.search.exceptions import (
    APIKeyNotFoundError,
    SearchAPIError,
    SearchConnectionError,
    SearchResponseError,
    SearchTimeoutError,
)
from shared.agent_tools.search.models import ProviderResult
from shared.agent_tools.search.providers.base import BaseProvider
from shared.utils.base_class import SearchResult


class TavilyProvider(BaseProvider):
    """
    Search provider using Tavily API for web search results.

    This provider uses Tavily's search API which offers both basic and advanced
    search depths. The advanced mode provides more comprehensive results but
    takes longer to process.

    Attributes:
        name: Provider identifier used for logging and tracking.
        engines: Single engine provider - no rotation needed.

    Environment Variables:
        TAVILY_API_KEY: API key for Tavily service authentication.
    """

    name: str = "tavily"
    engines: List[Optional[str]] = [None]

    def __init__(
        self,
        search_depth: str = "basic",
        country: str = "vietnam",
    ) -> None:
        """
        Initialize the Tavily provider with search settings.

        Args:
            search_depth: Search depth mode - "basic" for fast results or
                "advanced" for more comprehensive results.
            country: Country for localized results (default: "vietnam").
        """
        self.search_depth = search_depth
        self.country = country
        self._api_url = "https://api.tavily.com/search"

    def is_available(self) -> bool:
        """Check if Tavily API key is configured."""
        return bool(os.getenv("TAVILY_API_KEY"))

    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for multiple queries using Tavily API.

        Processes queries concurrently using ThreadPoolExecutor for better
        performance.

        Args:
            queries: List of search query strings to process.
            engine: Ignored for this single-engine provider.
            num_results: Maximum number of results per query.

        Returns:
            ProviderResult with successful results and any failed queries.
        """
        start_time = time.time()
        success_results = {}
        failed_queries = []

        # Get API key
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            logger.error(
                APIKeyNotFoundError(provider="Tavily", env_var="TAVILY_API_KEY")
            )
            return ProviderResult(
                success_results={},
                failed_queries=queries,
                engine_used=f"{self.name}_default",
                response_time=time.time() - start_time,
            )

        # Process queries concurrently
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {
                executor.submit(self._search_single, query, num_results, api_key): query
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
                    logger.error(f"Tavily search error for '{query}': {e}")
                    failed_queries.append(query)

        return ProviderResult(
            success_results=success_results,
            failed_queries=failed_queries,
            engine_used=f"{self.name}_default",
            response_time=time.time() - start_time,
        )

    def _search_single(
        self,
        query: str,
        num_results: int,
        api_key: str,
    ) -> List[SearchResult]:
        """
        Execute a single search query against Tavily API.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.
            api_key: Tavily API authentication key.

        Returns:
            List of SearchResult objects, empty list if search fails.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "query": query,
            "search_depth": self.search_depth,
            "max_results": num_results,
            "country": self.country,
        }

        try:
            response = requests.post(
                self._api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(
                    SearchAPIError(
                        provider="Tavily",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                )
                return []

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(
                    SearchResponseError(provider="Tavily", error="No results found")
                )
                return []

            return [
                SearchResult(
                    title=result.get("title", "No title"),
                    url=result.get("url", ""),
                    snippet=result.get("content", result.get("snippet", "")),
                )
                for result in results
            ]

        except requests.exceptions.Timeout:
            logger.error(SearchTimeoutError(provider="Tavily", query=query))
            return []
        except requests.exceptions.RequestException as e:
            logger.error(SearchConnectionError(provider="Tavily", error=str(e)))
            return []
        except Exception as e:
            logger.error(SearchResponseError(provider="Tavily", error=str(e)))
            return []
