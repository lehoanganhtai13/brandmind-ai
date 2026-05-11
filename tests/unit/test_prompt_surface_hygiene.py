"""Regression tests for runtime prompt hygiene."""

from __future__ import annotations

from pathlib import Path

from prompts.brand_strategy.subagents import (
    CREATIVE_STUDIO_SYSTEM_PROMPT,
    DOCUMENT_GENERATOR_SYSTEM_PROMPT,
    MARKET_RESEARCH_SYSTEM_PROMPT,
    SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT,
)
from prompts.brand_strategy.system_prompt import BRAND_STRATEGY_SYSTEM_PROMPT

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MARKET_RESEARCH_SKILL = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy/market-research/SKILL.md"
)


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


def test_pptx_dispatch_schema_matches_generator_content_contract() -> None:
    """Keep PPTX instructions aligned with the generator's template-key input shape."""
    assert "=== PPTX CONTENT JSON MAP" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "phase_1_output" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "target_segments" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "phase_5_output" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert '"roadmap"' in BRAND_STRATEGY_SYSTEM_PROMPT
    assert '"measurement"' in BRAND_STRATEGY_SYSTEM_PROMPT

    assert "phase_5_roadmap_summary" not in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "phase_5_kpi_summary" not in BRAND_STRATEGY_SYSTEM_PROMPT
    assert 'phase_5_output: {"roadmap":' in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "generate_document.content` object" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "structured object/dict, not a quoted JSON string" in (
        DOCUMENT_GENERATOR_SYSTEM_PROMPT
    )
    docx_tool_line = next(
        line
        for line in DOCUMENT_GENERATOR_SYSTEM_PROMPT.splitlines()
        if line.startswith("1. `generate_document`")
    )
    assert "content` argument that is a JSON STRING" not in docx_tool_line
    assert "top-level `slides` argument" in DOCUMENT_GENERATOR_SYSTEM_PROMPT
    assert "accepts a `slides` argument" not in DOCUMENT_GENERATOR_SYSTEM_PROMPT


def test_xlsx_schema_matches_actionable_kpi_dashboard_contract() -> None:
    """Keep KPI spreadsheet instructions aligned with the dashboard template."""
    expected_columns = ("Method", "Baseline", "Cadence", "Owner", "Notes")
    for column in expected_columns:
        assert column in BRAND_STRATEGY_SYSTEM_PROMPT
        assert column in DOCUMENT_GENERATOR_SYSTEM_PROMPT
    assert "Monthly Tracking rows" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "exact KPI names and intent" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "do not replace an agreed metric" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "Every `Target` must include both value and deadline/horizon" in (
        DOCUMENT_GENERATOR_SYSTEM_PROMPT
    )


def test_main_prompt_has_scope_and_research_sufficiency_guardrails() -> None:
    """Protect repositioning runs from scope drift and browser-heavy over-research."""
    expected_phrases = (
        "Evidence discipline",
        "first-party evidence",
        "Scope classification guardrail",
        "premium extension",
        "REPOSITIONING",
        "Research sufficiency guardrail",
        "Do not launch parallel browser deep-dives",
    )
    for phrase in expected_phrases:
        assert phrase in BRAND_STRATEGY_SYSTEM_PROMPT


def test_market_research_skill_has_input_sufficiency_budget() -> None:
    """Keep market-research sub-agent bounded when the user already provides data."""
    skill_text = _MARKET_RESEARCH_SKILL.read_text(encoding="utf-8")
    expected_phrases = (
        "INPUT SUFFICIENCY & TOOL BUDGET",
        "what the user already supplied",
        "first-party research input",
        "top 2-3 most decision-relevant competitors",
        "Stop collecting",
    )
    for phrase in expected_phrases:
        assert phrase in skill_text
