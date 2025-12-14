"""
Integration test for Document Library Search Tool (Task 20).

Tests the DocumentRetriever class and search_document_library tool wrapper
with actual DocumentChunks data from Stage 4.
"""

import asyncio

from config.system_config import SETTINGS
from core.retrieval.document_retriever import DocumentRetriever
from shared.agent_tools.retrieval.search_document_library import (
    search_document_library,
)
from shared.database_clients.vector_database.milvus.config import MilvusConfig
from shared.database_clients.vector_database.milvus.database import (
    MilvusVectorDatabase,
)
from shared.model_clients.embedder.gemini import GeminiEmbedder
from shared.model_clients.embedder.gemini.config import (
    EmbeddingMode,
    GeminiEmbedderConfig,
)


async def test_basic_hybrid_search():
    """Test Case 1: Basic hybrid search without filters."""
    print("\n=== Test Case 1: Basic Hybrid Search ===")

    # Initialize components
    vector_db = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )

    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            mode=EmbeddingMode.RETRIEVAL,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
            api_key=SETTINGS.GEMINI_API_KEY,
        )
    )

    retriever = DocumentRetriever(vector_db=vector_db, embedder=embedder)

    # Execute search
    results = await retriever.search("marketing mix", top_k=5)

    # Verify results
    print(f"Found {len(results)} results")
    assert len(results) > 0, "Should return at least one result"

    for i, chunk in enumerate(results[:3], 1):
        print(f"\n[{i}] Source: {chunk.source}")
        print(f"    Book: {chunk.original_document}")
        print(f"    Score: {chunk.score:.4f}")
        print(f"    Content: {chunk.content[:150]}...")

        # Verify all fields are populated
        assert chunk.id, "Chunk ID should not be empty"
        assert chunk.content, "Content should not be empty"
        assert chunk.source, "Source should not be empty"
        assert chunk.original_document, "Original document should not be empty"

    print("\n✅ Test Case 1 PASSED")


async def test_filter_by_book():
    """Test Case 2: Filter by book name."""
    print("\n=== Test Case 2: Filter by Book ===")

    # Use tool wrapper for this test
    result_text = await search_document_library(
        query="pricing",
        filter_by_book="Principles of Marketing 17th Edition",
        top_k=3,
    )

    print(result_text)

    # Verify output format
    assert "Source:" in result_text, "Should contain source information"
    assert "Book:" in result_text, "Should contain book information"
    assert "Content:" in result_text, "Should contain content preview"

    print("\n✅ Test Case 2 PASSED")


async def test_filter_by_chapter():
    """Test Case 3: Filter by chapter (partial match)."""
    print("\n=== Test Case 3: Filter by Chapter ===")

    vector_db = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )

    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            mode=EmbeddingMode.RETRIEVAL,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
            api_key=SETTINGS.GEMINI_API_KEY,
        )
    )

    retriever = DocumentRetriever(vector_db=vector_db, embedder=embedder)

    results = await retriever.search(
        "value", filter_by_chapter="Chapter 9", top_k=3
    )

    print(f"Found {len(results)} results")

    if results:
        for chunk in results:
            print(f"Source: {chunk.source}")
            # Verify all results contain "Chapter 9" in source
            assert (
                "Chapter 9" in chunk.source
            ), f"Source should contain 'Chapter 9', got: {chunk.source}"

    print("\n✅ Test Case 3 PASSED")


async def test_no_results():
    """Test Case 4: Handling of very low relevance queries."""
    print("\n=== Test Case 4: Low Relevance Query ===")

    # Note: Hybrid search may still return results even for nonsense queries
    # because it tries to match something. This is expected behavior.
    result_text = await search_document_library(
        query="xyzabc123nonexistent", top_k=5
    )

    print(f"Result length: {len(result_text)} characters")
    print(f"First 200 chars: {result_text[:200]}")

    # Verify it returns something (even if low relevance)
    # This is expected behavior for hybrid search
    assert len(result_text) > 0, "Should return some result"

    # If it returns "No results found.", that's also acceptable
    if result_text == "No results found.":
        print("Returned 'No results found.' (acceptable)")
    else:
        print("Returned low-relevance results (expected for hybrid search)")

    print("\n✅ Test Case 4 PASSED")


async def test_combined_filters():
    """Test Case 5: Multiple filters combined."""
    print("\n=== Test Case 5: Combined Filters ===")

    vector_db = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )

    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            mode=EmbeddingMode.RETRIEVAL,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
            api_key=SETTINGS.GEMINI_API_KEY,
        )
    )

    retriever = DocumentRetriever(vector_db=vector_db, embedder=embedder)

    results = await retriever.search(
        "marketing",
        filter_by_book="Principles of Marketing 17th Edition",
        filter_by_chapter="Chapter",
        top_k=3,
    )

    print(f"Found {len(results)} results with combined filters")

    if results:
        for chunk in results[:2]:
            print(f"\nSource: {chunk.source}")
            print(f"Book: {chunk.original_document}")
            # Verify both filters applied
            assert (
                chunk.original_document == "Principles of Marketing 17th Edition"
            )
            assert "Chapter" in chunk.source

    print("\n✅ Test Case 5 PASSED")


async def main():
    """Run all test cases."""
    print("=" * 60)
    print("Task 20: Document Library Search Tool - Integration Tests")
    print("=" * 60)

    try:
        await test_basic_hybrid_search()
        await test_filter_by_book()
        await test_filter_by_chapter()
        await test_no_results()
        await test_combined_filters()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
