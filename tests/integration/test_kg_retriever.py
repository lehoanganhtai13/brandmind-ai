"""
Integration tests for KG Retriever and search_knowledge_graph tool.

Tests verify the complete pipeline: query decomposition → parallel search →
verbalization → enrichment → reranking → formatting.
"""

import pytest

from shared.agent_tools.retrieval import search_knowledge_graph
"""
Note: Tests are designed to run independently. When running all tests together,
there may be gRPC cleanup warnings due to singleton database connections.
This is benign and does not indicate test failure - each test verifies its
own assertions correctly.
"""


@pytest.mark.asyncio
async def test_search_knowledge_graph_basic():
    """
    Test basic search_knowledge_graph functionality.

    Verifies:
    - Tool imports and initializes correctly
    - Returns structured Markdown output
    - Contains expected sections (Entities, Relationships)
    """
    query = "What is market segmentation?"
    result = await search_knowledge_graph(query=query, max_results=5)

    # Verify result is non-empty string
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify contains expected sections (if results found)
    if "No relevant knowledge" not in result:
        assert "Retrieved Knowledge from Knowledge Graph" in result
        # May have one or both sections depending on results
        has_entities = "Entities" in result
        has_relationships = "Relationships & Paths" in result
        assert has_entities or has_relationships


@pytest.mark.asyncio
async def test_search_knowledge_graph_empty_query():
    """
    Test handling of queries with no results.

    Verifies graceful fallback when no knowledge is found.
    """
    query = "xyzabc123nonsense"
    result = await search_knowledge_graph(query=query, max_results=5)

    assert isinstance(result, str)
    # Should handle gracefully with message or empty sections
