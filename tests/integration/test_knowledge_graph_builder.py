"""
Integration tests for Knowledge Graph Builder.

Tests entity resolution, dual storage coordination, and end-to-end graph building.
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
from core.knowledge_graph.curator.knowledge_graph_builder import build_knowledge_graph
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
        await client.async_delete_collection("EntityDescriptions")
    except Exception:
        pass
    try:
        await client.async_delete_collection("RelationDescriptions")
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
            graph_name="test_kg",
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
            task_type="SEMANTIC",
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
        )
    )


@pytest.mark.asyncio
async def test_collection_creation(milvus_client):
    """Test Case: Create EntityDescriptions and RelationDescriptions collections."""
    print("\n" + "=" * 80)
    print("TEST: Collection Creation with BM25 Support")
    print("=" * 80)

    # 1. Create EntityDescriptions collection
    await milvus_client.async_create_collection(
        collection_name="EntityDescriptions",
        collection_structure=ENTITY_DESCRIPTIONS_SCHEMA,
        bm25_function_config=ENTITY_BM25_CONFIG,
    )
    print("✓ Created EntityDescriptions collection with BM25 functions")

    # 2. Create RelationDescriptions collection
    await milvus_client.async_create_collection(
        collection_name="RelationDescriptions",
        collection_structure=RELATION_DESCRIPTIONS_SCHEMA,
        bm25_function_config=RELATION_BM25_CONFIG,
    )
    print("✓ Created RelationDescriptions collection with BM25 function")

    # 3. Verify collections exist
    collections = await milvus_client.async_list_collections()
    assert "EntityDescriptions" in collections
    assert "RelationDescriptions" in collections
    print(f"✓ Verified collections: {collections}")


@pytest.mark.asyncio
async def test_entity_resolution_duplicates(
    milvus_client, falkor_client, embedder
):
    """Test Case 1: Entity Resolution - Known Duplicates."""
    print("\n" + "=" * 80)
    print("TEST: Entity Resolution - Known Duplicates")
    print("=" * 80)

    # Setup collections
    await milvus_client.async_create_collection(
        collection_name="EntityDescriptions",
        collection_structure=ENTITY_DESCRIPTIONS_SCHEMA,
        bm25_function_config=ENTITY_BM25_CONFIG,
    )
    await milvus_client.async_create_collection(
        collection_name="RelationDescriptions",
        collection_structure=RELATION_DESCRIPTIONS_SCHEMA,
        bm25_function_config=RELATION_BM25_CONFIG,
    )

    # Create sample triples with known duplicates
    sample_data = {
        "extractions": [
            {
                "chunk_id": "chunk_1",
                "source_hierarchy": "Test > Marketing",
                "extraction": {
                    "entities": [
                        {
                            "name": "Market Segmentation",
                            "type": "MarketingConcept",
                            "description": "Dividing market into distinct groups.",
                        }
                    ],
                    "relationships": [],
                },
            },
            {
                "chunk_id": "chunk_2",
                "source_hierarchy": "Test > Marketing",
                "extraction": {
                    "entities": [
                        {
                            "name": "Segmentation",
                            "type": "MarketingConcept",
                            "description": "Process of dividing a market into segments.",
                        }
                    ],
                    "relationships": [],
                },
            },
        ]
    }

    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_data, f)
        triples_path = Path(f.name)

    try:
        # Build knowledge graph
        stats = await build_knowledge_graph(
            triples_path=triples_path,
            graph_db=falkor_client,
            vector_db=milvus_client,
            embedder=embedder,
        )

        print(f"Stats: {stats}")

        # Verify merge happened
        assert stats["entities_created"] == 1, "Should create 1 entity"
        assert stats["entities_merged"] == 1, "Should merge 1 duplicate"
        print(
            "✓ Duplicates merged: created=1, merged=1"
        )

    finally:
        triples_path.unlink()


@pytest.mark.asyncio
async def test_entity_resolution_different(milvus_client, falkor_client, embedder):
    """Test Case 2: Entity Resolution - Different Entities."""
    print("\n" + "=" * 80)
    print("TEST: Entity Resolution - Different Entities")
    print("=" * 80)

    # Setup collections
    await milvus_client.async_create_collection(
        collection_name="EntityDescriptions",
        collection_structure=ENTITY_DESCRIPTIONS_SCHEMA,
        bm25_function_config=ENTITY_BM25_CONFIG,
    )
    await milvus_client.async_create_collection(
        collection_name="RelationDescriptions",
        collection_structure=RELATION_DESCRIPTIONS_SCHEMA,
        bm25_function_config=RELATION_BM25_CONFIG,
    )

    # Create sample with different entities

    sample_data = {
        "extractions": [
            {
                "chunk_id": "chunk_1",
                "extraction": {
                    "entities": [
                        {
                            "name": "Product Differentiation",
                            "type": "MarketingStrategy",
                            "description": "Strategy to distinguish product from competitors.",
                        }
                    ],
                    "relationships": []
                },
            },
            {
                "chunk_id": "chunk_2",
                "extraction": {
                    "entities": [
                        {
                            "name": "Market Differentiation",
                            "type": "MarketingStrategy",
                            "description": "Differentiating in the marketplace.",
                        }
                    ],
                    "relationships": []
                },
            }
        ]
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_data, f)
        triples_path = Path(f.name)

    try:
        stats = await build_knowledge_graph(
            triples_path=triples_path,
            graph_db=falkor_client,
            vector_db=milvus_client,
            embedder=embedder,
        )

        print(f"Stats: {stats}")

        # Verify both remain separate
        assert stats["entities_created"] == 2, "Should create 2 separate entities"
        assert stats["entities_merged"] == 0, "Should not merge different entities"
        print("✓ Different entities kept separate: created=2, merged=0")

    finally:
        triples_path.unlink()


@pytest.mark.asyncio
async def test_dual_storage_consistency(milvus_client, falkor_client, embedder):
    """Test Case 5: Dual Storage Consistency."""
    print("\n" + "=" * 80)
    print("TEST: Dual Storage Consistency")
    print("=" * 80)

    # Clean Graph DB from previous tests
    try:
        all_nodes_query = "MATCH (n) DETACH DELETE n"
        await falkor_client.async_execute_query(all_nodes_query)
    except Exception:
        pass

    # Setup collections
    await milvus_client.async_create_collection(
        collection_name="EntityDescriptions",
        collection_structure=ENTITY_DESCRIPTIONS_SCHEMA,
        bm25_function_config=ENTITY_BM25_CONFIG,
    )
    await milvus_client.async_create_collection(
        collection_name="RelationDescriptions",
        collection_structure=RELATION_DESCRIPTIONS_SCHEMA,
        bm25_function_config=RELATION_BM25_CONFIG,
    )

    # Create simple graph
    sample_data = {
        "extractions": [
            {
                "chunk_id": "chunk_1",
                "extraction": {
                    "entities": [
                        {
                            "name": "SEO",
                            "type": "Technique",
                            "description": "Search Engine Optimization",
                        },
                        {
                            "name": "Website Traffic",
                            "type": "Metric",
                            "description": "Number of visitors to website",
                        },
                    ],
                    "relationships": [
                        {
                            "source": "SEO",
                            "target": "Website Traffic",
                            "relation_type": "increases",
                            "description": "SEO techniques increase website traffic",
                        }
                    ],
                },
            }
        ]
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_data, f)
        triples_path = Path(f.name)

    try:
        stats = await build_knowledge_graph(
            triples_path=triples_path,
            graph_db=falkor_client,
            vector_db=milvus_client,
            embedder=embedder,
        )

        print(f"Stats: {stats}")
        assert stats["entities_created"] == 2
        assert stats["relations_created"] == 1


        # Verify Graph DB: Check nodes and relationships exist
        # Query all nodes
        nodes_query = "MATCH (n) RETURN n.id as id, n.name as name, labels(n) as labels"
        nodes_result = await falkor_client.async_execute_query(nodes_query)
        
        assert len(nodes_result.result_set) == 2, f"Expected 2 nodes in Graph DB, got {len(nodes_result.result_set)}"
        node_names = {row[1] for row in nodes_result.result_set}  # row[1] is "name" column
        assert node_names == {"SEO", "Website Traffic"}, f"Node names mismatch: {node_names}"
        
        # Get node IDs for Vector DB verification
        node_ids = [row[0] for row in nodes_result.result_set]
        print(f"DEBUG: Node IDs from Graph DB: {node_ids}")

        # Load collections before querying
        await milvus_client.async_load_collection("EntityDescriptions")
        await milvus_client.async_load_collection("RelationDescriptions")
        
        # Wait for data consistency (get_items might be eventually consistent)
        import asyncio
        await asyncio.sleep(2)

        # Query relationship
        rel_query = """
        MATCH (s)-[r]->(t) 
        RETURN s.name as source, type(r) as rel_type, t.name as target, r.description as desc, r.vector_db_ref_id as vector_id
        """
        rel_result = await falkor_client.async_execute_query(rel_query)
        
        assert len(rel_result.result_set) == 1, f"Expected 1 relationship in Graph DB, got {len(rel_result.result_set)}"
        assert rel_result.result_set[0][0] == "SEO"  # First column is source
        assert rel_result.result_set[0][2] == "Website Traffic"  # Third column is target
        assert rel_result.result_set[0][1] == "INCREASES"  # Second column is rel_type
        
        # Get relation ID for Vector DB verification
        relation_id = rel_result.result_set[0][4]
        
        print("✓ Graph DB verification passed: 2 nodes, 1 relationship")
        
        # Verify Vector DB: Check entity and relation descriptions exist
        # Use async_get_items to check existence directly by ID
        
        # Query entities using async_get_items
        entity_query_result = await milvus_client.async_get_items(
            ids=node_ids,
            collection_name="EntityDescriptions",
            output_fields=["id", "name", "type", "description"],
            consistency_level="Strong",
        )
        
        assert len(entity_query_result) == 2, f"Expected 2 entities in Vector DB, got {len(entity_query_result)}"
        entity_names_vdb = {e["name"] for e in entity_query_result}
        assert entity_names_vdb == {"SEO", "Website Traffic"}, f"Entity names in Vector DB mismatch: {entity_names_vdb}"
        
        # Query relations using async_get_items
        relation_query_result = await milvus_client.async_get_items(
            ids=[relation_id],
            collection_name="RelationDescriptions",
            output_fields=["id", "relation_type", "description"],
            consistency_level="Strong",
        )
        
        assert len(relation_query_result) == 1, f"Expected 1 relation in Vector DB, got {len(relation_query_result)}"
        assert relation_query_result[0]["relation_type"] == "increases"
        
        print("✓ Vector DB verification passed: 2 entities, 1 relation found via get_items")

        print("✓ Dual storage consistency verified")

    finally:
        triples_path.unlink()


# Manual test runner
if __name__ == "__main__":
    import asyncio

    async def run_tests():
        """Run all tests manually."""
        from shared.database_clients.vector_database.milvus import (
            MilvusVectorDatabase,
        )
        from shared.database_clients.graph_database.falkordb import FalkorDBClient
        from shared.model_clients.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

        # Initialize clients
        milvus = MilvusVectorDatabase(
            config=MilvusConfig(
                host=SETTINGS.MILVUS_HOST,
                port=SETTINGS.MILVUS_PORT,
                user="root",
                password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
            )
        )

        falkor = FalkorDBClient(
            config=FalkorDBConfig(
                host=SETTINGS.FALKORDB_HOST,
                port=SETTINGS.FALKORDB_PORT,
                username=SETTINGS.FALKORDB_USERNAME,
                password=SETTINGS.FALKORDB_PASSWORD,
                graph_name="test_kg",
            )
        )

        embedder_client = GeminiEmbedder(
            config=GeminiEmbedderConfig(
                api_key=SETTINGS.GEMINI_API_KEY,
                model="gemini-embedding-001",
                task_type="SEMANTIC",
                output_dimensionality=SETTINGS.EMBEDDING_DIM,
            )
        )

        try:
            print("\n🧪 Running Knowledge Graph Builder Tests...\n")

            # Test 1: Collection Creation
            await test_collection_creation(milvus)

            # Test 2: Entity Resolution - Duplicates
            await test_entity_resolution_duplicates(milvus, falkor, embedder_client)

            # Test 3: Entity Resolution - Different
            await test_entity_resolution_different(milvus, falkor, embedder_client)

            # Test 4: Dual Storage
            await test_dual_storage_consistency(milvus, falkor, embedder_client)

            print("\n✅ All tests completed!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise

        finally:
            # Cleanup
            try:
                await milvus.async_delete_collection("EntityDescriptions")
                await milvus.async_delete_collection("RelationDescriptions")
            except Exception:
                pass

    asyncio.run(run_tests())
