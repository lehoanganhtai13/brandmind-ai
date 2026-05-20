"""Supported model profiles for the BrandMind main strategy agent."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BRAND_STRATEGY_MAIN_MODEL = "gemini-3.5-flash"
SUPPORTED_BRAND_STRATEGY_MAIN_MODELS = (
    "gemini-3.5-flash",
    "gemini-3-flash",
)


class UnsupportedBrandStrategyModelError(ValueError):
    """Raised when BrandMind is configured with an unsupported model id."""


@dataclass(frozen=True)
class BrandStrategyMainModelProfile:
    """Runtime configuration for a supported BrandMind main-agent model."""

    model_id: str
    display_name: str
    provider: str = "google"
    temperature: float = 1.0
    thinking_level: str = "high"
    max_output_tokens: int = 8000
    context_window: int = 262144
    include_thoughts: bool = True


BRAND_STRATEGY_MAIN_MODEL_PROFILES = {
    "gemini-3.5-flash": BrandStrategyMainModelProfile(
        model_id="gemini-3.5-flash",
        display_name="Gemini 3.5 Flash",
    ),
    "gemini-3-flash": BrandStrategyMainModelProfile(
        model_id="gemini-3-flash-preview",
        display_name="Gemini 3 Flash",
    ),
}


def get_default_brand_strategy_main_model_profile() -> BrandStrategyMainModelProfile:
    """Return BrandMind's default best-supported main-agent model profile."""
    return BRAND_STRATEGY_MAIN_MODEL_PROFILES[DEFAULT_BRAND_STRATEGY_MAIN_MODEL]


def resolve_brand_strategy_main_model_profile(
    model_id: str | None,
) -> BrandStrategyMainModelProfile:
    """Resolve a configured model id to a supported BrandMind profile."""
    normalized_model_id = (model_id or "").strip() or DEFAULT_BRAND_STRATEGY_MAIN_MODEL
    try:
        return BRAND_STRATEGY_MAIN_MODEL_PROFILES[normalized_model_id]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_BRAND_STRATEGY_MAIN_MODELS)
        raise UnsupportedBrandStrategyModelError(
            f"Unsupported BrandMind main-agent model: {normalized_model_id}. "
            f"Supported models: {supported}."
        ) from exc
