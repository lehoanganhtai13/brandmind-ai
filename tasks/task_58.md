# Task 58: Source-Grounded Benchmark Dataset Schema And Validator

## Metadata

- **Epic**: Marketing KG Evaluation — HippoRAG comparison
- **Priority**: High
- **Status**: Implemented
- **Estimated Effort**: 1-2 days for schema, evidence packets, and validator
- **Team**: Backend / Evaluation
- **Related Tasks**: `tasks/task_57.md`, `evaluation/hipporag_comparison/export_corpus.py`
- **Blocking**: Trusted 5-book benchmark dataset generation and review
- **Blocked by**: None for the schema/validator slice

### Progress Checklist

> Agent: Update checkboxes as each section is completed. Do not mark a section done until it is
> fully verified.

- [x] Agent Protocol — Read and confirmed from `tasks/task_template.md`
- [x] Context & Goals — Problem definition and success metrics
- [x] Solution Design — Architecture and technical approach
- [x] Pre-Implementation Research — Findings logged before coding
- [x] Implementation Plan — Phased execution plan drafted
- [x] Implementation Detail — Full ready-to-apply code reviewed by user before file writes
    - [x] Component 1 — Benchmark dataset schema
    - [x] Component 2 — Evidence packet builder for source-first curation
    - [x] Component 3 — Dataset validator CLI
    - [x] Component 4 — Unit tests
- [x] Test Execution Log — All tests run and results recorded
- [x] Decision Log — Key decisions documented
- [x] Task Summary — Final implementation summary completed

## Reference Documentation

- **Coding Standards**: `tasks/task_template.md`, Rule 4 and Rule 2.5.
- **Eval design guidance**: `/Users/lehoanganhtai/.codex/skills/llm-eval-design/SKILL.md` and
  `/Users/lehoanganhtai/.codex/skills/llm-eval-design/references/dataset-construction.md`.
- **Foundation task**: `tasks/task_57.md`.
- **Existing exporter**: `evaluation/hipporag_comparison/export_corpus.py`.
- **Existing benchmark pattern**: `evaluation/kg_tools_search_baseline_comparison.py`.
- **Existing old question sets**: `evaluation/test_questions.py` and
  `evaluation/test_questions_extended.py`.
- **Source corpus**: `data/parsed_documents/*/chunks.json`.

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

Task 57 created the HippoRAG runtime foundation and exported the five-book corpus. The next
benchmark risk is dataset quality: if questions are not source-grounded, diverse, and auditable,
the HippoRAG vs BrandMind comparison can look runnable but remain weak as thesis evidence.

### Goal

Create the project-owned schema, source-first evidence packet builder, and validator needed to
curate a trusted 150-item benchmark dataset. This task does not generate the final answers with an
LLM yet; it creates the audited data contract and the source packet workflow that makes later
generation defensible.

### Success Metrics / Acceptance Criteria

- **Schema**: Benchmark items validate the minimal approved fields:
  `id`, `question`, `gold_answer`, `answer_key_facts`, `required_sources`, `book_scope`,
  `question_type`, `difficulty`, and `evidence_digest`.
- **Source grounding**: Validator rejects any `required_sources` not present in the Task 57
  metadata sidecar.
- **Fairness**: Schema remains system-neutral; it does not include runtime outputs like
  `retrieved_sources`, `latency_ms`, or judge scores.
- **Diversity**: Dataset-level summary reports counts by `book_scope`, `question_type`, and
  `difficulty`.
- **Curation workflow**: Evidence packet builder creates source-first packets from the five
  canonical books and excludes `test_sample_stage4`.
- **Tests**: Unit tests cover schema validation, missing-source detection, duplicate IDs, cross-book
  constraints, and evidence packet generation without live API calls.

------------------------------------------------------------------------

## Solution Design

### Proposed Approach

**Source-first curation pipeline**: Build evidence packets from parsed chunks first, then validate
any curated or generated questions against those packet source IDs. This avoids creating questions
from general marketing knowledge and then trying to retrofit citations afterward.

### Technology Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| Pydantic `BaseModel` | Benchmark schema validation | Fits structured data with runtime validation |
| Dataclasses | Internal evidence packet records | Lightweight for derived non-boundary records |
| JSON | Dataset and packet storage | Easy to review, diff, and version-control |
| Pytest | Unit tests | Existing project test convention |

### Architecture Overview

```text
data/parsed_documents/*/chunks.json
    |
    | build_evidence_packets.py
    v
.codex/benchmarks/hipporag/dataset/evidence_packets.json
    |
    | human/LLM curation in a later task
    v
evaluation/hipporag_comparison/datasets/marketing_5books_benchmark.json
    |
    | validate_benchmark_dataset.py
    v
validated source-grounded benchmark dataset
```

### Issues & Solutions

1. **Generated questions can drift into generic marketing knowledge** -> evidence packets are built
   before questions and include required source IDs.
2. **Runtime and curation schemas can get mixed** -> benchmark schema contains only curated item
   fields; runner outputs will be separate files in later tasks.
3. **Cross-book questions need stricter checks** -> schema requires at least two distinct book
   slugs for `book_scope="cross_book"`.
4. **Over-engineering risk** -> keep schema small and auditable; use summaries for diversity
   diagnostics instead of adding many optional metadata fields.

------------------------------------------------------------------------

## Pre-Implementation Research

### Codebase Audit

- **Files read**:
  - `tasks/task_template.md`
  - `tasks/task_57.md`
  - `evaluation/hipporag_comparison/export_corpus.py`
  - `evaluation/kg_tools_search_baseline_comparison.py`
  - `evaluation/test_questions.py`
  - `evaluation/test_questions_extended.py`
  - `pyproject.toml`
  - `data/parsed_documents/*/chunks.json`
- **Relevant patterns found**:
  - Task 57 already exposes canonical book order and stable source IDs via
    `book_slug::chunk_id`.
  - Parsed chunks include enough source metadata for curation: `source`, `original_document`,
    `author`, `pages`, `section_summary`, `word_count`, and `content`.
  - Existing old question files mix question, ground truth, and a loose string source. New schema
    should keep source IDs explicit and machine-validatable.
  - Existing baseline runner stores runtime results separately from question definitions; Task 58
    should preserve that separation.
- **Potential conflicts**:
  - The current broader `make test-unit` is blocked by unrelated missing modules
    `langchain_text_splitters` and `textual`. This task will verify with targeted tests plus
    `make typecheck`, same as Task 57.

### External Library / API Research

- **Library/API**: Pydantic and local eval-design guidance.
- **Documentation source**:
  - `/Users/lehoanganhtai/.codex/skills/llm-eval-design/SKILL.md`
  - `/Users/lehoanganhtai/.codex/skills/llm-eval-design/references/dataset-construction.md`
- **Key findings**:
  - Golden datasets should be small enough to audit, stratified by task category, difficulty, and
    source scope.
  - Source-first construction is safer than synthetic-first construction for trusted QA evals.
  - Curated dataset definitions should be versioned and separated from runtime outputs.
- **Interface confirmed**:
  - Pydantic `BaseModel`, `Field`, `model_validator`, and `field_validator`.
  - Existing Task 57 `build_records(parsed_root)` returns corpus records plus metadata keyed by
    stable `source_id`.

### Unknown / Risks Identified

- [x] Whether every field can be filled from the books: yes for schema validation, because the
  evidence packets include source IDs, section summaries, excerpts, and pages.
- [x] Whether final question text should be generated in this task: no. This task prepares the
  source-first curation and validation layer; final LLM/human curation is a later task.
- [x] Whether to store the final curated benchmark JSON under `evaluation/hipporag_comparison/datasets/`
  or keep it in ignored `.codex` until reviewed: proposed path is tracked only after human review.

### Research Status

- [x] All referenced documentation read
- [x] Existing codebase patterns understood
- [x] External dependencies verified
- [x] No unresolved ambiguities remain for this schema/validator slice

------------------------------------------------------------------------

## Implementation Plan

### Phase 1: Dataset schema

1. Add `evaluation/hipporag_comparison/benchmark_schema.py`.
   - Define compact enums for `BookScope`, `QuestionType`, and `Difficulty`.
   - Define `BenchmarkItem` and `BenchmarkDataset` as Pydantic models.
   - Add dataset summary helpers for review diagnostics.

### Phase 2: Evidence packets

1. Add `evaluation/hipporag_comparison/build_evidence_packets.py`.
   - Reuse Task 57 corpus export helpers.
   - Generate source-first packets from five canonical books.
   - Write JSON under ignored `.codex/benchmarks/hipporag/dataset/evidence_packets.json`.

### Phase 3: Validation CLI

1. Add `evaluation/hipporag_comparison/validate_benchmark_dataset.py`.
   - Load a curated dataset JSON file.
   - Load Task 57 metadata sidecar.
   - Validate schema, unique IDs, source existence, cross-book source coverage, and distribution.

### Phase 4: Tests

1. Add focused tests to `tests/unit/test_hipporag_benchmark_dataset.py`.
   - No live LiteLLM, Gemini, HippoRAG, Milvus, or FalkorDB calls.
2. Run:
   - `uv run pytest tests/unit/test_hipporag_benchmark_dataset.py -q`
   - `uv run ruff format --check evaluation/hipporag_comparison tests/unit/test_hipporag_benchmark_dataset.py`
   - `uv run ruff check evaluation/hipporag_comparison tests/unit/test_hipporag_benchmark_dataset.py`
   - `make typecheck`

### Rollback Plan

Remove the new files:

- `evaluation/hipporag_comparison/benchmark_schema.py`
- `evaluation/hipporag_comparison/build_evidence_packets.py`
- `evaluation/hipporag_comparison/validate_benchmark_dataset.py`
- `tests/unit/test_hipporag_benchmark_dataset.py`

No existing BrandMind runtime, Milvus collection, FalkorDB graph, or Task 57 corpus output is
modified by this task.

------------------------------------------------------------------------

## Implementation Detail

> This section was the pre-apply review surface. The user approved it, and the implementation has
> now been applied. The final tracked code is the source of truth where it differs from the
> originally reviewed snippets.

### Component 1: Benchmark dataset schema

> Status: Implemented in `evaluation/hipporag_comparison/benchmark_schema.py`.

#### Requirement 1 — Define minimal source-grounded benchmark schema

- **Requirement**: Provide a Pydantic schema for curated benchmark items that is strict enough for
  source-grounded evaluation and small enough to audit.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/benchmark_schema.py` `[NEW]`

```python
"""Schema for the source-grounded HippoRAG comparison benchmark.

The curated benchmark dataset is intentionally separate from runtime result
files. It stores only stable question definitions and gold labels. Retrieval
outputs, latency, reader answers, and judge scores belong in runner result
files created by later benchmark tasks.
"""

from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class BookScope(str, Enum):
    """Allowed source scopes for benchmark items."""

    HOW_BRANDS_GROW = "how_brands_grow_what_marketers_dont_know"
    INFLUENCE = "influence_new_and_expanded_the_psychology_of_persuasion"
    KOTLER = "kotler_and_armstrong_principles_of_marketing"
    POSITIONING = "positioning_the_battle_for_your_mind"
    STRATEGIC_BRAND_MANAGEMENT = "strategic_brand_management"
    CROSS_BOOK = "cross_book"


class QuestionType(str, Enum):
    """Question categories used for dataset diversity diagnostics."""

    DEFINITION = "definition"
    MECHANISM = "mechanism"
    COMPARE_CONTRAST = "compare_contrast"
    APPLICATION = "application"
    SYNTHESIS = "synthesis"
    DIAGNOSIS = "diagnosis"


class Difficulty(str, Enum):
    """Difficulty bands for benchmark stratification."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BenchmarkItem(BaseModel):
    """One source-grounded benchmark question.

    Args:
        id: Stable benchmark item ID.
        question: User-facing question text.
        gold_answer: Reference answer grounded in the required source chunks.
        answer_key_facts: Atomic facts expected in a correct answer.
        required_sources: Stable source IDs in ``book_slug::chunk_id`` format.
        book_scope: Single-book or cross-book scope.
        question_type: Evaluation category used for diversity tracking.
        difficulty: Difficulty band.
        evidence_digest: Short human-readable summary of why the sources support
            the gold answer.
    """

    id: str = Field(min_length=3, pattern=r"^BM5B-[A-Z0-9-]+$")
    question: str = Field(min_length=20)
    gold_answer: str = Field(min_length=80)
    answer_key_facts: list[str] = Field(min_length=2)
    required_sources: list[str] = Field(min_length=1)
    book_scope: BookScope
    question_type: QuestionType
    difficulty: Difficulty
    evidence_digest: str = Field(min_length=40)

    @field_validator("question", "gold_answer", "evidence_digest")
    @classmethod
    def strip_text(cls, value: str) -> str:
        """Normalize boundary strings without changing their meaning."""

        return value.strip()

    @field_validator("answer_key_facts", "required_sources")
    @classmethod
    def reject_empty_or_duplicate_values(cls, values: list[str]) -> list[str]:
        """Reject empty and duplicate list values while preserving order."""

        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("List values must not be empty.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("List values must be unique.")
        return normalized

    @model_validator(mode="after")
    def validate_source_scope(self) -> "BenchmarkItem":
        """Validate that source IDs match the declared book scope."""

        if any("::" not in source_id for source_id in self.required_sources):
            raise ValueError("Each required source must use book_slug::chunk_id format.")
        source_book_slugs = {
            source_id.split("::", maxsplit=1)[0] for source_id in self.required_sources
        }
        if self.book_scope is BookScope.CROSS_BOOK:
            if len(source_book_slugs) < 2:
                raise ValueError("Cross-book items require sources from at least two books.")
            return self
        if source_book_slugs != {self.book_scope.value}:
            raise ValueError("Single-book items must use sources from exactly the book scope.")
        return self


class BenchmarkDataset(BaseModel):
    """Versioned collection of source-grounded benchmark questions."""

    dataset_id: str = Field(default="brandmind_marketing_5books_v1", min_length=3)
    dataset_version: str = Field(default="0.1.0", min_length=1)
    description: str = Field(min_length=20)
    items: list[BenchmarkItem] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_item_ids(self) -> "BenchmarkDataset":
        """Ensure each benchmark item ID appears once."""

        ids = [item.id for item in self.items]
        duplicates = sorted(item_id for item_id, count in Counter(ids).items() if count > 1)
        if duplicates:
            raise ValueError(f"Duplicate benchmark item IDs: {duplicates}")
        return self

    def distribution_summary(self) -> dict[str, dict[str, int]]:
        """Return review-friendly counts across core stratification dimensions."""

        return {
            "book_scope": dict(Counter(item.book_scope.value for item in self.items)),
            "question_type": dict(Counter(item.question_type.value for item in self.items)),
            "difficulty": dict(Counter(item.difficulty.value for item in self.items)),
        }
```

### Component 2: Evidence packet builder

> Status: Implemented in `evaluation/hipporag_comparison/build_evidence_packets.py`.

#### Requirement 2 — Build source-first evidence packets

- **Requirement**: Build reviewable evidence packets from five canonical books so later question
  generation starts from book evidence, not generic marketing knowledge.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/build_evidence_packets.py` `[NEW]`

```python
"""Build source-first evidence packets for benchmark curation.

Evidence packets are not final benchmark questions. They are compact groups of
source chunks that a human or later LLM generation task can use to produce
source-grounded questions, gold answers, answer key facts, and required source
IDs.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from evaluation.hipporag_comparison.export_corpus import (
    SourceMetadata,
    build_records,
    write_json,
)

DEFAULT_PACKET_OUTPUT = Path(
    ".codex/benchmarks/hipporag/dataset/evidence_packets.json"
)


@dataclass(frozen=True)
class EvidenceSource:
    """One source chunk included in an evidence packet."""

    source_id: str
    book_slug: str
    source: str
    pages: list[int]
    section_summary: str
    excerpt: str
    word_count: int | None


@dataclass(frozen=True)
class EvidencePacket:
    """A compact evidence group used to curate benchmark questions."""

    packet_id: str
    candidate_scope: str
    difficulty_hint: str
    question_type_hint: str
    evidence_digest: str
    sources: list[EvidenceSource]


def compact_excerpt(text: str, max_chars: int = 900) -> str:
    """Create a stable one-line excerpt for review.

    Args:
        text: Source chunk text.
        max_chars: Maximum excerpt length.

    Returns:
        A compact excerpt that preserves the start of the source chunk.
    """

    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "…"


def metadata_score(metadata: SourceMetadata) -> tuple[int, int, str]:
    """Rank sources by usefulness for question curation.

    Args:
        metadata: Source metadata from the Task 57 exporter.

    Returns:
        A deterministic descending-sort score tuple.
    """

    has_summary = 1 if metadata.section_summary else 0
    word_count = metadata.word_count or 0
    return (has_summary, word_count, metadata.source_id)


def build_source_lookup(parsed_root: Path) -> dict[str, EvidenceSource]:
    """Build a source lookup from canonical parsed documents.

    Args:
        parsed_root: Root directory containing parsed document folders.

    Returns:
        Evidence sources keyed by stable source ID.
    """

    records, metadata_by_source_id = build_records(parsed_root)
    record_text_by_source_id = {record.title: record.text for record in records}
    return {
        source_id: EvidenceSource(
            source_id=source_id,
            book_slug=metadata.book_slug,
            source=metadata.source,
            pages=metadata.pages,
            section_summary=metadata.section_summary,
            excerpt=compact_excerpt(record_text_by_source_id[source_id]),
            word_count=metadata.word_count,
        )
        for source_id, metadata in metadata_by_source_id.items()
    }


def select_book_sources(
    source_lookup: dict[str, EvidenceSource],
    per_book_limit: int,
) -> dict[str, list[EvidenceSource]]:
    """Select high-signal sources for each canonical book.

    Args:
        source_lookup: Evidence sources keyed by source ID.
        per_book_limit: Maximum selected sources per book.

    Returns:
        Selected sources grouped by book slug.
    """

    grouped: dict[str, list[EvidenceSource]] = defaultdict(list)
    for source in source_lookup.values():
        grouped[source.book_slug].append(source)

    selected: dict[str, list[EvidenceSource]] = {}
    for book_slug, sources in grouped.items():
        selected[book_slug] = sorted(
            sources,
            key=lambda source: (
                1 if source.section_summary else 0,
                source.word_count or 0,
                source.source_id,
            ),
            reverse=True,
        )[:per_book_limit]
    return selected


def infer_question_type_hint(index: int) -> str:
    """Rotate question type hints to encourage curation diversity."""

    hints = [
        "definition",
        "mechanism",
        "compare_contrast",
        "application",
        "synthesis",
        "diagnosis",
    ]
    return hints[index % len(hints)]


def infer_difficulty_hint(index: int, source_count: int) -> str:
    """Infer a simple difficulty hint from packet position and source count."""

    if source_count >= 2:
        return "hard"
    if index % 3 == 0:
        return "easy"
    return "medium"


def build_single_book_packets(
    selected_by_book: dict[str, list[EvidenceSource]],
) -> list[EvidencePacket]:
    """Build one-source packets for single-book benchmark curation."""

    packets: list[EvidencePacket] = []
    for book_slug, sources in sorted(selected_by_book.items()):
        for index, source in enumerate(sources, start=1):
            packets.append(
                EvidencePacket(
                    packet_id=f"{book_slug}-single-{index:03d}",
                    candidate_scope=book_slug,
                    difficulty_hint=infer_difficulty_hint(index, source_count=1),
                    question_type_hint=infer_question_type_hint(index),
                    evidence_digest=source.section_summary or source.source,
                    sources=[source],
                )
            )
    return packets


def build_cross_book_packets(
    selected_by_book: dict[str, list[EvidenceSource]],
    cross_book_limit: int,
) -> list[EvidencePacket]:
    """Build paired-source packets for cross-book benchmark curation."""

    book_slugs = sorted(selected_by_book)
    packets: list[EvidencePacket] = []
    packet_index = 1
    for left_index, left_book in enumerate(book_slugs):
        for right_book in book_slugs[left_index + 1 :]:
            left_sources = selected_by_book[left_book]
            right_sources = selected_by_book[right_book]
            pair_count = min(len(left_sources), len(right_sources), 3)
            for source_index in range(pair_count):
                left_source = left_sources[source_index]
                right_source = right_sources[source_index]
                packets.append(
                    EvidencePacket(
                        packet_id=f"cross-book-{packet_index:03d}",
                        candidate_scope="cross_book",
                        difficulty_hint="hard",
                        question_type_hint=infer_question_type_hint(packet_index),
                        evidence_digest=(
                            f"{left_source.book_slug}: {left_source.section_summary or left_source.source} "
                            f"| {right_source.book_slug}: {right_source.section_summary or right_source.source}"
                        ),
                        sources=[left_source, right_source],
                    )
                )
                packet_index += 1
                if len(packets) >= cross_book_limit:
                    return packets
    return packets


def build_evidence_packets(
    parsed_root: Path,
    per_book_limit: int = 40,
    cross_book_limit: int = 30,
) -> list[EvidencePacket]:
    """Build single-book and cross-book evidence packets.

    Args:
        parsed_root: Root directory containing parsed document folders.
        per_book_limit: Maximum single-book packets per canonical book.
        cross_book_limit: Maximum cross-book packets.

    Returns:
        Evidence packets in deterministic order.

    Raises:
        ValueError: If a limit is not positive.
    """

    if per_book_limit <= 0:
        raise ValueError("per_book_limit must be positive.")
    if cross_book_limit <= 0:
        raise ValueError("cross_book_limit must be positive.")

    source_lookup = build_source_lookup(parsed_root)
    selected_by_book = select_book_sources(source_lookup, per_book_limit=per_book_limit)
    return [
        *build_single_book_packets(selected_by_book),
        *build_cross_book_packets(selected_by_book, cross_book_limit=cross_book_limit),
    ]


def write_evidence_packets(packets: list[EvidencePacket], output_path: Path) -> None:
    """Write evidence packets as pretty JSON."""

    write_json(
        output_path,
        {
            "packet_count": len(packets),
            "packets": [
                {
                    **asdict(packet),
                    "source_ids": [source.source_id for source in packet.sources],
                }
                for packet in packets
            ],
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for evidence packet generation."""

    parser = argparse.ArgumentParser(
        description="Build source-first evidence packets for the 5-book benchmark.",
    )
    parser.add_argument(
        "--parsed-root",
        type=Path,
        default=Path("data/parsed_documents"),
        help="Root directory containing parsed document folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PACKET_OUTPUT,
        help="Output evidence packet JSON path.",
    )
    parser.add_argument(
        "--per-book-limit",
        type=int,
        default=40,
        help="Maximum selected single-book packets per canonical book.",
    )
    parser.add_argument(
        "--cross-book-limit",
        type=int,
        default=30,
        help="Maximum selected cross-book packets.",
    )
    return parser.parse_args()


def main() -> None:
    """Run evidence packet generation from the command line."""

    args = parse_args()
    packets = build_evidence_packets(
        parsed_root=args.parsed_root,
        per_book_limit=args.per_book_limit,
        cross_book_limit=args.cross_book_limit,
    )
    write_evidence_packets(packets, args.output)


if __name__ == "__main__":
    main()
```

### Component 3: Dataset validator CLI

> Status: Implemented in `evaluation/hipporag_comparison/validate_benchmark_dataset.py`.

#### Requirement 3 — Validate curated dataset against source metadata

- **Requirement**: Provide a CLI that validates curated benchmark JSON against the schema and the
  Task 57 source metadata sidecar.

- **Implementation**:

Target file: `evaluation/hipporag_comparison/validate_benchmark_dataset.py` `[NEW]`

```python
"""Validate source-grounded benchmark datasets for the HippoRAG comparison."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import ValidationError

from evaluation.hipporag_comparison.benchmark_schema import BenchmarkDataset

DEFAULT_DATASET_PATH = Path(
    "evaluation/hipporag_comparison/datasets/marketing_5books_benchmark.json"
)
DEFAULT_METADATA_PATH = Path(
    ".codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json"
)


@dataclass(frozen=True)
class DatasetValidationReport:
    """Validation outcome for a curated benchmark dataset."""

    is_valid: bool
    item_count: int
    errors: list[str]
    distribution_summary: dict[str, dict[str, int]]


def load_json(path: Path) -> object:
    """Load a JSON file with UTF-8 encoding."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_available_source_ids(metadata_path: Path) -> set[str]:
    """Load source IDs from the Task 57 metadata sidecar."""

    payload = load_json(metadata_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected metadata object in {metadata_path}.")
    sources = payload.get("sources")
    if not isinstance(sources, dict):
        raise ValueError(f"Expected sources object in {metadata_path}.")
    return set(sources)


def find_missing_sources(
    dataset: BenchmarkDataset,
    available_source_ids: set[str],
) -> list[str]:
    """Find required source IDs absent from the exported metadata sidecar."""

    missing: list[str] = []
    for item in dataset.items:
        for source_id in item.required_sources:
            if source_id not in available_source_ids:
                missing.append(f"{item.id}: missing source {source_id}")
    return missing


def validate_benchmark_dataset(
    dataset_path: Path,
    metadata_path: Path,
) -> DatasetValidationReport:
    """Validate benchmark dataset structure and source grounding.

    Args:
        dataset_path: Path to curated benchmark dataset JSON.
        metadata_path: Path to Task 57 source metadata sidecar.

    Returns:
        Validation report with errors and distribution diagnostics.
    """

    errors: list[str] = []
    dataset: BenchmarkDataset | None = None
    try:
        dataset = BenchmarkDataset.model_validate(load_json(dataset_path))
    except ValidationError as exc:
        errors.extend(str(error) for error in exc.errors())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    if dataset is None:
        return DatasetValidationReport(
            is_valid=False,
            item_count=0,
            errors=errors,
            distribution_summary={},
        )

    try:
        available_source_ids = load_available_source_ids(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        available_source_ids = set()

    errors.extend(find_missing_sources(dataset, available_source_ids))
    return DatasetValidationReport(
        is_valid=not errors,
        item_count=len(dataset.items),
        errors=errors,
        distribution_summary=dataset.distribution_summary(),
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for dataset validation."""

    parser = argparse.ArgumentParser(
        description="Validate the source-grounded 5-book benchmark dataset.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Curated benchmark dataset JSON path.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help="Task 57 source metadata sidecar path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run dataset validation and exit non-zero on failure."""

    args = parse_args()
    report = validate_benchmark_dataset(args.dataset, args.metadata)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    if not report.is_valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

### Component 4: Unit tests

> Status: Implemented in `tests/unit/test_hipporag_benchmark_dataset.py`.

#### Requirement 4 — Test schema, validator, and evidence packet builder

- **Requirement**: Add targeted tests for dataset validation without live services.

- **Implementation**:

Target file: `tests/unit/test_hipporag_benchmark_dataset.py` `[NEW]`

```python
"""Unit tests for HippoRAG benchmark dataset schema and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
    BookScope,
    Difficulty,
    QuestionType,
)
from evaluation.hipporag_comparison.build_evidence_packets import build_evidence_packets
from evaluation.hipporag_comparison.export_corpus import CANONICAL_BOOK_DIRS
from evaluation.hipporag_comparison.validate_benchmark_dataset import (
    validate_benchmark_dataset,
)


def make_item(
    item_id: str = "BM5B-KOTLER-001",
    required_sources: list[str] | None = None,
    book_scope: BookScope = BookScope.KOTLER,
) -> BenchmarkItem:
    """Create a valid benchmark item fixture."""

    return BenchmarkItem(
        id=item_id,
        question="How should a marketer apply this source-grounded principle?",
        gold_answer=(
            "A correct answer should explain the marketing principle, connect it to the cited "
            "source evidence, and state the practical implication for a marketer."
        ),
        answer_key_facts=[
            "The answer must name the relevant marketing principle.",
            "The answer must connect the principle to the cited source evidence.",
        ],
        required_sources=required_sources
        or ["kotler_and_armstrong_principles_of_marketing::chunk_1"],
        book_scope=book_scope,
        question_type=QuestionType.APPLICATION,
        difficulty=Difficulty.MEDIUM,
        evidence_digest=(
            "The selected source explains a marketing principle and provides enough support for "
            "a practical application question."
        ),
    )


def write_fixture_chunks(parsed_root: Path, book_dir: str, chunk_id: str) -> None:
    """Write one parsed chunk fixture for a canonical book."""

    book_path = parsed_root / book_dir
    book_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [
            {
                "chunk_id": chunk_id,
                "content": f"Detailed source text for {book_dir}.",
                "metadata": {
                    "author": "Author",
                    "original_document": f"{book_dir}.pdf",
                    "pages": [1],
                    "section_summary": f"Summary for {book_dir}.",
                    "source": f"Source for {book_dir}.",
                    "word_count": 120,
                },
            }
        ]
    }
    (book_path / "chunks.json").write_text(json.dumps(payload), encoding="utf-8")


def test_benchmark_item_accepts_valid_single_book_source() -> None:
    """Single-book items should validate when source slugs match scope."""

    item = make_item()

    assert item.book_scope is BookScope.KOTLER
    assert item.required_sources == [
        "kotler_and_armstrong_principles_of_marketing::chunk_1"
    ]


def test_benchmark_item_rejects_cross_book_with_one_book() -> None:
    """Cross-book items need at least two source book slugs."""

    with pytest.raises(ValidationError):
        make_item(
            item_id="BM5B-CROSS-001",
            required_sources=["kotler_and_armstrong_principles_of_marketing::chunk_1"],
            book_scope=BookScope.CROSS_BOOK,
        )


def test_benchmark_dataset_rejects_duplicate_ids() -> None:
    """Dataset item IDs should be unique."""

    with pytest.raises(ValidationError):
        BenchmarkDataset(
            description="A source-grounded test dataset for duplicate ID validation.",
            items=[make_item(), make_item()],
        )


def test_validate_benchmark_dataset_reports_missing_sources(tmp_path: Path) -> None:
    """Validator should reject required sources absent from metadata."""

    dataset_path = tmp_path / "dataset.json"
    metadata_path = tmp_path / "metadata.json"
    dataset = BenchmarkDataset(
        description="A source-grounded test dataset for missing source validation.",
        items=[make_item()],
    )
    dataset_path.write_text(dataset.model_dump_json(), encoding="utf-8")
    metadata_path.write_text(json.dumps({"sources": {}}), encoding="utf-8")

    report = validate_benchmark_dataset(dataset_path, metadata_path)

    assert not report.is_valid
    assert report.item_count == 1
    assert "missing source" in report.errors[0]


def test_validate_benchmark_dataset_accepts_existing_sources(tmp_path: Path) -> None:
    """Validator should accept datasets whose required sources exist in metadata."""

    source_id = "kotler_and_armstrong_principles_of_marketing::chunk_1"
    dataset_path = tmp_path / "dataset.json"
    metadata_path = tmp_path / "metadata.json"
    dataset = BenchmarkDataset(
        description="A source-grounded test dataset for valid source validation.",
        items=[make_item(required_sources=[source_id])],
    )
    dataset_path.write_text(dataset.model_dump_json(), encoding="utf-8")
    metadata_path.write_text(
        json.dumps({"sources": {source_id: {"source_id": source_id}}}),
        encoding="utf-8",
    )

    report = validate_benchmark_dataset(dataset_path, metadata_path)

    assert report.is_valid
    assert (
        report.distribution_summary["book_scope"][
            "kotler_and_armstrong_principles_of_marketing"
        ]
        == 1
    )


def test_build_evidence_packets_uses_canonical_books(tmp_path: Path) -> None:
    """Evidence packet builder should use canonical books and create cross-book packets."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    packets = build_evidence_packets(
        parsed_root=tmp_path,
        per_book_limit=1,
        cross_book_limit=2,
    )

    single_book_packets = [packet for packet in packets if packet.candidate_scope != "cross_book"]
    cross_book_packets = [packet for packet in packets if packet.candidate_scope == "cross_book"]
    assert len(single_book_packets) == len(CANONICAL_BOOK_DIRS)
    assert len(cross_book_packets) == 2
    assert all(packet.sources for packet in packets)
```

------------------------------------------------------------------------

## Test Execution Log

- `uv run pytest tests/unit/test_hipporag_benchmark_dataset.py -q`
  - **Result**: Pass, `6 passed`.
  - **Purpose**: Verified schema validation, missing-source detection, duplicate ID rejection,
    cross-book source constraints, and evidence packet generation.
- `uv run pytest tests/unit/test_hipporag_benchmark_dataset.py tests/unit/test_hipporag_comparison.py -q`
  - **Result**: Pass, `15 passed`.
  - **Purpose**: Verified Task 58 changes together with the Task 57 foundation tests.
- `uv run ruff format --check evaluation/hipporag_comparison tests/unit/test_hipporag_benchmark_dataset.py`
  - **Result**: Pass, all seven files already formatted after one formatting pass.
- `uv run ruff check evaluation/hipporag_comparison tests/unit/test_hipporag_benchmark_dataset.py`
  - **Result**: Pass, all checks passed.
- `uv run python -m evaluation.hipporag_comparison.build_evidence_packets`
  - **Result**: Pass.
  - **Output**: `.codex/benchmarks/hipporag/dataset/evidence_packets.json`.
  - **Packet count**: 230 total packets: 40 single-book packets for each of the five canonical
    books and 30 cross-book packets.
- `make typecheck`
  - **Result**: Pass.
  - **Coverage**: `ruff format src/`, `ruff check src/ --fix`, mypy for shared/core/config, and
    bandit for `src/`.

------------------------------------------------------------------------

## Decision Log

- **2026-05-09**: Keep curated dataset schema separate from runtime result schema so fairness
  diagnostics do not pollute gold labels.
- **2026-05-09**: Use Pydantic `BaseModel` for benchmark boundary objects because the dataset file
  is a persisted contract that needs validation, not just a structural interface.
- **2026-05-09**: Build evidence packets before question generation to reduce generic marketing
  knowledge leakage and make every item source-auditable.
- **2026-05-09**: Do not generate final LLM-written questions in this task. The next task should use
  these packets to generate candidate questions and then run validation/human review.

------------------------------------------------------------------------

## Task Summary

Implemented the source-grounded benchmark dataset schema and validator foundation. The project now
has Pydantic boundary models for benchmark items/datasets, an evidence packet builder that starts
question curation from the five-book source corpus, a validator CLI that checks curated datasets
against the Task 57 metadata sidecar, and focused unit tests.

The builder generated 230 evidence packets under ignored `.codex/benchmarks/hipporag/dataset/`.
This prepares the next phase: generate candidate benchmark questions from evidence packets, review
them, and save the approved 150-item dataset under a tracked dataset path.
