"""Validate source-grounded benchmark datasets for the HippoRAG comparison."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import ValidationError

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BookScope,
    Difficulty,
    QuestionType,
    ReasoningType,
)

DEFAULT_DATASET_PATH = Path(
    "evaluation/hipporag_comparison/datasets/marketing_5books_benchmark.json"
)
DEFAULT_METADATA_PATH = Path(
    ".codex/benchmarks/hipporag/corpus/marketing_5books_metadata.json"
)
HARD_DATASET_ID = "brandmind_marketing_5books_multihop_hard_v2"
HARD_SCOPE_QUOTAS = {"cross_book": 90, "intra_book": 60}
HARD_SOURCE_COUNT_QUOTAS = {"2": 20, "3": 60, "4": 50, "5": 20}
HARD_QUESTION_TYPE_QUOTAS = {
    QuestionType.MECHANISM.value: 30,
    QuestionType.COMPARE_CONTRAST.value: 30,
    QuestionType.APPLICATION.value: 30,
    QuestionType.SYNTHESIS.value: 30,
    QuestionType.DIAGNOSIS.value: 30,
}
HARD_REASONING_TYPE_QUOTAS = {
    reasoning_type.value: 30 for reasoning_type in ReasoningType
}


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


def find_hard_profile_errors(dataset: BenchmarkDataset) -> list[str]:
    """Find distribution and item-contract errors for the v2-hard dataset."""

    if dataset.dataset_id != HARD_DATASET_ID:
        return []

    errors: list[str] = []
    if len(dataset.items) != 150:
        errors.append(
            f"v2-hard dataset must contain 150 items, got {len(dataset.items)}"
        )

    summary = dataset.distribution_summary()
    scope_counts = {
        "cross_book": summary["book_scope"].get(BookScope.CROSS_BOOK.value, 0),
        "intra_book": sum(
            count
            for scope, count in summary["book_scope"].items()
            if scope != BookScope.CROSS_BOOK.value
        ),
    }
    expected_distributions = {
        "scope": (scope_counts, HARD_SCOPE_QUOTAS),
        "required_source_count": (
            summary["required_source_count"],
            HARD_SOURCE_COUNT_QUOTAS,
        ),
        "question_type": (summary["question_type"], HARD_QUESTION_TYPE_QUOTAS),
        "reasoning_type": (summary["reasoning_type"], HARD_REASONING_TYPE_QUOTAS),
    }
    for name, (actual, expected) in expected_distributions.items():
        if actual != expected:
            errors.append(
                f"v2-hard {name} distribution mismatch: {actual} != {expected}"
            )

    for item in dataset.items:
        if item.difficulty is not Difficulty.HARD:
            errors.append(f"{item.id}: difficulty must be hard.")
        if item.question_type is QuestionType.DEFINITION:
            errors.append(f"{item.id}: definition questions are not allowed.")
        if item.single_source_sufficient is not False:
            errors.append(f"{item.id}: single_source_sufficient must be false.")
        if item.reasoning_type is None:
            errors.append(f"{item.id}: missing reasoning_type.")
        if not item.answer_key_fact_sources:
            errors.append(f"{item.id}: missing answer_key_fact_sources.")
    return errors


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
    errors.extend(find_hard_profile_errors(dataset))
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
