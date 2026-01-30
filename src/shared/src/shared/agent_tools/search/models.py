"""
Internal data models for the search module.

This module contains Pydantic models used internally within the search providers
and orchestrator. These models are not exposed outside the search module.

For shared models used across multiple modules, see `shared/utils/base_class.py`.
"""

from typing import Dict, List

from pydantic import BaseModel, Field

from shared.utils.base_class import SearchResult


class ProviderResult(BaseModel):
    """
    Encapsulates the result of a search provider operation.

    This model is used internally to communicate results between search providers
    and the main orchestrator. It tracks both successful results and failed queries
    to enable retry logic across provider chains.

    Attributes:
        success_results: Dictionary mapping query strings to their search results.
            Each query that succeeded will have an entry with a list of SearchResult.
        failed_queries: List of query strings that failed to return results.
            These queries may be retried with the next available engine or provider.
        engine_used: Identifier of the engine/provider that processed these queries.
            Format: "{provider_name}_{engine_name}" (e.g., "searxng_duckduckgo").
        response_time: Time in seconds taken to complete the search operation.
    """

    success_results: Dict[str, List[SearchResult]] = Field(default_factory=dict)
    failed_queries: List[str] = Field(default_factory=list)
    engine_used: str = ""
    response_time: float = 0.0
