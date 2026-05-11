"""Tests for the strict artifact content acceptance gate."""

from __future__ import annotations

from evaluation.judge.artifact_judge import (
    _LEVEL_ACCEPTABLE,
    _LEVEL_FAIL,
    _LEVEL_GOOD,
    ArtifactResult,
    JudgeReport,
    _apply_aggregate_verdict,
    _quality_level_for_criteria,
)


def _criterion(criterion_id: str, judgment: str) -> dict[str, str]:
    """Build a minimal criterion verdict for quality-level tests."""
    return {
        "id": criterion_id,
        "judgment": judgment,
        "evidence": "evidence",
        "explanation": "explanation",
    }


def _passing_artifact(artifact_type: str) -> ArtifactResult:
    """Build a judged artifact that passes the content gate."""
    return ArtifactResult(
        artifact_type=artifact_type,
        artifact_path=f"/tmp/{artifact_type}",
        passed=True,
        quality_level=_LEVEL_ACCEPTABLE,
    )


def test_required_criteria_met_with_good_gap_is_acceptable() -> None:
    """An artifact is acceptable when required criteria pass but good criteria do not."""
    criteria = [
        _criterion("DOC-1", "MET"),
        _criterion("DOC-2", "MET"),
        _criterion("DOC-3", "MET"),
        _criterion("DOC-4", "MET"),
        _criterion("DOC-5", "UNMET"),
    ]

    level = _quality_level_for_criteria("strategy_document", criteria)

    assert level == _LEVEL_ACCEPTABLE


def test_good_level_requires_good_criterion() -> None:
    """An artifact reaches GOOD only when the artifact-specific good criterion passes."""
    criteria = [
        _criterion("PPT-1", "MET"),
        _criterion("PPT-2", "MET"),
        _criterion("PPT-3", "MET"),
        _criterion("PPT-4", "MET"),
        _criterion("PPT-5", "MET"),
    ]

    level = _quality_level_for_criteria("presentation", criteria)

    assert level == _LEVEL_GOOD


def test_missing_required_criterion_fails_even_with_three_met() -> None:
    """The old three-MET threshold is not enough for strict artifact acceptance."""
    criteria = [
        _criterion("KPI-1", "MET"),
        _criterion("KPI-2", "MET"),
        _criterion("KPI-3", "MET"),
        _criterion("KPI-4", "UNMET"),
        _criterion("KPI-5", "MET"),
        _criterion("KPI-6", "MET"),
        _criterion("KPI-7", "MET"),
    ]

    level = _quality_level_for_criteria("spreadsheet", criteria)

    assert level == _LEVEL_FAIL


def test_aggregate_requires_all_expected_artifacts_to_pass() -> None:
    """A strict session pass requires all expected artifacts to pass."""
    report = JudgeReport(
        session_dir="/tmp/session",
        rubric_path="/tmp/rubric.md",
        judge_model="gemini",
        artifacts=[
            _passing_artifact("brand_key_image"),
            _passing_artifact("strategy_document"),
            _passing_artifact("presentation"),
            _passing_artifact("spreadsheet"),
        ],
    )

    _apply_aggregate_verdict(report)

    assert report.aggregate_pass is True
    assert "4/4 expected artifacts pass" in report.aggregate_summary


def test_aggregate_fails_when_one_artifact_fails() -> None:
    """Three passing artifacts cannot close the strict product gate."""
    report = JudgeReport(
        session_dir="/tmp/session",
        rubric_path="/tmp/rubric.md",
        judge_model="gemini",
        artifacts=[
            _passing_artifact("brand_key_image"),
            _passing_artifact("strategy_document"),
            _passing_artifact("presentation"),
            ArtifactResult(
                artifact_type="spreadsheet",
                artifact_path="/tmp/spreadsheet",
                passed=False,
                quality_level=_LEVEL_FAIL,
            ),
        ],
    )

    _apply_aggregate_verdict(report)

    assert report.aggregate_pass is False
    assert "3/4 expected artifacts pass" in report.aggregate_summary


def test_aggregate_fails_when_artifact_is_skipped() -> None:
    """Skipped artifacts are product gaps and must not lower the pass floor."""
    report = JudgeReport(
        session_dir="/tmp/session",
        rubric_path="/tmp/rubric.md",
        judge_model="gemini",
        artifacts=[
            _passing_artifact("brand_key_image"),
            _passing_artifact("strategy_document"),
            _passing_artifact("presentation"),
            ArtifactResult(
                artifact_type="spreadsheet",
                artifact_path="",
                skipped=True,
                skip_reason="artifact not found on disk",
            ),
        ],
    )

    _apply_aggregate_verdict(report)

    assert report.aggregate_pass is False
    assert "1 missing or skipped" in report.aggregate_summary
