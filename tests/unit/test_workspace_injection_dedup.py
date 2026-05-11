"""Unit tests for phase-section deduplication in workspace injection.

The contract: only the last occurrence of each duplicate top-level
``## Phase N`` section is kept; non-phase content and unique phase
sections are preserved with their original relative order.
"""

from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from core.brand_strategy.session import BrandStrategySession, set_active_session
from shared.agent_middlewares.workspace_injection.middleware import (
    WorkspaceInjectionMiddleware,
    _dedup_phase_sections,
)

_PREAMBLE = "# My Brand\n\nSession: abc123\n\n"

_PHASE_0 = (
    "## Phase 0: Business Context (COMPLETED)\n"
    "Brand scope: new_brand.\n\n"
)

_PHASE_1 = (
    "## Phase 1: Market Research (COMPLETED)\n"
    "SWOT and perceptual map completed.\n\n"
)

_PHASE_5_SKELETON = (
    "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\n"
    "Documents: DOCX, PPTX, XLSX, Brand Key.\n\n"
)

_PHASE_5_FULL = (
    "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\n"
    "Kế hoạch chiến lược đầy đủ tiếng Việt."
    " Roadmap 3 horizon. KPI 6 chỉ số.\n\n"
)


def test_no_duplicates_returns_unchanged() -> None:
    content = _PREAMBLE + _PHASE_0 + _PHASE_1 + _PHASE_5_FULL
    result, removed = _dedup_phase_sections(content)
    assert removed == 0
    assert result == content


def test_single_duplicate_keeps_last() -> None:
    content = _PREAMBLE + _PHASE_0 + _PHASE_1 + _PHASE_5_SKELETON + _PHASE_5_FULL
    result, removed = _dedup_phase_sections(content)
    assert removed == 1
    assert _PHASE_5_SKELETON not in result
    assert _PHASE_5_FULL in result


def test_preamble_and_unique_phases_preserved() -> None:
    content = _PREAMBLE + _PHASE_0 + _PHASE_1 + _PHASE_5_SKELETON + _PHASE_5_FULL
    result, removed = _dedup_phase_sections(content)
    assert _PREAMBLE in result
    assert _PHASE_0 in result
    assert _PHASE_1 in result


def test_relative_order_preserved() -> None:
    content = _PREAMBLE + _PHASE_0 + _PHASE_1 + _PHASE_5_SKELETON + _PHASE_5_FULL
    result, _ = _dedup_phase_sections(content)
    idx_0 = result.index("## Phase 0")
    idx_1 = result.index("## Phase 1")
    idx_5 = result.index("## Phase 5")
    assert idx_0 < idx_1 < idx_5


def test_empty_content_returns_unchanged() -> None:
    result, removed = _dedup_phase_sections("")
    assert removed == 0
    assert result == ""


def test_no_phase_sections_returns_unchanged() -> None:
    content = "# Title\n\nSome intro text without phase headers.\n"
    result, removed = _dedup_phase_sections(content)
    assert removed == 0
    assert result == content


def test_triple_duplicate_keeps_only_last() -> None:
    phase_v1 = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nVersion 1.\n\n"
    phase_v2 = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nVersion 2.\n\n"
    phase_v3 = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nVersion 3.\n\n"
    content = _PREAMBLE + phase_v1 + phase_v2 + phase_v3
    result, removed = _dedup_phase_sections(content)
    assert removed == 2
    assert "Version 1." not in result
    assert "Version 2." not in result
    assert "Version 3." in result


def test_multiple_phases_with_one_duplicate() -> None:
    phase_0_dup = (
        "## Phase 0: Business Context (COMPLETED)\n"
        "Duplicate context block.\n\n"
    )
    content = _PREAMBLE + _PHASE_0 + _PHASE_1 + phase_0_dup + _PHASE_5_FULL
    result, removed = _dedup_phase_sections(content)
    assert removed == 1
    assert "Brand scope: new_brand." not in result
    assert "Duplicate context block." in result
    assert _PHASE_1 in result
    assert _PHASE_5_FULL in result


_PHASE_0_5 = (
    "## Phase 0.5: Brand Heritage (COMPLETED)\n"
    "Heritage audit completed.\n\n"
)


def test_phase_0_and_0_5_coexist_unchanged() -> None:
    content = _PREAMBLE + _PHASE_0 + _PHASE_0_5 + _PHASE_1 + _PHASE_5_FULL
    result, removed = _dedup_phase_sections(content)
    assert removed == 0
    assert result == content


def test_duplicate_phase_0_5_keeps_last() -> None:
    phase_0_5_dup = (
        "## Phase 0.5: Brand Heritage (COMPLETED)\n"
        "Updated heritage content.\n\n"
    )
    content = _PREAMBLE + _PHASE_0 + _PHASE_0_5 + phase_0_5_dup + _PHASE_1
    result, removed = _dedup_phase_sections(content)
    assert removed == 1
    assert "Heritage audit completed." not in result
    assert "Updated heritage content." in result
    assert _PHASE_0 in result
    assert _PHASE_1 in result


def test_injection_persists_deduped_brand_brief(tmp_path) -> None:
    workspace = tmp_path / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text(
        _PREAMBLE + _PHASE_0 + _PHASE_5_SKELETON + _PHASE_5_FULL,
        encoding="utf-8",
    )
    (workspace / "quality_gates.md").write_text("# Gates\n", encoding="utf-8")
    set_active_session(BrandStrategySession(session_id="abc123"))
    request = SimpleNamespace(messages=[HumanMessage(content="Build artifacts")])
    middleware = WorkspaceInjectionMiddleware(workspace_root=tmp_path)

    try:
        middleware._inject_if_first_turn(request)  # noqa: SLF001
    finally:
        set_active_session(None)

    persisted = brief.read_text(encoding="utf-8")
    assert _PHASE_5_SKELETON not in persisted
    assert _PHASE_5_FULL in persisted
    assert "=== WORKSPACE: brand_brief.md" in request.messages[0].content
