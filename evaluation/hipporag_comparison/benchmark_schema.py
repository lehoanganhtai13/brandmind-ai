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


class ReasoningType(str, Enum):
    """Hard benchmark reasoning patterns used for v2 diagnostics."""

    MECHANISM_BRIDGE = "mechanism_bridge"
    TENSION_RESOLUTION = "tension_resolution"
    DISTRIBUTED_DIAGNOSIS = "distributed_diagnosis"
    STRATEGY_SYNTHESIS = "strategy_synthesis"
    FAILURE_MODE_ANALYSIS = "failure_mode_analysis"


class AnswerKeyFactSource(BaseModel):
    """Source dependency metadata for one answer-key fact.

    Args:
        fact_index: One-based index into ``answer_key_facts``.
        source_ids: Required sources that support this fact.
        role: Dependency role. Use ``synthesis`` when the fact requires
            combining multiple sources.
    """

    fact_index: int = Field(ge=1)
    source_ids: list[str] = Field(min_length=1)
    role: str = Field(default="support", min_length=1)

    @field_validator("source_ids")
    @classmethod
    def reject_empty_or_duplicate_source_ids(cls, values: list[str]) -> list[str]:
        """Reject empty and duplicate source IDs while preserving order."""

        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Fact source IDs must not be empty.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Fact source IDs must be unique.")
        return normalized

    @field_validator("role")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        """Normalize dependency role labels for deterministic validation."""

        return value.strip().lower()


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
        reasoning_type: Optional hard-benchmark reasoning pattern.
        single_source_sufficient: Optional v2-hard insufficiency flag. V2-hard
            items require this to be ``False``.
        answer_key_fact_sources: Optional answer-key fact source dependencies.
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
    reasoning_type: ReasoningType | None = None
    single_source_sufficient: bool | None = None
    answer_key_fact_sources: list[AnswerKeyFactSource] = Field(default_factory=list)

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
            raise ValueError(
                "Each required source must use book_slug::chunk_id format."
            )
        source_book_slugs = {
            source_id.split("::", maxsplit=1)[0] for source_id in self.required_sources
        }
        if self.book_scope is BookScope.CROSS_BOOK:
            if len(source_book_slugs) < 2:
                raise ValueError(
                    "Cross-book items require sources from at least two books."
                )
            return self
        if source_book_slugs != {self.book_scope.value}:
            raise ValueError(
                "Single-book items must use sources from exactly the book scope."
            )
        return self

    @model_validator(mode="after")
    def validate_v2_hard_metadata(self) -> "BenchmarkItem":
        """Validate optional v2-hard metadata without constraining v1 items."""

        if self.answer_key_fact_sources:
            self._validate_fact_source_dependencies()

        if not self.uses_v2_hard_metadata:
            return self

        if self.reasoning_type is None:
            raise ValueError("V2-hard items require reasoning_type.")
        if self.single_source_sufficient is not False:
            raise ValueError("V2-hard items require single_source_sufficient=false.")
        if self.difficulty is not Difficulty.HARD:
            raise ValueError("V2-hard items must use difficulty=hard.")
        if self.question_type is QuestionType.DEFINITION:
            raise ValueError("V2-hard items must not use definition-only questions.")
        if not 2 <= len(self.required_sources) <= 5:
            raise ValueError("V2-hard items require 2 to 5 required sources.")
        if not self.answer_key_fact_sources:
            raise ValueError("V2-hard items require answer_key_fact_sources.")

        synthesis_fact_count = sum(
            1
            for fact_source in self.answer_key_fact_sources
            if fact_source.role == "synthesis" and len(fact_source.source_ids) > 1
        )
        if synthesis_fact_count < 2:
            raise ValueError(
                "V2-hard items require at least two multi-source synthesis facts."
            )
        return self

    @property
    def uses_v2_hard_metadata(self) -> bool:
        """Return whether this item opts into the v2-hard validation contract."""

        return (
            self.reasoning_type is not None
            or self.single_source_sufficient is not None
            or bool(self.answer_key_fact_sources)
        )

    def _validate_fact_source_dependencies(self) -> None:
        """Validate fact-source metadata against answer facts and sources."""

        required_sources = set(self.required_sources)
        used_sources: set[str] = set()
        seen_fact_indexes: set[int] = set()
        for fact_source in self.answer_key_fact_sources:
            if fact_source.fact_index > len(self.answer_key_facts):
                raise ValueError("Fact source index exceeds answer_key_facts length.")
            unknown_sources = sorted(set(fact_source.source_ids) - required_sources)
            if unknown_sources:
                raise ValueError(
                    f"Fact source mapping uses unknown sources: {unknown_sources}"
                )
            seen_fact_indexes.add(fact_source.fact_index)
            used_sources.update(fact_source.source_ids)

        if len(seen_fact_indexes) != len(self.answer_key_fact_sources):
            raise ValueError("Each answer_key_fact_sources entry needs a unique index.")
        missing_sources = sorted(required_sources - used_sources)
        if missing_sources:
            raise ValueError(
                "Every required source must support at least one fact: "
                f"{missing_sources}"
            )


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
        duplicates = sorted(
            item_id for item_id, count in Counter(ids).items() if count > 1
        )
        if duplicates:
            raise ValueError(f"Duplicate benchmark item IDs: {duplicates}")
        return self

    def distribution_summary(self) -> dict[str, dict[str, int]]:
        """Return review-friendly counts across core stratification dimensions."""

        return {
            "book_scope": dict(Counter(item.book_scope.value for item in self.items)),
            "question_type": dict(
                Counter(item.question_type.value for item in self.items)
            ),
            "difficulty": dict(Counter(item.difficulty.value for item in self.items)),
            "required_source_count": dict(
                Counter(str(len(item.required_sources)) for item in self.items)
            ),
            "reasoning_type": dict(
                Counter(
                    item.reasoning_type.value
                    for item in self.items
                    if item.reasoning_type is not None
                )
            ),
        }
