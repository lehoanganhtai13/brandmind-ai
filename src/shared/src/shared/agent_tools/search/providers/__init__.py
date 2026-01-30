"""
Search providers package.

This package contains all search provider implementations that follow the
BaseProvider interface. Each provider handles a specific search service
(SearXNG, Bing, Tavily, Perplexity, Scrapeless).

The main orchestrator (search_web.py) uses these providers in a chain,
trying each one in order until queries succeed or all providers are exhausted.
"""

from shared.agent_tools.search.providers.base import BaseProvider
from shared.agent_tools.search.providers.bing import BingProvider
from shared.agent_tools.search.providers.perplexity import PerplexityProvider
from shared.agent_tools.search.providers.scrapeless import ScrapelessProvider
from shared.agent_tools.search.providers.searxng import SearXNGProvider
from shared.agent_tools.search.providers.tavily import TavilyProvider

__all__ = [
    "BaseProvider",
    "SearXNGProvider",
    "BingProvider",
    "TavilyProvider",
    "PerplexityProvider",
    "ScrapelessProvider",
]
