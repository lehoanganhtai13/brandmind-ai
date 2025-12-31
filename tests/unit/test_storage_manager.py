import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.knowledge_graph.curator.storage_manager import StorageManager

@pytest.fixture
def mock_graph_db():
    return AsyncMock()

@pytest.fixture
def mock_vector_db():
    return AsyncMock()

@pytest.fixture
def mock_embedder():
    return AsyncMock()

@pytest.fixture
def storage_manager(mock_graph_db, mock_vector_db, mock_embedder):
    return StorageManager(
        graph_db=mock_graph_db,
        vector_db=mock_vector_db,
        embedder=mock_embedder
    )

@pytest.mark.asyncio
async def test_create_relation_new(storage_manager, mock_graph_db, mock_vector_db):
    """Test creating a NEW relation (should generate new UUID)."""
    
    # Mock check_query to return empty result (relation does not exist)
    mock_graph_db.async_execute_query.return_value.result_set = []

    result = await storage_manager.create_relation(
        source_entity_id="source-123",
        source_entity_type="Brand",
        target_entity_id="target-456",
        target_entity_type="Product",
        relation_type="HAS_PRODUCT",
        description="Brand has product",
        desc_embedding=[0.1, 0.2],
        source_chunk_id="chunk-789"
    )

    # Verify check query was called
    mock_graph_db.async_execute_query.assert_called()
    
    # Verify new relation created
    assert "relation_id" in result
    relation_id = result["relation_id"]
    
    # Verify Graph DB merge called with new ID
    mock_graph_db.async_merge_relationship.assert_called_once()
    call_args = mock_graph_db.async_merge_relationship.call_args[1]
    assert call_args["properties"]["vector_db_ref_id"] == relation_id
    
    # Verify Vector DB upsert called with same ID
    mock_vector_db.async_upsert_vectors.assert_called_once()
    vector_call_args = mock_vector_db.async_upsert_vectors.call_args[1]
    assert vector_call_args["data"][0]["id"] == relation_id


@pytest.mark.asyncio
async def test_create_relation_existing(storage_manager, mock_graph_db, mock_vector_db):
    """Test creating an EXISTING relation (should reuse UUID)."""
    
    existing_uuid = "existing-uuid-111"
    
    # Mock check_query to return existing UUID
    # Result set format depends on client, assuming list of records
    mock_graph_db.async_execute_query.return_value.result_set = [[existing_uuid]]

    result = await storage_manager.create_relation(
        source_entity_id="source-123",
        source_entity_type="Brand",
        target_entity_id="target-456",
        target_entity_type="Product",
        relation_type="HAS_PRODUCT",
        description="Updated description",
        desc_embedding=[0.1, 0.2],
        source_chunk_id="chunk-new"
    )

    # Verify ID matches existing
    assert result["relation_id"] == existing_uuid
    
    # Verify Graph DB merge uses existing ID
    call_args = mock_graph_db.async_merge_relationship.call_args[1]
    assert call_args["properties"]["vector_db_ref_id"] == existing_uuid
    
    # Verify Vector DB upsert uses existing ID (to update it, not create orphan)
    vector_call_args = mock_vector_db.async_upsert_vectors.call_args[1]
    assert vector_call_args["data"][0]["id"] == existing_uuid
