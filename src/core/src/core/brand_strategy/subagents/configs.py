"""Configuration for Brand Strategy sub-agents.

Defines model instances and tool assignments per sub-agent type.
Uses RetryChatGoogleGenerativeAI (with built-in 503/429 retry) instead of
string model names, because each model generation requires different configs:
- Gemini 2.5 models: thinking_budget (int), temperature=0.1
- Gemini 3 models: thinking_level (str), temperature=1.0

System prompts are imported from src/prompts/brand_strategy/subagents/.
"""

from __future__ import annotations

from config.system_config import SETTINGS
from shared.agent_models import RetryChatGoogleGenerativeAI

# Tool name lists per sub-agent (resolved to actual tools at build time)
MARKET_RESEARCH_TOOLS = [
    "search_web",
    "scrape_web_content",
    "get_search_autocomplete",
    "deep_research",
    "browse_and_research",
]

SOCIAL_MEDIA_TOOLS = [
    "search_web",
    "scrape_web_content",
    "browse_and_research",
    "analyze_social_profile",
]

CREATIVE_STUDIO_TOOLS = [
    "generate_image",
    "edit_image",
    "generate_brand_key",
]

DOCUMENT_GENERATOR_TOOLS = [
    "generate_document",
    "generate_presentation",
    "generate_spreadsheet",
    "export_to_markdown",
]


def create_subagent_models() -> dict[str, RetryChatGoogleGenerativeAI]:
    """Create model instances for each sub-agent type.

    Returns:
        Dict mapping sub-agent name to configured model instance.
    """
    return {
        # Market Research: Gemini 2.5 Flash Lite — cheap, fast, good at data gathering
        "market-research": RetryChatGoogleGenerativeAI(
            google_api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-2.5-flash-lite",
            temperature=0.1,
            thinking_budget=2000,
            max_output_tokens=8000,
            include_thoughts=False,
        ),
        # Social Media Analyst: Gemini 3 Flash — vision capable for social images
        "social-media-analyst": RetryChatGoogleGenerativeAI(
            google_api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-3-flash-preview",
            temperature=1.0,
            thinking_level="medium",
            max_output_tokens=8000,
            include_thoughts=False,
        ),
        # Creative Studio: Gemini 3 Flash — vision capable, evaluates generated images
        "creative-studio": RetryChatGoogleGenerativeAI(
            google_api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-3-flash-preview",
            temperature=1.0,
            thinking_level="medium",
            max_output_tokens=5000,
            include_thoughts=False,
        ),
        # Document Generator: Gemini 2.5 Flash Lite — cheap, structured output
        "document-generator": RetryChatGoogleGenerativeAI(
            google_api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-2.5-flash-lite",
            temperature=0.1,
            thinking_budget=2000,
            max_output_tokens=10000,
            include_thoughts=False,
        ),
    }
