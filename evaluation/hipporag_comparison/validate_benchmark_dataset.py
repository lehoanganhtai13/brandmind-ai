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
