"""Regression tests for runtime prompt hygiene."""

from __future__ import annotations

import re
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
    / "src/shared/src/shared/agent_skills/brand_strategy"
    / "brand-strategy-orchestrator/SKILL.md"
)
_COMMUNICATION_SKILL = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy"
    / "brand-communication-planning/SKILL.md"
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
_ORCHESTRATOR_REFERENCES = (
    _PROJECT_ROOT
    / "src/shared/src/shared/agent_skills/brand_strategy/brand-strategy-orchestrator"
    / "references"
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


def test_brand_key_dispatch_preserves_prioritized_customer_insight() -> None:
    """Brand Key dispatch should not rewrite the agreed Phase 1 insight."""
    assert "Phase 1 prioritized customer insight" in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "copy that wording exactly into the Brand Key dispatch" in (
        BRAND_STRATEGY_SYSTEM_PROMPT
    )
    assert "do not replace it with a more dramatic adjacent hosting insight" in (
        BRAND_STRATEGY_SYSTEM_PROMPT
    )


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
        (
            "External market and social research tools are not part "
            "of the main-agent surface"
        ),
        "Explicit research request override",
        "dispatch one bounded specialist pass",
        "Live browser authorization",
        "LIVE_BROWSER_VERIFICATION_APPROVED",
        'do not present a "market pulse"',
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
        "Public fact verification",
        "Keep the source ledger internally",
        "normal chat does not need visible source labels",
        "quick public check was inconclusive",
        "Do not use vague unsourced discovery phrases in any language",
        "Adaptive personalization",
        "interaction patterns across turns",
        "stakeholder-defense logic",
        "Turn pacing and phase humility",
        "Do not add extra question marks inside examples",
        "ask the smallest set of blocking questions",
        "ask one decision-changing blocker",
        "Treat scope as tentative",
        "natural step descriptions",
        "Backstage labels, business language",
        "Phase names and the number of phases are workflow state",
        "Artifact labels, user language",
        "File-format labels such as DOCX, PPTX, and XLSX are implementation details",
        "default to human artifact names",
        'do not announce a "6-step" or "6-phase" process',
        'do not say "Phase 0"',
        "The user is learning brand strategy, not operating the state machine",
        "diagnose the problem, audit existing equity, read the market",
        'say "brand equity audit" or "equity audit step" rather than "Phase 0.5"',
        "INTERNAL WORKFLOW",
        "natural consulting engagement",
        "phase count, and raw phase labels",
        "The opening reply is a diagnosis turn, not a process-map turn",
        "USER-FACING LANGUAGE CHECK",
        'Say "brand equity audit" instead of "Phase 0.5"',
        "not routed through a state machine",
        "only when the evidence is no longer tentative",
        "Ask the smallest set of structured blocking questions",
    )
    for phrase in expected_phrases:
        assert phrase in BRAND_STRATEGY_SYSTEM_PROMPT


def test_orchestrator_skill_keeps_phase_labels_internal() -> None:
    """Runtime skill should translate phase labels before speaking to users."""
    skill_text = _ORCHESTRATOR_SKILL.read_text(encoding="utf-8")

    assert "Phase numbers are internal navigation labels" in skill_text
    assert "natural step descriptions in the user's language" in skill_text
    assert "raw phase IDs for tool calls, todos, quality gates" in skill_text
    assert "OPENING-TURN GUARD" in skill_text
    assert "do not announce the phase count" in skill_text
    assert 'raw labels such as "Phase 0"' in skill_text
    assert "ask one decision-changing question" in skill_text
    assert 'Say "brand equity audit" instead of "Phase 0.5"' in skill_text
    assert "Brief the user on the next business task" in skill_text
    assert "`report_progress` is an internal operation, not a chat topic" in (
        skill_text
    )
    assert "business transition and next decision surface" in skill_text
    assert "Brief the user on Phase N+1" not in skill_text
    assert "not shown the state machine" in (skill_text)


def test_tool_invocation_example_avoids_user_facing_phase_labels() -> None:
    """Natural-language examples should not teach raw phase labels."""
    assert "I've advanced you to Phase 5" not in BRAND_STRATEGY_SYSTEM_PROMPT
    assert "we are ready to package the deliverables" in (BRAND_STRATEGY_SYSTEM_PROMPT)


def test_phase_0_reference_keeps_raw_phase_labels_internal() -> None:
    """Opening reference should not prime user-facing raw phase labels."""
    reference_text = _PHASE_0_REFERENCE.read_text(encoding="utf-8")

    assert "Do not announce the full workflow" in reference_text
    assert 'the raw label "Phase 0"' in reference_text
    assert "Staged Question Bank" in reference_text
    assert "not as a user-facing intake form" in reference_text
    assert "Do not copy all questions into chat" in reference_text
    assert "working hypothesis" in reference_text
    assert "Internal transition operation" in reference_text
    assert "Keep the tool name and call syntax out of chat" in reference_text


def test_phase_references_mark_progress_calls_as_internal() -> None:
    """Loaded phase references should not prime visible tool-call narration."""
    reference_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(_ORCHESTRATOR_REFERENCES.glob("phase_*.md"))
    )

    assert "**BEFORE proceeding**" not in reference_text
    assert "Internal transition operation" in reference_text
    assert "Keep the tool name and call syntax out of chat" in reference_text


def test_prompt_surfaces_keep_instruction_language_consistent() -> None:
    """Avoid mixing Vietnamese examples into otherwise English instructions."""
    orchestrator_text = _ORCHESTRATOR_SKILL.read_text(encoding="utf-8")
    communication_text = _COMMUNICATION_SKILL.read_text(encoding="utf-8")
    reference_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(_ORCHESTRATOR_REFERENCES.glob("*.md"))
    )
    combined = "\n".join(
        (
            BRAND_STRATEGY_SYSTEM_PROMPT,
            orchestrator_text,
            communication_text,
            reference_text,
        )
    )
    mixed_language_examples = (
        "Em thường",
        "bước chẩn đoán",
        "bước tiếp theo",
        "chúng ta",
        "Tôi nhìn",
        "Im lặng",
        "Sau câu hỏi",
        "Đừng lấp đầy",
    )

    for phrase in mixed_language_examples:
        assert phrase not in combined


def test_prompt_surfaces_do_not_embed_vietnamese_diacritic_examples() -> None:
    """Keep prompt instructions in one language; responses localize at runtime."""
    orchestrator_text = _ORCHESTRATOR_SKILL.read_text(encoding="utf-8")
    communication_text = _COMMUNICATION_SKILL.read_text(encoding="utf-8")
    reference_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(_ORCHESTRATOR_REFERENCES.glob("*.md"))
    )
    combined = "\n".join(
        (
            BRAND_STRATEGY_SYSTEM_PROMPT,
            orchestrator_text,
            communication_text,
            reference_text,
        )
    )
    vietnamese_diacritics = (
        r"[ăâêôơưđáàảãạấầẩẫậắằẳẵặ"
        r"éèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộ"
        r"ớờởỡợúùủũụứừửữựýỳỷỹỵ]"
    )

    assert not re.search(
        vietnamese_diacritics,
        combined,
        flags=re.IGNORECASE,
    )


def test_communication_skill_reinforces_phase_5_artifact_defense() -> None:
    """Keep Phase 5 skill aligned with artifact rationale and ROI gates."""
    skill_text = _COMMUNICATION_SKILL.read_text(encoding="utf-8")
    expected_phrases = (
        "pre-dispatch artifact rationale",
        "Brand Key one-pager",
        "Strategy DOCX",
        "Executive PPTX",
        "KPI XLSX",
        "budget defensibility line",
        "break-even or risk note",
    )

    for phrase in expected_phrases:
        assert phrase in skill_text


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
    specialist_block = source_text.split("specialist_research_tools: list[Any] = [", 1)[
        1
    ]
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
        "Browser/live social verification is outside your normal tool surface",
        "Source-grounding contract for public facts",
        "must carry the exact source platform/title/URL",
        "exact quote/snippet",
        "return a compact source ledger",
        "Put unsourced or quote-less items in an `Inconclusive` row",
        "Facts without exact quote/snippet support must remain `INCONCLUSIVE`",
        "INCONCLUSIVE",
    )
    for phrase in expected_phrases:
        assert phrase in MARKET_RESEARCH_SYSTEM_PROMPT


def test_social_media_routing_requires_live_verification_authorization() -> None:
    """Keep social audits from launching browser loops during strategy mentoring."""
    source_text = _SUBAGENT_MIDDLEWARE.read_text(encoding="utf-8")
    expected_phrases = (
        "Dispatch only when the user explicitly",
        "Do not dispatch for strategic reasoning from",
        "LIVE_BROWSER_VERIFICATION_APPROVED",
        "use lightweight search/scrape",
        "report the gap",
    )
    for phrase in expected_phrases:
        assert phrase in source_text

    social_expected = (
        "assignment contains `LIVE_BROWSER_VERIFICATION_APPROVED`",
        "If the assignment does not explicitly ask for live verification",
        "no more than 3 `search_web` queries",
        "report the uncertainty and move on",
    )
    for phrase in social_expected:
        assert phrase in SOCIAL_MEDIA_ANALYST_SYSTEM_PROMPT


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
        'Do not present a "market scan" from KG/doc search alone',
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
        (
            "Browser/live social verification is not part of the "
            "market-research default surface"
        ),
        "Stop collecting",
    )
    for phrase in expected_phrases:
        assert phrase in skill_text
