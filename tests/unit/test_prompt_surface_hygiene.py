"""Regression tests for runtime prompt hygiene."""

from __future__ import annotations

from prompts.brand_strategy.subagents import (
    CREATIVE_STUDIO_SYSTEM_PROMPT,
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
    MARKET_RESEARCH_SYSTEM_PROMPT,
    SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
)
from prompts.brand_strategy.system_prompt import BRAND_STRATEGY_SYSTEM_PROMPT


def test_main_prompt_uses_tool_schema_without_user_facing_subagent_jargon() -> None:
    """Keep internal routing schema while avoiding jargon likely to leak to users."""
    assert "subagent_type" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "sub-agent" not in BRAND_STRATEGY_SYSTEM_PROMPT.lower()


def test_subagent_prompts_are_host_system_neutral() -> None:
    """Sub-agent prompt roles should not brand their work as BrandMind AI output."""
    prompts = (
        CREATIVE_STUDIO_SYSTEM_PROMPT,
        DOCUMENT_GENERATOR_SYSTEM_PROMPT,
        MARKET_RESEARCH_SYSTEM_PROMPT,
        SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
    )

    for prompt in prompts:
        assert "BrandMind AI" not in prompt
        assert "BrandMind's" not in prompt
