"""Unit tests for source-grounded benchmark candidate generation."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

import pytest

from evaluation.hipporag_comparison.generate_benchmark_candidates import (
    CandidateGenerationError,
    ChatCompletionResult,
    GenerationConfig,
    TokenUsage,
    build_candidate_item,
    build_item_id,
    build_packet_prompt,
    extract_json_object,
    filter_packets,
    generate_candidates,
    packet_reasoning_effort,
)


def make_packet(
    *,
    packet_id: str = "kotler_and_armstrong_principles_of_marketing-single-001",
    scope: str = "kotler_and_armstrong_principles_of_marketing",
    difficulty: str = "medium",
    question_type: str = "application",
) -> dict[str, object]:
    """Create a valid evidence packet fixture."""

    source_id = f"{scope}::chunk_1"
    return {
        "packet_id": packet_id,
        "candidate_scope": scope,
        "difficulty_hint": difficulty,
        "question_type_hint": question_type,
        "evidence_digest": (
            "The source explains how a marketing principle should guide a "
            "managerial decision in a specific market situation."
        ),
        "sources": [
            {
                "source_id": source_id,
                "book_slug": scope,
                "source": "Chapter 1: Marketing Strategy",
                "pages": [1, 2],
                "section_summary": (
                    "A marketer should connect customer value, positioning, "
                    "and implementation choices."
                ),
                "excerpt": (
                    "Marketing strategy requires choosing a target market, "
                    "creating customer value, and aligning the offer with "
                    "positioning and execution choices."
                ),
                "word_count": 120,
            }
        ],
        "source_ids": [source_id],
    }


def make_candidate_payload(
    *,
    item_id: str = "BM5B-KOTLER-001",
    source_id: str = "kotler_and_armstrong_principles_of_marketing::chunk_1",
    scope: str = "kotler_and_armstrong_principles_of_marketing",
    question_type: str = "application",
    difficulty: str = "medium",
) -> dict[str, object]:
    """Create a schema-valid candidate payload fixture."""

    return {
        "id": item_id,
        "question": "How should a marketer apply this principle to positioning?",
        "gold_answer": (
            "A marketer should start from the target market choice, define the "
            "customer value to create, and connect positioning with execution "
            "decisions so the recommendation stays coherent."
        ),
        "answer_key_facts": [
            "The answer must mention the target market choice.",
            "The answer must connect customer value to positioning.",
            "The answer must explain the effect on marketing execution.",
        ],
        "required_sources": [source_id],
        "book_scope": scope,
        "question_type": question_type,
        "difficulty": difficulty,
        "evidence_digest": (
            "The source provides enough evidence about target market, customer "
            "value, positioning, and execution to judge the answer."
        ),
    }


class FakeChatClient:
    """Fake chat client that returns deterministic candidate JSON."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.reasoning_efforts: list[str] = []
        self.messages: list[Sequence[Mapping[str, str]]] = []

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        reasoning_effort: str,
    ) -> ChatCompletionResult:
        """Return the configured completion while recording call inputs."""

        self.messages.append(messages)
        self.reasoning_efforts.append(reasoning_effort)
        return ChatCompletionResult(
            content=self.content,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )


def test_build_packet_prompt_uses_only_packet_source_ids() -> None:
    """Prompt should include allowed packet sources and not unrelated IDs."""

    packet = make_packet()
    prompt = build_packet_prompt(packet, item_id="BM5B-KOTLER-001")

    assert "kotler_and_armstrong_principles_of_marketing::chunk_1" in prompt
    assert "strategic_brand_management::chunk_99" not in prompt
    assert "question_type: application" in prompt


def test_extract_json_object_accepts_fenced_output() -> None:
    """JSON parser should handle model output wrapped in Markdown fences."""

    payload = make_candidate_payload()
    raw_text = f"```json\n{json.dumps(payload, ensure_ascii=False)}\n```"

    parsed = extract_json_object(raw_text)

    assert parsed["id"] == "BM5B-KOTLER-001"


def test_build_candidate_item_rejects_unknown_source() -> None:
    """Candidate validation should reject ungrounded required_sources."""

    packet = make_packet()
    payload = make_candidate_payload(
        source_id="strategic_brand_management::chunk_99",
    )

    with pytest.raises(CandidateGenerationError, match="unknown sources"):
        build_candidate_item(json.dumps(payload), packet, "BM5B-KOTLER-001")


def test_build_item_id_is_stable_for_packet_scope() -> None:
    """Item IDs should be deterministic from scope and packet suffix."""

    packet = make_packet(
        packet_id="strategic_brand_management-single-017",
        scope="strategic_brand_management",
    )

    assert build_item_id(packet) == "BM5B-SBM-017"


def test_packet_reasoning_effort_is_adaptive() -> None:
    """Hard and cross-book packets should use the stronger reasoning setting."""

    config = GenerationConfig()
    normal_packet = make_packet(difficulty="medium")
    hard_packet = make_packet(difficulty="hard")
    cross_packet = make_packet(
        packet_id="cross-book-001",
        scope="cross_book",
        difficulty="hard",
    )

    assert packet_reasoning_effort(normal_packet, config) == "low"
    assert packet_reasoning_effort(hard_packet, config) == "medium"
    assert packet_reasoning_effort(cross_packet, config) == "medium"


def test_generate_candidates_with_fake_client_returns_valid_dataset() -> None:
    """Fake-client flow should produce a validated dataset and usage summary."""

    packet = make_packet()
    payload = make_candidate_payload()
    client = FakeChatClient(json.dumps(payload, ensure_ascii=False))

    result = generate_candidates(
        packets=[packet],
        chat_client=client,
        config=GenerationConfig(model="test-model"),
    )

    assert len(result.dataset.items) == 1
    assert result.dataset.items[0].id == "BM5B-KOTLER-001"
    assert result.failures == []
    assert result.usage.prompt_tokens == 10
    assert client.reasoning_efforts == ["low"]


def test_filter_packets_applies_scope_start_and_limit() -> None:
    """Packet filters should be deterministic for pilot generation."""

    packets = [
        make_packet(
            packet_id="kotler_and_armstrong_principles_of_marketing-single-001"
        ),
        make_packet(
            packet_id="kotler_and_armstrong_principles_of_marketing-single-002"
        ),
        make_packet(packet_id="cross-book-001", scope="cross_book"),
    ]

    filtered = filter_packets(
        packets,
        scope="kotler_and_armstrong_principles_of_marketing",
        start_index=1,
        limit=1,
    )

    assert len(filtered) == 1
    assert filtered[0]["packet_id"].endswith("002")
