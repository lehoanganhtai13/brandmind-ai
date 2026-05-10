"""Unit tests for knowledge-search source mapping helpers."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.knowledge_search_comparison.source_mapping import (
    CorpusRecord,
    SourceMapping,
    SourceMetadataRecord,
    load_source_mapping,
    normalize_text,
)


def make_mapping() -> SourceMapping:
    """Create a small source mapping fixture."""

    records = [
        CorpusRecord(
            title="book_one::chunk_1",
            text="A distinctive asset helps mental availability.",
            idx=0,
        ),
        CorpusRecord(
            title="book_two::chunk_2",
            text="Segmentation starts with customer needs.",
            idx=1,
        ),
        CorpusRecord(
            title="book_two::chunk_3",
            text="Segmentation starts with customer needs.",
            idx=2,
        ),
    ]
    metadata = {
        record.source_id: SourceMetadataRecord(
            source_id=record.source_id,
            chunk_id=record.source_id.split("::", maxsplit=1)[1],
        )
        for record in records
    }
    return SourceMapping(records=records, metadata_by_source_id=metadata)


def test_source_mapping_maps_exact_and_normalized_text() -> None:
    """HippoRAG raw text should map back to stable source IDs."""

    mapping = make_mapping()

    assert mapping.source_ids_for_text(
        "A distinctive asset helps mental availability."
    ) == ["book_one::chunk_1"]
    assert mapping.source_ids_for_text(
        "Segmentation   starts with\ncustomer needs."
    ) == ["book_two::chunk_2", "book_two::chunk_3"]
    assert mapping.duplicate_text_count == 1


def test_source_mapping_maps_documents_by_title_index_and_chunk_id() -> None:
    """Worker outputs and BrandMind chunk IDs should map to stable IDs."""

    mapping = make_mapping()

    assert mapping.source_ids_for_document({"title": "book_one::chunk_1"}) == [
        "book_one::chunk_1"
    ]
    assert mapping.source_ids_for_document({"idx": 1}) == ["book_two::chunk_2"]
    assert mapping.source_ids_for_chunk_id("chunk_3") == ["book_two::chunk_3"]


def test_source_mapping_extracts_source_ids_from_formatted_text() -> None:
    """Formatted tool output may already contain source IDs."""

    mapping = make_mapping()
    text = "Sources: book_one::chunk_1 and book_two::chunk_2."

    assert mapping.source_ids_in_text(text) == [
        "book_one::chunk_1",
        "book_two::chunk_2",
    ]


def test_load_source_mapping_from_files(tmp_path: Path) -> None:
    """Source mapping should load the exported corpus and metadata formats."""

    corpus_path = tmp_path / "corpus.json"
    metadata_path = tmp_path / "metadata.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "book_one::chunk_1",
                    "text": "Distinctive asset source text.",
                    "idx": 0,
                }
            ]
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "sources": {
                    "book_one::chunk_1": {
                        "source_id": "book_one::chunk_1",
                        "chunk_id": "chunk_1",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    mapping = load_source_mapping(corpus_path, metadata_path)

    assert mapping.source_ids_for_text("Distinctive asset source text.") == [
        "book_one::chunk_1"
    ]


def test_normalize_text_collapses_whitespace() -> None:
    """Whitespace-normalized joins should be stable."""

    assert normalize_text("a\n  b\tc") == "a b c"
