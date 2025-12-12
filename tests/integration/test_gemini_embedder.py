import pytest
import asyncio
from shared.model_clients.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig, EmbeddingMode

@pytest.mark.asyncio
async def test_gemini_embedder_semantic():
    """Test Gemini embedder in SEMANTIC mode."""
    config = GeminiEmbedderConfig(mode=EmbeddingMode.SEMANTIC)
    embedder = GeminiEmbedder(config)
    
    # Test single text embedding
    text = "This is a test sentence for semantic embedding."
    emb = await embedder.aget_text_embedding(text)
    assert len(emb) == 1536
    
    # Test batch text embedding
    texts = ["Sentence one.", "Sentence two."]
    embs = await embedder.aget_text_embeddings(texts)
    assert len(embs) == 2
    assert len(embs[0]) == 1536
    assert len(embs[1]) == 1536
    
    # Test query embedding (should be same task type as text in SEMANTIC mode)
    query = "Find similar sentences."
    q_emb = await embedder.aget_query_embedding(query)
    assert len(q_emb) == 1536

@pytest.mark.asyncio
async def test_gemini_embedder_retrieval():
    """Test Gemini embedder in RETRIEVAL mode."""
    config = GeminiEmbedderConfig(mode=EmbeddingMode.RETRIEVAL)
    embedder = GeminiEmbedder(config)
    
    # Test document embedding (RETRIEVAL_DOCUMENT task type)
    doc = "This is a document to be retrieved."
    doc_emb = await embedder.aget_text_embedding(doc)
    assert len(doc_emb) == 1536
    
    # Test query embedding (RETRIEVAL_QUERY task type)
    query = "search for document"
    q_emb = await embedder.aget_query_embedding(query)
    assert len(q_emb) == 1536

@pytest.mark.asyncio
async def test_gemini_embedder_normalization():
    """Test manual normalization for non-default dimensions."""
    # Note: 768 is a supported dimension that requires normalization if model default is 3072
    config = GeminiEmbedderConfig(
        mode=EmbeddingMode.SEMANTIC,
        output_dimensionality=768
    )
    embedder = GeminiEmbedder(config)
    
    text = "Normalization test."
    emb = await embedder.aget_text_embedding(text)
    assert len(emb) == 768
    
    # Check if normalized (L2 norm should be close to 1.0)
    import numpy as np
    norm = np.linalg.norm(emb)
    assert abs(norm - 1.0) < 1e-5

@pytest.mark.asyncio
async def test_gemini_embedder_large_batch():
    """Test Gemini embedder with more than 100 items (batch limit)."""
    config = GeminiEmbedderConfig(mode=EmbeddingMode.SEMANTIC)
    embedder = GeminiEmbedder(config)
    
    # Create 105 items
    texts = [f"This is sentence number {i}" for i in range(105)]
    
    # This should fail without chunking, pass with chunking
    embs = await embedder.aget_text_embeddings(texts)
    
    assert len(embs) == 105
    assert len(embs[0]) == 1536
    assert len(embs[-1]) == 1536
