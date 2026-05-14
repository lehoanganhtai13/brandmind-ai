from evaluation.judge import coherence_judge, problem_solving_judge


def test_coherence_judge_accepts_driver_transcript_schema() -> None:
    text = coherence_judge._format_transcript_for_judge(
        [
            {
                "turn": 1,
                "user_message": "Tôi cần làm mới thương hiệu quán cà phê.",
                "assistant_response": "Mình bắt đầu bằng chẩn đoán vấn đề.",
            }
        ]
    )

    assert "USER: Tôi cần làm mới thương hiệu quán cà phê." in text
    assert "AGENT: Mình bắt đầu bằng chẩn đoán vấn đề." in text


def test_problem_solving_judge_accepts_driver_transcript_schema() -> None:
    text = problem_solving_judge._format_transcript_for_judge(
        [
            {
                "turn": 1,
                "user_message": "Ngân sách của tôi khoảng 50 triệu.",
                "assistant_response": "Ta sẽ ưu tiên các hạng mục có ROI rõ.",
            }
        ]
    )

    assert "USER: Ngân sách của tôi khoảng 50 triệu." in text
    assert "AGENT: Ta sẽ ưu tiên các hạng mục có ROI rõ." in text


def test_methodology_judges_keep_legacy_transcript_schema() -> None:
    turn = {
        "turn": 1,
        "user": "Tôi cần tăng khách ngày thường.",
        "agent": "Ta sẽ tách business lunch và private dinner.",
    }

    assert "USER: Tôi cần tăng khách ngày thường." in (
        coherence_judge._format_transcript_for_judge([turn])
    )
    assert "AGENT: Ta sẽ tách business lunch và private dinner." in (
        problem_solving_judge._format_transcript_for_judge([turn])
    )
