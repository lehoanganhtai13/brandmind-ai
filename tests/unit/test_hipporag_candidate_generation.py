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
    sources = [
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
    ]
    return {
        "packet_id": packet_id,
        "candidate_scope": scope,
        "difficulty_hint": difficulty,
        "question_type_hint": question_type,
        "evidence_digest": (
            "The source explains how a marketing principle should guide a "
            "managerial decision in a specific market situation."
        ),
        "sources": sources,
        "source_ids": [source_id],
    }


def make_hard_packet() -> dict[str, object]:
    """Create a valid v2-hard evidence packet fixture."""

    packet = make_packet(
        packet_id="hard-v2-001",
        scope="kotler_and_armstrong_principles_of_marketing",
        difficulty="hard",
        question_type="synthesis",
    )
    packet["candidate_scope"] = "cross_book"
    first_source = packet["sources"][0]
    assert isinstance(first_source, dict)
    second_source = {
        **first_source,
        "source_id": "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2",
        "book_slug": "influence_new_and_expanded_the_psychology_of_persuasion",
        "source": "Chapter 2: Persuasion",
    }
    packet["sources"] = [first_source, second_source]
    packet["source_ids"] = [first_source["source_id"], second_source["source_id"]]
    packet["reasoning_type"] = "strategy_synthesis"
    packet["single_source_sufficient"] = False
    return packet


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


def make_hard_candidate_payload() -> dict[str, object]:
    """Create a schema-valid v2-hard candidate payload fixture."""

    first_source = "kotler_and_armstrong_principles_of_marketing::chunk_1"
    second_source = "influence_new_and_expanded_the_psychology_of_persuasion::chunk_2"
    return {
        **make_candidate_payload(
            item_id="BM5B-HARD-001",
            source_id=first_source,
            scope="cross_book",
            question_type="synthesis",
            difficulty="hard",
        ),
        "answer_key_facts": [
            "The answer must use the first source.",
            "The answer must use the second source.",
            "The answer must synthesize the sources.",
            "The answer must explain the distributed mechanism.",
            "The answer must state the strategic implication.",
        ],
        "required_sources": [first_source, second_source],
        "reasoning_type": "strategy_synthesis",
        "single_source_sufficient": False,
        "answer_key_fact_sources": [
            {"fact_index": 1, "source_ids": [first_source], "role": "support"},
            {"fact_index": 2, "source_ids": [second_source], "role": "support"},
            {
                "fact_index": 3,
                "source_ids": [first_source, second_source],
                "role": "synthesis",
            },
            {
                "fact_index": 4,
                "source_ids": [first_source, second_source],
                "role": "synthesis",
            },
            {"fact_index": 5, "source_ids": [first_source], "role": "support"},
        ],
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


def test_build_packet_prompt_includes_hard_metadata() -> None:
    """V2-hard prompts should expose reasoning and insufficiency constraints."""

    packet = make_hard_packet()
    prompt = build_packet_prompt(
        packet,
        item_id="BM5B-HARD-001",
        profile="v2-hard",
    )

    assert "reasoning_type: strategy_synthesis" in prompt
    assert "single_source_sufficient: false" in prompt
    assert "required_source_count: 2" in prompt


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


def test_build_item_id_is_stable_for_hard_profile() -> None:
    """Hard item IDs should use a dedicated namespace."""

    assert build_item_id(make_hard_packet(), profile="v2-hard") == "BM5B-HARD-001"


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


def test_generate_hard_candidates_with_fake_client_returns_valid_dataset() -> None:
    """V2-hard fake-client flow should preserve source-dependency metadata."""

    packet = make_hard_packet()
    payload = make_hard_candidate_payload()
    client = FakeChatClient(json.dumps(payload, ensure_ascii=False))

    result = generate_candidates(
        packets=[packet],
        chat_client=client,
        config=GenerationConfig(model="test-model", profile="v2-hard"),
    )

    assert result.dataset.items[0].reasoning_type.value == "strategy_synthesis"
    assert result.dataset.items[0].single_source_sufficient is False
    assert client.reasoning_efforts == ["medium"]


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
