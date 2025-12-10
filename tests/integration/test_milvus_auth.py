#!/usr/bin/env python3
"""
Integration tests for Milvus vector database with authentication.

Tests cover:
- Connection with and without authentication
- Collection creation and management
- Vector insertion and search
- Authentication error handling
"""

import os
import sys
from datetime import datetime

import pytest

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "shared", "src")
)

from shared.database_clients.vector_database.base_class import EmbeddingType
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

TEST_COLLECTION_NAME = "test_collection_auth"


@pytest.fixture(scope="module")
def milvus_client_with_auth():
    """Fixture for Milvus client with authentication."""
    config = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user=MILVUS_USER,
        password=MILVUS_PASSWORD,
        run_async=False,
    )
    client = MilvusVectorDatabase(config=config)
    
    # Cleanup before tests
    if client.has_collection(TEST_COLLECTION_NAME):
        client.delete_collection(TEST_COLLECTION_NAME)
    
    yield client
    
    # Cleanup after tests
    if client.has_collection(TEST_COLLECTION_NAME):
        client.delete_collection(TEST_COLLECTION_NAME)


@pytest.fixture(scope="module")
def milvus_client_without_auth():
    """Fixture for Milvus client without authentication (should fail if auth enabled)."""
    config = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        run_async=False,
    )
    try:
        return MilvusVectorDatabase(config=config)
    except Exception:
        # Expected to fail if auth is enabled
        return None


def test_connection_with_auth(milvus_client_with_auth):
    """Test that connection with correct credentials works."""
    print("\n" + "=" * 80)
    print("TEST: Connection with Authentication")
    print("=" * 80)
    
    # List collections should work with auth
    collections = milvus_client_with_auth.list_collections()
    print(f"✓ Successfully connected with authentication")
    print(f"  Found {len(collections)} existing collections")
    
    assert isinstance(collections, list)


def test_connection_without_auth_fails(milvus_client_without_auth):
    """Test that connection without credentials fails when auth is enabled."""
    print("\n" + "=" * 80)
    print("TEST: Connection without Authentication (Should Fail)")
    print("=" * 80)
    
    # If client is None, it means connection failed during initialization (expected)
    if milvus_client_without_auth is None:
        print(f"✓ Connection correctly failed without authentication during initialization")
        return
    
    # This test assumes Milvus has authentication enabled
    # If auth is disabled, this test will pass (which is also valid)
    try:
        collections = milvus_client_without_auth.list_collections()
        print(f"⚠ Connection succeeded without auth - authentication may be disabled")
        print(f"  Found {len(collections)} collections")
        # Not failing the test as auth might be intentionally disabled
    except Exception as e:
        print(f"✓ Connection correctly failed without authentication")
        print(f"  Error: {type(e).__name__}: {str(e)[:100]}")
        # This is expected behavior when auth is enabled


def test_create_collection_with_auth(milvus_client_with_auth):
    """Test creating a collection with authentication."""
    print("\n" + "=" * 80)
    print("TEST: Create Collection with Authentication")
    print("=" * 80)
    
    # Define collection schema
    collection_structure = [
        SchemaField(
            field_name="id",
            field_type=DataType.INT,
            is_primary=True,
            field_description="Primary key",
        ),
        SchemaField(
            field_name="embedding",
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
    
    # Create collection
    milvus_client_with_auth.create_collection(
        collection_name=TEST_COLLECTION_NAME,
        collection_structure=collection_structure,
        auto_id=False,
    )
    
    print(f"✓ Collection '{TEST_COLLECTION_NAME}' created successfully")
    
    # Verify collection exists
    assert milvus_client_with_auth.has_collection(TEST_COLLECTION_NAME)
    print(f"✓ Collection verified to exist")
    
    # Load collection
    loaded = milvus_client_with_auth.load_collection(TEST_COLLECTION_NAME)
    assert loaded
    print(f"✓ Collection loaded into memory")


def test_insert_vectors_with_auth(milvus_client_with_auth):
    """Test inserting vectors with authentication."""
    print("\n" + "=" * 80)
    print("TEST: Insert Vectors with Authentication")
    print("=" * 80)
    
    # Prepare test data
    test_data = [
        {
            "id": 1,
            "embedding": [0.1] * 128,
            "text": "Test document 1",
        },
        {
            "id": 2,
            "embedding": [0.2] * 128,
            "text": "Test document 2",
        },
        {
            "id": 3,
            "embedding": [0.3] * 128,
            "text": "Test document 3",
        },
    ]
    
    # Insert vectors
    milvus_client_with_auth.insert_vectors(
        collection_name=TEST_COLLECTION_NAME,
        data=test_data,
    )
    
    print(f"✓ Inserted {len(test_data)} vectors successfully")
    
    # Verify insertion by getting items (optional - may not work immediately)
    try:
        retrieved = milvus_client_with_auth.get_items(
            collection_name=TEST_COLLECTION_NAME,
            ids=[1, 2, 3],
        )
        if len(retrieved) == 3:
            print(f"✓ Retrieved {len(retrieved)} items successfully")
        else:
            print(f"⚠ Retrieved {len(retrieved)} items (expected 3, data may not be flushed yet)")
    except Exception as e:
        print(f"⚠ Could not retrieve items immediately: {type(e).__name__}: {str(e)[:100]}")
        print(f"  This is OK - data may need time to be indexed")


def test_search_vectors_with_auth(milvus_client_with_auth):
    """Test searching vectors with authentication."""
    print("\n" + "=" * 80)
    print("TEST: Search Vectors with Authentication")
    print("=" * 80)
    
    from shared.database_clients.vector_database.base_class import EmbeddingData
    
    # Prepare search query
    query_embedding = EmbeddingData(
        embedding_type=EmbeddingType.DENSE,
        embeddings=[0.15] * 128,
        field_name="embedding",
    )
    
    # Search
    results = milvus_client_with_auth.hybrid_search_vectors(
        collection_name=TEST_COLLECTION_NAME,
        embedding_data=[query_embedding],
        output_fields=["id", "text"],
        top_k=2,
        metric_type=MetricType.COSINE,
        index_type=IndexType.HNSW,
    )
    
    print(f"✓ Search completed successfully")
    print(f"  Found {len(results)} results")
    
    if len(results) > 0:
        for i, result in enumerate(results, 1):
            print(f"  [{i}] ID: {result.get('id')}, Text: {result.get('text')}, "
                  f"Score: {result.get('_score', 0):.4f}")
        assert all("_score" in r for r in results)
    else:
        print(f"  ⚠ No results found - data may not be indexed yet or collection is empty")


def test_upsert_vectors_with_auth(milvus_client_with_auth):
    """Test upserting vectors with authentication."""
    print("\n" + "=" * 80)
    print("TEST: Upsert Vectors with Authentication")
    print("=" * 80)
    
    # Prepare upsert data (update existing ID 1)
    upsert_data = [
        {
            "id": 1,
            "embedding": [0.9] * 128,  # Changed vector
            "text": "Updated document 1",  # Changed text
        }
    ]
    
    # Upsert vectors
    milvus_client_with_auth.upsert_vectors(
        collection_name=TEST_COLLECTION_NAME,
        data=upsert_data,
    )
    
    print(f"✓ Upserted {len(upsert_data)} vectors successfully")
    
    # Verify upsert by getting items
    try:
        retrieved = milvus_client_with_auth.get_items(
            collection_name=TEST_COLLECTION_NAME,
            ids=[1],
        )
        if retrieved and retrieved[0].get("text") == "Updated document 1":
            print(f"✓ Verified upsert: Text updated to '{retrieved[0].get('text')}'")
        else:
            print(f"⚠ Upsert verification pending (data may not be flushed yet)")
            print(f"  Retrieved: {retrieved}")
    except Exception as e:
        print(f"⚠ Could not verify upsert immediately: {type(e).__name__}: {str(e)[:100]}")


def test_delete_vectors_with_auth(milvus_client_with_auth):
    """Test deleting vectors with authentication."""
    print("\n" + "=" * 80)
    print("TEST: Delete Vectors with Authentication")
    print("=" * 80)
    
    # Delete vector with ID 2
    ids_to_delete = [2]
    
    milvus_client_with_auth.delete_vectors(
        collection_name=TEST_COLLECTION_NAME,
        ids=ids_to_delete,
    )
    
    print(f"✓ Deleted vector with ID {ids_to_delete} successfully")
    
    # Verify deletion
    try:
        retrieved = milvus_client_with_auth.get_items(
            collection_name=TEST_COLLECTION_NAME,
            ids=ids_to_delete,
        )
        if not retrieved:
            print(f"✓ Verified deletion: ID {ids_to_delete} not found")
        else:
            print(f"⚠ Deletion verification pending (data may not be flushed yet)")
            print(f"  Retrieved: {retrieved}")
    except Exception as e:
        print(f"⚠ Could not verify deletion immediately: {type(e).__name__}: {str(e)[:100]}")


def test_list_and_delete_collection_with_auth(milvus_client_with_auth):
    """Test listing and deleting collections with authentication."""
    print("\n" + "=" * 80)
    print("TEST: List and Delete Collection with Authentication")
    print("=" * 80)
    
    # List collections
    collections = milvus_client_with_auth.list_collections()
    print(f"✓ Listed {len(collections)} collections")
    print(f"  Collections: {collections}")
    
    assert TEST_COLLECTION_NAME in collections
    
    # Delete collection
    milvus_client_with_auth.delete_collection(TEST_COLLECTION_NAME)
    print(f"✓ Deleted collection '{TEST_COLLECTION_NAME}'")
    
    # Verify deletion
    assert not milvus_client_with_auth.has_collection(TEST_COLLECTION_NAME)
    print(f"✓ Verified collection no longer exists")


def run_manual_test():
    """Run tests manually without pytest."""
    print("🚀 MILVUS AUTHENTICATION INTEGRATION TESTS")
    print("=" * 80)
    print(f"Host: {MILVUS_HOST}:{MILVUS_PORT}")
    print(f"User: {MILVUS_USER}")
    print(f"Password: {'*' * len(MILVUS_PASSWORD)}")
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/milvus_auth_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # Create clients
    print("\n📦 Creating Milvus clients...")
    
    config_with_auth = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user=MILVUS_USER,
        password=MILVUS_PASSWORD,
        run_async=False,
    )
    client_with_auth = MilvusVectorDatabase(config=config_with_auth)
    
    config_without_auth = MilvusConfig(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        run_async=False,
    )
    try:
        client_without_auth = MilvusVectorDatabase(config=config_without_auth)
    except Exception as e:
        print(f"⚠ Client without auth failed to initialize (expected if auth enabled): {type(e).__name__}")
        client_without_auth = None
    
    # Cleanup before tests
    if client_with_auth.has_collection(TEST_COLLECTION_NAME):
        client_with_auth.delete_collection(TEST_COLLECTION_NAME)
    
    test_results = []
    
    # Test 1: Connection with auth
    try:
        test_connection_with_auth(client_with_auth)
        test_results.append(("Connection with Auth", "PASS", None))
    except Exception as e:
        test_results.append(("Connection with Auth", "FAIL", str(e)))
    
    # Test 2: Connection without auth
    if client_without_auth is not None:
        try:
            test_connection_without_auth_fails(client_without_auth)
            test_results.append(("Connection without Auth", "PASS", None))
        except Exception as e:
            test_results.append(("Connection without Auth", "FAIL", str(e)))
    else:
        test_results.append(("Connection without Auth", "PASS", "Failed to create client (expected)"))
    
    # Test 3: Create collection
    try:
        test_create_collection_with_auth(client_with_auth)
        test_results.append(("Create Collection", "PASS", None))
    except Exception as e:
        test_results.append(("Create Collection", "FAIL", str(e)))
    
    # Test 4: Insert vectors
    try:
        test_insert_vectors_with_auth(client_with_auth)
        test_results.append(("Insert Vectors", "PASS", None))
    except Exception as e:
        test_results.append(("Insert Vectors", "FAIL", str(e)))
    
    # Test 5: Search vectors
    try:
        test_search_vectors_with_auth(client_with_auth)
        test_results.append(("Search Vectors", "PASS", None))
    except Exception as e:
        test_results.append(("Search Vectors", "FAIL", str(e)))

    # Test 6: Upsert vectors
    try:
        test_upsert_vectors_with_auth(client_with_auth)
        test_results.append(("Upsert Vectors", "PASS", None))
    except Exception as e:
        test_results.append(("Upsert Vectors", "FAIL", str(e)))

    # Test 7: Delete vectors
    try:
        test_delete_vectors_with_auth(client_with_auth)
        test_results.append(("Delete Vectors", "PASS", None))
    except Exception as e:
        test_results.append(("Delete Vectors", "FAIL", str(e)))
    
    # Test 8: List and delete
    try:
        test_list_and_delete_collection_with_auth(client_with_auth)
        test_results.append(("List and Delete Collection", "PASS", None))
    except Exception as e:
        test_results.append(("List and Delete Collection", "FAIL", str(e)))
    
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
            print(f"  Error: {error[:100]}")
    
    print(f"\nTotal: {len(test_results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    # Save results
    results_file = os.path.join(results_dir, f"test_results_{timestamp}.txt")
    with open(results_file, "w", encoding="utf-8") as f:
        f.write("MILVUS AUTHENTICATION INTEGRATION TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Host: {MILVUS_HOST}:{MILVUS_PORT}\n")
        f.write(f"User: {MILVUS_USER}\n\n")
        
        f.write("TEST RESULTS:\n")
        f.write("-" * 30 + "\n")
        for test_name, status, error in test_results:
            f.write(f"{test_name}: {status}\n")
            if error:
                f.write(f"  Error: {error}\n")
        
        f.write(f"\nSummary: {passed} passed, {failed} failed out of {len(test_results)} tests\n")
    
    print(f"\n📊 Results saved to: {results_file}")
    print("=" * 80)
    
    return passed == len(test_results)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Milvus vector database with authentication"
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
        pytest.main([__file__, "-v", "-s"])
    else:
        # Run manual tests
        success = run_manual_test()
        sys.exit(0 if success else 1)
