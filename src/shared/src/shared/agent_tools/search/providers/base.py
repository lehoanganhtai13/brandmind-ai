"""
Base provider abstract class for search implementations.

This module defines the interface that all search providers must implement.
The abstract base class ensures consistent behavior across different search
services and enables the orchestrator to treat all providers uniformly.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from shared.agent_tools.search.models import ProviderResult


class BaseProvider(ABC):
    """
    Abstract base class for all search providers.

    All search providers (SearXNG, Bing, Tavily, Perplexity, Scrapeless) must
    inherit from this class and implement the `search` method. This ensures
    consistent behavior and enables the orchestrator to chain providers together.

    Class Attributes:
        name: Unique identifier for the provider (e.g., "searxng", "bing_direct").
            Used for logging and engine availability tracking.
        engines: List of engine identifiers available within this provider.
            For multi-engine providers like SearXNG, this contains engine names
            (e.g., ["duckduckgo", "startpage"]). For single-engine providers,
            use [None] to indicate no engine rotation is needed.

    Example:
        >>> class MyProvider(BaseProvider):
        ...     name = "my_provider"
        ...     engines = [None]  # Single engine
        ...
        ...     def search(self, queries, engine, num_results):
        ...         # Implementation here
        ...         return ProviderResult(...)
    """

    name: str
    engines: List[Optional[str]]

    def is_available(self) -> bool:
        """
        Check if this provider is available for use.

        Override this method in providers that require API keys or external
        dependencies. The orchestrator calls this before using a provider,
        allowing it to skip unavailable providers without wasting time.

        Returns:
            True if the provider is ready to accept requests, False otherwise.
            Default implementation returns True (always available).
        """
        return True

    @property
    def requires_delay(self) -> bool:
        """
        Check if this provider requires rate limiting delay between requests.

        Self-hosted services (like SearXNG) need delays to prevent overwhelming
        upstream search engines. Third-party APIs handle their own rate limits
        so no delay is needed.

        Returns:
            True if delay should be applied, False otherwise.
            Default implementation returns False (no delay for API providers).
        """
        return False

    @abstractmethod
    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for a batch of queries using the specified engine.

        This method processes multiple queries concurrently and returns results
        for all queries in a single ProviderResult. Failed queries are tracked
        separately to enable retry with the next engine or provider.

        Args:
            queries: List of search query strings to process. The orchestrator
                ensures this list is deduplicated and within batch size limits.
            engine: Specific engine to use within this provider. For single-engine
                providers, this will be None. For multi-engine providers like
                SearXNG, this specifies which backend engine to query.
            num_results: Maximum number of search results to return per query.

        Returns:
            ProviderResult containing:
                - success_results: Dict mapping successful queries to their results
                - failed_queries: List of queries that failed and should be retried
                - engine_used: Identifier of the engine that processed these queries
                - response_time: Time taken to complete the search operation

        Raises:
            SearchAPIError: If the search API returns an error response.
            SearchTimeoutError: If the request times out.
            SearchConnectionError: If unable to connect to the search service.
        """
        pass
