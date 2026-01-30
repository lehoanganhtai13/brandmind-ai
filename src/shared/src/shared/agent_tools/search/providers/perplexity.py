"""
Perplexity AI search provider implementation.

This provider uses the Perplexity AI API to perform AI-powered searches
with high-quality, contextually relevant results.
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


class PerplexityProvider(BaseProvider):
    """
    Search provider using Perplexity AI API for intelligent search results.

    This provider leverages Perplexity AI's advanced search capabilities to
    deliver contextually relevant results. It's particularly effective for
    complex queries that benefit from AI understanding.

    Attributes:
        name: Provider identifier used for logging and tracking.
        engines: Single engine provider - no rotation needed.

    Environment Variables:
        PERPLEXITY_API_KEY: API key for Perplexity AI service authentication.
    """

    name: str = "perplexity"
    engines: List[Optional[str]] = [None]

    def __init__(self, country: str = "VN") -> None:
        """
        Initialize the Perplexity provider with localization settings.

        Args:
            country: Country code for localized results (default: "VN").
        """
        self.country = country
        self._api_url = "https://api.perplexity.ai/search"

    def is_available(self) -> bool:
        """Check if Perplexity API key is configured."""
        return bool(os.getenv("PERPLEXITY_API_KEY"))

    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for multiple queries using Perplexity AI API.

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
        api_key = os.getenv("PERPLEXITY_API_KEY", "")
        if not api_key:
            logger.error(
                APIKeyNotFoundError(provider="Perplexity", env_var="PERPLEXITY_API_KEY")
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
                    logger.error(f"Perplexity search error for '{query}': {e}")
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
        Execute a single search query against Perplexity AI API.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.
            api_key: Perplexity AI API authentication key.

        Returns:
            List of SearchResult objects, empty list if search fails.
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "country": self.country,
            "max_results": num_results,
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
                        provider="Perplexity",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                )
                return []

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(
                    SearchResponseError(provider="Perplexity", error="No results found")
                )
                return []

            return [
                SearchResult(
                    title=result.get("title", "No title"),
                    url=result.get("url", ""),
                    snippet=result.get("snippet", result.get("description", "")),
                )
                for result in results
            ]

        except requests.exceptions.Timeout:
            logger.error(SearchTimeoutError(provider="Perplexity", query=query))
            return []
        except requests.exceptions.RequestException as e:
            logger.error(SearchConnectionError(provider="Perplexity", error=str(e)))
            return []
        except Exception as e:
            logger.error(SearchResponseError(provider="Perplexity", error=str(e)))
            return []
