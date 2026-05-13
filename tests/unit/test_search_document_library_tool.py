"""Unit tests for the document-library search tool formatting."""

from __future__ import annotations

import importlib

import pytest

from core.retrieval.models import DocumentChunkResult

module = importlib.import_module("shared.agent_tools.retrieval.search_document_library")


class FakeDocumentRetriever:
    """Retriever test double that returns one long source chunk."""

    async def search(self, **_kwargs: object) -> list[DocumentChunkResult]:
        """Return a deterministic long chunk without touching Milvus."""

        return [
            DocumentChunkResult(
                id="chunk-1",
                content=("A" * 500) + "KEY_FACT_AFTER_500" + ("B" * 3500),
                source="Chapter 12: Mental and Physical Availability",
                original_document="How Brands Grow: What Marketers Don't Know",
            )
        ]

    async def get_chunks_by_ids(
        self,
        chunk_ids: list[str],
    ) -> list[DocumentChunkResult]:
        """Return exact chunks for IDs that exist in the fake index."""

        chunks = {
            "chunk-1": DocumentChunkResult(
                id="chunk-1",
                content="Exact passage from a KG source pointer.",
                source="Chapter 12: Mental and Physical Availability",
                original_document="How Brands Grow: What Marketers Don't Know",
            )
        }
        return [chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks]


def test_expand_document_query_adds_source_language_terms() -> None:
    """Common Vietnamese concepts should include compact English corpus terms."""

    expanded = module.expand_document_query("tiếp thị bền vững trong chương 20")

    assert "sustainable marketing principles" in expanded
    assert "consumer-oriented marketing" in expanded


@pytest.mark.asyncio
async def test_document_library_returns_more_than_legacy_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Long chunks should expose facts that appear after the first 500 chars."""

    monkeypatch.setattr(module, "_get_retriever", lambda: FakeDocumentRetriever())

    result = await module.search_document_library(query="availability", top_k=1)

    assert "Context hint: ranked document search." in result
    assert "Opening evidence:" in result
    assert "KEY_FACT_AFTER_500" in result
    assert result.rstrip().endswith("...")


@pytest.mark.asyncio
async def test_document_library_labels_lower_ranked_neighbors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ranked output should separate direct evidence from broader neighbors."""

    class MultiResultRetriever(FakeDocumentRetriever):
        async def search(self, **_kwargs: object) -> list[DocumentChunkResult]:
            return [
                DocumentChunkResult(
                    id=f"chunk-{index}",
                    content=(
                        f"passage {index} " + ("N" * 2000)
                        if index == 4
                        else f"passage {index}"
                    ),
                    source="Chapter 3: Analyzing the Marketing Environment",
                    original_document="Principles of Marketing 17th Edition",
                )
                for index in range(1, 5)
            ]

    monkeypatch.setattr(module, "_get_retriever", lambda: MultiResultRetriever())

    result = await module.search_document_library(query="family structure", top_k=4)

    assert "Lower-ranked neighboring passages" in result
    assert result.index("Lower-ranked neighboring passages") < result.index(
        "[4] Source"
    )
    assert "may be neighboring context or noise" in result
    assert "N" * 700 not in result
    lower_neighbor = result[result.index("[4] Source") :]
    assert "Opening evidence:" not in lower_neighbor


def test_extract_opening_evidence_preserves_first_sentence() -> None:
    """Top-result opening cues should make direct conclusions easy to notice."""

    opening = module.extract_opening_evidence(
        "Thus, marketers need to form more precise age-specific segments. "
        "More important, defining people by birth date may be less effective."
    )

    assert opening == "Thus, marketers need to form more precise age-specific segments."


@pytest.mark.asyncio
async def test_document_library_expands_agent_query_before_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Agent-generated follow-up queries should be translated into corpus terms."""

    class CapturingRetriever(FakeDocumentRetriever):
        captured_query: str | None = None

        async def search(self, **kwargs: object) -> list[DocumentChunkResult]:
            self.captured_query = str(kwargs["query"])
            return await super().search(**kwargs)

    retriever = CapturingRetriever()
    monkeypatch.setattr(module, "_get_retriever", lambda: retriever)

    await module.search_document_library(
        query="changing family dynamics adaptation market segmentation strategy",
        top_k=1,
    )

    assert retriever.captured_query is not None
    assert "The Changing American Family" in retriever.captured_query
    assert "age-specific segments" in retriever.captured_query


@pytest.mark.asyncio
async def test_document_library_can_fetch_exact_source_chunk_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KG source pointers should let the agent read an exact document chunk."""

    monkeypatch.setattr(module, "_get_retriever", lambda: FakeDocumentRetriever())

    result = await module.search_document_library(
        query="mental availability",
        source_chunk_id="chunk-1",
        top_k=1,
    )

    assert "Context hint: exact source_chunk_id lookup." in result
    assert "Source chunk ID: chunk-1" in result
    assert "Exact passage from a KG source pointer." in result
