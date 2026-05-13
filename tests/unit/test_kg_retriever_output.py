"""Unit tests for knowledge-graph retrieval output formatting."""

from __future__ import annotations

from core.retrieval.kg_retriever import KGRetriever
from core.retrieval.models import SourceMetadata, VerbalizedFact


def test_kg_output_exposes_actionable_doc_lookup_pointer() -> None:
    """KG output should expose exact and scoped follow-up routes per fact."""

    retriever = KGRetriever.__new__(KGRetriever)
    output = retriever._format_output(
        [
            VerbalizedFact(
                type="global",
                text="Brand salience depends on mental availability.",
                source_chunk_ids=["chunk-123", "chunk-456"],
                source_metadata=[
                    SourceMetadata(
                        source="Chapter 12: Mental and Physical Availability",
                        original_document="How Brands Grow: What Marketers Don't Know",
                    ),
                    SourceMetadata(
                        source="Chapter 13: Advertising",
                        original_document="How Brands Grow: What Marketers Don't Know",
                    ),
                ],
            )
        ]
    )

    assert "Evidence map:" in output
    assert "Source chunk IDs: chunk-123, chunk-456" in output
    assert "Exact verify:" in output
    assert 'source_chunk_id="chunk-123"' in output
    assert 'source_chunk_id="chunk-456"' in output
    assert "Scoped explore:" in output
    assert 'filter_by_chapter="Chapter 12"' in output
    assert 'filter_by_chapter="Chapter 13"' in output
