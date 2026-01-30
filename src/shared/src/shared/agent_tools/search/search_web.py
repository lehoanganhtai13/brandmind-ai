"""
Search web orchestrator - main entry point for web search operations.

This module provides the primary search_web function that orchestrates
multiple search providers in a chain, processing queries in batches
with concurrent execution and automatic fallback to next provider/engine
when failures occur.

Key Features:
- Batch processing: max 3 concurrent queries per batch
- Provider chain: SearXNG → Perplexity → Tavily → Bing
- Engine rotation: within multi-engine providers (e.g., SearXNG)
- Dynamic rate limiting: 3.5s delay per query in batch
- Cross-call state persistence: engine availability tracking
"""

import logging
import time
from typing import Any, Dict, List

from loguru import logger

from shared.agent_tools.search.exceptions import SearchValidationError
from shared.agent_tools.search.providers import (
    BaseProvider,
    BingProvider,
    PerplexityProvider,
    ScrapelessProvider,
    SearXNGProvider,
    TavilyProvider,
)
from shared.utils.base_class import SearchResult

# Configure logging levels for third-party libraries
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# =============================================================================
# Configuration Constants
# =============================================================================

MAX_QUERIES = 5  # Maximum number of queries per search_web call
MAX_BATCH_SIZE = 3  # Maximum concurrent queries per batch
BASE_DELAY = 3.5  # Base delay in seconds per query

# =============================================================================
# Provider Chain Configuration
# =============================================================================

# Provider chain: tried in order, each provider exhausts all its engines
# before moving to the next provider.
# Bing is last because its results can be inconsistent.
PROVIDERS: List[BaseProvider] = [
    SearXNGProvider(),  # Multi-engine: duckduckgo, startpage
    PerplexityProvider(),  # AI-powered search
    TavilyProvider(),  # Web search API
    BingProvider(),  # Direct curl scraping - fallback (inconsistent results)
]

# =============================================================================
# Global State (persists across search_web calls)
# =============================================================================

# Track when each engine becomes available again
# Key format: "{provider_name}_{engine_name}" (e.g., "searxng_duckduckgo")
_engine_available_at: Dict[str, float] = {}


# =============================================================================
# Main Search Function
# =============================================================================


def search_web(
    queries: List[str],
    number_of_results: int = 10,
) -> Dict[str, Any]:
    """
    Main search orchestrator with provider chain and batch processing.

    This function processes a list of search queries using multiple providers
    in a chain. It supports concurrent execution within batches, engine
    rotation for multi-engine providers, and automatic fallback to the next
    provider when all engines of the current provider fail.

    Features:
    - Input validation: max 5 queries, raises SearchValidationError if exceeded
    - Query deduplication: removes duplicate queries while preserving order
    - Batch processing: max 3 concurrent queries per batch
    - Dynamic delay: 3.5s × batch_size delay after each batch
    - Engine rotation: failed queries retry on next engine within provider
    - Provider chain: exhausted provider moves to next in chain
    - State persistence: engine availability tracked across calls

    Args:
        queries: List of search query strings (max 5 after deduplication).
        number_of_results: Maximum number of results per query (default: 10).

    Returns:
        Dictionary with structure:
            {
                "queries": {
                    "query1": {
                        "results": List[SearchResult],
                        "response_time": float,
                        "result_count": int,
                        "engine_used": str
                    },
                    ...
                },
                "total_execution_time": float,
                "total_queries": int,
                "average_time_per_query": float
            }

    Raises:
        SearchValidationError: If queries list is empty or exceeds MAX_QUERIES.

    Example:
        >>> results = search_web(["Python tutorial", "Flask framework"])
        >>> for query, data in results["queries"].items():
        ...     print(f"{query}: {data['result_count']} results")
    """
    total_start_time = time.time()

    # -------------------------------------------------------------------------
    # Input Validation
    # -------------------------------------------------------------------------

    # Deduplicate queries while preserving order
    unique_queries = list(dict.fromkeys(queries))
    if len(unique_queries) < len(queries):
        logger.info(f"Deduplicated queries: {len(queries)} → {len(unique_queries)}")

    # Validate query count
    if not unique_queries:
        raise SearchValidationError(
            message="Queries list cannot be empty",
            field="queries",
            value=queries,
        )

    if len(unique_queries) > MAX_QUERIES:
        raise SearchValidationError(
            message=f"Too many queries. Maximum allowed is {MAX_QUERIES}, "
            f"got {len(unique_queries)}",
            field="queries",
            value=len(unique_queries),
        )

    logger.info(
        f"Starting web search for {len(unique_queries)} queries: {unique_queries}"
    )

    # -------------------------------------------------------------------------
    # Process Queries Through Provider Chain
    # -------------------------------------------------------------------------

    remaining_queries = list(unique_queries)
    all_results: Dict[str, Dict[str, Any]] = {}

    for provider in PROVIDERS:
        if not remaining_queries:
            break

        # Skip providers that are not available (e.g., missing API key)
        if not provider.is_available():
            logger.debug(f"Skipping provider {provider.name} - not available")
            continue

        for engine in provider.engines:
            if not remaining_queries:
                break

            engine_key = f"{provider.name}_{engine or 'default'}"

            # Keep processing batches with this engine until failures occur
            # This ensures we use the same working provider for all queries
            engine_had_failure = False

            while remaining_queries and not engine_had_failure:
                # Check engine availability (rate limiting from previous calls)
                # Only applies to providers that require delay (e.g., SearXNG)
                if provider.requires_delay:
                    now = time.time()
                    wait_time = _engine_available_at.get(engine_key, 0) - now

                    if wait_time > 0:
                        logger.debug(
                            f"Engine {engine_key} busy, waiting {wait_time:.2f}s"
                        )
                        time.sleep(wait_time)

                # Process batch (max 3 concurrent queries)
                batch = remaining_queries[:MAX_BATCH_SIZE]
                logger.info(
                    f"Processing batch of {len(batch)} queries with "
                    f"provider={provider.name}, engine={engine}"
                )

                # Execute batch search
                result = provider.search(batch, engine, number_of_results)

                # Update engine availability (dynamic delay based on batch size)
                if provider.requires_delay:
                    delay = BASE_DELAY * len(batch)
                    _engine_available_at[engine_key] = time.time() + delay
                    logger.debug(f"Engine {engine_key} unavailable for {delay:.2f}s")

                # Store successful results
                for query, search_results in result.success_results.items():
                    all_results[query] = {
                        "results": search_results,
                        "response_time": result.response_time / len(batch),
                        "result_count": len(search_results),
                        "engine_used": result.engine_used,
                    }

                # Check for failures
                if result.failed_queries:
                    # Some failed - move to next engine/provider
                    logger.warning(
                        f"{len(result.failed_queries)} queries failed on "
                        f"{engine_key}, will retry with next engine/provider"
                    )
                    remaining_queries = (
                        result.failed_queries + remaining_queries[MAX_BATCH_SIZE:]
                    )
                    engine_had_failure = True
                else:
                    # All succeeded - continue with remaining unprocessed queries
                    remaining_queries = remaining_queries[MAX_BATCH_SIZE:]

    # -------------------------------------------------------------------------
    # Handle Queries That Failed All Providers
    # -------------------------------------------------------------------------

    for query in remaining_queries:
        logger.error(f"All providers failed for query: {query}")
        all_results[query] = {
            "results": [],
            "response_time": 0.0,
            "result_count": 0,
            "engine_used": "none",
        }

    # -------------------------------------------------------------------------
    # Build Response
    # -------------------------------------------------------------------------

    total_execution_time = time.time() - total_start_time
    total_queries_count = len(unique_queries)

    logger.info(
        f"Search completed: {total_queries_count} queries in "
        f"{total_execution_time:.2f}s"
    )

    return {
        "queries": all_results,
        "total_execution_time": total_execution_time,
        "total_queries": total_queries_count,
        "average_time_per_query": (
            total_execution_time / total_queries_count
            if total_queries_count > 0
            else 0.0
        ),
    }


# =============================================================================
# Legacy Function Exports (for backward compatibility)
# =============================================================================

# Re-export individual provider functions for backward compatibility
# These may be deprecated in future versions


def deep_serp_search(query: str, number_of_results: int = 10) -> List[SearchResult]:
    """
    Legacy wrapper for Scrapeless deep SERP search.

    This function is provided for backward compatibility. Consider using
    search_web() instead for better reliability through provider chaining.

    Args:
        query: The search query string.
        number_of_results: Maximum number of results to return.

    Returns:
        List of SearchResult objects.
    """
    provider = ScrapelessProvider()
    result = provider.search([query], None, number_of_results)
    return result.success_results.get(query, [])


def perplexity_search(
    query: str,
    number_of_results: int = 10,
    country: str = "VN",
) -> List[SearchResult]:
    """
    Legacy wrapper for Perplexity AI search.

    This function is provided for backward compatibility. Consider using
    search_web() instead for better reliability through provider chaining.

    Args:
        query: The search query string.
        number_of_results: Maximum number of results to return.
        country: Country code for localized results.

    Returns:
        List of SearchResult objects.
    """
    provider = PerplexityProvider(country=country)
    result = provider.search([query], None, number_of_results)
    return result.success_results.get(query, [])


def tavily_search(
    query: str,
    number_of_results: int = 10,
    search_depth: str = "basic",
    country: str = "vietnam",
) -> List[SearchResult]:
    """
    Legacy wrapper for Tavily search.

    This function is provided for backward compatibility. Consider using
    search_web() instead for better reliability through provider chaining.

    Args:
        query: The search query string.
        number_of_results: Maximum number of results to return.
        search_depth: Search depth mode ("basic" or "advanced").
        country: Country for localized results.

    Returns:
        List of SearchResult objects.
    """
    provider = TavilyProvider(search_depth=search_depth, country=country)
    result = provider.search([query], None, number_of_results)
    return result.success_results.get(query, [])


def bing_web_search(query: str, number_of_results: int = 10) -> List[SearchResult]:
    """
    Legacy wrapper for direct Bing web search.

    This function is provided for backward compatibility. Consider using
    search_web() instead for better reliability through provider chaining.

    Args:
        query: The search query string.
        number_of_results: Maximum number of results to return.

    Returns:
        List of SearchResult objects.
    """
    provider = BingProvider()
    result = provider.search([query], None, number_of_results)
    return result.success_results.get(query, [])
