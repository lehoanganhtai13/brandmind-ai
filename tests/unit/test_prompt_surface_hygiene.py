"""Regression tests for runtime prompt hygiene."""

from __future__ import annotations

from pathlib import Path

from core.brand_strategy.content_check import PHASE_DELIVERABLE_SPECS
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
_ORCHESTRATOR_SKILL = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator/SKILL.md"
)
_PHASE_1_REFERENCE = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator"
    / "references/phase_1_research.md"
)
_PHASE_0_REFERENCE = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator"
    / "references/phase_0_diagnosis.md"
)
_SUBAGENT_MIDDLEWARE = (
    _PROJECT_ROOT / "src/core/src/core/brand_strategy/subagents/middleware.py"
)
_AGENT_CONFIG = _PROJECT_ROOT / "src/core/src/core/brand_strategy/agent_config.py"


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
        "Decision-grade market understanding",
        "Do not delegate market research by default",
        'do not call `task(subagent_type="market-research")`',
        "search only if truly needed",
        "Do not launch parallel browser deep-dives",
        "External market and social research tools are not part of the main-agent surface",
        "Explicit research request override",
        "dispatch one bounded `market-research` specialist pass",
        "do not present a \"market pulse\"",
        'use `task(subagent_type="market-research")` before claiming you scanned',
        "dispatch a bounded specialist brief",
    )
    for phrase in expected_phrases:
        assert phrase in BRAND_STRATEGY_SYSTEM_PROMPT


def test_main_prompt_has_chat_process_quality_guardrails() -> None:
    """Keep chat-process fixes focused on evidence, pacing, and personalization."""
    expected_phrases = (
        "Framework-minimal mentoring",
        "Frameworks are scaffolds, not the product",
        "teach at most one named lens",
        "Evidence humility",
        "what the user supplied, what a tool/source verified",
        "Do not invent credentials",
        "Adaptive personalization",
        "interaction patterns across turns",
        "Em thường cần defend với sếp",
        "Turn pacing and phase humility",
        "ask at most three blocking questions",
        "Treat scope as tentative",
        "prefer \"bước chẩn đoán\"",
        "only when the evidence is no longer tentative",
        "The opening reply is not a workflow-map turn",
        "Ask 2-3 structured blocking questions first",
    )
    for phrase in expected_phrases:
        assert phrase in BRAND_STRATEGY_SYSTEM_PROMPT


def test_orchestrator_skill_keeps_phase_labels_internal() -> None:
    """Runtime skill should translate phase labels before speaking to users."""
    skill_text = _ORCHESTRATOR_SKILL.read_text(encoding="utf-8")

    assert "Phase numbers are internal navigation labels" in skill_text
    assert "bước chẩn đoán" in skill_text
    assert "Never make the user feel they are reading internal process labels" in (
        skill_text
    )


def test_phase_4_content_gate_avoids_named_framework_overload() -> None:
    """Phase 4 gate should require customer mechanics, not framework name-dropping."""
    spec = PHASE_DELIVERABLE_SPECS["phase_4"]

    assert "Persuasion mechanics" in spec
    assert "Customer journey flow" in spec
    assert "named frameworks are optional" in spec
    assert "do not require named funnel jargon" in spec
    assert "Cialdini persuasion" not in spec
    assert "AIDA mapping" not in spec


def test_main_agent_keeps_external_research_specialist_owned() -> None:
    """Keep web/social evidence tools out of the orchestrator's direct surface."""
    source_text = _AGENT_CONFIG.read_text(encoding="utf-8")
    main_tools_block = source_text.split("main_agent_tools: list[Any] = [", 1)[1]
    main_tools_block = main_tools_block.split("specialist_research_tools", 1)[0]
    specialist_block = source_text.split("specialist_research_tools: list[Any] = [", 1)[1]
    specialist_block = specialist_block.split("specialist_generation_tools", 1)[0]

    external_tools = (
        "search_web",
        "scrape_web_content",
        "browse_and_research",
        "deep_research",
        "analyze_social_profile",
        "get_search_autocomplete",
    )
    for tool_name in external_tools:
        assert tool_name not in main_tools_block
        assert tool_name in specialist_block

def test_brand_strategy_runtime_does_not_use_tool_warehouse() -> None:
    """Keep the orchestrator runtime free of stale ToolSearch instructions."""
    source_text = _AGENT_CONFIG.read_text(encoding="utf-8")
    forbidden_prompt_phrases = (
        "Tool Inventory",
        "Warehouse Pattern",
        "`tool_search(query)`",
        "`load_tools",
        "`unload_tools",
    )
    for phrase in forbidden_prompt_phrases:
        assert phrase not in BRAND_STRATEGY_SYSTEM_PROMPT

    forbidden_runtime_phrases = (
        "create_tool_search_middleware",
        "BRAND_STRATEGY_TOOL_CATALOG",
        "tool_search_middleware",
    )
    for phrase in forbidden_runtime_phrases:
        assert phrase not in source_text


def test_market_research_prompt_has_assignment_budget() -> None:
    """Keep the research specialist from expanding bounded Phase 1 briefs."""
    expected_phrases = (
        "ASSIGNMENT BUDGET COMES FIRST",
        "Do not expand a bounded request into a full market crawl",
        "no more than 3 `search_web` queries",
        "at most 5 queries per call",
        "Use `browse_and_research` only when the assignment explicitly requires",
    )
    for phrase in expected_phrases:
        assert phrase in MARKET_RESEARCH_SYSTEM_PROMPT


def test_market_research_task_description_requires_explicit_need() -> None:
    """Keep task routing from launching external research after sufficient input."""
    source_text = _SUBAGENT_MIDDLEWARE.read_text(encoding="utf-8")
    expected_phrases = (
        "Dispatch only when the user explicitly asks",
        "one critical missing fact",
        "cannot be resolved from the",
        "search only if truly",
        "synthesize that context in the main agent",
    )
    for phrase in expected_phrases:
        assert phrase in source_text


def test_workspace_protocol_prevents_file_write_retry_loops() -> None:
    """Keep phase transitions from burning turns on known existing files."""
    expected_phrases = (
        "Workspace write budget",
        "already exist",
        "one focused `edit_file` per touched file",
        "stop editing that file for the turn",
        "Do not create alternate workspace files",
    )
    for phrase in expected_phrases:
        assert phrase in BRAND_STRATEGY_SYSTEM_PROMPT


def test_phase_1_references_use_bounded_research_delegation() -> None:
    """Keep loaded Phase 1 guidance aligned with sufficiency-first routing."""
    orchestrator_text = _ORCHESTRATOR_SKILL.read_text(encoding="utf-8")
    phase_1_text = _PHASE_1_REFERENCE.read_text(encoding="utf-8")

    expected_orchestrator_phrases = (
        "decision-grade market synthesis",
        "only when a bounded evidence gap requires fresh research",
        "missing evidence question that would change the strategy",
    )
    for phrase in expected_orchestrator_phrases:
        assert phrase in orchestrator_text

    expected_phase_1_phrases = (
        "do not delegate by default",
        "Inventory first-party inputs",
        "If those inputs are enough",
        "delegate one bounded `market-research` pass",
    )
    for phrase in expected_phase_1_phrases:
        assert phrase in phase_1_text


def test_phase_0_reference_routes_explicit_research_requests() -> None:
    """Keep diagnosis runs from faking market scans with theory retrieval."""
    phase_0_text = _PHASE_0_REFERENCE.read_text(encoding="utf-8")
    expected_phrases = (
        "Explicit Research Request",
        "dispatch one bounded `market-research` pass",
        "Do not present a \"market scan\" from KG/doc search alone",
    )
    for phrase in expected_phrases:
        assert phrase in phase_0_text


def test_market_research_skill_has_input_sufficiency_budget() -> None:
    """Keep market-research sub-agent bounded when the user already provides data."""
    skill_text = _MARKET_RESEARCH_SKILL.read_text(encoding="utf-8")
    expected_phrases = (
        "INPUT SUFFICIENCY & TOOL BUDGET",
        "what the user already supplied",
        "first-party research input",
        "top 2-3 most decision-relevant competitors",
        "Respect the orchestrator's assignment budget",
        "Never pass more than 5 queries",
        "Use `browse_and_research` only when the assignment explicitly asks",
        "Stop collecting",
    )
    for phrase in expected_phrases:
        assert phrase in skill_text
