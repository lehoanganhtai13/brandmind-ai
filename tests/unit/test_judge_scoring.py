"""Unit tests for evaluation/judge/scoring.py.

Tests cover scoring formula, quality gate, and Fleiss' Kappa computation.
"""

from __future__ import annotations

import pytest

from evaluation.judge.scoring import (
    calculate_all_scores,
    calculate_dimension_score,
    compute_fleiss_kappa,
    _interpret_kappa,
)


# ---------------------------------------------------------------------------
# Test 1: All Gates Pass
# ---------------------------------------------------------------------------
class TestDimensionScoreAllGatesPass:
    """Verify scoring when all gates pass."""

    def test_all_gates_pass_with_std_and_excel(self):
        """Input: 23 GATE MET, 20/24 STD MET, 10/15 EXCEL MET, 0.5 deductions.

        Expected: 6.0 + (20/24)*2.0 + (10/15)*2.0 - 0.5 = 8.0
        """
        criteria = (
            [{"type": "GATE", "judgment": "MET"} for _ in range(23)]
            + [{"type": "STD", "judgment": "MET"} for _ in range(20)]
            + [{"type": "STD", "judgment": "UNMET"} for _ in range(4)]
            + [{"type": "EXCEL", "judgment": "MET"} for _ in range(10)]
            + [{"type": "EXCEL", "judgment": "UNMET"} for _ in range(5)]
        )
        result = calculate_dimension_score(criteria, anti_pattern_deductions=0.5)

        assert result["gates_met"] == 23
        assert result["gates_total"] == 23
        assert result["standard_met"] == 20
        assert result["standard_total"] == 24
        assert result["excellence_met"] == 10
        assert result["excellence_total"] == 15
        assert result["anti_pattern_deductions"] == 0.5

        # 6.0 + (20/24)*2.0 + (10/15)*2.0 = 6.0 + 1.6667 + 1.3333 = 9.0
        # 9.0 - 0.5 = 8.5
        expected_raw = round(6.0 + (20 / 24) * 2.0 + (10 / 15) * 2.0, 2)
        assert result["raw_score"] == expected_raw
        assert result["final_score"] == round(expected_raw - 0.5, 2)

    def test_gates_only(self):
        """All gates pass, no STD/EXCEL → score = 6.0."""
        criteria = [{"type": "GATE", "judgment": "MET"} for _ in range(5)]
        result = calculate_dimension_score(criteria)
        assert result["final_score"] == 6.0

    def test_cannot_assess_excluded(self):
        """CANNOT_ASSESS criteria excluded from denominators."""
        criteria = [
            {"type": "GATE", "judgment": "MET"},
            {"type": "GATE", "judgment": "CANNOT_ASSESS"},
            {"type": "STD", "judgment": "MET"},
            {"type": "STD", "judgment": "CANNOT_ASSESS"},
        ]
        result = calculate_dimension_score(criteria)
        assert result["gates_total"] == 1
        assert result["standard_total"] == 1
        # All gates pass (1/1), all std pass (1/1)
        assert result["final_score"] == 8.0  # 6.0 + 2.0 + 0.0


# ---------------------------------------------------------------------------
# Test 2: Gate Failure
# ---------------------------------------------------------------------------
class TestDimensionScoreGateFailure:
    """Verify gate failure caps at 5.0."""

    def test_gate_failure(self):
        """Input: 20/23 GATE MET. Expected: (20/23) * 5.0 = 4.35."""
        criteria = (
            [{"type": "GATE", "judgment": "MET"} for _ in range(20)]
            + [{"type": "GATE", "judgment": "UNMET"} for _ in range(3)]
            + [{"type": "STD", "judgment": "MET"} for _ in range(24)]
            + [{"type": "EXCEL", "judgment": "MET"} for _ in range(15)]
        )
        result = calculate_dimension_score(criteria)
        expected = round((20 / 23) * 5.0, 2)
        assert result["final_score"] == expected
        assert result["raw_score"] == expected

    def test_all_gates_fail(self):
        """All gates UNMET → score = 0."""
        criteria = [{"type": "GATE", "judgment": "UNMET"} for _ in range(5)]
        result = calculate_dimension_score(criteria)
        assert result["final_score"] == 0.0

    def test_anti_pattern_deductions_capped(self):
        """Deductions capped at 2.0."""
        criteria = [{"type": "GATE", "judgment": "MET"} for _ in range(5)]
        result = calculate_dimension_score(criteria, anti_pattern_deductions=5.0)
        assert result["anti_pattern_deductions"] == 2.0
        assert result["final_score"] == 4.0  # 6.0 - 2.0


# ---------------------------------------------------------------------------
# Test 3: Overall Score — Quality Gate
# ---------------------------------------------------------------------------
class TestOverallScoreQualityGate:
    """Verify quality < 7.0 caps overall."""

    def test_quality_gate_caps_overall(self):
        """Quality=6.5, Mentor=9.0, Personal=8.0.

        weighted = 6.5*0.5 + 9.0*0.3 + 8.0*0.2 = 3.25 + 2.7 + 1.6 = 7.55
        But quality < 7.0 → capped at 6.0.
        """
        judge_result = {
            "criteria": (
                # Quality: all gates pass, but some std fail → score < 7.0
                [{"id": "Q0-G1", "type": "GATE", "judgment": "MET"}]
                + [{"id": f"Q0-S{i}", "type": "STD", "judgment": "UNMET"} for i in range(10)]
                + [{"id": f"Q0-E{i}", "type": "EXCEL", "judgment": "UNMET"} for i in range(5)]
                # Mentor: perfect
                + [{"id": f"M1-G{i}", "type": "GATE", "judgment": "MET"} for i in range(4)]
                + [{"id": f"M1-S{i}", "type": "STD", "judgment": "MET"} for i in range(10)]
                + [{"id": f"M1-E{i}", "type": "EXCEL", "judgment": "MET"} for i in range(6)]
                # Personalization: strong
                + [{"id": f"P1-G{i}", "type": "GATE", "judgment": "MET"} for i in range(5)]
                + [{"id": f"P1-S{i}", "type": "STD", "judgment": "MET"} for i in range(10)]
                + [{"id": f"P1-E{i}", "type": "EXCEL", "judgment": "MET"} for i in range(3)]
            ),
            "anti_patterns": [],
        }
        scores = calculate_all_scores(judge_result)

        # Quality: 1 gate passes, 0/10 std, 0/5 excel → 6.0
        assert scores["quality"]["final_score"] == 6.0
        assert scores["quality_gate_applied"] is True
        assert scores["overall"] <= 6.0

    def test_no_quality_gate_when_above_7(self):
        """Quality >= 7.0 → no cap applied."""
        judge_result = {
            "criteria": (
                # Quality: all gates + half std → 7.0
                [{"id": f"Q-G{i}", "type": "GATE", "judgment": "MET"} for i in range(5)]
                + [{"id": f"Q-S{i}", "type": "STD", "judgment": "MET"} for i in range(5)]
                + [{"id": f"Q-S{i+5}", "type": "STD", "judgment": "UNMET"} for i in range(5)]
                # Mentor: all pass
                + [{"id": f"M-G{i}", "type": "GATE", "judgment": "MET"} for i in range(4)]
                + [{"id": f"M-S{i}", "type": "STD", "judgment": "MET"} for i in range(10)]
                + [{"id": f"M-E{i}", "type": "EXCEL", "judgment": "MET"} for i in range(6)]
                # Personalization: all pass
                + [{"id": f"P-G{i}", "type": "GATE", "judgment": "MET"} for i in range(5)]
                + [{"id": f"P-S{i}", "type": "STD", "judgment": "MET"} for i in range(13)]
                + [{"id": f"P-E{i}", "type": "EXCEL", "judgment": "MET"} for i in range(5)]
            ),
            "anti_patterns": [],
        }
        scores = calculate_all_scores(judge_result)
        assert scores["quality"]["final_score"] == 7.0
        assert scores["quality_gate_applied"] is False
        assert scores["overall"] > 6.0


# ---------------------------------------------------------------------------
# Test 4: Fleiss' Kappa — Perfect Agreement
# ---------------------------------------------------------------------------
class TestFleissKappa:
    """Verify Fleiss' Kappa computation."""

    def test_perfect_agreement(self):
        """All judges agree on all criteria → kappa = 1.0."""
        judges = [
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q0-G2", "judgment": "MET"},
                {"id": "Q0-S1", "judgment": "UNMET"},
            ]}
            for _ in range(3)
        ]
        result = compute_fleiss_kappa(judges)
        assert result["overall_kappa"] == 1.0
        assert result["interpretation"] == "almost perfect"
        assert result["n_raters"] == 3
        assert len(result["high_agreement"]) == 3

    def test_no_agreement(self):
        """Judges disagree maximally on 2-category ratings."""
        judges = [
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q0-G2", "judgment": "UNMET"},
            ]},
            {"criteria": [
                {"id": "Q0-G1", "judgment": "UNMET"},
                {"id": "Q0-G2", "judgment": "MET"},
            ]},
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q0-G2", "judgment": "UNMET"},
            ]},
        ]
        result = compute_fleiss_kappa(judges)
        # With 3 raters and this pattern, kappa should be low
        assert result["overall_kappa"] < 0.5

    def test_single_judge(self):
        """Need >= 2 judges."""
        result = compute_fleiss_kappa([{"criteria": [{"id": "Q0-G1", "judgment": "MET"}]}])
        assert "error" in result

    def test_cannot_assess_excluded(self):
        """CANNOT_ASSESS entries excluded from Kappa."""
        judges = [
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q05-G1", "judgment": "CANNOT_ASSESS"},
            ]},
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q05-G1", "judgment": "CANNOT_ASSESS"},
            ]},
            {"criteria": [
                {"id": "Q0-G1", "judgment": "MET"},
                {"id": "Q05-G1", "judgment": "CANNOT_ASSESS"},
            ]},
        ]
        result = compute_fleiss_kappa(judges)
        assert result["n_criteria"] == 1  # Only Q0-G1 included
        assert result["overall_kappa"] == 1.0


# ---------------------------------------------------------------------------
# Test: Kappa Interpretation
# ---------------------------------------------------------------------------
class TestKappaInterpretation:
    """Verify Landis & Koch interpretation."""

    @pytest.mark.parametrize("kappa,expected", [
        (-0.1, "poor"),
        (0.1, "slight"),
        (0.3, "fair"),
        (0.5, "moderate"),
        (0.7, "substantial"),
        (0.9, "almost perfect"),
        (1.0, "almost perfect"),
    ])
    def test_interpretation(self, kappa: float, expected: str):
        assert _interpret_kappa(kappa) == expected


# ---------------------------------------------------------------------------
# Test: Anti-Pattern Deductions in calculate_all_scores
# ---------------------------------------------------------------------------
class TestAntiPatternDeductions:
    """Verify anti-pattern deductions are applied per dimension."""

    def test_anti_patterns_deduct_from_correct_dimension(self):
        judge_result = {
            "criteria": (
                [{"id": "Q0-G1", "type": "GATE", "judgment": "MET"}]
                + [{"id": "M1-G1", "type": "GATE", "judgment": "MET"}]
                + [{"id": "P1-G1", "type": "GATE", "judgment": "MET"}]
            ),
            "anti_patterns": [
                {
                    "id": "AP-1",
                    "instances": [
                        {"turn": 5, "evidence": "...", "dimension_affected": ["quality", "mentor"]},
                    ],
                },
                {
                    "id": "AP-3",
                    "instances": [
                        {"turn": 10, "evidence": "...", "dimension_affected": ["quality", "personalization"]},
                    ],
                },
            ],
        }
        scores = calculate_all_scores(judge_result)
        # Quality: 2 AP instances × 0.5 = 1.0 deduction
        assert scores["quality"]["anti_pattern_deductions"] == 1.0
        # Mentor: 1 AP instance × 0.5 = 0.5 deduction
        assert scores["mentor"]["anti_pattern_deductions"] == 0.5
        # Personalization: 1 AP instance × 0.5 = 0.5 deduction
        assert scores["personalization"]["anti_pattern_deductions"] == 0.5
