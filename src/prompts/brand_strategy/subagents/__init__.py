"""Sub-agent system prompts for Brand Strategy.

Each sub-agent has its own prompt file organized by business function.
"""

from prompts.brand_strategy.subagents.creative_studio import (
    CREATIVE_STUDIO_SYSTEM_PROMPT,
)
from prompts.brand_strategy.subagents.document_generator import (
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
)
from prompts.brand_strategy.subagents.market_research import (
    MARKET_RESEARCH_SYSTEM_PROMPT,
)
from prompts.brand_strategy.subagents.social_media import (
    SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
)

__all__ = [
    "CREATIVE_STUDIO_SYSTEM_PROMPT",
    "DOCUMENT_GENERATOR_SYSTEM_PROMPT",
    "MARKET_RESEARCH_SYSTEM_PROMPT",
    "SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT",
]
