"""Unit tests for Brand Strategy Orchestrator (Task 42).

Tests PhaseState, BrandBrief, QualityGateEngine,
RebrandDecisionMatrix, and ProactiveLoopDetector.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from core.brand_strategy.orchestrator import (
    BrandBrief,
    BrandScope,
    LoopTrigger,
    Phase,
    PhaseState,
    PhaseTransition,
    ProactiveLoopDetector,
    QualityGateEngine,
    QualityGateResult,
    RebrandDecisionMatrix,
    RebrandDecisionResult,
)


# ===== PhaseState & Phase Sequencing =====


class TestPhaseState:
    """Test phase state machine."""

    def test_initial_state(self):
        state = PhaseState()
        assert state.current_phase == Phase.PHASE_0
        assert state.scope is None
        assert state.transition_history == []

    def test_new_brand_sequence(self):
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        seq = state.get_phase_sequence()
        assert Phase.PHASE_0 in seq
        assert Phase.PHASE_0_5 not in seq
        assert Phase.PHASE_1 in seq
        assert Phase.PHASE_5 in seq

    def test_full_rebrand_includes_phase_05(self):
        state = PhaseState(scope=BrandScope.FULL_REBRAND)
        seq = state.get_phase_sequence()
        assert Phase.PHASE_0_5 in seq
        idx_0 = seq.index(Phase.PHASE_0)
        idx_05 = seq.index(Phase.PHASE_0_5)
        assert idx_05 == idx_0 + 1

    def test_refresh_skips_phase_2(self):
        """REFRESH scope skips Phase 2 (brand positioning)."""
        state = PhaseState(scope=BrandScope.REFRESH)
        seq = state.get_phase_sequence()
        assert Phase.PHASE_2 not in seq
        assert Phase.PHASE_0_5 in seq
        assert Phase.PHASE_3 in seq

    def test_advance_requires_scope(self):
        state = PhaseState()
        with pytest.raises(ValueError, match="scope not set"):
            state.advance()

    def test_advance_through_new_brand(self):
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        assert state.current_phase == Phase.PHASE_0

        state.advance()
        assert state.current_phase == Phase.PHASE_1

        state.advance()
        assert state.current_phase == Phase.PHASE_2

        state.advance()
        assert state.current_phase == Phase.PHASE_3

        state.advance()
        assert state.current_phase == Phase.PHASE_4

        state.advance()
        assert state.current_phase == Phase.PHASE_5

        state.advance()
        assert state.current_phase == Phase.COMPLETED

        assert len(state.transition_history) == 6

    def test_advance_past_completed_raises(self):
        state = PhaseState(
            scope=BrandScope.NEW_BRAND,
            current_phase=Phase.COMPLETED,
        )
        with pytest.raises(ValueError, match="workflow complete"):
            state.advance()

    def test_get_next_phase_no_scope(self):
        state = PhaseState()
        assert state.get_next_phase() is None

    def test_transition_history_recorded(self):
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        state.advance(gate_passed=True, notes="Phase 0 done")
        assert len(state.transition_history) == 1
        t = state.transition_history[0]
        assert t.from_phase == Phase.PHASE_0
        assert t.to_phase == Phase.PHASE_1
        assert t.gate_passed is True
        assert t.notes == "Phase 0 done"

    def test_loopback(self):
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        state.advance()  # → phase_1
        state.advance()  # → phase_2

        result = state.loopback(Phase.PHASE_1, "Need more research")
        assert result == Phase.PHASE_1
        assert state.current_phase == Phase.PHASE_1
        assert state.loopback_count == 1
        assert "LOOPBACK" in state.transition_history[-1].notes

    def test_loopback_to_future_phase_raises(self):
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        state.advance()  # → phase_1
        with pytest.raises(ValueError, match="must be before"):
            state.loopback(Phase.PHASE_2, "Invalid")

    def test_loopback_to_invalid_phase_raises(self):
        """NEW_BRAND doesn't have phase_0_5 in sequence."""
        state = PhaseState(scope=BrandScope.NEW_BRAND)
        state.advance()  # → phase_1
        with pytest.raises(ValueError, match="not in current scope"):
            state.loopback(Phase.PHASE_0_5, "Invalid")

    def test_is_rebrand(self):
        assert PhaseState(scope=BrandScope.REFRESH).is_rebrand() is True
        assert PhaseState(scope=BrandScope.REPOSITIONING).is_rebrand() is True
        assert PhaseState(scope=BrandScope.FULL_REBRAND).is_rebrand() is True
        assert PhaseState(scope=BrandScope.NEW_BRAND).is_rebrand() is False
        assert PhaseState(scope=None).is_rebrand() is False


class TestPhaseTransition:
    """Test PhaseTransition model."""

    def test_defaults(self):
        t = PhaseTransition(
            from_phase=Phase.PHASE_0,
            to_phase=Phase.PHASE_1,
        )
        assert t.gate_passed is True
        assert t.notes == ""
        assert t.timestamp is not None


# ===== BrandBrief =====


class TestBrandBrief:
    """Test BrandBrief model."""

    def test_empty_brief(self):
        brief = BrandBrief()
        assert brief.session_id == ""
        assert brief.brand_name == ""
        assert brief.phase_0_output == {}
        assert brief.phase_0_5_output is None

    def test_add_phase_output(self):
        brief = BrandBrief()
        brief.add_phase_output("phase_0", {"problem": "Test"})
        assert brief.phase_0_output == {"problem": "Test"}

    def test_add_phase_0_5_output(self):
        brief = BrandBrief()
        brief.add_phase_output("phase_0_5", {"audit": "Done"})
        assert brief.phase_0_5_output == {"audit": "Done"}

    def test_invalid_phase_raises(self):
        brief = BrandBrief()
        with pytest.raises(ValueError, match="Invalid phase"):
            brief.add_phase_output("phase_99", {})

    def test_get_context_for_phase(self):
        brief = BrandBrief(
            brand_name="Test Café",
            scope="NEW_BRAND",
            budget_tier="starter",
        )
        brief.add_phase_output("phase_0", {"problem": "Low revenue"})
        brief.add_phase_output("phase_1", {"competitors": ["A", "B"]})

        ctx = brief.get_context_for_phase("phase_2")
        assert ctx["brand_name"] == "Test Café"
        assert "phase_0" in ctx["prior_phases"]
        assert "phase_1" in ctx["prior_phases"]
        assert "phase_2" not in ctx["prior_phases"]

    def test_get_context_excludes_future_phases(self):
        brief = BrandBrief()
        brief.add_phase_output("phase_0", {"data": 1})
        brief.add_phase_output("phase_3", {"data": 3})

        ctx = brief.get_context_for_phase("phase_1")
        assert "phase_0" in ctx["prior_phases"]
        assert "phase_3" not in ctx["prior_phases"]

    def test_executive_summary(self):
        brief = BrandBrief(
            brand_name="Coffee Lab",
            scope="NEW_BRAND",
            budget_tier="growth",
        )
        brief.add_phase_output("phase_0", {"summary": "New café concept"})
        summary = brief.get_executive_summary()
        assert "Coffee Lab" in summary
        assert "NEW_BRAND" in summary
        assert "New café concept" in summary

    def test_to_document_content(self):
        brief = BrandBrief(brand_name="X", scope="NEW_BRAND")
        content = brief.to_document_content()
        assert content["metadata"]["brand_name"] == "X"
        assert "sections" in content
        assert "assets" in content

    def test_serialization_roundtrip(self):
        brief = BrandBrief(
            brand_name="Test",
            scope="REFRESH",
            budget_tier="enterprise",
        )
        brief.add_phase_output("phase_0", {"scope": "REFRESH"})
        brief.add_phase_output("phase_0_5", {"audit": "complete"})

        json_str = brief.model_dump_json(indent=2)
        loaded = BrandBrief.model_validate_json(json_str)
        assert loaded.brand_name == "Test"
        assert loaded.phase_0_output == {"scope": "REFRESH"}
        assert loaded.phase_0_5_output == {"audit": "complete"}

    def test_save_and_load(self, tmp_path):
        brief = BrandBrief(brand_name="Save Test")
        brief.add_phase_output("phase_0", {"test": True})

        filepath = str(tmp_path / "brief.json")
        brief.save(filepath)

        loaded = BrandBrief.load(filepath)
        assert loaded.brand_name == "Save Test"
        assert loaded.phase_0_output["test"] is True

    def test_generated_assets_tracking(self):
        brief = BrandBrief()
        brief.generated_images.append("mood_board_1.png")
        brief.generated_documents.append("strategy.pdf")
        assert len(brief.generated_images) == 1
        assert len(brief.generated_documents) == 1

        summary = brief.get_executive_summary()
        assert "1 assets" in summary
        assert "1 files" in summary


# ===== QualityGateEngine =====


class TestQualityGateEngine:
    """Test quality gate evaluation."""

    def test_phase_0_gate_all_passed(self):
        engine = QualityGateEngine()
        result = engine.evaluate(
            "phase_0",
            "new_brand",
            [
                "p0_problem",
                "p0_scope",
                "p0_category",
                "p0_location",
                "p0_budget",
                "p0_user_confirm",
            ],
        )
        assert result.passed is True
        assert result.pass_rate == 1.0
        assert result.missing_items == []

    def test_phase_0_gate_missing_items(self):
        engine = QualityGateEngine()
        result = engine.evaluate(
            "phase_0",
            "new_brand",
            ["p0_problem", "p0_scope"],
        )
        assert result.passed is False
        assert result.pass_rate < 1.0
        assert len(result.missing_items) == 4

    def test_scope_filter_new_brand_skips_05(self):
        engine = QualityGateEngine()
        checklist = engine.get_checklist("phase_0_5", "new_brand")
        # All phase_0_5 items have scope_filter excluding new_brand
        assert len(checklist) == 0

    def test_scope_filter_rebrand_includes_05(self):
        engine = QualityGateEngine()
        checklist = engine.get_checklist("phase_0_5", "full_rebrand")
        assert len(checklist) == 4

    def test_phase_3_transition_rebrand_only(self):
        engine = QualityGateEngine()

        new_brand_items = engine.get_checklist("phase_3", "new_brand")
        rebrand_items = engine.get_checklist("phase_3", "full_rebrand")
        # Rebrand has extra "Identity transition" item
        assert len(rebrand_items) > len(new_brand_items)

    def test_phase_5_rebrand_has_transition_items(self):
        engine = QualityGateEngine()
        items = engine.get_checklist("phase_5", "full_rebrand")
        ids = [item.id for item in items]
        assert "p5_transition" in ids
        assert "p5_stakeholder" in ids

    def test_phase_5_new_brand_no_transition(self):
        engine = QualityGateEngine()
        items = engine.get_checklist("phase_5", "new_brand")
        ids = [item.id for item in items]
        assert "p5_transition" not in ids
        assert "p5_stakeholder" not in ids

    def test_unknown_phase_returns_passed(self):
        engine = QualityGateEngine()
        result = engine.evaluate("phase_99", "new_brand", [])
        assert result.passed is True

    def test_format_checklist(self):
        engine = QualityGateEngine()
        md = engine.format_checklist(
            "phase_0",
            "new_brand",
            completed_items=["p0_problem"],
        )
        assert "[x]" in md
        assert "[ ]" in md
        assert "p0_problem" in md


# ===== RebrandDecisionMatrix =====


class TestRebrandDecisionMatrix:
    """Test rebrand signal scoring."""

    def test_reinforce_low_scores(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {
                "Brand-Market Misalignment": 0,
                "Competitive Erosion": 1,
                "Audience Disconnect": 0,
                "Internal Fragmentation": 0,
                "Reputation Damage": 0,
                "Strategic Pivot": 0,
            }
        )
        assert result.total_score == 1
        assert result.recommended_scope == "reinforce"

    def test_refresh_medium_scores(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {
                "Brand-Market Misalignment": 1,
                "Competitive Erosion": 1,
                "Audience Disconnect": 1,
                "Internal Fragmentation": 1,
                "Reputation Damage": 0,
                "Strategic Pivot": 1,
            }
        )
        assert result.total_score == 5
        assert result.recommended_scope == "refresh"

    def test_repositioning_high_scores(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {
                "Brand-Market Misalignment": 2,
                "Competitive Erosion": 1,
                "Audience Disconnect": 2,
                "Internal Fragmentation": 1,
                "Reputation Damage": 1,
                "Strategic Pivot": 1,
            }
        )
        assert result.total_score == 8
        assert result.recommended_scope == "repositioning"

    def test_full_rebrand_max_scores(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {
                "Brand-Market Misalignment": 2,
                "Competitive Erosion": 2,
                "Audience Disconnect": 2,
                "Internal Fragmentation": 2,
                "Reputation Damage": 2,
                "Strategic Pivot": 2,
            }
        )
        assert result.total_score == 12
        assert result.recommended_scope == "full_rebrand"

    def test_scores_clamped_to_0_2(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {"Brand-Market Misalignment": 5}  # Over 2
        )
        assert result.signals[0].score == 2  # Clamped

    def test_negative_scores_clamped(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score(
            {"Brand-Market Misalignment": -1}
        )
        assert result.signals[0].score == 0

    def test_missing_signals_default_zero(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score({})
        assert result.total_score == 0
        assert result.recommended_scope == "reinforce"

    def test_max_score_is_12(self):
        matrix = RebrandDecisionMatrix()
        result = matrix.score({})
        assert result.max_score == 12

    def test_diagnostic_questions(self):
        matrix = RebrandDecisionMatrix()
        questions = matrix.get_diagnostic_questions()
        assert len(questions) == 6
        assert all("**" in q for q in questions)


# ===== ProactiveLoopDetector =====


class TestProactiveLoopDetector:
    """Test proactive loop trigger detection."""

    def test_no_triggers_when_no_context(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers("phase_2", "new_brand", {})
        assert fired == []

    def test_stress_deliverability_triggers(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_2",
            "new_brand",
            {"stress_test_deliverability_failed": True},
        )
        assert len(fired) == 1
        assert fired[0].id == "stress_deliverability"
        assert fired[0].target_phase == "phase_0"

    def test_stress_relevance_triggers(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_2",
            "new_brand",
            {"stress_test_relevance_failed": True},
        )
        assert len(fired) == 1
        assert fired[0].id == "stress_relevance"

    def test_naming_blocked_triggers(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_3",
            "new_brand",
            {"naming_all_blocked": True},
        )
        assert len(fired) == 1
        assert fired[0].id == "naming_blocked"

    def test_scope_filter_excludes_new_brand(self):
        """audit_no_equity only fires for rebrand scopes."""
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_0_5",
            "new_brand",
            {"no_salvageable_equity": True},
        )
        assert len(fired) == 0

    def test_scope_filter_includes_full_rebrand(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_0_5",
            "full_rebrand",
            {"no_salvageable_equity": True},
        )
        assert len(fired) == 1
        assert fired[0].id == "audit_no_equity"

    def test_multiple_triggers_fire(self):
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_2",
            "new_brand",
            {
                "stress_test_deliverability_failed": True,
                "stress_test_relevance_failed": True,
            },
        )
        assert len(fired) == 2
        ids = {t.id for t in fired}
        assert ids == {"stress_deliverability", "stress_relevance"}

    def test_wrong_phase_no_trigger(self):
        """Trigger at phase_2 shouldn't fire at phase_3."""
        detector = ProactiveLoopDetector()
        fired = detector.check_triggers(
            "phase_3",
            "new_brand",
            {"stress_test_deliverability_failed": True},
        )
        assert len(fired) == 0

    def test_format_trigger_explanation(self):
        detector = ProactiveLoopDetector()
        trigger = LoopTrigger(
            id="test",
            detected_at="phase_2",
            target_phase="phase_1",
            condition="Test condition",
            action="Test action",
        )
        result = detector.format_trigger_explanation(trigger)
        assert "condition" in result
        assert "recommended_action" in result
        assert "target_phase" in result
        assert "agent_guidance" in result
