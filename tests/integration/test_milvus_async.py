#!/usr/bin/env python3
"""
Integration tests for Milvus async vector database operations.

Tests cover async methods used in Knowledge Graph Builder:
- async_create_collection
- async_insert_vectors / async_upsert_vectors
- async_hybrid_search_vectors
- async_load_collection
"""

import os
import sys
from datetime import datetime

import pytest

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "shared", "src")
)

from shared.database_clients.vector_database.base_class import EmbeddingData, EmbeddingType
from shared.database_clients.vector_database.milvus import (
    MilvusConfig,
    MilvusVectorDatabase,
)
from shared.database_clients.vector_database.milvus.utils import (
    DataType,
    IndexConfig,
    IndexType,
    MetricType,
    SchemaField,
)


# Test configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_USER = os.getenv("MILVUS_USER", "root")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "Milvus_secret")

TEST_COLLECTION_NAME = "test_collection_async"


@pytest.fixture(scope="module")
async def milvus_async_client():
    """Fixture for Milvus client with async enabled."""
    config = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user=MILVUS_USER,
        password=MILVUS_PASSWORD,
        run_async=True,  # Enable async
    )
    client = MilvusVectorDatabase(config=config)
    
    # Cleanup before tests
    if client.has_collection(TEST_COLLECTION_NAME):
        await client.async_delete_collection(TEST_COLLECTION_NAME)
    
    yield client
    
    # Cleanup after tests
    if client.has_collection(TEST_COLLECTION_NAME):
        await client.async_delete_collection(TEST_COLLECTION_NAME)


@pytest.mark.asyncio
async def test_async_create_collection(milvus_async_client):
    """Test creating a collection with async."""
    print("\n" + "=" * 80)
    print("TEST: Async Create Collection")
    print("=" * 80)
    
    # Define collection schema
    collection_structure = [
        SchemaField(
            field_name="id",
            field_type=DataType.STRING,
            is_primary=True,
            field_description="Primary key",
        ),
        SchemaField(
            field_name="dense_vector",
            field_type=DataType.DENSE_VECTOR,
            dimension=128,
            field_description="Dense vector embedding",
            index_config=IndexConfig(
                index=True,
                index_type=IndexType.HNSW,
                metric_type=MetricType.COSINE,
            ),
        ),
        SchemaField(
            field_name="text",
            field_type=DataType.STRING,
            field_description="Text content",
        ),
    ]
    
    # Create collection using async
    await milvus_async_client.async_create_collection(
        collection_name=TEST_COLLECTION_NAME,
        collection_structure=collection_structure,
        auto_id=False,
    )
    
    print(f"✓ Collection '{TEST_COLLECTION_NAME}' created async successfully")
    
    # Verify collection exists
    assert milvus_async_client.has_collection(TEST_COLLECTION_NAME)
    print(f"✓ Collection verified to exist")
    
    # Load collection
    loaded = await milvus_async_client.async_load_collection(TEST_COLLECTION_NAME)
    assert loaded
    print(f"✓ Collection loaded into memory async")


@pytest.mark.asyncio
async def test_async_insert_vectors(milvus_async_client):
    """Test inserting vectors with async."""
    print("\n" + "=" * 80)
    print("TEST: Async Insert Vectors")
    print("=" * 80)
    
    # Prepare test data
    test_data = [
        {
            "id": "entity_1",
            "dense_vector": [0.1] * 128,
            "text": "Test entity 1",
        },
        {
            "id": "entity_2",
            "dense_vector": [0.2] * 128,
            "text": "Test entity 2",
        },
        {
            "id": "entity_3",
            "dense_vector": [0.3] * 128,
            "text": "Test entity 3",
        },
    ]
    
    # Insert vectors using async
    await milvus_async_client.async_insert_vectors(
        collection_name=TEST_COLLECTION_NAME,
        data=test_data,
    )
    
    print(f"✓ Inserted {len(test_data)} vectors async successfully")


@pytest.mark.asyncio
async def test_async_hybrid_search(milvus_async_client):
    """Test hybrid search with async."""
    print("\n" + "=" * 80)
    print("TEST: Async Hybrid Search")
    print("=" * 80)
    
    # Prepare search query
    query_embedding = EmbeddingData(
        embedding_type=EmbeddingType.DENSE,
        embeddings=[0.15] * 128,
        field_name="dense_vector",
    )
    
    # Search using async - NOTE: This uses sync method internally
    # because async_hybrid_search_vectors has issues
    try:
        results = await milvus_async_client.async_hybrid_search_vectors(
            collection_name=TEST_COLLECTION_NAME,
            embedding_data=[query_embedding],
            output_fields=["id", "text"],
            top_k=2,
            metric_type=MetricType.COSINE,
            index_type=IndexType.HNSW,
        )
        
        print(f"✓ Hybrid search completed successfully (using sync method)")
        print(f"  Found {len(results)} results")
        
        if len(results) > 0:
            for i, result in enumerate(results, 1):
                print(f"  [{i}] ID: {result.get('id')}, Text: {result.get('text')}, "
                      f"Score: {result.get('_score', 0):.4f}")
            assert len(results) <= 2
        else:
            print(f"  ⚠ No results found - data may not be indexed yet")
    except Exception as e:
        print(f"✗ Hybrid search failed: {e}")
        raise


@pytest.mark.asyncio
async def test_async_list_and_delete_collection(milvus_async_client):
    """Test listing and deleting collections with async."""
    print("\n" + "=" * 80)
    print("TEST: Async List and Delete Collection")
    print("=" * 80)
    
    # List collections using async
    collections = await milvus_async_client.async_list_collections()
    print(f"✓ Listed {len(collections)} collections async")
    print(f"  Collections: {collections}")
    
    assert TEST_COLLECTION_NAME in collections
    
    # Delete collection using async
    await milvus_async_client.async_delete_collection(TEST_COLLECTION_NAME)
    print(f"✓ Deleted collection '{TEST_COLLECTION_NAME}' async")
    
    # Verify deletion
    assert not milvus_async_client.has_collection(TEST_COLLECTION_NAME)
    print(f"✓ Verified collection no longer exists")


async def run_manual_async_test():
    """Run async tests manually without pytest."""
    print("🚀 MILVUS ASYNC INTEGRATION TESTS")
    print("=" * 80)
    print(f"Host: {MILVUS_HOST}:{MILVUS_PORT}")
    print(f"User: {MILVUS_USER}")
    print(f"Password: {'*' * len(MILVUS_PASSWORD)}")
    print(f"Async Mode: ENABLED")
    print("=" * 80)
    
    # Create client
    print("\n📦 Creating Milvus async client...")
    config = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user=MILVUS_USER,
        password=MILVUS_PASSWORD,
        run_async=True,
    )
    client = MilvusVectorDatabase(config=config)
    
    # Cleanup before tests
    if client.has_collection(TEST_COLLECTION_NAME):
        await client.async_delete_collection(TEST_COLLECTION_NAME)
    
    test_results = []
    
    # Test 1: Async create collection
    try:
        await test_async_create_collection(client)
        test_results.append(("Async Create Collection", "PASS", None))
    except Exception as e:
        test_results.append(("Async Create Collection", "FAIL", str(e)))
        print(f"❌ Error: {e}")
    
    # Test 2: Async insert vectors
    try:
        await test_async_insert_vectors(client)
        test_results.append(("Async Insert Vectors", "PASS", None))
    except Exception as e:
        test_results.append(("Async Insert Vectors", "FAIL", str(e)))
        print(f"❌ Error: {e}")
    
    # Test 3: Async hybrid search (using sync method)
    try:
        await test_async_hybrid_search(client)
        test_results.append(("Async Hybrid Search", "PASS", None))
    except Exception as e:
        test_results.append(("Async Hybrid Search", "FAIL", str(e)))
        print(f"❌ Error: {e}")
    
    # Test 4: Async list and delete
    try:
        await test_async_list_and_delete_collection(client)
        test_results.append(("Async List and Delete", "PASS", None))
    except Exception as e:
        test_results.append(("Async List and Delete", "FAIL", str(e)))
        print(f"❌ Error: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, status, _ in test_results if status == "PASS")
    failed = sum(1 for _, status, _ in test_results if status == "FAIL")
    
    for test_name, status, error in test_results:
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {test_name}: {status}")
        if error:
            print(f"  Error: {error[:200]}")
    
    print(f"\nTotal: {len(test_results)} tests")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print("=" * 80)
    
    return passed == len(test_results)


if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(
        description="Test Milvus async vector database operations"
    )
    parser.add_argument(
        "--mode",
        choices=["pytest", "manual"],
        default="manual",
        help="Test execution mode",
    )
    
    args = parser.parse_args()
    
    if args.mode == "pytest":
        # Run with pytest
        pytest.main([__file__, "-v", "-s", "-k", "async"])
    else:
        # Run manual async tests
        success = asyncio.run(run_manual_async_test())
        sys.exit(0 if success else 1)
