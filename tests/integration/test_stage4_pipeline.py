"""
Integration tests for Stage 4 Pipeline (Indexing).

Tests both Stream A (Document Library) and Stream B (Knowledge Graph Builder)
with sample data to verify CLI integration, collection creation, and resume functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from config.system_config import SETTINGS
from core.knowledge_graph.curator.collection_schemas import (
    ENTITY_BM25_CONFIG,
    ENTITY_DESCRIPTIONS_SCHEMA,
    RELATION_BM25_CONFIG,
    RELATION_DESCRIPTIONS_SCHEMA,
)
from core.knowledge_graph.curator.document_library import (
    DOCUMENT_CHUNKS_BM25_CONFIG,
    DOCUMENT_CHUNKS_SCHEMA,
)
from shared.database_clients.graph_database.falkordb import FalkorDBClient
from shared.database_clients.graph_database.falkordb.config import FalkorDBConfig
from shared.database_clients.vector_database.milvus import MilvusVectorDatabase
from shared.database_clients.vector_database.milvus.config import MilvusConfig
from shared.model_clients.embedder.gemini import GeminiEmbedder
from shared.model_clients.embedder.gemini.config import GeminiEmbedderConfig


@pytest_asyncio.fixture
async def milvus_client():
    """Create Milvus client for testing."""
    client = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )
    yield client
    # Cleanup collections after tests
    try:
        await client.async_delete_collection("TestDocumentChunks")
    except Exception:
        pass
    try:
        await client.async_delete_collection("TestEntityDescriptions")
    except Exception:
        pass
    try:
        await client.async_delete_collection("TestRelationDescriptions")
    except Exception:
        pass


@pytest_asyncio.fixture
async def falkor_client():
    """Create FalkorDB client for testing."""
    client = FalkorDBClient(
        config=FalkorDBConfig(
            host=SETTINGS.FALKORDB_HOST,
            port=SETTINGS.FALKORDB_PORT,
            username=SETTINGS.FALKORDB_USERNAME,
            password=SETTINGS.FALKORDB_PASSWORD,
            graph_name="test_stage4_pipeline",
        )
    )
    yield client
    # Cleanup graph after tests
    try:
        await client.async_delete_graph()
    except Exception:
        pass


@pytest.fixture
def embedder():
    """Create Gemini embedder for testing."""
    return GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-embedding-001",
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
        )
    )


@pytest.fixture
def sample_chunks_data():
    """Sample chunks data for Document Library testing."""
    return {
        "chunks": [
            {
                "chunk_id": "test-chunk-001",
                "content": "Marketing strategy creates customer value through planned approaches.",
                "metadata": {
                    "source": "Test > Marketing",
                    "original_document": "Test Doc",
                    "author": "Test Author",
                    "pages": ["page_1.md"],
                    "word_count": 10,
                },
            },
            {
                "chunk_id": "test-chunk-002",
                "content": "Product differentiation helps companies stand out in markets.",
                "metadata": {
                    "source": "Test > Strategy",
                    "original_document": "Test Doc",
                    "author": "Test Author",
                    "pages": ["page_2.md"],
                    "word_count": 8,
                },
            },
        ],
        "total_chunks": 2,
        "avg_chunk_size": 9,
    }


@pytest.fixture
def sample_triples_data():
    """Sample triples data for Knowledge Graph testing."""
    return {
        "total_chunks": 2,
        "total_entities": 4,
        "total_relations": 2,
        "extractions": [
            {
                "chunk_id": "test-chunk-001",
                "source_hierarchy": "Test > Marketing",
                "extraction": {
                    "entities": [
                        {
                            "name": "Marketing Strategy",
                            "type": "MarketingConcept",
                            "description": "A planned approach to creating customer value",
                        },
                        {
                            "name": "Customer Value",
                            "type": "MarketingConcept",
                            "description": "The benefits customers receive from products",
                        },
                    ],
                    "relationships": [
                        {
                            "source": "Marketing Strategy",
                            "target": "Customer Value",
                            "relation_type": "creates",
                            "description": "Marketing strategy creates customer value",
                        }
                    ],
                },
            },
            {
                "chunk_id": "test-chunk-002",
                "source_hierarchy": "Test > Strategy",
                "extraction": {
                    "entities": [
                        {
                            "name": "Product Differentiation",
                            "type": "MarketingStrategy",
                            "description": "Strategy to stand out in competitive markets",
                        },
                        {
                            "name": "Market Segmentation",
                            "type": "MarketingStrategy",
                            "description": "Dividing markets into distinct buyer groups",
                        },
                    ],
                    "relationships": [
                        {
                            "source": "Market Segmentation",
                            "target": "Product Differentiation",
                            "relation_type": "enables",
                            "description": "Segmentation enables better differentiation",
                        }
                    ],
                },
            },
        ],
    }


@pytest.mark.asyncio
async def test_stream_a_document_library_idempotency(
    milvus_client, embedder, sample_chunks_data
):
    """
    Test Case 1: Stream A (Document Library) with idempotency.
    
    Verifies:
    - Collection creation with correct schema and BM25 config
    - Embedding and indexing of document chunks
    - Idempotent behavior on repeated runs
    """
    print("\\n" + "=" * 80)
    print("TEST: Stream A - Document Library with Idempotency")
    print("=" * 80)

    # Create collection
    collection_name = "TestDocumentChunks"
    await milvus_client.async_create_collection(
        collection_name=collection_name,
        collection_structure=DOCUMENT_CHUNKS_SCHEMA,
        bm25_function_config=DOCUMENT_CHUNKS_BM25_CONFIG,
    )
    print(f"✓ Created collection '{collection_name}'")

    # Prepare test data in temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        chunks_path = Path(tmpdir) / "chunks.json"
        with open(chunks_path, "w") as f:
            json.dump(sample_chunks_data, f)

        # Import and run build_document_library
        from core.knowledge_graph.curator.document_library import build_document_library

        # Run 1: Initial indexing
        stats1 = await build_document_library(
            chunks_path=chunks_path,
            vector_db=milvus_client,
            embedder=embedder,
            collection_name=collection_name,
            progress_path=Path(tmpdir) / "progress.json",
        )

        assert stats1["embedded"] == 2, "Should embed 2 chunks"
        assert stats1["upserted"] == 2, "Should upsert 2 chunks"
        assert stats1["errors"] == 0, "Should have no errors"
        print(f"✓ Run 1: Indexed {stats1['upserted']} chunks")

        # Run 2: Resume (should skip already processed)
        stats2 = await build_document_library(
            chunks_path=chunks_path,
            vector_db=milvus_client,
            embedder=embedder,
            collection_name=collection_name,
            progress_path=Path(tmpdir) / "progress.json",
        )

        assert stats2["embedded"] == 0, "Should skip already processed chunks"
        assert stats2["upserted"] == 0, "Should not upsert duplicates"
        print(f"✓ Run 2: Skipped {2} already processed chunks (idempotent)")

    print(f"✅ Stream A test passed!")


@pytest.mark.asyncio
async def test_stream_b_knowledge_graph(
    milvus_client, falkor_client, embedder, sample_triples_data
):
    """
    Test Case 2: Stream B (Knowledge Graph Builder).
    
    Verifies:
    - Entity and relation collection creation
    - Entity resolution and graph building
    - Dual storage (FalkorDB + Milvus)
    """
    print("\\n" + "=" * 80)
    print("TEST: Stream B - Knowledge Graph Builder")
    print("=" * 80)

    # Create collections
    entity_collection = "TestEntityDescriptions"
    relation_collection = "TestRelationDescriptions"

    await milvus_client.async_create_collection(
        collection_name=entity_collection,
        collection_structure=ENTITY_DESCRIPTIONS_SCHEMA,
        bm25_function_config=ENTITY_BM25_CONFIG,
    )
    await milvus_client.async_create_collection(
        collection_name=relation_collection,
        collection_structure=RELATION_DESCRIPTIONS_SCHEMA,
        bm25_function_config=RELATION_BM25_CONFIG,
    )
    print(f"✓ Created collections: '{entity_collection}', '{relation_collection}'")

    # Prepare test data
    with tempfile.TemporaryDirectory() as tmpdir:
        triples_path = Path(tmpdir) / "triples.json"
        with open(triples_path, "w") as f:
            json.dump(sample_triples_data, f)

        # Import and run build_knowledge_graph
        from core.knowledge_graph.curator.knowledge_graph_builder import (
            build_knowledge_graph,
        )

        # Use SEMANTIC embedder for KG
        kg_embedder = GeminiEmbedder(
            config=GeminiEmbedderConfig(
                api_key=SETTINGS.GEMINI_API_KEY,
                model="gemini-embedding-001",
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=SETTINGS.EMBEDDING_DIM,
            )
        )

        stats = await build_knowledge_graph(
            triples_path=triples_path,
            graph_db=falkor_client,
            vector_db=milvus_client,
            embedder=kg_embedder,
            entity_collection_name=entity_collection,
            relation_collection_name=relation_collection,
            progress_path=Path(tmpdir) / "kg_progress.json",
        )

        assert stats["entities_created"] == 4, "Should create 4 entities"
        assert stats["entities_merged"] == 0, "Should merge 0 entities (no duplicates)"
        assert stats["relations_created"] == 2, "Should create 2 relations"
        print(
            f"✓ Created {stats['entities_created']} entities, "
            f"{stats['relations_created']} relations"
        )

    print(f"✅ Stream B test passed!")
