"""Shared result schemas for the knowledge-search answer-flow benchmark."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ComparisonSystem(str, Enum):
    """Systems compared by the answer-flow benchmark."""

    BRANDMIND_AGENT = "brandmind_agent"
    HYBRID_SEARCH_AGENT = "hybrid_search_agent"
    HIPPORAG_AGENT = "hipporag_agent"


ModelProvider = Literal["auto", "gemini", "litellm"]
AnswerProvider = ModelProvider
JudgeProvider = ModelProvider
ReasoningLevel = Literal["minimal", "low", "medium", "high"]


class TokenUsage(BaseModel):
    """Token usage diagnostics for one model call or full answer flow."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class ToolTrace(BaseModel):
    """Trace for one search tool call made during an answer flow."""

    tool_name: str = Field(min_length=1)
    query: str = Field(min_length=1)
    output_preview: str = ""
    source_ids: list[str] = Field(default_factory=list)
    latency_ms: int = Field(default=0, ge=0)
    error: str | None = None

    @model_validator(mode="after")
    def normalize_source_ids(self) -> "ToolTrace":
        """Remove empty or duplicate source IDs while preserving order."""

        self.source_ids = _unique_non_empty(self.source_ids)
        return self


class AnswerJudgeResult(BaseModel):
    """Reference-based judgment for one final answer.

    Args:
        is_correct: Overall correctness judgment.
        reasoning: Short explanation grounded in gold labels.
        covered_facts: Answer-key facts present in the final answer.
        missing_facts: Answer-key facts absent from the final answer.
        unsupported_claims: Optional major claims not supported by the dataset.
        fact_coverage: Fraction of answer-key facts covered by the answer.
    """

    is_correct: bool
    reasoning: str = Field(min_length=1)
    covered_facts: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    fact_coverage: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def compute_fact_coverage(self) -> "AnswerJudgeResult":
        """Compute fact coverage from covered and missing fact lists."""

        self.covered_facts = _unique_non_empty(self.covered_facts)
        self.missing_facts = _unique_non_empty(self.missing_facts)
        self.unsupported_claims = _unique_non_empty(self.unsupported_claims)
        total_facts = len(self.covered_facts) + len(self.missing_facts)
        self.fact_coverage = (
            len(self.covered_facts) / total_facts if total_facts else 0.0
        )
        return self


class AnswerFlowRecord(BaseModel):
    """One system's answer, tool trace, and judge result for one benchmark item."""

    item_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    book_scope: str | None = None
    question_type: str | None = None
    difficulty: str | None = None
    reasoning_type: str | None = None
    required_source_count: int | None = Field(default=None, ge=0)
    system: ComparisonSystem
    final_answer: str = ""
    judge: AnswerJudgeResult | None = None
    tool_traces: list[ToolTrace] = Field(default_factory=list)
    latency_ms: int = Field(default=0, ge=0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    error: str | None = None
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def retrieved_source_ids(self) -> list[str]:
        """Return all unique source IDs surfaced by search tools."""

        return _unique_non_empty(
            source_id for trace in self.tool_traces for source_id in trace.source_ids
        )


class ComparisonRunConfig(BaseModel):
    """Configuration recorded with every comparison run artifact."""

    dataset_path: Path
    output_path: Path
    systems: list[ComparisonSystem] = Field(default_factory=list)
    answer_provider: AnswerProvider = "auto"
    answer_model: str = "gemini-2.5-flash-lite"
    judge_provider: JudgeProvider = "auto"
    judge_model: str = "gemini-2.5-flash"
    judge_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    judge_thinking_budget: int | None = Field(default=2000, ge=0)
    judge_thinking_level: ReasoningLevel | None = None
    answer_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    answer_thinking_budget: int | None = Field(default=2000, ge=0)
    answer_thinking_level: ReasoningLevel | None = None
    top_k: int = Field(default=5, gt=0)
    candidate_top_k: int = Field(default=10, gt=0)
    max_tool_calls: int = Field(default=4, gt=0)
    recursion_limit: int = Field(default=60, gt=0)
    brandmind_evidence_recovery: bool = False
    checkpoint_path: Path | None = None
    resume: bool = False
    concurrency: int = Field(default=1, gt=0)
    progress_interval: int = Field(default=10, ge=0)
    limit: int | None = Field(default=None, ge=0)
    offset: int = Field(default=0, ge=0)
    dry_run_fixture: bool = False

    @model_validator(mode="after")
    def validate_systems(self) -> "ComparisonRunConfig":
        """Default systems and normalize provider-specific reasoning controls."""

        if not self.systems:
            self.systems = list(ComparisonSystem)
        if self.answer_provider == "auto":
            self.answer_provider = _infer_model_provider(self.answer_model)
        if self.judge_provider == "auto":
            self.judge_provider = _infer_model_provider(self.judge_model)
        if self.answer_provider == "litellm":
            self.answer_thinking_budget = None
        elif _is_gemini_3_model(self.answer_model):
            self.answer_thinking_budget = None
        else:
            self.answer_thinking_level = None
        if self.judge_provider == "litellm":
            self.judge_thinking_budget = None
        else:
            self.judge_thinking_level = None
        return self


class SystemSummary(BaseModel):
    """Aggregate metrics for one system in a benchmark run."""

    system: ComparisonSystem
    total_items: int = Field(ge=0)
    answered_items: int = Field(ge=0)
    correct_items: int = Field(ge=0)
    error_items: int = Field(ge=0)
    mean_fact_coverage: float = Field(ge=0.0, le=1.0)
    mean_tool_calls: float = Field(ge=0.0)
    mean_latency_ms: float = Field(ge=0.0)


class ComparisonRunResult(BaseModel):
    """Structured output artifact for a full or pilot comparison run."""

    run_id: str = Field(default_factory=lambda: uuid4().hex)
    dataset_id: str
    dataset_version: str
    config: ComparisonRunConfig
    records: list[AnswerFlowRecord]
    summaries: list[SystemSummary] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @model_validator(mode="after")
    def populate_summaries(self) -> "ComparisonRunResult":
        """Compute summaries when callers provide only per-item records."""

        if not self.summaries:
            self.summaries = summarize_records(self.records)
        return self


def summarize_records(records: list[AnswerFlowRecord]) -> list[SystemSummary]:
    """Aggregate answer-flow records by system.

    Args:
        records: Per-system benchmark records.

    Returns:
        One summary per system present in the records.
    """

    summaries: list[SystemSummary] = []
    records_by_system: dict[ComparisonSystem, list[AnswerFlowRecord]] = {}
    for record in records:
        records_by_system.setdefault(record.system, []).append(record)

    for system, system_records in records_by_system.items():
        total = len(system_records)
        correctness = Counter(
            record.judge.is_correct
            for record in system_records
            if record.judge is not None
        )
        fact_coverages = [
            record.judge.fact_coverage
            for record in system_records
            if record.judge is not None
        ]
        summaries.append(
            SystemSummary(
                system=system,
                total_items=total,
                answered_items=sum(
                    1 for record in system_records if bool(record.final_answer)
                ),
                correct_items=correctness[True],
                error_items=sum(1 for record in system_records if record.error),
                mean_fact_coverage=_mean(fact_coverages),
                mean_tool_calls=_mean(
                    [len(record.tool_traces) for record in system_records]
                ),
                mean_latency_ms=_mean([record.latency_ms for record in system_records]),
            )
        )
    return summaries


def _mean(values: list[int] | list[float]) -> float:
    """Return the arithmetic mean for a possibly empty list."""

    return sum(values) / len(values) if values else 0.0


def _is_gemini_3_model(model: str) -> bool:
    """Return whether a model name should use Gemini 3 thinking controls."""

    return "gemini-3" in model.casefold()


def _infer_model_provider(model: str) -> Literal["gemini", "litellm"]:
    """Infer the model provider from a model ID when CLI config uses auto."""

    return "gemini" if model.casefold().startswith("gemini-") else "litellm"


def _unique_non_empty(values: object) -> list[str]:
    """Return unique non-empty strings from an iterable-like object."""

    if not isinstance(values, list | tuple | set):
        values = list(values) if hasattr(values, "__iter__") else []

    seen: set[str] = set()
    unique_values: list[str] = []
    for raw_value in values:
        value = str(raw_value).strip()
        if value and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values
