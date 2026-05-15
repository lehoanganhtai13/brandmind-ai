"""Regression tests for deterministic chat-process audit signals."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.judge.chat_process_audit import audit_transcript


def _write_transcript(path: Path, turns: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"turns": turns}, ensure_ascii=False), encoding="utf-8")


def test_flags_unsupported_claims_and_internal_language(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.json"
    _write_transcript(
        transcript,
        [
            {
                "turn": 1,
                "user": "Tôi cần làm brand strategy.",
                "agent": (
                    "Research shows Gen Z needs this. CAC will be lower by 30%. "
                    "We are now in Phase 1 and will export PPTX later."
                ),
            }
        ],
    )

    result = audit_transcript(transcript)

    summary = result["summary"]
    assert summary["unsupported_claim_risk_turns_ge_3"] == [1]
    assert summary["totals"]["claim.research_claim"] == 1
    assert summary["totals"]["claim.trend_claim"] == 1
    assert summary["totals"]["claim.precise_metric"] == 1
    assert summary["totals"]["internal.phase_id"] == 1
    assert summary["totals"]["internal.file_extension"] == 1


def test_provenance_language_reduces_unsupported_claim_risk(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.json"
    _write_transcript(
        transcript,
        [
            {
                "turn": 1,
                "user_message": "Dữ liệu của tôi cho thấy khách trẻ giảm.",
                "assistant_response": (
                    "Dựa trên thông tin bạn chia sẻ, đây là giả thuyết "
                    "tạm thời: "
                    "xu hướng khách trẻ giảm có thể cần kiểm chứng thêm."
                ),
            }
        ],
    )

    result = audit_transcript(transcript)

    turn = result["turns"][0]
    assert turn["claim_flags"]["trend_claim"] == 1
    assert turn["provenance_hits"] >= 2
    assert turn["unsupported_claim_risk"] == 0


def test_verification_language_does_not_count_as_claim_risk(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.json"
    _write_transcript(
        transcript,
        [
            {
                "turn": 1,
                "user": "Team nghe nói Gen Z thích healthy nhưng chưa có dữ liệu.",
                "agent": (
                    "Before using the Gen Z healthy trend as a fact, we need "
                    "to verify it. If this remains an assumption, I would "
                    "treat it as a hypothesis for the next diagnosis step."
                ),
            }
        ],
    )

    result = audit_transcript(transcript)

    assert result["turns"][0]["claim_flags"]["trend_claim"] >= 1
    assert result["turns"][0]["unsupported_claim_risk"] == 0


def test_detects_high_adjacent_repetition(tmp_path: Path) -> None:
    repeated = " ".join(["business lunch private dinner weekday booking"] * 20)
    transcript = tmp_path / "transcript.json"
    _write_transcript(
        transcript,
        [
            {"turn": 1, "user": "A", "agent": repeated},
            {"turn": 2, "user": "B", "agent": repeated + " thêm một câu mới."},
        ],
    )

    result = audit_transcript(transcript)

    assert result["turns"][1]["adjacent_repeat_ratio"] >= 0.5
    assert result["summary"]["repeat_turns_ratio_ge_0_15"] == [2]
