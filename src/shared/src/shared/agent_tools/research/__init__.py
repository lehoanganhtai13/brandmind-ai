"""Deep research tool — multi-step research pipeline.

Provides deep_research function that combines search_web +
scrape_web_content + LLM synthesis for comprehensive research.
"""

from .deep_research import deep_research

__all__ = ["deep_research"]
