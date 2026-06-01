"""Unit tests for BrandMind main-agent model profile selection."""

import pytest

from core.brand_strategy.model_profiles import (
    DEFAULT_BRAND_STRATEGY_MAIN_MODEL,
    SUPPORTED_BRAND_STRATEGY_MAIN_MODELS,
    UnsupportedBrandStrategyModelError,
    get_default_brand_strategy_main_model_profile,
    list_supported_brand_strategy_main_models,
    resolve_brand_strategy_main_model_profile,
)


def test_default_main_model_profile_is_gemini_35_flash() -> None:
    profile = get_default_brand_strategy_main_model_profile()

    assert DEFAULT_BRAND_STRATEGY_MAIN_MODEL == "gemini-3.5-flash"
    assert profile.model_id == "gemini-3.5-flash"
    assert profile.thinking_level == "medium"
    assert profile.context_window == 262144


def test_supported_main_model_list_is_explicit() -> None:
    assert SUPPORTED_BRAND_STRATEGY_MAIN_MODELS == (
        "gemini-3.5-flash",
        "gemini-3-flash",
    )


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("", "gemini-3.5-flash"),
        (None, "gemini-3.5-flash"),
        (" gemini-3-flash ", "gemini-3-flash-preview"),
    ],
)
def test_resolve_main_model_profile(configured: str | None, expected: str) -> None:
    profile = resolve_brand_strategy_main_model_profile(configured)

    assert profile.model_id == expected


def test_gemini_3_flash_profile_hides_preview_from_user_facing_name() -> None:
    profile = resolve_brand_strategy_main_model_profile("gemini-3-flash")

    assert profile.display_name == "Gemini 3 Flash"
    assert profile.model_id == "gemini-3-flash-preview"


def test_resolve_main_model_profile_rejects_unsupported_model() -> None:
    with pytest.raises(UnsupportedBrandStrategyModelError) as exc:
        resolve_brand_strategy_main_model_profile("gemini-3.1-pro-preview")

    assert "Unsupported BrandMind main-agent model" in str(exc.value)
    assert "gemini-3.5-flash" in str(exc.value)
    assert "gemini-3-flash-preview" not in str(exc.value)


def test_list_supported_main_models_pairs_public_key_with_profile() -> None:
    pairs = list_supported_brand_strategy_main_models()

    public_keys = [public_key for public_key, _ in pairs]
    assert public_keys == list(SUPPORTED_BRAND_STRATEGY_MAIN_MODELS)

    by_key = {public_key: profile for public_key, profile in pairs}
    assert by_key["gemini-3.5-flash"].display_name == "Gemini 3.5 Flash"
    assert by_key["gemini-3-flash"].display_name == "Gemini 3 Flash"
    assert by_key["gemini-3-flash"].model_id == "gemini-3-flash-preview"
    assert by_key["gemini-3.5-flash"].description
    assert by_key["gemini-3-flash"].description
