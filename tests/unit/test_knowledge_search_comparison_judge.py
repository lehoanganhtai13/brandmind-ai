"""Unit tests for knowledge-search comparison judge helpers."""

from __future__ import annotations

from evaluation.knowledge_search_comparison.judge import (
    GeminiAnswerJudge,
    LiteLLMAnswerJudge,
    create_answer_judge,
    litellm_openai_base_url,
    parse_json_object,
)


def test_create_answer_judge_selects_litellm_provider() -> None:
    """Judge factory should create a LiteLLM judge for Sonnet calibration."""

    judge = create_answer_judge(
        provider="litellm",
        model="claude-sonnet-4.6",
        temperature=0.2,
        thinking_level="medium",
    )

    assert isinstance(judge, LiteLLMAnswerJudge)
    assert judge.model == "claude-sonnet-4.6"
    assert judge.temperature == 0.2
    assert judge.reasoning_effort == "medium"


def test_create_answer_judge_selects_gemini_provider() -> None:
    """Judge factory should preserve the default Gemini judge path."""

    judge = create_answer_judge(
        provider="gemini",
        model="gemini-2.5-flash",
        thinking_budget=1000,
    )

    assert isinstance(judge, GeminiAnswerJudge)
    assert judge.model == "gemini-2.5-flash"
    assert judge.thinking_budget == 1000


def test_parse_json_object_handles_fenced_output() -> None:
    """JSON parsing should accept fenced output from OpenAI-compatible models."""

    payload = parse_json_object(
        """
        ```json
        {
          "is_correct": true,
          "reasoning": "All facts are covered.",
          "covered_facts": ["fact A"],
          "missing_facts": [],
          "unsupported_claims": []
        }
        ```
        """
    )

    assert payload["is_correct"] is True
    assert payload["covered_facts"] == ["fact A"]


def test_litellm_openai_base_url_normalizes_proxy_root() -> None:
    """LiteLLM judge should target the OpenAI-compatible `/v1` endpoint."""

    assert litellm_openai_base_url("http://localhost:4000") == (
        "http://localhost:4000/v1"
    )
    assert litellm_openai_base_url("http://localhost:4000/v1") == (
        "http://localhost:4000/v1"
    )
