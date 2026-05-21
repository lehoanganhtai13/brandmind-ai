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
    """Runtime configuration for a supported BrandMind main-agent model.

    ``description`` is the short user-facing copy the model picker shows
    underneath the display name so junior marketers can pick the right
    profile without having to know the underlying model trade-offs.
    """

    model_id: str
    display_name: str
    description: str = ""
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
        description="Best for deep strategy sessions",
    ),
    "gemini-3-flash": BrandStrategyMainModelProfile(
        model_id="gemini-3-flash-preview",
        display_name="Gemini 3 Flash",
        description="Fast full strategy at lower cost",
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


def list_supported_brand_strategy_main_models() -> list[
    tuple[str, BrandStrategyMainModelProfile]
]:
    """Return the supported (public_key, profile) pairs in canonical order.

    The public key is what callers echo back into
    :func:`resolve_brand_strategy_main_model_profile`; it is distinct
    from ``profile.model_id`` which carries the internal Google API
    model identifier. This helper drives the web model picker so the
    UI is fed by backend configuration rather than hard-coded names.

    Returns:
        pairs (list[tuple[str, BrandStrategyMainModelProfile]]): supported
        main-agent options, ordered to match
        ``SUPPORTED_BRAND_STRATEGY_MAIN_MODELS``.
    """
    return [
        (public_key, BRAND_STRATEGY_MAIN_MODEL_PROFILES[public_key])
        for public_key in SUPPORTED_BRAND_STRATEGY_MAIN_MODELS
    ]
