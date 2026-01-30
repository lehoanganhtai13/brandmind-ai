"""
Scrapeless search provider implementation.

This provider uses the Scrapeless API to perform deep searches on Google SERP.
It provides high-quality search results with support for Vietnamese localization.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import requests
from loguru import logger

from shared.agent_tools.search.exceptions import (
    APIKeyNotFoundError,
    SearchAPIError,
    SearchResponseError,
)
from shared.agent_tools.search.models import ProviderResult
from shared.agent_tools.search.providers.base import BaseProvider
from shared.utils.base_class import Payload, SearchResult


class ScrapelessProvider(BaseProvider):
    """
    Search provider using Scrapeless API for Google SERP results.

    This provider leverages the Scrapeless API to perform deep searches on Google,
    returning high-quality organic search results. It's optimized for Vietnamese
    queries with configurable localization settings.

    Attributes:
        name: Provider identifier used for logging and tracking.
        engines: Single engine provider - no rotation needed.

    Environment Variables:
        SCRAPELESS_API_KEY: API key for Scrapeless service authentication.
    """

    name: str = "scrapeless"
    engines: List[Optional[str]] = [None]

    def __init__(
        self,
        country: str = "vn",
        language: str = "vi",
        location: str = "Ho Chi Minh City, Viet Nam",
        google_domain: str = "google.com.vn",
    ) -> None:
        """
        Initialize the Scrapeless provider with localization settings.

        Args:
            country: Country code for search results (default: "vn").
            language: Language code for search interface (default: "vi").
            location: Geographic location for localized results.
            google_domain: Google domain to use for searches.
        """
        self.country = country
        self.language = language
        self.location = location
        self.google_domain = google_domain
        self._api_host = "api.scrapeless.com"
        self._api_url = f"https://{self._api_host}/api/v1/scraper/request"

    def is_available(self) -> bool:
        """Check if Scrapeless API key is configured."""
        return bool(os.getenv("SCRAPELESS_API_KEY"))

    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for multiple queries using Scrapeless API.

        Processes queries concurrently using ThreadPoolExecutor for better
        performance. Each query is sent as a separate API request.

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
        api_key = os.getenv("SCRAPELESS_API_KEY", "")
        if not api_key:
            logger.error(
                APIKeyNotFoundError(provider="Scrapeless", env_var="SCRAPELESS_API_KEY")
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
                    logger.error(f"Scrapeless search error for '{query}': {e}")
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
        Execute a single search query against Scrapeless API.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.
            api_key: Scrapeless API authentication key.

        Returns:
            List of SearchResult objects, empty list if search fails.
        """
        headers = {"x-api-token": api_key}
        input_data = {
            "q": query,
            "gl": self.country,
            "hl": self.language,
            "location": self.location,
            "google_domain": self.google_domain,
            "num": str(num_results),
        }
        payload = Payload(actor="scraper.google.search", input=input_data)
        json_payload = json.dumps(payload.__dict__)

        try:
            response = requests.post(
                self._api_url,
                headers=headers,
                data=json_payload,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(
                    SearchAPIError(
                        provider="Scrapeless",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                )
                return []

            data = response.json()
            results = data.get("organic_results", [])

            if not results:
                logger.warning(
                    SearchResponseError(provider="Scrapeless", error="No results found")
                )
                return []

            return [
                SearchResult(
                    title=result.get("title", "No title"),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", ""),
                )
                for result in results
            ]

        except requests.exceptions.Timeout:
            logger.error(f"Scrapeless request timed out for query: {query}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Scrapeless connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Scrapeless unexpected error: {e}")
            return []
