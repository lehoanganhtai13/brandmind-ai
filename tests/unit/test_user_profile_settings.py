"""Unit tests for BrandMind onboarding profile settings."""

from __future__ import annotations

import json
from pathlib import Path

import shared.workspace as workspace_mod
from shared.agent_middlewares.proactive_context import ProactiveContextBuilder
from shared.agent_middlewares.proactive_context import middleware as proactive_mod
from shared.workspace.profile_settings import (
    BrandStrategyFamiliarity,
    ExperienceYears,
    JobDomain,
    JobRole,
    MentoringStyle,
    StakeholderContext,
    UserProfileSettings,
    apply_profile_settings_to_profile,
    default_user_profile_settings,
    get_user_profile_settings_options,
    load_user_profile_settings,
    render_user_profile_settings,
    save_user_profile_settings,
)


def test_default_user_profile_settings_are_balanced_fallback() -> None:
    """Missing onboarding data falls back to a safe balanced prior."""
    settings = default_user_profile_settings()

    assert settings.job_domain is JobDomain.UNKNOWN
    assert settings.role is JobRole.UNKNOWN
    assert settings.brand_strategy_familiarity is BrandStrategyFamiliarity.UNKNOWN
    assert settings.mentoring_style is MentoringStyle.BALANCED
    assert settings.onboarding_completed is False


def test_profile_settings_options_expose_ui_choices() -> None:
    """Clients can render onboarding controls from backend-owned mappings."""
    options = get_user_profile_settings_options()

    assert {option.value for option in options.role} >= {
        "marketing_executive",
        "brand_manager",
        "student_junior",
    }
    assert {option.value for option in options.mentoring_style} == {
        "compact_first",
        "balanced",
        "teaching_first",
    }


def test_render_settings_creates_prompt_friendly_managed_block() -> None:
    """Onboarding settings render into concise agent-readable context."""
    settings = UserProfileSettings(
        job_domain=JobDomain.FB,
        role=JobRole.BRAND_MANAGER,
        experience_years=ExperienceYears.FIVE_PLUS,
        brand_strategy_familiarity=BrandStrategyFamiliarity.ADVANCED,
        mentoring_style=MentoringStyle.COMPACT_FIRST,
        stakeholder_context=StakeholderContext.BOSS,
        onboarding_completed=True,
    )

    rendered = render_user_profile_settings(settings)

    assert "## Onboarding Profile" in rendered
    assert "Source: onboarding settings" in rendered
    assert "Role: Brand Manager" in rendered
    assert "Preferred mentoring density: Compact first" in rendered
    assert "initial calibration prior, not as a fixed mode" in rendered
    assert "Pacing: Start from the current decision or blocker" in rendered
    assert "Scaffolding: Use concise business language" in rendered
    assert "Decision framing: surface options and tradeoffs" in rendered
    assert "Domain lens: for F&B" in rendered
    assert "Adaptation: recalibrate from the user's actual replies" in rendered


def test_render_settings_composes_compact_pacing_with_beginner_scaffold() -> None:
    """Compact style still preserves enough scaffolding for a new user."""
    settings = UserProfileSettings(
        role=JobRole.STUDENT_JUNIOR,
        experience_years=ExperienceYears.ZERO_TO_ONE,
        brand_strategy_familiarity=BrandStrategyFamiliarity.NEW,
        mentoring_style=MentoringStyle.COMPACT_FIRST,
        onboarding_completed=True,
    )

    rendered = render_user_profile_settings(settings)

    assert "Pacing: Start from the current decision or blocker" in rendered
    assert "Scaffolding: Use plain language" in rendered
    assert "keep any teaching moment to one sentence" in rendered
    assert "pair concrete examples with the next decision" in rendered


def test_render_settings_composes_balanced_pacing_with_advanced_scaffold() -> None:
    """Balanced density can still stay senior when the user profile is advanced."""
    settings = UserProfileSettings(
        role=JobRole.BRAND_MANAGER,
        experience_years=ExperienceYears.FIVE_PLUS,
        brand_strategy_familiarity=BrandStrategyFamiliarity.ADVANCED,
        mentoring_style=MentoringStyle.BALANCED,
        stakeholder_context=StakeholderContext.CLIENT,
        onboarding_completed=True,
    )

    rendered = render_user_profile_settings(settings)

    assert "Pacing: Orient the decision briefly" in rendered
    assert "Scaffolding: Use concise business language" in rendered
    assert "name frameworks only when they change the decision" in rendered
    assert "surface options and tradeoffs in compact language" in rendered
    assert "client-facing and approval-ready" in rendered


def test_apply_profile_settings_replaces_only_managed_block() -> None:
    """Refreshing onboarding leaves agent-learned profile notes intact."""
    initial = apply_profile_settings_to_profile(
        "# User Profile\n\n## Communication Preferences\nUser prefers Vietnamese.\n",
        UserProfileSettings(
            role=JobRole.MARKETING_EXECUTIVE,
            mentoring_style=MentoringStyle.BALANCED,
            onboarding_completed=True,
        ),
    )
    updated = apply_profile_settings_to_profile(
        initial,
        UserProfileSettings(
            role=JobRole.BRAND_MANAGER,
            mentoring_style=MentoringStyle.COMPACT_FIRST,
            onboarding_completed=True,
        ),
    )

    assert updated.count("<!-- brandmind-profile-settings:start -->") == 1
    assert "Role: Brand Manager" in updated
    assert "Role: Marketing Executive" not in updated
    assert "User prefers Vietnamese." in updated


def test_save_profile_settings_persists_json_and_profile_markdown(
    tmp_path: Path,
) -> None:
    """Saving settings updates both the structured file and prompt surface."""
    settings = UserProfileSettings(
        job_domain=JobDomain.FB,
        role=JobRole.MARKETING_EXECUTIVE,
        experience_years=ExperienceYears.THREE_TO_FIVE,
        brand_strategy_familiarity=BrandStrategyFamiliarity.COMFORTABLE,
        mentoring_style=MentoringStyle.COMPACT_FIRST,
        stakeholder_context=StakeholderContext.BOSS,
        onboarding_completed=True,
    )

    saved = save_user_profile_settings(settings, home=tmp_path)

    settings_path = tmp_path / "user" / "profile_settings.json"
    profile_path = tmp_path / "user" / "profile.md"
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    profile = profile_path.read_text(encoding="utf-8")

    assert saved.updated_at
    assert payload["role"] == "marketing_executive"
    assert payload["mentoring_style"] == "compact_first"
    assert "Role: Marketing Executive" in profile
    assert "Preferred mentoring density: Compact first" in profile


def test_load_profile_settings_returns_default_for_missing_file(
    tmp_path: Path,
) -> None:
    """Profile settings are optional until onboarding completes."""
    settings = load_user_profile_settings(home=tmp_path)

    assert settings == default_user_profile_settings()


def test_proactive_context_reads_saved_onboarding_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Rendered settings become normal profile context for the mentor."""
    monkeypatch.setattr(proactive_mod.workspace_mod, "BRANDMIND_HOME", tmp_path)
    monkeypatch.setattr(workspace_mod, "BRANDMIND_HOME", tmp_path)
    save_user_profile_settings(
        UserProfileSettings(
            role=JobRole.BRAND_MANAGER,
            brand_strategy_familiarity=BrandStrategyFamiliarity.ADVANCED,
            mentoring_style=MentoringStyle.COMPACT_FIRST,
            onboarding_completed=True,
        ),
        home=tmp_path,
    )

    packet = ProactiveContextBuilder().build(
        "Tôi muốn làm brand strategy cho một nhà hàng mới.",
    )
    rendered = packet.to_prompt()

    assert "User profile" in rendered
    assert "Brand Manager" in rendered
    assert "Compact first" in rendered
    assert "ask_needed_blockers" in rendered
