"""Unit tests for the HippoRAG subprocess worker helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from evaluation.knowledge_search_comparison import hipporag_worker


class FakeHippoRag:
    """Fixture HippoRAG client returning numpy score arrays."""

    def retrieve(self, queries: list[str], num_to_retrieve: int):
        """Return one native retrieval solution."""

        return [
            type(
                "FakeSolution",
                (),
                {
                    "docs": ["Mental availability depends on memory structures."],
                    "doc_scores": np.array([0.75]),
                },
            )()
        ]


class FakeSourceMapping:
    """Fixture source mapper for raw passage text."""

    def source_ids_for_document(self, document: str) -> list[str]:
        """Map the fake passage to a stable source ID."""

        assert document == "Mental availability depends on memory structures."
        return ["how_brands_grow::chunk_1"]


def test_retrieve_with_hipporag_accepts_numpy_score_arrays(monkeypatch) -> None:
    """Worker retrieval should normalize HippoRAG numpy score arrays."""

    monkeypatch.setattr(
        hipporag_worker, "build_hipporag", lambda _config: FakeHippoRag()
    )
    monkeypatch.setattr(
        hipporag_worker,
        "load_source_mapping",
        lambda _corpus_path, _metadata_path: FakeSourceMapping(),
    )

    response = hipporag_worker.retrieve_with_hipporag(
        query="mental availability",
        top_k=1,
        save_dir=Path("ignored"),
        corpus_path=Path("ignored"),
        metadata_path=Path("ignored"),
    )

    assert response.passages[0].score == 0.75
    assert response.passages[0].source_ids == ["how_brands_grow::chunk_1"]
