"""Unit tests for Brand Strategy sub-agent model configuration."""

from core.brand_strategy.subagents.configs import (
    CREATIVE_STUDIO_MAX_OUTPUT_TOKENS,
    DOCUMENT_GENERATOR_MAX_OUTPUT_TOKENS,
    MARKET_RESEARCH_MAX_OUTPUT_TOKENS,
    SOCIAL_MEDIA_MAX_OUTPUT_TOKENS,
    create_subagent_models,
)


def test_subagent_models_use_role_specific_output_budgets() -> None:
    """Research-heavy sub-agents get enough output budget for complete handoffs."""
    models = create_subagent_models()

    assert (
        models["market-research"].max_output_tokens == MARKET_RESEARCH_MAX_OUTPUT_TOKENS
    )
    assert (
        models["social-media-analyst"].max_output_tokens
        == SOCIAL_MEDIA_MAX_OUTPUT_TOKENS
    )
    assert (
        models["creative-studio"].max_output_tokens == CREATIVE_STUDIO_MAX_OUTPUT_TOKENS
    )
    assert (
        models["document-generator"].max_output_tokens
        == DOCUMENT_GENERATOR_MAX_OUTPUT_TOKENS
    )


def test_market_research_uses_tool_reliable_gemini_3_flash() -> None:
    """Market research needs reliable source-ledger handoff, not cheapest output."""
    models = create_subagent_models()

    assert models["market-research"].model == "gemini-3-flash-preview"
    assert models["market-research"].thinking_level == "medium"
