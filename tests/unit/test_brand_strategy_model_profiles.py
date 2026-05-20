"""Unit tests for BrandMind main-agent model profile selection."""

import pytest

from core.brand_strategy.model_profiles import (
    DEFAULT_BRAND_STRATEGY_MAIN_MODEL,
    SUPPORTED_BRAND_STRATEGY_MAIN_MODELS,
    UnsupportedBrandStrategyModelError,
    get_default_brand_strategy_main_model_profile,
    resolve_brand_strategy_main_model_profile,
)


def test_default_main_model_profile_is_gemini_35_flash() -> None:
    profile = get_default_brand_strategy_main_model_profile()

    assert DEFAULT_BRAND_STRATEGY_MAIN_MODEL == "gemini-3.5-flash"
    assert profile.model_id == "gemini-3.5-flash"
    assert profile.thinking_level == "high"
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
