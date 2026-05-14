import json

from evaluation.judge import coherence_judge, problem_solving_judge, run_judges


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


def test_chat_process_judge_accepts_driver_transcript_schema(tmp_path) -> None:
    session_dir = tmp_path / "pilot"
    session_dir.mkdir()
    (session_dir / "transcript.json").write_text(
        json.dumps(
            {
                "system": "brandmind",
                "turns": [
                    {
                        "turn": 1,
                        "user_message": "Tôi cần kéo khách ngày thường.",
                        "assistant_response": "Ta sẽ tập trung business lunch.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text = run_judges._load_session_input(session_dir)
    warnings = run_judges._validate_transcript(session_dir)

    assert "USER: Tôi cần kéo khách ngày thường." in text
    assert "AGENT: Ta sẽ tập trung business lunch." in text
    assert warnings == []


def test_chat_process_judge_accepts_top_level_list_transcript(tmp_path) -> None:
    session_dir = tmp_path / "pilot"
    session_dir.mkdir()
    (session_dir / "transcript.json").write_text(
        json.dumps(
            [
                {
                    "turn": 1,
                    "user_message": "Tôi cần kéo khách ngày thường.",
                    "assistant_response": "Ta sẽ tập trung business lunch.",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text = run_judges._load_session_input(session_dir)
    warnings = run_judges._validate_transcript(session_dir)

    assert "SESSION TRANSCRIPT (System: unknown)" in text
    assert "USER: Tôi cần kéo khách ngày thường." in text
    assert "AGENT: Ta sẽ tập trung business lunch." in text
    assert warnings == []


def test_b_and_c_judges_accept_top_level_list_transcript(tmp_path) -> None:
    session_dir = tmp_path / "pilot"
    session_dir.mkdir()
    (session_dir / "transcript.json").write_text(
        json.dumps(
            [
                {
                    "turn": 1,
                    "user_message": "Tôi cần kéo khách ngày thường.",
                    "assistant_response": "Ta sẽ tập trung business lunch.",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    coherence_id, coherence_turns = coherence_judge._load_transcript_data(
        session_dir
    )
    problem_id, problem_turns = problem_solving_judge._load_transcript_data(
        session_dir
    )

    assert coherence_id == "pilot"
    assert problem_id == "pilot"
    assert coherence_turns[0]["assistant_response"] == (
        "Ta sẽ tập trung business lunch."
    )
    assert problem_turns[0]["user_message"] == "Tôi cần kéo khách ngày thường."


def test_chat_process_judge_keeps_legacy_transcript_schema(tmp_path) -> None:
    session_dir = tmp_path / "pilot"
    session_dir.mkdir()
    (session_dir / "transcript.json").write_text(
        json.dumps(
            {
                "system": "brandmind",
                "turns": [
                    {
                        "turn": 1,
                        "user": "Tôi muốn reposition quán.",
                        "agent": "Mình bắt đầu bằng audit tài sản hiện có.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text = run_judges._load_session_input(session_dir)
    warnings = run_judges._validate_transcript(session_dir)

    assert "USER: Tôi muốn reposition quán." in text
    assert "AGENT: Mình bắt đầu bằng audit tài sản hiện có." in text
    assert warnings == []


def test_chat_process_judge_uses_final_metadata_schema(tmp_path) -> None:
    session_dir = tmp_path / "pilot"
    session_dir.mkdir()
    (session_dir / "metadata.json").write_text(
        json.dumps(
            {
                "final_metadata": {
                    "scope": "repositioning",
                    "completed_phases": ["phase_0", "phase_0_5"],
                }
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "transcript.json").write_text(
        json.dumps({"system": "brandmind", "turns": []}),
        encoding="utf-8",
    )

    text = run_judges._load_session_input(session_dir)

    assert "- Scope: repositioning" in text
    assert "- Completed phases: phase_0, phase_0_5" in text
