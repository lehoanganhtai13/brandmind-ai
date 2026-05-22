"""User profile settings for BrandMind personalization.

This module owns the structured onboarding settings that the Web UI and TUI
can collect before a strategy session starts. It renders those settings into
the durable ``/user/profile.md`` prompt surface as a compact managed block so
the agent gets a useful personalization prior without locking its behavior.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field

import shared.workspace as workspace_mod

PROFILE_SETTINGS_FILENAME = "profile_settings.json"
PROFILE_SETTINGS_START = "<!-- brandmind-profile-settings:start -->"
PROFILE_SETTINGS_END = "<!-- brandmind-profile-settings:end -->"
EnumT = TypeVar("EnumT", bound=Enum)


class JobDomain(str, Enum):
    """User's main working domain."""

    UNKNOWN = "unknown"
    FB = "fb"
    RETAIL = "retail"
    SERVICE = "service"
    AGENCY = "agency"
    EDUCATION = "education"
    OTHER = "other"


class JobRole(str, Enum):
    """User's current role in the work."""

    UNKNOWN = "unknown"
    OWNER_FOUNDER = "owner_founder"
    MARKETING_EXECUTIVE = "marketing_executive"
    BRAND_MANAGER = "brand_manager"
    AGENCY_CONSULTANT = "agency_consultant"
    STUDENT_JUNIOR = "student_junior"
    OTHER = "other"


class ExperienceYears(str, Enum):
    """Approximate marketing or business experience."""

    UNKNOWN = "unknown"
    ZERO_TO_ONE = "0_1"
    ONE_TO_THREE = "1_3"
    THREE_TO_FIVE = "3_5"
    FIVE_PLUS = "5_plus"


class BrandStrategyFamiliarity(str, Enum):
    """How familiar the user is with brand-strategy work."""

    UNKNOWN = "unknown"
    NEW = "new"
    BASIC = "basic"
    COMFORTABLE = "comfortable"
    ADVANCED = "advanced"


class MentoringStyle(str, Enum):
    """Preferred default density for BrandMind's mentoring."""

    COMPACT_FIRST = "compact_first"
    BALANCED = "balanced"
    TEACHING_FIRST = "teaching_first"


class StakeholderContext(str, Enum):
    """Who the user usually needs to persuade with the output."""

    UNKNOWN = "unknown"
    SELF = "self"
    BOSS = "boss"
    CLIENT = "client"
    INVESTOR = "investor"
    TEAM = "team"


class UserProfileSettings(BaseModel):
    """Structured onboarding settings used to seed BrandMind personalization."""

    job_domain: JobDomain = Field(
        default=JobDomain.UNKNOWN,
        description="Main domain the user works in.",
    )
    role: JobRole = Field(
        default=JobRole.UNKNOWN,
        description="User role or working position.",
    )
    experience_years: ExperienceYears = Field(
        default=ExperienceYears.UNKNOWN,
        description="Approximate marketing or business experience.",
    )
    brand_strategy_familiarity: BrandStrategyFamiliarity = Field(
        default=BrandStrategyFamiliarity.UNKNOWN,
        description="How familiar the user is with brand strategy.",
    )
    mentoring_style: MentoringStyle = Field(
        default=MentoringStyle.BALANCED,
        description="Preferred default mentoring density.",
    )
    stakeholder_context: StakeholderContext = Field(
        default=StakeholderContext.UNKNOWN,
        description="Primary stakeholder the user needs to convince.",
    )
    onboarding_completed: bool = Field(
        default=False,
        description="Whether the user has completed or skipped onboarding.",
    )
    updated_at: str | None = Field(
        default=None,
        description="UTC timestamp when these settings were last saved.",
    )


class UserProfileOption(BaseModel):
    """One UI option for a profile-setting field."""

    value: str
    label: str
    description: str = ""


class UserProfileSettingsOptions(BaseModel):
    """Option lists the UI can render without duplicating backend mappings."""

    job_domain: list[UserProfileOption]
    role: list[UserProfileOption]
    experience_years: list[UserProfileOption]
    brand_strategy_familiarity: list[UserProfileOption]
    mentoring_style: list[UserProfileOption]
    stakeholder_context: list[UserProfileOption]


_DOMAIN_LABELS = {
    JobDomain.UNKNOWN: ("Unknown", "Use the default BrandMind strategy posture."),
    JobDomain.FB: ("F&B", "Food and beverage brands, venues, menus, and hospitality."),
    JobDomain.RETAIL: ("Retail", "Retail products, stores, and consumer commerce."),
    JobDomain.SERVICE: ("Service", "Service businesses and local customer experience."),
    JobDomain.AGENCY: ("Agency", "Agency or consulting work for client brands."),
    JobDomain.EDUCATION: ("Education", "Student, teaching, or learning context."),
    JobDomain.OTHER: ("Other", "A different domain not listed here."),
}
_ROLE_LABELS = {
    JobRole.UNKNOWN: ("Unknown", "Let BrandMind infer cautiously from the chat."),
    JobRole.OWNER_FOUNDER: ("Owner / Founder", "Owns business direction and budget."),
    JobRole.MARKETING_EXECUTIVE: (
        "Marketing Executive",
        "Executes marketing work and needs practical next steps.",
    ),
    JobRole.BRAND_MANAGER: (
        "Brand Manager",
        "Owns brand direction and stakeholder-ready decisions.",
    ),
    JobRole.AGENCY_CONSULTANT: (
        "Agency / Consultant",
        "Works on strategy for client stakeholders.",
    ),
    JobRole.STUDENT_JUNIOR: (
        "Student / Junior",
        "Needs more scaffolding and concept explanation.",
    ),
    JobRole.OTHER: ("Other", "A role not listed here."),
}
_EXPERIENCE_LABELS = {
    ExperienceYears.UNKNOWN: ("Unknown", "Use a balanced default."),
    ExperienceYears.ZERO_TO_ONE: ("0-1 years", "New to marketing or brand work."),
    ExperienceYears.ONE_TO_THREE: ("1-3 years", "Some practical exposure."),
    ExperienceYears.THREE_TO_FIVE: ("3-5 years", "Experienced working marketer."),
    ExperienceYears.FIVE_PLUS: ("5+ years", "Senior or deeply experienced user."),
}
_FAMILIARITY_LABELS = {
    BrandStrategyFamiliarity.UNKNOWN: ("Unknown", "Use a balanced default."),
    BrandStrategyFamiliarity.NEW: (
        "New",
        "Explain concepts before asking the user to apply them.",
    ),
    BrandStrategyFamiliarity.BASIC: (
        "Basic",
        "Use plain language and brief concept framing.",
    ),
    BrandStrategyFamiliarity.COMFORTABLE: (
        "Comfortable",
        "Go straight to decisions with compact rationale.",
    ),
    BrandStrategyFamiliarity.ADVANCED: (
        "Advanced",
        "Use concise strategic language and expand only on request.",
    ),
}
_MENTORING_LABELS = {
    MentoringStyle.COMPACT_FIRST: (
        "Compact first",
        "Start from the decision point; explain only what is needed now.",
    ),
    MentoringStyle.BALANCED: (
        "Balanced",
        "Give enough context to orient the decision without lecturing.",
    ),
    MentoringStyle.TEACHING_FIRST: (
        "Teach step by step",
        "Explain the principle before asking the user to apply it.",
    ),
}
_STAKEHOLDER_LABELS = {
    StakeholderContext.UNKNOWN: (
        "Unknown",
        "Do not assume a stakeholder unless the user says so.",
    ),
    StakeholderContext.SELF: ("Self", "The user is deciding for their own work."),
    StakeholderContext.BOSS: (
        "Boss / Internal stakeholder",
        "Make recommendations easier to defend upward.",
    ),
    StakeholderContext.CLIENT: (
        "Client",
        "Frame outputs for client-facing approval.",
    ),
    StakeholderContext.INVESTOR: (
        "Investor",
        "Make assumptions and business logic explicit.",
    ),
    StakeholderContext.TEAM: (
        "Team",
        "Make decisions easy for a team to execute.",
    ),
}


def default_user_profile_settings() -> UserProfileSettings:
    """Return BrandMind's safe personalization fallback."""
    return UserProfileSettings()


def get_user_profile_settings_options() -> UserProfileSettingsOptions:
    """Return option lists for onboarding UI controls."""
    return UserProfileSettingsOptions(
        job_domain=_options_from_labels(_DOMAIN_LABELS),
        role=_options_from_labels(_ROLE_LABELS),
        experience_years=_options_from_labels(_EXPERIENCE_LABELS),
        brand_strategy_familiarity=_options_from_labels(_FAMILIARITY_LABELS),
        mentoring_style=_options_from_labels(_MENTORING_LABELS),
        stakeholder_context=_options_from_labels(_STAKEHOLDER_LABELS),
    )


def load_user_profile_settings(
    home: Path | None = None,
) -> UserProfileSettings:
    """Load saved profile settings, returning defaults when unavailable."""
    settings_path = _settings_path(home)
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
        return UserProfileSettings.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError):
        return default_user_profile_settings()


def save_user_profile_settings(
    settings: UserProfileSettings,
    home: Path | None = None,
) -> UserProfileSettings:
    """Persist settings and refresh the managed profile prompt block."""
    saved = settings.model_copy(
        update={"updated_at": datetime.now(timezone.utc).isoformat()}
    )
    user_dir = _user_dir(home)
    user_dir.mkdir(parents=True, exist_ok=True)
    _settings_path(home).write_text(
        saved.model_dump_json(indent=2),
        encoding="utf-8",
    )

    profile_path = _profile_path(home)
    current_profile = _read_or_default_profile(profile_path)
    updated_profile = apply_profile_settings_to_profile(current_profile, saved)
    profile_path.write_text(updated_profile, encoding="utf-8")
    return saved


def render_user_profile_settings(settings: UserProfileSettings) -> str:
    """Render settings as a compact prompt-friendly Markdown block."""
    source = (
        "onboarding settings"
        if settings.onboarding_completed
        else "default fallback settings"
    )
    confidence = "explicit user-provided" if settings.onboarding_completed else "low"
    guidance_lines = _agent_guidance_lines(settings)

    return "\n".join(
        [
            PROFILE_SETTINGS_START,
            "## Onboarding Profile",
            f"Source: {source}",
            f"Confidence: {confidence}",
            "",
            "- Job domain: " + _label(settings.job_domain, _DOMAIN_LABELS),
            "- Role: " + _label(settings.role, _ROLE_LABELS),
            "- Experience: " + _label(settings.experience_years, _EXPERIENCE_LABELS),
            "- Brand strategy familiarity: "
            + _label(settings.brand_strategy_familiarity, _FAMILIARITY_LABELS),
            "- Preferred mentoring density: "
            + _label(settings.mentoring_style, _MENTORING_LABELS),
            "- Stakeholder context: "
            + _label(settings.stakeholder_context, _STAKEHOLDER_LABELS),
            "",
            "Agent guidance:",
            *[f"- {line}" for line in guidance_lines],
            PROFILE_SETTINGS_END,
        ]
    )


def apply_profile_settings_to_profile(
    profile_text: str,
    settings: UserProfileSettings,
) -> str:
    """Insert or replace the managed settings block in ``profile.md``."""
    block = render_user_profile_settings(settings)
    if PROFILE_SETTINGS_START in profile_text and PROFILE_SETTINGS_END in profile_text:
        before, rest = profile_text.split(PROFILE_SETTINGS_START, 1)
        _, after = rest.split(PROFILE_SETTINGS_END, 1)
        updated = before.rstrip() + "\n\n" + block + "\n" + after.lstrip()
        return updated.rstrip() + "\n"

    text = profile_text.strip() or workspace_mod.USER_PROFILE_TEMPLATE.strip()
    lines = text.splitlines()
    if lines and lines[0].strip() == "# User Profile":
        profile_lines = [lines[0], "", block, "", *lines[1:]]
        return "\n".join(profile_lines).rstrip() + "\n"

    return f"# User Profile\n\n{block}\n\n{text}\n"


def read_user_profile_markdown(home: Path | None = None) -> str:
    """Return the current profile markdown, or the empty profile template."""
    return _read_or_default_profile(_profile_path(home))


def _settings_path(home: Path | None) -> Path:
    return _user_dir(home) / PROFILE_SETTINGS_FILENAME


def _profile_path(home: Path | None) -> Path:
    return _user_dir(home) / "profile.md"


def _user_dir(home: Path | None) -> Path:
    root = home or workspace_mod.BRANDMIND_HOME
    return root / "user"


def _read_or_default_profile(profile_path: Path) -> str:
    try:
        return profile_path.read_text(encoding="utf-8")
    except OSError:
        return workspace_mod.USER_PROFILE_TEMPLATE


def _options_from_labels(
    labels: Mapping[EnumT, tuple[str, str]],
) -> list[UserProfileOption]:
    return [
        UserProfileOption(value=item.value, label=label, description=description)
        for item, (label, description) in labels.items()
    ]


def _label(value: EnumT, labels: Mapping[EnumT, tuple[str, str]]) -> str:
    label, _ = labels[value]
    return label


def _agent_guidance_lines(settings: UserProfileSettings) -> list[str]:
    """Compose prompt guidance from profile fields without creating hard modes."""
    return [
        ("Use these settings as an initial calibration prior, not as a fixed mode."),
        "Pacing: " + _pacing_guidance(settings),
        "Scaffolding: " + _scaffolding_guidance(settings),
        "Decision framing: " + _decision_framing_guidance(settings),
        "Domain lens: " + _domain_guidance(settings),
        (
            "Adaptation: recalibrate from the user's actual replies and save "
            "durable profile changes only with source evidence."
        ),
    ]


def _pacing_guidance(settings: UserProfileSettings) -> str:
    """Translate mentoring density into turn-level pacing guidance."""
    if settings.mentoring_style is MentoringStyle.TEACHING_FIRST:
        return (
            "Give a brief concept frame when it helps the current decision, "
            "then ask the next blocker."
        )
    if settings.mentoring_style is MentoringStyle.COMPACT_FIRST:
        return (
            "Start from the current decision or blocker, then add only the "
            "rationale needed now."
        )
    return (
        "Orient the decision briefly, then ask the next blocker without turning "
        "the reply into an intake form."
    )


def _scaffolding_guidance(settings: UserProfileSettings) -> str:
    """Estimate the starting scaffold from role, experience, and familiarity."""
    competence = _competence_estimate(settings)
    if competence == "advanced":
        return (
            "Use concise business language and move to the next blocker; name "
            "frameworks only when they change the decision."
        )
    if competence == "beginner":
        if settings.mentoring_style is MentoringStyle.COMPACT_FIRST:
            return (
                "Use plain language and keep any teaching moment to one sentence "
                "before asking the user to apply it."
            )
        return (
            "Use plain language and one useful teaching moment before asking the "
            "user to apply a new concept."
        )
    return (
        "Use plain language with compact rationale; explain a framework only at "
        "first use or when it affects the decision."
    )


def _competence_estimate(settings: UserProfileSettings) -> str:
    """Return a coarse starting competence estimate for scaffolding."""
    score = 0
    if settings.brand_strategy_familiarity in {
        BrandStrategyFamiliarity.COMFORTABLE,
        BrandStrategyFamiliarity.ADVANCED,
    }:
        score += 2
    if settings.brand_strategy_familiarity in {
        BrandStrategyFamiliarity.NEW,
        BrandStrategyFamiliarity.BASIC,
    }:
        score -= 2
    if settings.experience_years in {
        ExperienceYears.THREE_TO_FIVE,
        ExperienceYears.FIVE_PLUS,
    }:
        score += 1
    if settings.experience_years is ExperienceYears.ZERO_TO_ONE:
        score -= 1
    if settings.role in {
        JobRole.BRAND_MANAGER,
        JobRole.AGENCY_CONSULTANT,
        JobRole.OWNER_FOUNDER,
    }:
        score += 1
    if settings.role is JobRole.STUDENT_JUNIOR:
        score -= 1

    if score >= 3:
        return "advanced"
    if score <= -2:
        return "beginner"
    return "developing"


def _decision_framing_guidance(settings: UserProfileSettings) -> str:
    """Compose role and stakeholder into a decision-framing hint."""
    role_guidance = {
        JobRole.OWNER_FOUNDER: (
            "connect brand choices to budget, operations, revenue risk, and "
            "owner decisions"
        ),
        JobRole.MARKETING_EXECUTIVE: (
            "prioritize practical next actions and recommendations the user can "
            "bring to a manager"
        ),
        JobRole.BRAND_MANAGER: (
            "surface options and tradeoffs in compact language without basic "
            "brand lectures"
        ),
        JobRole.AGENCY_CONSULTANT: (
            "make reasoning client-ready, with assumptions and tradeoffs clear"
        ),
        JobRole.STUDENT_JUNIOR: (
            "pair concrete examples with the next decision so learning stays usable"
        ),
        JobRole.OTHER: "adapt the framing to the user's stated working role",
        JobRole.UNKNOWN: "infer role cautiously from the chat before specializing",
    }[settings.role]
    stakeholder_guidance = _stakeholder_guidance(settings.stakeholder_context)
    return f"{role_guidance}; {stakeholder_guidance}."


def _stakeholder_guidance(stakeholder: StakeholderContext) -> str:
    """Return stakeholder-specific pressure without changing the strategy process."""
    return {
        StakeholderContext.BOSS: (
            "make the next decision easy to defend upward without a long theory preface"
        ),
        StakeholderContext.CLIENT: "make the output client-facing and approval-ready",
        StakeholderContext.INVESTOR: "make assumptions and business logic explicit",
        StakeholderContext.TEAM: "make the next actions easy for a team to execute",
        StakeholderContext.SELF: "support the user's own decision-making",
        StakeholderContext.UNKNOWN: (
            "do not assume an external stakeholder until the user says so"
        ),
    }[stakeholder]


def _domain_guidance(settings: UserProfileSettings) -> str:
    """Return domain-specific context cues for the first strategy turns."""
    return {
        JobDomain.FB: (
            "for F&B, ground questions in customer occasion, venue experience, "
            "offer or menu, location, booking or revenue, and repeat behavior."
        ),
        JobDomain.RETAIL: (
            "for retail, ground questions in shopper mission, assortment, "
            "channel, margin, conversion, and repeat purchase."
        ),
        JobDomain.SERVICE: (
            "for service brands, ground questions in trust, service journey, "
            "proof, lead flow, and repeat usage."
        ),
        JobDomain.AGENCY: (
            "for agency work, separate end-client evidence from the user's own "
            "working preferences."
        ),
        JobDomain.EDUCATION: (
            "for education context, keep examples concrete and learning-oriented."
        ),
        JobDomain.OTHER: "use the user's stated domain as the evidence frame.",
        JobDomain.UNKNOWN: (
            "do not force industry assumptions; infer cautiously and ask only "
            "for blockers that cannot be collected elsewhere."
        ),
    }[settings.job_domain]
