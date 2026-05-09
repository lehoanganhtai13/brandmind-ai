"""Unit tests for HippoRAG benchmark foundation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from evaluation.hipporag_comparison.export_corpus import (
    CANONICAL_BOOK_DIRS,
    build_records,
    export_corpus,
    normalize_pages,
    slugify,
)


def test_slugify_removes_timestamp_suffix() -> None:
    """Directory timestamps should not leak into stable benchmark book slugs."""

    slug = slugify("Positioning_The_Battle_for_Your_Mind_20260206_170800")

    assert slug == "positioning_the_battle_for_your_mind"


@pytest.mark.parametrize(
    ("raw_pages", "expected"),
    [
        (7, [7]),
        ("8", [8]),
        ([3, "2", "bad", 3], [2, 3]),
        (None, []),
        ({"page": 1}, []),
    ],
)
def test_normalize_pages(raw_pages: object, expected: list[int]) -> None:
    """Page metadata should normalize to a stable integer list."""

    assert normalize_pages(raw_pages) == expected


def write_fixture_chunks(parsed_root: Path, book_dir: str, chunk_id: str) -> None:
    """Write one minimal parsed-document chunks fixture."""

    book_path = parsed_root / book_dir
    book_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [
            {
                "chunk_id": chunk_id,
                "content": f"Content for {book_dir}.",
                "metadata": {
                    "author": "Author",
                    "original_document": f"{book_dir}.pdf",
                    "pages": [1, "2"],
                    "section_summary": "Section summary.",
                    "source": "Fixture source.",
                    "word_count": 4,
                },
            }
        ],
        "total_chunks": 1,
    }
    (book_path / "chunks.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_records_exports_all_canonical_books(tmp_path: Path) -> None:
    """Exporter should preserve deterministic order and stable source IDs."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    records, metadata_by_source_id = build_records(tmp_path)

    assert len(records) == len(CANONICAL_BOOK_DIRS)
    assert len(metadata_by_source_id) == len(CANONICAL_BOOK_DIRS)
    assert records[0].idx == 0
    assert records[0].title.endswith("::chunk_0")
    assert records[0].title in metadata_by_source_id
    assert metadata_by_source_id[records[0].title].pages == [1, 2]


def test_export_corpus_writes_corpus_and_metadata(tmp_path: Path) -> None:
    """Exporter should write HippoRAG corpus JSON and metadata sidecar."""

    for index, book_dir in enumerate(CANONICAL_BOOK_DIRS):
        write_fixture_chunks(tmp_path, book_dir, f"chunk_{index}")

    corpus_path = tmp_path / "out" / "corpus.json"
    metadata_path = tmp_path / "out" / "metadata.json"

    export_corpus(tmp_path, corpus_path, metadata_path)

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert len(corpus) == len(CANONICAL_BOOK_DIRS)
    assert corpus[0] == {
        "title": corpus[0]["title"],
        "text": f"Content for {CANONICAL_BOOK_DIRS[0]}.",
        "idx": 0,
    }
    assert metadata["total_records"] == len(CANONICAL_BOOK_DIRS)
    assert corpus[0]["title"] in metadata["sources"]


def test_install_gemini_embedding_dimension_patch_passes_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The HippoRAG embedding patch should pass dimensions to the client call."""

    captured: dict[str, object] = {}

    class FakeEmbeddingsClient:
        """Fake OpenAI-compatible embeddings client for testing."""

        def create(
            self,
            *,
            input: list[str],
            model: str,
            dimensions: int,
        ) -> SimpleNamespace:
            """Capture call parameters and return one fake embedding."""

            captured["input"] = input
            captured["model"] = model
            captured["dimensions"] = dimensions
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])])

    class FakeOpenAIEmbeddingModel:
        """Fake HippoRAG embedding model patched by the adapter."""

        def __init__(self) -> None:
            self.client = SimpleNamespace(embeddings=FakeEmbeddingsClient())
            self.embedding_model_name = "gemini-embedding-001"

    hipporag_module = ModuleType("hipporag")
    embedding_model_module = ModuleType("hipporag.embedding_model")
    openai_module = ModuleType("hipporag.embedding_model.OpenAI")
    openai_module.OpenAIEmbeddingModel = FakeOpenAIEmbeddingModel

    import sys

    monkeypatch.setitem(sys.modules, "hipporag", hipporag_module)
    monkeypatch.setitem(sys.modules, "hipporag.embedding_model", embedding_model_module)
    monkeypatch.setitem(sys.modules, "hipporag.embedding_model.OpenAI", openai_module)

    from evaluation.hipporag_comparison.hipporag_litellm import (
        install_gemini_embedding_dimension_patch,
    )

    install_gemini_embedding_dimension_patch(embedding_dimensions=1536)

    model = openai_module.OpenAIEmbeddingModel()
    embeddings = model.encode(["line one\nline two"])

    assert embeddings.shape == (1, 2)
    assert captured == {
        "input": ["line one line two"],
        "model": "gemini-embedding-001",
        "dimensions": 1536,
    }
