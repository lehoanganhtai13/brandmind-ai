"""Unit tests for the knowledge-search comparison dataset loader."""

from __future__ import annotations

import pytest

from evaluation.knowledge_search_comparison.dataset import (
    DEFAULT_DATASET_PATH,
    DEFAULT_HARD_DATASET_PATH,
    load_benchmark_dataset,
    select_benchmark_items,
)


def test_load_canonical_dataset_has_150_items() -> None:
    """The canonical comparison dataset should load the final 150 items."""

    dataset = load_benchmark_dataset(DEFAULT_DATASET_PATH)

    assert dataset.dataset_id == "brandmind_marketing_5books_v1"
    assert len(dataset.items) == 150
    assert set(dataset.distribution_summary()["book_scope"].values()) == {25}


def test_load_hard_dataset_has_v2_multihop_profile() -> None:
    """The hard comparison dataset should preserve v2 multi-hop metadata."""

    dataset = load_benchmark_dataset(DEFAULT_HARD_DATASET_PATH)
    summary = dataset.distribution_summary()

    assert dataset.dataset_id == "brandmind_marketing_5books_multihop_hard_v2"
    assert len(dataset.items) == 150
    assert summary["difficulty"] == {"hard": 150}
    assert summary["required_source_count"] == {"2": 20, "3": 60, "4": 50, "5": 20}
    assert set(summary["reasoning_type"].values()) == {30}
    assert all(not item.single_source_sufficient for item in dataset.items)


def test_select_benchmark_items_uses_limit_and_offset() -> None:
    """Pilot slicing should be deterministic and bounds-safe."""

    dataset = load_benchmark_dataset(DEFAULT_DATASET_PATH)
    selected = select_benchmark_items(dataset, offset=2, limit=3)

    assert [item.id for item in selected] == [item.id for item in dataset.items[2:5]]


def test_select_benchmark_items_rejects_negative_values() -> None:
    """Negative slice inputs should fail fast."""

    dataset = load_benchmark_dataset(DEFAULT_DATASET_PATH)

    with pytest.raises(ValueError, match="offset"):
        select_benchmark_items(dataset, offset=-1)

    with pytest.raises(ValueError, match="limit"):
        select_benchmark_items(dataset, limit=-1)
