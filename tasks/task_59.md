# Task 59: Source-First Candidate Question Generation

## Metadata

- **Epic**: Marketing KG Evaluation — HippoRAG comparison
- **Priority**: High
- **Status**: Done
- **Estimated Effort**: 1-2 days for generator, validation, and candidate artifact
- **Team**: Backend / Evaluation
- **Related Tasks**: `tasks/task_57.md`, `tasks/task_58.md`
- **Blocking**: Final 150-item 5-book benchmark dataset
- **Blocked by**: None

### Progress Checklist

> Agent: Update checkboxes as each section is completed. Do not mark a section done until it is
> fully verified.

- [x] Agent Protocol — Read and confirmed from `tasks/task_template.md`
- [x] Context & Goals — Problem definition and success metrics
- [x] Solution Design — Architecture and technical approach
- [x] Pre-Implementation Research — Findings logged before coding
- [x] Implementation Plan — Phased execution plan drafted
- [x] Implementation Detail — Full ready-to-apply code reviewed by user before file writes
    - [x] Component 1 — Internal candidate generator script
    - [x] Component 2 — Unit tests for prompt, parsing, validation, and fake client flow
    - [x] Component 3 — Run candidate generation on evidence packets
- [x] Test Execution Log — All tests run and results recorded
- [x] Decision Log — Key decisions documented
- [x] Task Summary — Final implementation summary completed

## Reference Documentation

- **Coding Standards**: `tasks/task_template.md`, Rule 4 and Rule 2.5.
- **Prompt standards**: `tasks/task_template.md`, Rule 5, plus
  `/Users/lehoanganhtai/.codex/skills/prompt-engineering-patterns/SKILL.md`.
- **Eval design guidance**: `/Users/lehoanganhtai/.codex/skills/llm-eval-design/SKILL.md` and
  `/Users/lehoanganhtai/.codex/skills/llm-eval-design/references/dataset-construction.md`.
- **Dataset schema and packet builder**: `tasks/task_58.md`,
  `evaluation/hipporag_comparison/benchmark_schema.py`,
  `evaluation/hipporag_comparison/build_evidence_packets.py`,
  `evaluation/hipporag_comparison/validate_benchmark_dataset.py`.
- **Evidence packet artifact**:
  `.codex/benchmarks/hipporag/dataset/evidence_packets.json`.

------------------------------------------------------------------------

## Agent Protocol

This task follows `tasks/task_template.md`:

1. Research before writing implementation code.
2. Stop and ask if requirements conflict.
3. Fill Implementation Detail with full ready-to-apply code before project files are written.
4. Use production-grade Python: module/class/function docstrings, type hints, double quotes,
   English-only code comments, and focused modules.
5. Do not print, store, or commit secrets.

------------------------------------------------------------------------

## Context & Goals

### Context

Task 58 created 230 source-first evidence packets from the five-book corpus. The next benchmark
step is to generate candidate questions from those packets while preserving source grounding. The
final reviewed dataset target remains 150 items: 25 per book plus 25 cross-book questions. This
task creates the candidate-generation tool and ignored candidate artifact; final dataset review and
trimming happens in a later task.

### Goal

Generate machine-validated candidate benchmark items from evidence packets through the local
LiteLLM proxy, using a prompt that forces source-grounded output and rejects sources not present in
the packet.

### Success Metrics / Acceptance Criteria

- **Prompt discipline**: Generator prompt starts from evidence, not generic marketing knowledge,
  and asks for one schema-compatible JSON item per packet.
- **Source safety**: Generated `required_sources` must be a subset of the packet `source_ids`;
  otherwise the item is rejected.
- **Schema safety**: Each generated item must validate as `BenchmarkItem`.
- **Artifact**: Generator writes candidate dataset JSON under ignored
  `.codex/benchmarks/hipporag/dataset/candidate_questions.json`.
- **Reviewability**: Output includes distribution summary and skipped-packet errors.
- **Tests**: Unit tests cover prompt construction, JSON parsing, invalid-source rejection,
  deterministic item IDs, and fake-client generation without live API calls.

------------------------------------------------------------------------

## Solution Design

### Proposed Approach

**Generate one candidate item per evidence packet, then validate immediately.** The tool treats
LLM generation as untrusted. It builds a strict packet-specific prompt, parses JSON, verifies
source subset constraints, validates with Task 58 Pydantic models, and only then writes candidates.

### Technology Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| Python standard library `urllib` | LiteLLM `/v1/chat/completions` call | Avoids adding dependencies |
| Pydantic schema from Task 58 | Candidate validation | Reuses source-grounded contract |
| Protocol for chat client | Testable generation flow | Fake client can test without network |
| JSON artifact under `.codex` | Candidate output | Reviewable but not committed before human approval |

### Architecture Overview

```text
.codex/benchmarks/hipporag/dataset/evidence_packets.json
    |
    | generate_benchmark_candidates.py
    | - strict packet prompt
    | - LiteLLM http://localhost:4000/v1/chat/completions
    | - source subset check
    | - BenchmarkItem validation
    v
.codex/benchmarks/hipporag/dataset/candidate_questions.json
    |
    | later review/trim task
    v
evaluation/hipporag_comparison/datasets/marketing_5books_benchmark.json
```

### Issues & Solutions

1. **LLM may invent sources** -> reject any `required_sources` outside packet `source_ids`.
2. **LLM may output prose or fenced JSON** -> robust JSON extraction from raw text or code fences.
3. **Candidate generation can cost time/tokens** -> support `--limit`, `--scope`, and
   `--start-index` for controlled pilots before full generation.
4. **Final dataset should not be auto-trusted** -> write candidates to ignored `.codex`; final
   tracked dataset requires review and separate validation.

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `tasks/task_template.md`
  - `tasks/task_58.md`
  - `evaluation/hipporag_comparison/benchmark_schema.py`
  - `evaluation/hipporag_comparison/build_evidence_packets.py`
  - `evaluation/hipporag_comparison/validate_benchmark_dataset.py`
  - `.codex/benchmarks/hipporag/dataset/evidence_packets.json`
- **Relevant patterns found**:
  - `BenchmarkItem` already enforces ID format, minimum answer/fact lengths, unique required
    sources, and cross-book source coverage.
  - Evidence packets already expose `packet_id`, `candidate_scope`, `difficulty_hint`,
    `question_type_hint`, `evidence_digest`, `source_ids`, and per-source excerpts.
  - `.codex/` is ignored, so generated candidates can be inspected without polluting git.
- **Potential conflicts**:
  - This script reads an API key from an environment variable but must never print it.
  - Full candidate generation over 230 packets may be slow; the CLI needs pilot controls.

### External Library / API Research

- **Library/API**: OpenAI-compatible LiteLLM chat completions.
- **Documentation source**: Existing verified local LiteLLM setup from Tasks 57-58.
- **Key findings**:
  - Local LiteLLM runs at `http://localhost:4000/v1`.
  - Available quality-first low-cost model is `gemini-3.1-flash-lite-preview`.
  - Pilot generation showed reasoning effort `medium` can improve hard/cross-book synthesis
    but needs a larger `max_tokens` budget, so the implementation uses adaptive reasoning:
    `low` for normal packets and `medium` for hard or cross-book packets.
  - The project already uses LiteLLM as the bridge and avoids storing secrets in memory.
- **Interface confirmed**:
  - `POST /v1/chat/completions` with JSON body:
    `model`, `messages`, `temperature`, `max_tokens`.

### Unknown / Risks Identified

- [x] Whether generation should create the final tracked dataset directly: no. It should create
  candidates under ignored `.codex` first.
- [x] Whether source subset validation can be deterministic: yes, because packet `source_ids` are
  explicit.
- [ ] Whether all 230 packets produce high-quality items on first pass: unknown until generation
  runs; skipped/error packets are captured for review.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain for this candidate-generation slice

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Generator CLI

1. Add `evaluation/hipporag_comparison/generate_benchmark_candidates.py`.
   - Read evidence packet JSON.
   - Filter by `--scope`, `--limit`, and `--start-index`.
   - Build packet-specific prompt.
   - Call LiteLLM via a testable chat client.
   - Parse JSON, validate source subset, validate `BenchmarkItem`, and write `BenchmarkDataset`.

### Phase 2: Unit tests

1. Add `tests/unit/test_hipporag_candidate_generation.py`.
   - Test prompt construction includes source IDs and excludes unrelated source IDs.
   - Test JSON extraction from fenced and plain model output.
   - Test invalid source rejection.
   - Test fake-client generation produces a valid dataset.

### Phase 3: Candidate artifact

1. Run a small pilot first:
   - `uv run python -m evaluation.hipporag_comparison.generate_benchmark_candidates --limit 5`
2. If pilot passes, run broader generation:
   - `uv run python -m evaluation.hipporag_comparison.generate_benchmark_candidates`
3. Validate the produced candidate artifact with the same schema checks.

### Verification Commands

- `uv run pytest tests/unit/test_hipporag_candidate_generation.py -q`
- `uv run pytest tests/unit/test_hipporag_candidate_generation.py tests/unit/test_hipporag_benchmark_dataset.py tests/unit/test_hipporag_comparison.py -q`
- `uv run ruff format --check evaluation/hipporag_comparison tests/unit/test_hipporag_candidate_generation.py`
- `uv run ruff check evaluation/hipporag_comparison tests/unit/test_hipporag_candidate_generation.py`
- `make typecheck`

### Rollback Plan

Remove the new files:

- `evaluation/hipporag_comparison/generate_benchmark_candidates.py`
- `tests/unit/test_hipporag_candidate_generation.py`

Remove ignored generated artifact if needed:

- `.codex/benchmarks/hipporag/dataset/candidate_questions.json`

------------------------------------------------------------------------

## Implementation Detail

> This section is the pre-apply review surface. Do not write the project files below until the
> user confirms this detail.

### Component 1: Internal candidate generator script

> Status: Done

#### Requirement 1 — Generate schema-valid candidates from evidence packets

- **Requirement**: Add a testable CLI that generates candidate benchmark items through local
  LiteLLM and rejects ungrounded outputs.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/generate_benchmark_candidates.py` `[NEW]`

```python
"""Generate source-grounded benchmark candidate questions from evidence packets."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
)
from evaluation.hipporag_comparison.export_corpus import write_json

DEFAULT_EVIDENCE_PACKETS_PATH = Path(
    ".codex/benchmarks/hipporag/dataset/evidence_packets.json"
)
DEFAULT_CANDIDATES_OUTPUT = Path(
    ".codex/benchmarks/hipporag/dataset/candidate_questions.json"
)
DEFAULT_LITELLM_BASE_URL = "http://localhost:4000/v1"
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

GENERATION_SYSTEM_PROMPT = """You generate source-grounded marketing benchmark questions for evaluating retrieval systems.

Use only the evidence packet supplied by the user. Do not use outside marketing knowledge except to phrase a clear question and concise answer around the supplied evidence.

Return exactly one JSON object. Do not wrap it in markdown. The JSON object must contain: question, gold_answer, answer_key_facts, required_sources, question_type, difficulty, evidence_digest.

The required_sources array must use only source IDs listed in the evidence packet. If the packet has candidate_scope cross_book, use at least two source IDs from different books. Otherwise use one or more source IDs from the packet's single book.

Write questions in Vietnamese because the benchmark targets Vietnamese junior marketers. Keep book titles and framework names in their original language when that improves precision.

Make the item answerable from the supplied sources, but not answerable by a generic marketing cliché. The gold_answer must state the core concept, the reasoning, and the practical marketing implication.
"""


class CandidateGenerationError(Exception):
    """Raised when one packet cannot produce a valid benchmark candidate."""


class ChatClient(Protocol):
    """Protocol for a chat-completion client used by the generator."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return assistant text for a chat completion request."""


@dataclass(frozen=True)
class GenerationConfig:
    """Runtime configuration for candidate generation."""

    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_LITELLM_BASE_URL
    api_key_env: str = "LITELLM_API_KEY"
    temperature: float = 0.2
    max_tokens: int = 1800
    timeout_seconds: int = 90


@dataclass(frozen=True)
class GenerationFailure:
    """Captured failure for one evidence packet."""

    packet_id: str
    error: str


@dataclass(frozen=True)
class GenerationResult:
    """Candidate generation output and diagnostics."""

    dataset: BenchmarkDataset
    failures: list[GenerationFailure]


class LiteLLMChatClient:
    """Small OpenAI-compatible LiteLLM client using the Python standard library."""

    def __init__(self, config: GenerationConfig) -> None:
        """Create a LiteLLM client.

        Args:
            config: LiteLLM request configuration.

        Raises:
            ValueError: If the configured API key environment variable is empty.
        """

        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key environment variable: {config.api_key_env}")
        self.config = config
        self.api_key = api_key

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Call LiteLLM chat completions and return assistant content."""

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        request = urllib.request.Request(
            url=f"{self.config.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise CandidateGenerationError(str(exc)) from exc

        choices = response_payload.get("choices", [])
        if not choices:
            raise CandidateGenerationError("LiteLLM response did not include choices.")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise CandidateGenerationError("LiteLLM response did not include text content.")
        return content


def load_json(path: Path) -> object:
    """Load JSON from disk with UTF-8 encoding."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_evidence_packets(path: Path) -> list[dict[str, object]]:
    """Load evidence packets from the Task 58 artifact."""

    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected evidence packet object in {path}.")
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError(f"Expected packets list in {path}.")
    return [packet for packet in packets if isinstance(packet, dict)]


def filter_packets(
    packets: list[dict[str, object]],
    *,
    scope: str | None,
    start_index: int,
    limit: int | None,
) -> list[dict[str, object]]:
    """Filter packets for controlled generation pilots."""

    if start_index < 0:
        raise ValueError("start_index must be non-negative.")
    filtered = [
        packet
        for packet in packets
        if scope is None or str(packet.get("candidate_scope")) == scope
    ]
    sliced = filtered[start_index:]
    if limit is None:
        return sliced
    if limit <= 0:
        raise ValueError("limit must be positive when provided.")
    return sliced[:limit]


def packet_source_ids(packet: dict[str, object]) -> list[str]:
    """Return packet source IDs as strings."""

    source_ids = packet.get("source_ids")
    if not isinstance(source_ids, list):
        raise CandidateGenerationError("Evidence packet is missing source_ids.")
    normalized = [str(source_id).strip() for source_id in source_ids]
    if any(not source_id for source_id in normalized):
        raise CandidateGenerationError("Evidence packet contains an empty source ID.")
    return normalized


def build_item_id(packet: dict[str, object], index: int) -> str:
    """Build a deterministic candidate item ID from packet scope and order."""

    scope = str(packet.get("candidate_scope", "unknown")).upper()
    scope_code = re.sub(r"[^A-Z0-9]+", "-", scope).strip("-")
    return f"BM5B-{scope_code}-{index:03d}"


def build_generation_messages(packet: dict[str, object]) -> list[dict[str, str]]:
    """Build chat messages for one packet-specific generation request."""

    packet_payload = {
        "packet_id": packet.get("packet_id"),
        "candidate_scope": packet.get("candidate_scope"),
        "difficulty_hint": packet.get("difficulty_hint"),
        "question_type_hint": packet.get("question_type_hint"),
        "evidence_digest": packet.get("evidence_digest"),
        "source_ids": packet_source_ids(packet),
        "sources": packet.get("sources"),
    }
    return [
        {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(packet_payload, ensure_ascii=False, indent=2),
        },
    ]


def extract_json_object(text: str) -> dict[str, object]:
    """Extract a JSON object from model text.

    Args:
        text: Raw model output.

    Returns:
        Parsed JSON object.

    Raises:
        CandidateGenerationError: If no JSON object can be parsed.
    """

    stripped = text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fenced_match:
        stripped = fenced_match.group(1)
    elif not stripped.startswith("{"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise CandidateGenerationError("Model output did not contain a JSON object.")
        stripped = stripped[start : end + 1]
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise CandidateGenerationError(f"Invalid JSON output: {exc}") from exc
    if not isinstance(payload, dict):
        raise CandidateGenerationError("Model output JSON must be an object.")
    return payload


def build_item_from_payload(
    payload: dict[str, object],
    packet: dict[str, object],
    item_id: str,
) -> BenchmarkItem:
    """Validate one model payload as a benchmark item."""

    allowed_sources = set(packet_source_ids(packet))
    raw_sources = payload.get("required_sources")
    if not isinstance(raw_sources, list):
        raise CandidateGenerationError("required_sources must be a list.")
    required_sources = [str(source_id).strip() for source_id in raw_sources]
    unknown_sources = sorted(set(required_sources) - allowed_sources)
    if unknown_sources:
        raise CandidateGenerationError(f"Generated item used unknown sources: {unknown_sources}")

    return BenchmarkItem(
        id=item_id,
        question=str(payload.get("question", "")).strip(),
        gold_answer=str(payload.get("gold_answer", "")).strip(),
        answer_key_facts=[
            str(fact).strip() for fact in payload.get("answer_key_facts", [])
        ],
        required_sources=required_sources,
        book_scope=str(packet.get("candidate_scope", "")).strip(),
        question_type=str(payload.get("question_type", "")).strip(),
        difficulty=str(payload.get("difficulty", "")).strip(),
        evidence_digest=str(payload.get("evidence_digest", "")).strip(),
    )


def generate_candidate_for_packet(
    packet: dict[str, object],
    client: ChatClient,
    item_id: str,
) -> BenchmarkItem:
    """Generate and validate one candidate item from one evidence packet."""

    response_text = client.complete(build_generation_messages(packet))
    payload = extract_json_object(response_text)
    return build_item_from_payload(payload, packet, item_id)


def generate_candidates(
    packets: list[dict[str, object]],
    client: ChatClient,
    *,
    dataset_description: str,
) -> GenerationResult:
    """Generate a candidate dataset from evidence packets."""

    items: list[BenchmarkItem] = []
    failures: list[GenerationFailure] = []
    for index, packet in enumerate(packets, start=1):
        packet_id = str(packet.get("packet_id", f"packet-{index}"))
        try:
            item = generate_candidate_for_packet(
                packet=packet,
                client=client,
                item_id=build_item_id(packet, index),
            )
            items.append(item)
        except (CandidateGenerationError, ValueError) as exc:
            failures.append(GenerationFailure(packet_id=packet_id, error=str(exc)))

    dataset = BenchmarkDataset(
        description=dataset_description,
        items=items,
    )
    return GenerationResult(dataset=dataset, failures=failures)


def write_generation_result(result: GenerationResult, output_path: Path) -> None:
    """Write candidate dataset and generation diagnostics."""

    write_json(
        output_path,
        {
            "dataset": result.dataset.model_dump(mode="json"),
            "distribution_summary": result.dataset.distribution_summary(),
            "failure_count": len(result.failures),
            "failures": [asdict(failure) for failure in result.failures],
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for candidate generation."""

    parser = argparse.ArgumentParser(
        description="Generate source-grounded benchmark candidates from evidence packets.",
    )
    parser.add_argument(
        "--packets",
        type=Path,
        default=DEFAULT_EVIDENCE_PACKETS_PATH,
        help="Evidence packets JSON path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CANDIDATES_OUTPUT,
        help="Candidate dataset JSON output path.",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default=None,
        help="Optional candidate_scope filter, for example cross_book.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Zero-based start index after optional scope filtering.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of packets to process.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="LiteLLM model name.",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_LITELLM_BASE_URL,
        help="OpenAI-compatible LiteLLM base URL.",
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="LITELLM_API_KEY",
        help="Environment variable containing the LiteLLM API key.",
    )
    return parser.parse_args()


def main() -> None:
    """Run candidate generation from the command line."""

    args = parse_args()
    packets = filter_packets(
        load_evidence_packets(args.packets),
        scope=args.scope,
        start_index=args.start_index,
        limit=args.limit,
    )
    client = LiteLLMChatClient(
        GenerationConfig(
            model=args.model,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
        )
    )
    result = generate_candidates(
        packets=packets,
        client=client,
        dataset_description=(
            "Source-grounded candidate benchmark questions generated from five-book evidence packets."
        ),
    )
    write_generation_result(result, args.output)


if __name__ == "__main__":
    main()
```

### Component 2: Unit tests

> Status: Done

#### Requirement 2 — Test candidate generation without live API calls

- **Requirement**: Add unit tests for prompt construction, JSON parsing, source validation, and
  fake-client generation.

- **Implementation**:

Target file: `tests/unit/test_hipporag_candidate_generation.py` `[NEW]`

```python
"""Unit tests for source-grounded candidate question generation."""

from __future__ import annotations

import json

import pytest

from evaluation.hipporag_comparison.generate_benchmark_candidates import (
    CandidateGenerationError,
    build_generation_messages,
    build_item_from_payload,
    extract_json_object,
    filter_packets,
    generate_candidates,
)


class FakeChatClient:
    """Fake chat client returning a fixed candidate payload."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return one valid candidate JSON response."""

        assert messages
        return json.dumps(
            {
                "question": "Làm sao áp dụng nguyên tắc này vào quyết định marketing?",
                "gold_answer": (
                    "Một câu trả lời đúng phải nêu nguyên tắc marketing trong nguồn, giải thích "
                    "cơ chế chiến lược, và chỉ ra hệ quả thực hành cho marketer khi ra quyết định."
                ),
                "answer_key_facts": [
                    "Nêu đúng nguyên tắc marketing được nguồn hỗ trợ.",
                    "Giải thích được cơ chế hoặc logic chiến lược trong nguồn.",
                ],
                "required_sources": [
                    "kotler_and_armstrong_principles_of_marketing::chunk_1"
                ],
                "question_type": "application",
                "difficulty": "medium",
                "evidence_digest": (
                    "Nguồn được chọn giải thích một nguyên tắc marketing và cung cấp đủ bằng "
                    "chứng để tạo câu hỏi ứng dụng."
                ),
            }
        )


def make_packet() -> dict[str, object]:
    """Create one evidence packet fixture."""

    return {
        "packet_id": "kotler-single-001",
        "candidate_scope": "kotler_and_armstrong_principles_of_marketing",
        "difficulty_hint": "medium",
        "question_type_hint": "application",
        "evidence_digest": "A packet digest grounded in a Kotler source.",
        "source_ids": ["kotler_and_armstrong_principles_of_marketing::chunk_1"],
        "sources": [
            {
                "source_id": "kotler_and_armstrong_principles_of_marketing::chunk_1",
                "book_slug": "kotler_and_armstrong_principles_of_marketing",
                "source": "Chapter 1",
                "pages": [1],
                "section_summary": "Summary.",
                "excerpt": "Evidence excerpt.",
                "word_count": 120,
            }
        ],
    }


def test_build_generation_messages_includes_packet_sources() -> None:
    """Prompt messages should include only the current packet source IDs."""

    messages = build_generation_messages(make_packet())
    user_payload = json.loads(messages[1]["content"])

    assert messages[0]["role"] == "system"
    assert user_payload["source_ids"] == [
        "kotler_and_armstrong_principles_of_marketing::chunk_1"
    ]


def test_extract_json_object_accepts_fenced_json() -> None:
    """Generator should parse fenced JSON returned by chat models."""

    payload = extract_json_object('```json\n{"question": "abc"}\n```')

    assert payload == {"question": "abc"}


def test_build_item_from_payload_rejects_unknown_sources() -> None:
    """Generated items must not use source IDs outside the packet."""

    payload = {
        "question": "Làm sao áp dụng nguyên tắc này vào quyết định marketing?",
        "gold_answer": (
            "Một câu trả lời đúng phải nêu nguyên tắc marketing trong nguồn, giải thích cơ chế, "
            "và chỉ ra hệ quả thực hành cho marketer khi ra quyết định."
        ),
        "answer_key_facts": [
            "Nêu đúng nguyên tắc marketing được nguồn hỗ trợ.",
            "Giải thích được cơ chế hoặc logic chiến lược trong nguồn.",
        ],
        "required_sources": ["other_book::chunk_9"],
        "question_type": "application",
        "difficulty": "medium",
        "evidence_digest": (
            "Nguồn được chọn giải thích một nguyên tắc marketing và cung cấp đủ bằng chứng."
        ),
    }

    with pytest.raises(CandidateGenerationError):
        build_item_from_payload(payload, make_packet(), "BM5B-KOTLER-001")


def test_filter_packets_supports_scope_start_and_limit() -> None:
    """Packet filtering should support safe pilot runs."""

    packets = [
        {"candidate_scope": "book_a", "packet_id": "a1", "source_ids": ["book_a::1"]},
        {"candidate_scope": "book_b", "packet_id": "b1", "source_ids": ["book_b::1"]},
        {"candidate_scope": "book_b", "packet_id": "b2", "source_ids": ["book_b::2"]},
    ]

    filtered = filter_packets(packets, scope="book_b", start_index=1, limit=1)

    assert filtered == [packets[2]]


def test_generate_candidates_with_fake_client() -> None:
    """Fake client flow should produce a schema-valid candidate dataset."""

    result = generate_candidates(
        packets=[make_packet()],
        client=FakeChatClient(),
        dataset_description="A source-grounded candidate dataset for tests.",
    )

    assert len(result.dataset.items) == 1
    assert result.failures == []
    assert result.dataset.items[0].id == (
        "BM5B-KOTLER-AND-ARMSTRONG-PRINCIPLES-OF-MARKETING-001"
    )
```

### Component 3: Candidate artifact generation

> Status: Done

#### Requirement 3 — Generate candidate artifact from evidence packets

- **Requirement**: Run the generator against evidence packets and write candidate questions to
  ignored `.codex` output for review.

- **Implementation**:

No additional source file is required. After code is applied and tests pass, run:

```bash
uv run python -m evaluation.hipporag_comparison.generate_benchmark_candidates --limit 5
```

If the 5-packet pilot output validates, run:

```bash
uv run python -m evaluation.hipporag_comparison.generate_benchmark_candidates
```

The output path is:

```text
.codex/benchmarks/hipporag/dataset/candidate_questions.json
```

------------------------------------------------------------------------

## Test Execution Log

- **2026-05-09**:
  `uv run pytest tests/unit/test_hipporag_candidate_generation.py -q` → 7 passed.
- **2026-05-09**:
  `uv run pytest tests/unit/test_hipporag_candidate_generation.py tests/unit/test_hipporag_benchmark_dataset.py tests/unit/test_hipporag_comparison.py -q`
  → 22 passed.
- **2026-05-09**:
  `uv run ruff format --check evaluation/hipporag_comparison tests/unit/test_hipporag_candidate_generation.py`
  → 8 files already formatted.
- **2026-05-09**:
  `uv run ruff check evaluation/hipporag_comparison tests/unit/test_hipporag_candidate_generation.py`
  → all checks passed.
- **2026-05-09**: `make typecheck` → ruff, mypy, and bandit passed.
- **2026-05-09**:
  Live pilot generation with `--limit 5` wrote
  `.codex/benchmarks/hipporag/dataset/candidate_questions_pilot.json` with 5/5 valid
  candidates and estimated cost `$0.006108`.
- **2026-05-09**:
  Full generation wrote `.codex/benchmarks/hipporag/dataset/candidate_questions.json`;
  initial run produced 222/230 valid candidates and 8 diagnosis-type fixed-field failures.
- **2026-05-09**:
  Prompt was corrected to explicitly list `diagnosis`; the 8 failed packets were rerun and
  merged. Final artifact contains 230/230 valid candidates, 0 failures, 249,038 prompt tokens,
  183,861 completion tokens, 61,776 reasoning tokens, and estimated cost `$0.338051`.
- **2026-05-09**:
  Quality audit found the first candidate pool still contained low-value `Index`, `Front Matter`,
  and citation-list source chunks. `build_evidence_packets.py` was updated to filter those source
  types and diversify selected evidence across sections.
- **2026-05-09**:
  Evidence packets were regenerated with 230 packets and no index/front-matter/reference-list
  sources in the selected pool.
- **2026-05-09**:
  Candidate generation was rerun from the cleaner evidence packets. Initial run produced 228/230
  valid candidates; two truncated JSON outputs were rerun and merged. Final clean candidate pool
  contains 230/230 valid candidates, 0 failures, 245,886 prompt tokens, 200,701 completion tokens,
  79,167 reasoning tokens, and estimated cost `$0.362523`.
- **2026-05-09**:
  Added final curation script and generated tracked dataset
  `evaluation/hipporag_comparison/datasets/marketing_5books_benchmark_v1.json` with 150 valid
  final items: 25 per canonical book plus 25 cross-book.
- **2026-05-09**:
  Final validation with `validate_benchmark_dataset.py` passed against the Task 57 metadata
  sidecar. Final selected set has 0 low-value/short-answer/few-facts audit flags.
- **2026-05-09**:
  Final verification after curation:
  `uv run pytest tests/unit/test_hipporag_candidate_generation.py tests/unit/test_hipporag_benchmark_dataset.py tests/unit/test_hipporag_comparison.py tests/unit/test_hipporag_curation.py -q`
  → 26 passed; targeted ruff format/check passed; manual line-length audit passed; `make typecheck`
  passed.

------------------------------------------------------------------------

## Decision Log

- **2026-05-09**: Generate candidates under ignored `.codex` first; do not track final dataset
  until human review/trim is complete.
- **2026-05-09**: Treat model output as untrusted and validate source subset plus Pydantic schema
  before writing candidate items.
- **2026-05-09**: Use a standard-library LiteLLM client to avoid introducing dependency changes.
- **2026-05-09**: Use `gemini-3.1-flash-lite-preview` by default for quality-first candidate
  generation, with adaptive reasoning (`low` normal, `medium` hard/cross-book) and a
  `max_tokens` default of 2200.
- **2026-05-09**: Use `LITELLM_API_KEY` as the default proxy key env name because the local
  environment exposes that variable; do not print or store the value.
- **2026-05-09**: Keep this as an internal generation script, not a public BrandMind CLI command.
- **2026-05-09**: Add token usage and estimated cost to the generated artifact so later curation
  can report real spend, not only pre-run estimates.
- **2026-05-09**: Do not accept candidate generation as the golden set. Filter low-value source
  packets, regenerate candidates from cleaner evidence, and then curate a tracked 150-item dataset
  with deterministic quality gates and stratified scope/type coverage.

------------------------------------------------------------------------

## Task Summary

Task 59 is implemented and verified end to end. Added
`evaluation/hipporag_comparison/generate_benchmark_candidates.py`,
`evaluation/hipporag_comparison/curate_benchmark_dataset.py`,
`tests/unit/test_hipporag_candidate_generation.py`, and
`tests/unit/test_hipporag_curation.py`. The generator reads Task 58 evidence packets, calls local
LiteLLM through `gemini-3.1-flash-lite-preview`, applies adaptive reasoning, validates fixed
fields and source subsets, validates every item with `BenchmarkItem`, records token usage, and
writes reviewable candidate artifacts under ignored `.codex`. The curation script filters weak
candidate cases and writes the tracked final benchmark dataset.

Final tracked benchmark dataset:
`evaluation/hipporag_comparison/datasets/marketing_5books_benchmark_v1.json`.

Final artifact status:

- 150 final benchmark questions
- 25 items per canonical book plus 25 cross-book
- 0 selected low-value/short-answer/few-facts audit flags
- Source metadata validation passed for all required sources
- Final distribution: 30 mechanism, 25 compare/contrast, 24 application, 24 synthesis,
  23 diagnosis, 24 definition
- Difficulty distribution: 85 medium, 40 easy, 25 hard

Next task: implement runners for BrandMind native dual-retrieval, HippoRAG native retrieval, and
the controlled shared-reader comparison against the final 150-item dataset.
