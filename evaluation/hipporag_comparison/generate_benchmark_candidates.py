"""Generate source-grounded benchmark candidates from evidence packets.

Business context:
    The HippoRAG comparison needs a high-quality question pool before a final
    human curation pass. This module treats the LLM as an untrusted drafting
    aid: it prompts from source packets, parses one JSON candidate per packet,
    rejects ungrounded source IDs, validates the benchmark schema, and writes
    a reviewable candidate artifact under ``.codex``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, cast

from pydantic import ValidationError

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
)
from evaluation.hipporag_comparison.build_evidence_packets import DEFAULT_PACKET_OUTPUT
from evaluation.hipporag_comparison.export_corpus import write_json

DEFAULT_OUTPUT_PATH = Path(
    ".codex/benchmarks/hipporag/dataset/candidate_questions.json"
)
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
DEFAULT_BASE_URL = "http://localhost:4000/v1"
DEFAULT_API_KEY_ENV = "LITELLM_API_KEY"
DEFAULT_INPUT_PRICE_PER_MILLION = 0.25
DEFAULT_OUTPUT_PRICE_PER_MILLION = 1.50

DATASET_DESCRIPTION = (
    "Source-grounded candidate benchmark questions generated from the five "
    "canonical BrandMind marketing books for HippoRAG comparison curation."
)

BOOK_SCOPE_CODES = {
    "how_brands_grow_what_marketers_dont_know": "HBG",
    "influence_new_and_expanded_the_psychology_of_persuasion": "INFLUENCE",
    "kotler_and_armstrong_principles_of_marketing": "KOTLER",
    "positioning_the_battle_for_your_mind": "POSITIONING",
    "strategic_brand_management": "SBM",
    "cross_book": "CROSS",
}

GENERATION_SYSTEM_PROMPT = """## Role
You create source-grounded benchmark questions for comparing marketing RAG systems.

## Non-negotiable rules
Use only the evidence packet. Do not use outside marketing knowledge.
Write the user-facing fields in natural Vietnamese.
Create one benchmark item that is answerable from the listed sources.
Keep the question specific enough that a generic answer would be incomplete.
Use every required source when the packet is cross-book.
Never cite, invent, or rename a source ID that is not in the allowed list.
Return JSON only. Do not wrap the JSON in Markdown.

## Output JSON shape
{
  "id": "BM5B-SCOPE-001",
  "question": "Vietnamese benchmark question",
  "gold_answer": "Vietnamese reference answer grounded in the evidence",
  "answer_key_facts": [
    "Atomic fact that a correct answer must include",
    "Atomic fact that a correct answer must include"
  ],
  "required_sources": ["book_slug::chunk_id"],
  "book_scope": "scope",
  "question_type": "use the requested question_type exactly",
  "difficulty": "easy|medium|hard",
  "evidence_digest": "Why the listed sources support the answer"
}

## Quality bar
Make the gold answer complete enough to judge a retrieval system answer.
Include 3 to 5 answer_key_facts when the evidence supports that many.
Use the requested question type and difficulty exactly.
Valid question_type values are definition, mechanism, compare_contrast,
application, synthesis, and diagnosis.
If the evidence is too thin, ask a narrower question instead of adding facts.
"""


class CandidateGenerationError(RuntimeError):
    """Raised when a packet cannot produce a valid benchmark candidate."""


@dataclass(frozen=True)
class GenerationConfig:
    """Runtime configuration for candidate generation.

    Args:
        model: LiteLLM model name.
        base_url: OpenAI-compatible LiteLLM base URL.
        api_key_env: Environment variable containing the LiteLLM API key.
        temperature: Sampling temperature for candidate drafting.
        max_tokens: Maximum completion tokens, including model reasoning tokens.
        default_reasoning_effort: Reasoning level for normal packets.
        hard_reasoning_effort: Reasoning level for hard and cross-book packets.
        request_timeout_seconds: HTTP timeout for one LiteLLM request.
    """

    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    api_key_env: str = DEFAULT_API_KEY_ENV
    temperature: float = 0.15
    max_tokens: int = 2200
    default_reasoning_effort: str = "low"
    hard_reasoning_effort: str = "medium"
    request_timeout_seconds: int = 180


@dataclass(frozen=True)
class TokenUsage:
    """Token accounting returned by the LiteLLM-compatible endpoint."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "TokenUsage":
        """Build token usage from an OpenAI-compatible response payload.

        Args:
            payload: Decoded response JSON from the chat completion endpoint.

        Returns:
            Token counts. Missing fields default to zero because providers vary.
        """

        raw_usage = payload.get("usage")
        if not isinstance(raw_usage, Mapping):
            return cls()
        completion_details = raw_usage.get("completion_tokens_details")
        details = completion_details if isinstance(completion_details, Mapping) else {}
        return cls(
            prompt_tokens=read_int(raw_usage, "prompt_tokens"),
            completion_tokens=read_int(raw_usage, "completion_tokens"),
            total_tokens=read_int(raw_usage, "total_tokens"),
            reasoning_tokens=read_int(details, "reasoning_tokens"),
        )

    def add(self, other: "TokenUsage") -> "TokenUsage":
        """Return summed token usage."""

        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )


@dataclass(frozen=True)
class ChatCompletionResult:
    """Text and usage from one chat completion request."""

    content: str
    usage: TokenUsage = TokenUsage()


class ChatClient(Protocol):
    """Interface for live and fake chat completion clients."""

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        reasoning_effort: str,
    ) -> ChatCompletionResult:
        """Return one model completion for the provided messages."""


@dataclass(frozen=True)
class GenerationFailure:
    """Reviewable failure for a packet that did not validate."""

    packet_id: str
    error: str


@dataclass(frozen=True)
class CandidateGenerationResult:
    """Validated candidate generation output and diagnostics."""

    dataset: BenchmarkDataset
    failures: list[GenerationFailure]
    usage: TokenUsage
    processed_packet_count: int
    model: str
    reasoning_policy: dict[str, str]


class LiteLLMChatClient:
    """Small OpenAI-compatible HTTP client for local LiteLLM.

    Args:
        config: Runtime request configuration.

    Raises:
        ValueError: If the configured API key environment variable is missing.
    """

    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.api_key = os.environ.get(config.api_key_env)
        if not self.api_key:
            raise ValueError(
                f"Missing API key environment variable: {config.api_key_env}"
            )

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        reasoning_effort: str,
    ) -> ChatCompletionResult:
        """Call the local LiteLLM chat completions endpoint."""

        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": [dict(message) for message in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if reasoning_effort and reasoning_effort != "none":
            payload["reasoning_effort"] = reasoning_effort

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - local configured endpoint.
                request,
                timeout=self.config.request_timeout_seconds,
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise CandidateGenerationError(
                f"LiteLLM HTTP {exc.code}: {body[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise CandidateGenerationError(f"LiteLLM request failed: {exc}") from exc

        response_mapping = require_mapping(response_payload, "response payload")
        choices = require_list(response_mapping.get("choices"), "choices")
        if not choices:
            raise CandidateGenerationError("LiteLLM response did not include choices.")
        first_choice = require_mapping(choices[0], "first choice")
        message = require_mapping(first_choice.get("message"), "choice message")
        content = require_string(message.get("content"), "choice message content")
        return ChatCompletionResult(
            content=content,
            usage=TokenUsage.from_payload(response_mapping),
        )


def read_int(mapping: Mapping[object, object], key: str) -> int:
    """Read an integer field from a mapping, defaulting to zero."""

    value = mapping.get(key)
    return value if isinstance(value, int) else 0


def require_mapping(value: object, label: str) -> dict[str, object]:
    """Validate that a decoded JSON value is an object."""

    if not isinstance(value, dict):
        raise CandidateGenerationError(f"Expected {label} to be an object.")
    return cast(dict[str, object], value)


def require_list(value: object, label: str) -> list[object]:
    """Validate that a decoded JSON value is a list."""

    if not isinstance(value, list):
        raise CandidateGenerationError(f"Expected {label} to be a list.")
    return value


def require_string(value: object, label: str) -> str:
    """Validate that a decoded JSON value is a non-empty string."""

    if not isinstance(value, str) or not value.strip():
        raise CandidateGenerationError(f"Expected {label} to be a non-empty string.")
    return value.strip()


def load_packets(path: Path) -> list[dict[str, object]]:
    """Load evidence packets from the Task 58 artifact.

    Args:
        path: JSON file containing a ``packets`` array.

    Returns:
        Evidence packet dictionaries in artifact order.

    Raises:
        CandidateGenerationError: If the artifact shape is invalid.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    root = require_mapping(payload, "evidence packet artifact")
    raw_packets = require_list(root.get("packets"), "packets")
    return [require_mapping(packet, "packet") for packet in raw_packets]


def packet_scope(packet: Mapping[str, object]) -> str:
    """Return the benchmark scope declared by a packet."""

    return require_string(packet.get("candidate_scope"), "candidate_scope")


def packet_difficulty(packet: Mapping[str, object]) -> str:
    """Return the requested difficulty declared by a packet."""

    return require_string(packet.get("difficulty_hint"), "difficulty_hint")


def packet_question_type(packet: Mapping[str, object]) -> str:
    """Return the requested question type declared by a packet."""

    return require_string(packet.get("question_type_hint"), "question_type_hint")


def packet_source_ids(packet: Mapping[str, object]) -> list[str]:
    """Return allowed source IDs for a packet."""

    raw_source_ids = require_list(packet.get("source_ids"), "source_ids")
    return [require_string(source_id, "source_id") for source_id in raw_source_ids]


def packet_sources(packet: Mapping[str, object]) -> list[dict[str, object]]:
    """Return source objects for a packet."""

    raw_sources = require_list(packet.get("sources"), "sources")
    return [require_mapping(source, "source") for source in raw_sources]


def build_item_id(packet: Mapping[str, object]) -> str:
    """Build a deterministic benchmark item ID from packet metadata."""

    scope = packet_scope(packet)
    code = BOOK_SCOPE_CODES.get(scope)
    if code is None:
        code = re.sub(r"[^A-Z0-9]+", "-", scope.upper()).strip("-")
    packet_id = require_string(packet.get("packet_id"), "packet_id")
    match = re.search(r"(\d+)$", packet_id)
    if not match:
        raise CandidateGenerationError(f"Packet has no numeric suffix: {packet_id}")
    return f"BM5B-{code}-{int(match.group(1)):03d}"


def packet_reasoning_effort(
    packet: Mapping[str, object],
    config: GenerationConfig,
) -> str:
    """Select the reasoning effort for a packet.

    Hard and cross-book packets receive medium reasoning because they need more
    synthesis. Simpler single-book packets use low reasoning to control cost.
    """

    if packet_scope(packet) == "cross_book" or packet_difficulty(packet) == "hard":
        return config.hard_reasoning_effort
    return config.default_reasoning_effort


def build_packet_prompt(packet: Mapping[str, object], item_id: str) -> str:
    """Build the user prompt for one evidence packet.

    Args:
        packet: Evidence packet generated by Task 58.
        item_id: Deterministic item ID the output must use.

    Returns:
        A packet-specific prompt containing only allowed evidence.
    """

    source_blocks = []
    for index, source in enumerate(packet_sources(packet), start=1):
        source_id = require_string(source.get("source_id"), "source_id")
        book_slug = require_string(source.get("book_slug"), "book_slug")
        pages = require_list(source.get("pages"), "source pages")
        page_text = ", ".join(str(page) for page in pages) if pages else "unknown"
        source_blocks.append(
            "\n".join(
                [
                    f"### Source {index}",
                    f"source_id: {source_id}",
                    f"book_slug: {book_slug}",
                    f"source: {require_string(source.get('source'), 'source')}",
                    f"pages: {page_text}",
                    "section_summary:",
                    require_string(
                        source.get("section_summary"),
                        "section_summary",
                    ),
                    "excerpt:",
                    require_string(source.get("excerpt"), "excerpt"),
                ]
            )
        )

    allowed_source_ids = "\n".join(
        f"- {source_id}" for source_id in packet_source_ids(packet)
    )
    return "\n\n".join(
        [
            "## Task",
            "Create exactly one source-grounded benchmark candidate.",
            "",
            "## Required fixed fields",
            f"id: {item_id}",
            f"book_scope: {packet_scope(packet)}",
            f"question_type: {packet_question_type(packet)}",
            f"difficulty: {packet_difficulty(packet)}",
            "",
            "## Evidence digest",
            require_string(packet.get("evidence_digest"), "evidence_digest"),
            "",
            "## Allowed required_sources",
            allowed_source_ids,
            "",
            "## Source evidence",
            "\n\n".join(source_blocks),
        ]
    )


def extract_json_object(raw_text: str) -> dict[str, object]:
    """Extract a JSON object from plain or fenced model output."""

    stripped = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    candidate_text = fence_match.group(1).strip() if fence_match else stripped
    if not candidate_text.startswith("{"):
        start_index = candidate_text.find("{")
        end_index = candidate_text.rfind("}")
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise CandidateGenerationError("Model output did not contain JSON.")
        candidate_text = candidate_text[start_index : end_index + 1]
    try:
        parsed = json.loads(candidate_text)
    except json.JSONDecodeError as exc:
        raise CandidateGenerationError(f"Model output JSON is invalid: {exc}") from exc
    return require_mapping(parsed, "model candidate")


def validate_source_subset(
    candidate: Mapping[str, object],
    packet: Mapping[str, object],
) -> None:
    """Reject candidates that cite sources outside the packet."""

    required_sources = require_list(
        candidate.get("required_sources"),
        "candidate required_sources",
    )
    normalized_required = [
        require_string(source_id, "candidate required source")
        for source_id in required_sources
    ]
    allowed = set(packet_source_ids(packet))
    unknown = sorted(set(normalized_required) - allowed)
    if unknown:
        raise CandidateGenerationError(f"Candidate used unknown sources: {unknown}")


def validate_fixed_fields(
    candidate: Mapping[str, object],
    packet: Mapping[str, object],
    item_id: str,
) -> None:
    """Ensure fixed stratification fields match the source packet."""

    expected_fields = {
        "id": item_id,
        "book_scope": packet_scope(packet),
        "question_type": packet_question_type(packet),
        "difficulty": packet_difficulty(packet),
    }
    mismatches = {
        field: (candidate.get(field), expected)
        for field, expected in expected_fields.items()
        if candidate.get(field) != expected
    }
    if mismatches:
        raise CandidateGenerationError(f"Candidate fixed-field mismatch: {mismatches}")


def build_candidate_item(
    raw_content: str,
    packet: Mapping[str, object],
    item_id: str,
) -> BenchmarkItem:
    """Parse and validate one model-generated benchmark item."""

    candidate = extract_json_object(raw_content)
    validate_fixed_fields(candidate, packet, item_id)
    validate_source_subset(candidate, packet)
    try:
        return BenchmarkItem.model_validate(candidate)
    except ValidationError as exc:
        raise CandidateGenerationError(str(exc)) from exc


def filter_packets(
    packets: Sequence[dict[str, object]],
    scope: str | None,
    start_index: int,
    limit: int | None,
) -> list[dict[str, object]]:
    """Apply deterministic packet filters from CLI arguments."""

    if start_index < 0:
        raise ValueError("start_index must be non-negative.")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive when provided.")

    filtered = [
        packet for packet in packets if scope is None or packet_scope(packet) == scope
    ]
    filtered = filtered[start_index:]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def generate_candidates(
    packets: Sequence[dict[str, object]],
    chat_client: ChatClient,
    config: GenerationConfig,
    progress: Callable[[str], None] | None = None,
) -> CandidateGenerationResult:
    """Generate and validate candidate benchmark items.

    Args:
        packets: Evidence packets to process.
        chat_client: Live or fake chat completion client.
        config: Generation configuration.
        progress: Optional status callback for long-running generation.

    Returns:
        Validated dataset candidates and generation diagnostics.

    Raises:
        CandidateGenerationError: If no packet produces a valid candidate.
    """

    items: list[BenchmarkItem] = []
    failures: list[GenerationFailure] = []
    total_usage = TokenUsage()

    for index, packet in enumerate(packets, start=1):
        packet_id = require_string(packet.get("packet_id"), "packet_id")
        item_id = build_item_id(packet)
        reasoning_effort = packet_reasoning_effort(packet, config)
        messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": build_packet_prompt(packet, item_id)},
        ]
        try:
            completion = chat_client.complete(messages, reasoning_effort)
            total_usage = total_usage.add(completion.usage)
            items.append(build_candidate_item(completion.content, packet, item_id))
            if progress is not None:
                progress(f"[{index}/{len(packets)}] {packet_id} -> ok")
        except CandidateGenerationError as exc:
            failures.append(GenerationFailure(packet_id=packet_id, error=str(exc)))
            if progress is not None:
                progress(f"[{index}/{len(packets)}] {packet_id} -> failed")

    if not items:
        raise CandidateGenerationError("No valid candidates generated.")

    dataset = BenchmarkDataset(description=DATASET_DESCRIPTION, items=items)
    return CandidateGenerationResult(
        dataset=dataset,
        failures=failures,
        usage=total_usage,
        processed_packet_count=len(packets),
        model=config.model,
        reasoning_policy={
            "default": config.default_reasoning_effort,
            "hard_or_cross_book": config.hard_reasoning_effort,
        },
    )


def estimate_cost_usd(
    usage: TokenUsage,
    input_price_per_million: float,
    output_price_per_million: float,
) -> float:
    """Estimate generation cost from token counts and provided prices."""

    input_cost = usage.prompt_tokens * input_price_per_million / 1_000_000
    output_cost = usage.completion_tokens * output_price_per_million / 1_000_000
    return round(input_cost + output_cost, 6)


def write_generation_result(
    result: CandidateGenerationResult,
    output_path: Path,
    input_price_per_million: float,
    output_price_per_million: float,
) -> None:
    """Write candidate dataset plus diagnostics to a JSON artifact."""

    write_json(
        output_path,
        {
            "dataset": result.dataset.model_dump(mode="json"),
            "distribution_summary": result.dataset.distribution_summary(),
            "generation": {
                "model": result.model,
                "reasoning_policy": result.reasoning_policy,
                "processed_packet_count": result.processed_packet_count,
                "success_count": len(result.dataset.items),
                "failure_count": len(result.failures),
                "usage": asdict(result.usage),
                "estimated_cost_usd": estimate_cost_usd(
                    result.usage,
                    input_price_per_million,
                    output_price_per_million,
                ),
                "input_price_per_million": input_price_per_million,
                "output_price_per_million": output_price_per_million,
            },
            "failures": [asdict(failure) for failure in result.failures],
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for internal candidate generation."""

    parser = argparse.ArgumentParser(
        description="Generate source-grounded 5-book benchmark candidates.",
    )
    parser.add_argument(
        "--evidence-packets",
        type=Path,
        default=DEFAULT_PACKET_OUTPUT,
        help="Path to Task 58 evidence packet JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path for generated candidate dataset JSON.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="LiteLLM model name.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="OpenAI-compatible LiteLLM base URL.",
    )
    parser.add_argument(
        "--api-key-env",
        default=DEFAULT_API_KEY_ENV,
        help="Environment variable containing the LiteLLM API key.",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help="Optional candidate_scope filter, such as cross_book.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Zero-based index after optional scope filtering.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum packet count for pilots.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.15,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2200,
        help="Maximum completion tokens per request.",
    )
    parser.add_argument(
        "--default-reasoning-effort",
        default="low",
        help="Reasoning effort for normal packets.",
    )
    parser.add_argument(
        "--hard-reasoning-effort",
        default="medium",
        help="Reasoning effort for hard and cross-book packets.",
    )
    parser.add_argument(
        "--input-price-per-million",
        type=float,
        default=DEFAULT_INPUT_PRICE_PER_MILLION,
        help="Estimated input token price used only for cost reporting.",
    )
    parser.add_argument(
        "--output-price-per-million",
        type=float,
        default=DEFAULT_OUTPUT_PRICE_PER_MILLION,
        help="Estimated output token price used only for cost reporting.",
    )
    return parser.parse_args()


def print_progress(message: str) -> None:
    """Print long-running generation progress without buffering."""

    print(message, flush=True)


def main() -> None:
    """Run internal candidate generation from the command line."""

    args = parse_args()
    config = GenerationConfig(
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        default_reasoning_effort=args.default_reasoning_effort,
        hard_reasoning_effort=args.hard_reasoning_effort,
    )
    packets = filter_packets(
        load_packets(args.evidence_packets),
        scope=args.scope,
        start_index=args.start_index,
        limit=args.limit,
    )
    result = generate_candidates(
        packets=packets,
        chat_client=LiteLLMChatClient(config),
        config=config,
        progress=print_progress,
    )
    write_generation_result(
        result,
        output_path=args.output,
        input_price_per_million=args.input_price_per_million,
        output_price_per_million=args.output_price_per_million,
    )
    print(
        "Wrote "
        f"{len(result.dataset.items)} candidates with {len(result.failures)} "
        f"failures to {args.output}"
    )


if __name__ == "__main__":
    main()
