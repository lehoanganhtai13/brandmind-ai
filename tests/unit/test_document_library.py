import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from core.knowledge_graph.curator.document_library import build_document_library, DOCUMENT_CHUNKS_SCHEMA, DOCUMENT_CHUNKS_BM25_CONFIG
from shared.database_clients.vector_database.base_vector_database import BaseVectorDatabase
from shared.model_clients.embedder.base_embedder import BaseEmbedder

@pytest.fixture
def mock_vector_db():
    db = MagicMock(spec=BaseVectorDatabase)
    db.async_has_collection = AsyncMock(return_value=False)
    db.async_create_collection = AsyncMock()
    db.async_insert_vectors = AsyncMock()
    return db

@pytest.fixture
def mock_embedder():
    embedder = MagicMock(spec=BaseEmbedder)
    # Return dummy embeddings (list of floats) matching input length
    def side_effect(texts, **kwargs):
        return [[0.1] * 1536] * len(texts)
    
    embedder.aget_text_embeddings = AsyncMock(side_effect=side_effect)
    return embedder

@pytest.fixture
def chunks_file(tmp_path):
    file_path = tmp_path / "chunks.json"
    data = {
        "chunks": [
            {"chunk_id": "1", "content": "Chunk 1", "metadata": {"source": "doc1"}},
            {"chunk_id": "2", "content": "Chunk 2", "metadata": {"source": "doc1"}},
        ]
    }
    with open(file_path, "w") as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def progress_file(tmp_path):
    return tmp_path / "progress.json"

@pytest.mark.asyncio
async def test_build_document_library_creation(mock_vector_db, mock_embedder, chunks_file):
    """Test that collection is created if it doesn't exist."""
    await build_document_library(
        chunks_path=chunks_file,
        vector_db=mock_vector_db,
        embedder=mock_embedder,
        collection_name="TestCollection"
    )
    
    mock_vector_db.async_has_collection.assert_called_with("TestCollection")
    mock_vector_db.async_create_collection.assert_called_with(
        collection_name="TestCollection",
        collection_structure=DOCUMENT_CHUNKS_SCHEMA,
        bm25_function_config=DOCUMENT_CHUNKS_BM25_CONFIG
    )

@pytest.mark.asyncio
async def test_build_document_library_batching(mock_vector_db, mock_embedder, chunks_file):
    """Test batch processing and upsert."""
    stats = await build_document_library(
        chunks_path=chunks_file,
        vector_db=mock_vector_db,
        embedder=mock_embedder,
        batch_size=1 # Force 2 batches
    )
    
    assert stats["embedded"] == 2
    assert stats["upserted"] == 2
    assert mock_embedder.aget_text_embeddings.call_count == 2
    assert mock_vector_db.async_insert_vectors.call_count == 2

@pytest.mark.asyncio
async def test_build_document_library_resume(mock_vector_db, mock_embedder, chunks_file, progress_file):
    """Test resuming from progress file."""
    # Create progress file marking chunk 1 as done
    with open(progress_file, "w") as f:
        json.dump({"processed_ids": ["1"]}, f)
        
    stats = await build_document_library(
        chunks_path=chunks_file,
        vector_db=mock_vector_db,
        embedder=mock_embedder,
        progress_path=progress_file
    )
    
    # Should only process chunk 2
    assert stats["embedded"] == 1 # Only 1 chunk embedded (mock returns 2 items but we pass 1)
    # Wait, mock returns fixed list of 2 embeddings. 
    # If we pass 1 chunk, we expect 1 embedding.
    # We should adjust mock to return list of correct length based on input
    
    # But for this test, we just check call count
    assert mock_embedder.aget_text_embeddings.call_count == 1
    assert mock_vector_db.async_insert_vectors.call_count == 1
    
    # Verify progress file updated
    with open(progress_file, "r") as f:
        progress = json.load(f)
        assert "2" in progress["processed_ids"]
