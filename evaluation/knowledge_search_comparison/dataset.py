"""Dataset loading helpers for the knowledge-search comparison benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.hipporag_comparison.benchmark_schema import (
    BenchmarkDataset,
    BenchmarkItem,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = PACKAGE_ROOT / "datasets" / "marketing_5books_benchmark_v1.json"


def load_benchmark_dataset(path: Path = DEFAULT_DATASET_PATH) -> BenchmarkDataset:
    """Load the canonical five-book benchmark dataset.

    Args:
        path: Dataset JSON path using the ``BenchmarkDataset`` schema.

    Returns:
        Parsed and validated benchmark dataset.

    Raises:
        FileNotFoundError: If the dataset path does not exist.
        ValueError: If the dataset cannot be parsed as a JSON object.
    """

    if not path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected benchmark dataset object in {path}.")
    return BenchmarkDataset(**payload)


def select_benchmark_items(
    dataset: BenchmarkDataset,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[BenchmarkItem]:
    """Select a deterministic slice of benchmark items for pilot or full runs.

    Args:
        dataset: Loaded benchmark dataset.
        limit: Optional maximum number of items to return.
        offset: Number of initial items to skip.

    Returns:
        A list of selected benchmark items.

    Raises:
        ValueError: If ``limit`` or ``offset`` is negative.
    """

    if offset < 0:
        raise ValueError("offset must be non-negative.")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative.")

    if limit is None:
        return dataset.items[offset:]
    return dataset.items[offset : offset + limit]
