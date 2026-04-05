"""Score calculation and inter-rater agreement for BrandMind evaluation.

Implements scoring formula from BRANDMIND_EVAL_RUBRIC.md Section 3.2
and Fleiss' Kappa for inter-rater agreement.
"""

from __future__ import annotations

from typing import Any


def calculate_dimension_score(
    criteria: list[dict[str, Any]],
    anti_pattern_deductions: float = 0.0,
) -> dict[str, Any]:
    """Calculate score for a single dimension using gated formula.

    Formula:
    - Any GATE UNMET → score = (gates_met / gates_total) * 5.0
    - All gates pass → 6.0 + (std_ratio * 2.0) + (excel_ratio * 2.0)
    - Minus anti-pattern deductions (max 2.0)
    - CANNOT_ASSESS excluded from denominators
    """
    gates = [c for c in criteria if c["type"] == "GATE" and c["judgment"] != "CANNOT_ASSESS"]
    standards = [c for c in criteria if c["type"] == "STD" and c["judgment"] != "CANNOT_ASSESS"]
    excels = [c for c in criteria if c["type"] == "EXCEL" and c["judgment"] != "CANNOT_ASSESS"]

    gates_met = sum(1 for c in gates if c["judgment"] == "MET")
    gates_total = len(gates)
    std_met = sum(1 for c in standards if c["judgment"] == "MET")
    std_total = len(standards)
    excel_met = sum(1 for c in excels if c["judgment"] == "MET")
    excel_total = len(excels)

    if gates_total > 0 and gates_met < gates_total:
        raw_score = (gates_met / gates_total) * 5.0
    else:
        base = 6.0
        std_bonus = (std_met / std_total * 2.0) if std_total > 0 else 0.0
        excel_bonus = (excel_met / excel_total * 2.0) if excel_total > 0 else 0.0
        raw_score = base + std_bonus + excel_bonus

    deductions = min(anti_pattern_deductions, 2.0)
    return {
        "gates_met": gates_met,
        "gates_total": gates_total,
        "standard_met": std_met,
        "standard_total": std_total,
        "excellence_met": excel_met,
        "excellence_total": excel_total,
        "anti_pattern_deductions": deductions,
        "raw_score": round(raw_score, 2),
        "final_score": round(max(0.0, raw_score - deductions), 2),
    }


def calculate_all_scores(judge_result: dict[str, Any]) -> dict[str, Any]:
    """Calculate all dimension scores from a judge's criterion-level results.

    Separates criteria by dimension prefix (Q=quality, M=mentor, P=personalization),
    counts anti-pattern deductions per dimension, and computes overall score.
    """
    criteria = judge_result.get("criteria", [])
    anti_patterns = judge_result.get("anti_patterns", [])

    # Count anti-pattern deductions per dimension
    dim_deductions: dict[str, float] = {"quality": 0, "mentor": 0, "personalization": 0}
    for ap in anti_patterns:
        for inst in ap.get("instances", []):
            for dim in inst.get("dimension_affected", []):
                dim_deductions[dim] = dim_deductions.get(dim, 0) + 0.5

    # Split criteria by dimension
    quality_criteria = [c for c in criteria if c["id"].startswith("Q")]
    mentor_criteria = [c for c in criteria if c["id"].startswith("M")]
    personal_criteria = [c for c in criteria if c["id"].startswith("P")]

    q_score = calculate_dimension_score(quality_criteria, dim_deductions["quality"])
    m_score = calculate_dimension_score(mentor_criteria, dim_deductions["mentor"])
    p_score = calculate_dimension_score(personal_criteria, dim_deductions["personalization"])

    # Overall with quality gate
    weighted = q_score["final_score"] * 0.50 + m_score["final_score"] * 0.30 + p_score["final_score"] * 0.20
    quality_gate = q_score["final_score"] < 7.0
    overall = min(weighted, 6.0) if quality_gate else weighted

    return {
        "quality": q_score,
        "mentor": m_score,
        "personalization": p_score,
        "overall": round(overall, 2),
        "quality_gate_applied": quality_gate,
        "pass": overall >= 8.0,
    }


def compute_fleiss_kappa(judge_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute Fleiss' Kappa inter-rater agreement.

    Analyzes criterion-level agreement (MET vs UNMET) across judges.
    CANNOT_ASSESS excluded. Only criteria rated by ALL judges included.
    """
    if len(judge_results) < 2:
        return {"error": "Need >= 2 judges"}

    n_raters = len(judge_results)

    # Build criterion → ratings matrix
    criterion_ratings: dict[str, list[int]] = {}
    for result in judge_results:
        for c in result.get("criteria", []):
            if c["judgment"] == "CANNOT_ASSESS":
                continue
            cid = c["id"]
            criterion_ratings.setdefault(cid, []).append(1 if c["judgment"] == "MET" else 0)

    # Only criteria rated by ALL judges
    complete = {k: v for k, v in criterion_ratings.items() if len(v) == n_raters}
    if not complete:
        return {"error": "No criteria rated by all judges"}

    n = len(complete)
    cat_totals = [0, 0]  # [UNMET, MET]
    p_values = []

    for ratings in complete.values():
        met = sum(ratings)
        unmet = n_raters - met
        cat_totals[0] += unmet
        cat_totals[1] += met
        pi = (met * (met - 1) + unmet * (unmet - 1)) / (n_raters * (n_raters - 1))
        p_values.append(pi)

    p_bar = sum(p_values) / n
    total = n * n_raters
    p_e = sum((c / total) ** 2 for c in cat_totals)
    kappa = (p_bar - p_e) / (1.0 - p_e) if p_e != 1.0 else 1.0

    # Identify low/high agreement criteria
    per_criterion = {}
    for cid, ratings in complete.items():
        majority = max(sum(ratings), n_raters - sum(ratings))
        per_criterion[cid] = round(majority / n_raters, 2)

    return {
        "overall_kappa": round(kappa, 3),
        "interpretation": _interpret_kappa(kappa),
        "n_criteria": n,
        "n_raters": n_raters,
        "low_agreement": [c for c, a in per_criterion.items() if a < 0.67],
        "high_agreement": [c for c, a in per_criterion.items() if a == 1.0],
        "per_criterion": per_criterion,
    }


def _interpret_kappa(kappa: float) -> str:
    """Landis & Koch (1977) interpretation scale."""
    if kappa < 0:
        return "poor"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
