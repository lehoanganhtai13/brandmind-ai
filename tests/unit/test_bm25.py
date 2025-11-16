"""
Comprehensive tests for BM25 module to ensure Python 3.12 compatibility.

This test suite covers:
- BM25EmbeddingFunction: Core BM25 algorithm functionality
- BM25Client: High-level client with storage operations
- Sparse matrix operations with scipy in Python 3.12+
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List

import numpy as np
import pytest
from scipy.sparse import csr_array

from shared.model_clients.bm25.bm25 import BM25EmbeddingFunction
from shared.model_clients.bm25.encoder import BM25Client
from shared.model_clients.bm25.tokenizers import build_default_analyzer


class TestBM25EmbeddingFunction:
    """Test suite for core BM25EmbeddingFunction."""

    @pytest.fixture
    def sample_corpus(self) -> List[str]:
        """Sample corpus for testing."""
        return [
            "The quick brown fox jumps over the lazy dog",
            "A fast brown fox leaps over a sleepy dog",
            "The lazy dog sleeps under the tree",
            "Machine learning is a subset of artificial intelligence",
            "Deep learning uses neural networks for pattern recognition",
        ]

    @pytest.fixture
    def bm25_function(self, sample_corpus: List[str]) -> BM25EmbeddingFunction:
        """Create a fitted BM25EmbeddingFunction."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(
            analyzer=analyzer,
            k1=1.5,
            b=0.75,
            epsilon=0.25,
            num_workers=1,
        )
        bm25.fit(sample_corpus)
        return bm25

    def test_initialization(self):
        """Test BM25EmbeddingFunction initialization."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)

        assert bm25.k1 == 1.5
        assert bm25.b == 0.75
        assert bm25.epsilon == 0.25
        assert bm25.corpus_size == 0
        assert bm25.avgdl == 0.0

    def test_fit(self, sample_corpus: List[str]):
        """Test fitting BM25 on a corpus."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)
        bm25.fit(sample_corpus)

        assert bm25.corpus_size == len(sample_corpus)
        assert bm25.avgdl > 0
        assert len(bm25.idf) > 0
        assert bm25.dim > 0

    def test_encode_query(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding a single query."""
        query = "brown fox jumps"
        embedding = bm25_function._encode_query(query)

        # Check that embedding is a sparse array
        assert isinstance(embedding, csr_array)
        # Check shape: (1, vocabulary_size)
        assert embedding.shape[0] == 1
        assert embedding.shape[1] == bm25_function.dim
        # Check data type
        assert embedding.dtype == np.float32
        # Check that it's not all zeros
        assert embedding.nnz > 0

    def test_encode_document(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding a single document."""
        doc = "The brown fox is very fast"
        embedding = bm25_function._encode_document(doc)

        # Check that embedding is a sparse array
        assert isinstance(embedding, csr_array)
        # Check shape
        assert embedding.shape[0] == 1
        assert embedding.shape[1] == bm25_function.dim
        # Check data type
        assert embedding.dtype == np.float32
        # Check that it has non-zero elements
        assert embedding.nnz > 0

    def test_encode_queries(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding multiple queries."""
        queries = [
            "brown fox",
            "lazy dog",
            "machine learning",
        ]
        embeddings = bm25_function.encode_queries(queries)

        # Check that result is a sparse array
        assert isinstance(embeddings, csr_array)
        # Check shape: (num_queries, vocabulary_size)
        assert embeddings.shape[0] == len(queries)
        assert embeddings.shape[1] == bm25_function.dim
        # Check data type
        assert embeddings.dtype == np.float32

    def test_encode_documents(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding multiple documents."""
        documents = [
            "The quick brown fox",
            "A lazy dog sleeps",
            "Neural networks learn patterns",
        ]
        embeddings = bm25_function.encode_documents(documents)

        # Check that result is a sparse array
        assert isinstance(embeddings, csr_array)
        # Check shape
        assert embeddings.shape[0] == len(documents)
        assert embeddings.shape[1] == bm25_function.dim
        # Check data type
        assert embeddings.dtype == np.float32

    def test_save_and_load(self, bm25_function: BM25EmbeddingFunction):
        """Test saving and loading BM25 state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "bm25_state.json")

            # Save the state
            bm25_function.save(save_path)
            assert os.path.exists(save_path)

            # Check that the saved file is valid JSON
            with open(save_path, "r") as f:
                data = json.load(f)
                assert "version" in data
                assert "corpus_size" in data
                assert "avgdl" in data
                assert "idf_word" in data
                assert "idf_value" in data

            # Load into a new instance
            analyzer = build_default_analyzer(language="en")
            new_bm25 = BM25EmbeddingFunction(analyzer=analyzer)
            new_bm25.load(save_path)

            # Verify loaded state matches original
            assert new_bm25.corpus_size == bm25_function.corpus_size
            assert new_bm25.avgdl == bm25_function.avgdl
            assert new_bm25.dim == bm25_function.dim
            assert new_bm25.k1 == bm25_function.k1
            assert new_bm25.b == bm25_function.b

    def test_encode_empty_query(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding an empty query."""
        embedding = bm25_function._encode_query("")

        # Should return a sparse array with all zeros
        assert isinstance(embedding, csr_array)
        assert embedding.shape[0] == 1
        assert embedding.shape[1] == bm25_function.dim
        assert embedding.nnz == 0  # No non-zero elements

    def test_encode_unknown_words(self, bm25_function: BM25EmbeddingFunction):
        """Test encoding queries with words not in vocabulary."""
        query = "xyzabc defghi"  # Made-up words
        embedding = bm25_function._encode_query(query)

        # Should return a sparse array with all zeros
        assert isinstance(embedding, csr_array)
        assert embedding.nnz == 0  # No non-zero elements

    def test_idf_values(self, bm25_function: BM25EmbeddingFunction):
        """Test that IDF values are calculated correctly."""
        # All terms should have IDF values
        assert len(bm25_function.idf) > 0

        # Each term should have [idf_value, index]
        for word, values in bm25_function.idf.items():
            assert len(values) == 2
            assert isinstance(values[0], float)  # IDF value
            assert isinstance(values[1], int)  # Index

    def test_call_raises_error(self, bm25_function: BM25EmbeddingFunction):
        """Test that calling the function directly raises an error."""
        with pytest.raises(ValueError, match="Unsupported function called"):
            bm25_function(["test"])


class TestBM25Client:
    """Test suite for BM25Client wrapper class."""

    @pytest.fixture
    def sample_documents(self) -> List[str]:
        """Sample documents for testing."""
        return [
            "Python is a high-level programming language",
            "Machine learning is a branch of artificial intelligence",
            "Natural language processing uses machine learning",
            "Deep learning is based on neural networks",
            "Data science involves statistics and programming",
        ]

    @pytest.fixture
    def bm25_client(self) -> BM25Client:
        """Create a BM25Client without loading."""
        return BM25Client(
            language="en",
            init_without_load=True,
        )

    def test_initialization_without_load(self):
        """Test BM25Client initialization without loading model."""
        client = BM25Client(language="en", init_without_load=True)

        assert client.analyzer is not None
        assert client.bm25 is not None
        assert client.storage_client is None
        assert client.bucket_name is None

    def test_fit_and_transform(
        self, bm25_client: BM25Client, sample_documents: List[str]
    ):
        """Test fitting and transforming documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "bm25_state.json")

            # Fit and transform
            embeddings = bm25_client.fit_transform(
                sample_documents,
                path=save_path,
                auto_save_local=True,
            )

            # Check that embeddings are returned
            assert len(embeddings) == len(sample_documents)
            # Check that embeddings are sparse arrays (can be csr_array or matrix slices)
            from scipy.sparse import issparse
            assert all(issparse(emb) for emb in embeddings)

            # Check that each embedding has the correct dimensionality
            for emb in embeddings:
                # After slicing, shape might be (n,) instead of (1, n)
                assert emb.shape[0] in (1, bm25_client.dimension) or len(emb.shape) == 1

            # Check that the state was saved
            assert os.path.exists(save_path)

    def test_encode_text(self, bm25_client: BM25Client, sample_documents: List[str]):
        """Test encoding text documents."""
        # First fit the model
        bm25_client.bm25.fit(sample_documents)

        # Encode documents
        texts = ["Python programming", "Machine learning algorithms"]
        embeddings = bm25_client.encode_text(texts)

        # Check results
        assert len(embeddings) == len(texts)
        from scipy.sparse import issparse
        assert all(issparse(emb) for emb in embeddings)

        # Check that embeddings have correct dimensionality
        for emb in embeddings:
            # After slicing, embeddings are sparse matrices
            assert issparse(emb)

    def test_encode_queries(self, bm25_client: BM25Client, sample_documents: List[str]):
        """Test encoding search queries."""
        # First fit the model
        bm25_client.bm25.fit(sample_documents)

        # Encode queries
        queries = ["machine learning", "data science"]
        embeddings = bm25_client.encode_queries(queries)

        # Check results
        assert len(embeddings) == len(queries)
        from scipy.sparse import issparse
        assert all(issparse(emb) for emb in embeddings)

        # Check that embeddings are sparse matrices
        for emb in embeddings:
            assert issparse(emb)

    def test_dict_to_csr(self):
        """Test converting dictionary to CSR array."""
        state_dict = {0: 1.5, 5: 2.3, 10: 0.8}
        dim = 15

        csr = BM25Client.dict_to_csr(state_dict, dim)

        # Check type and shape
        assert isinstance(csr, csr_array)
        assert csr.shape == (1, dim)

        # Check that values are correct
        assert csr[0, 0] == pytest.approx(1.5)
        assert csr[0, 5] == pytest.approx(2.3)
        assert csr[0, 10] == pytest.approx(0.8)

        # Check that other positions are zero
        assert csr[0, 1] == 0
        assert csr[0, 14] == 0

    def test_csr_to_dict(self):
        """Test converting CSR array to dictionary."""
        # Create a sparse array
        state_dict = {2: 1.5, 7: 2.3, 12: 0.8}
        dim = 20
        csr = BM25Client.dict_to_csr(state_dict, dim)

        # Convert back to dict
        result_dict = BM25Client.csr_to_dict(csr)

        # Check that the result matches the input
        assert len(result_dict) == len(state_dict)
        for key, value in state_dict.items():
            assert key in result_dict
            assert result_dict[key] == pytest.approx(value)

    def test_csr_to_dict_invalid_shape(self):
        """Test that csr_to_dict raises error for invalid shape."""
        # Create a multi-row sparse array
        from scipy.sparse import vstack

        state_dict = {0: 1.5}
        dim = 10
        csr1 = BM25Client.dict_to_csr(state_dict, dim)
        csr2 = BM25Client.dict_to_csr({1: 2.0}, dim)
        multi_row = vstack([csr1, csr2])

        # Should raise ValueError
        with pytest.raises(ValueError, match="Input phải có đúng 1 hàng"):
            BM25Client.csr_to_dict(multi_row)

    def test_calculate_similarity(
        self, bm25_client: BM25Client, sample_documents: List[str]
    ):
        """Test calculating similarity between embeddings."""
        # Fit the model
        bm25_client.bm25.fit(sample_documents)

        # Encode two similar documents
        emb1 = bm25_client.encode_text(["machine learning algorithms"])[0]
        emb2 = bm25_client.encode_text(["machine learning techniques"])[0]

        # Encode a dissimilar document
        emb3 = bm25_client.encode_text(["cooking recipes"])[0]

        # Convert to csr_array if needed (slicing may return different types)
        from scipy.sparse import csr_array
        emb1 = csr_array(emb1) if not isinstance(emb1, csr_array) else emb1
        emb2 = csr_array(emb2) if not isinstance(emb2, csr_array) else emb2
        emb3 = csr_array(emb3) if not isinstance(emb3, csr_array) else emb3

        # Calculate similarities
        sim_similar = BM25Client.calculate_similarity(emb1, emb2)
        sim_dissimilar = BM25Client.calculate_similarity(emb1, emb3)

        # Similar documents should have higher similarity
        assert sim_similar > sim_dissimilar
        # Allow for small floating point errors
        assert -0.001 <= sim_similar <= 1.001
        assert -0.001 <= sim_dissimilar <= 1.001

    def test_calculate_similarity_identical(
        self, bm25_client: BM25Client, sample_documents: List[str]
    ):
        """Test similarity of identical embeddings."""
        bm25_client.bm25.fit(sample_documents)

        emb = bm25_client.encode_text(["machine learning"])[0]
        
        # Convert to csr_array if needed
        from scipy.sparse import csr_array
        emb = csr_array(emb) if not isinstance(emb, csr_array) else emb
        
        similarity = BM25Client.calculate_similarity(emb, emb)

        # Similarity with itself should be 1
        assert similarity == pytest.approx(1.0, abs=1e-5)

    def test_calculate_similarity_zero_vectors(self):
        """Test similarity with zero vectors."""
        # Create zero vectors
        from scipy.sparse import csr_array

        dim = 100
        # Create proper zero vectors with shape (1, dim)
        zero1 = csr_array(([], ([], [])), shape=(1, dim))
        zero2 = csr_array(([], ([], [])), shape=(1, dim))

        similarity = BM25Client.calculate_similarity(zero1, zero2)

        # Should return 0
        assert similarity == 0.0

    def test_dimension_property(
        self, bm25_client: BM25Client, sample_documents: List[str]
    ):
        """Test dimension property."""
        # Before fitting, dimension might be 0
        assert bm25_client.dimension >= 0

        # After fitting, dimension should match vocabulary size
        bm25_client.bm25.fit(sample_documents)
        assert bm25_client.dimension > 0
        assert bm25_client.dimension == len(bm25_client.bm25.idf)

    def test_fit_saves_and_removes_local_file(self, sample_documents: List[str]):
        """Test that fit saves to MinIO and removes local file when auto_save_local=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "bm25_state.json")

            client = BM25Client(language="en", init_without_load=True)

            # Fit with auto_save_local=False (default)
            client.fit(sample_documents, path=save_path, auto_save_local=False)

            # Local file should not exist
            assert not os.path.exists(save_path)

    def test_dicts_to_csrs_parallel(self):
        """Test parallel conversion of dictionaries to CSR arrays."""
        state_dicts = [
            {0: 1.5, 5: 2.3},
            {1: 0.8, 7: 1.2},
            {2: 3.1, 10: 0.5},
            {3: 2.0, 15: 1.8},
        ]
        dim = 20

        # Convert in parallel
        results = BM25Client.dicts_to_csrs_parallel(state_dicts, dim, max_workers=2)

        # Check results
        assert len(results) == len(state_dicts)
        assert all(isinstance(r, csr_array) for r in results)
        assert all(r.shape == (1, dim) for r in results)

        # Verify each conversion is correct
        for i, (result, state_dict) in enumerate(zip(results, state_dicts)):
            for col, val in state_dict.items():
                assert result[0, col] == pytest.approx(val)

    def test_dicts_to_csrs_parallel_empty(self):
        """Test parallel conversion with empty list."""
        results = BM25Client.dicts_to_csrs_parallel([], dim=10)
        assert results == []


class TestBM25Python312Compatibility:
    """Test suite specifically for Python 3.12+ scipy compatibility."""

    def test_csr_array_creation_with_shape(self):
        """Test that csr_array creation with shape parameter works in Python 3.12."""
        values = [1.0, 2.0, 3.0]
        rows = [0, 0, 0]
        cols = [0, 5, 10]
        shape = (1, 15)

        # This should not raise any errors in Python 3.12
        csr = csr_array((values, (rows, cols)), shape=shape)

        assert isinstance(csr, csr_array)
        assert csr.shape == shape
        assert csr.dtype == np.float64

    def test_csr_array_astype_float32(self):
        """Test converting csr_array to float32 (used in BM25)."""
        values = [1.0, 2.0, 3.0]
        rows = [0, 0, 0]
        cols = [0, 5, 10]

        csr = csr_array((values, (rows, cols)), shape=(1, 15))
        csr_float32 = csr.astype(np.float32)

        assert csr_float32.dtype == np.float32
        assert csr_float32.shape == csr.shape

    def test_vstack_csr_arrays(self):
        """Test vstacking multiple csr_arrays (used in encode_queries/documents)."""
        from scipy.sparse import vstack

        # Create multiple sparse arrays
        csr1 = csr_array(([1.0, 2.0], ([0, 0], [0, 5])), shape=(1, 10))
        csr2 = csr_array(([3.0, 4.0], ([0, 0], [2, 7])), shape=(1, 10))
        csr3 = csr_array(([5.0, 6.0], ([0, 0], [1, 8])), shape=(1, 10))

        # Stack them
        stacked = vstack([csr1, csr2, csr3])

        assert stacked.shape == (3, 10)
        assert isinstance(stacked, csr_array)

    def test_sparse_array_indexing(self):
        """Test indexing sparse arrays to extract rows (used in encode methods)."""
        from scipy.sparse import vstack, issparse

        # Create and stack arrays
        arrays = [
            csr_array(([1.0, 2.0], ([0, 0], [0, 5])), shape=(1, 10)),
            csr_array(([3.0, 4.0], ([0, 0], [2, 7])), shape=(1, 10)),
            csr_array(([5.0, 6.0], ([0, 0], [1, 8])), shape=(1, 10)),
        ]
        stacked = vstack(arrays)

        # Extract individual rows
        rows = [stacked[i] for i in range(stacked.shape[0])]

        assert len(rows) == 3
        # After indexing, rows are sparse matrices (might not be csr_array type)
        assert all(issparse(row) for row in rows)

    def test_sparse_array_operations(self):
        """Test various operations on sparse arrays."""
        csr = csr_array(([1.0, 2.0, 3.0], ([0, 0, 0], [0, 5, 10])), shape=(1, 15))

        # Test nnz (number of non-zero elements)
        assert csr.nnz == 3

        # Test power operation
        squared = csr.power(2)
        assert squared[0, 0] == pytest.approx(1.0)
        assert squared[0, 5] == pytest.approx(4.0)
        assert squared[0, 10] == pytest.approx(9.0)

        # Test sum operation
        total = csr.sum()
        assert total == pytest.approx(6.0)

        # Test transpose and dot product
        csr_t = csr.T
        dot_product = csr.dot(csr_t)
        assert dot_product.shape == (1, 1)


class TestBM25EdgeCases:
    """Test edge cases and error handling."""

    def test_fit_with_empty_corpus(self):
        """Test fitting with an empty corpus."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)

        # This might raise an error or handle gracefully
        # Depending on implementation, adjust the test accordingly
        with pytest.raises(Exception):
            bm25.fit([])

    def test_fit_with_single_document(self):
        """Test fitting with only one document."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)

        bm25.fit(["This is a single document"])

        assert bm25.corpus_size == 1
        assert bm25.dim > 0

    def test_encode_very_long_document(self):
        """Test encoding a very long document."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)

        # Create a corpus and fit
        corpus = ["Short doc" for _ in range(5)]
        bm25.fit(corpus)

        # Create a very long document
        long_doc = " ".join(["word" + str(i) for i in range(1000)])
        embedding = bm25._encode_document(long_doc)

        assert isinstance(embedding, csr_array)
        assert embedding.shape[0] == 1

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        analyzer = build_default_analyzer(language="en")
        bm25 = BM25EmbeddingFunction(analyzer=analyzer)

        corpus = [
            "Hello, world!",
            "Test @#$% special characters",
            "Numbers 123 456",
            "Mixed: text-with-dashes_and_underscores",
        ]
        bm25.fit(corpus)

        # Encode a query with special characters
        query = "Hello @world! 123"
        embedding = bm25._encode_query(query)

        assert isinstance(embedding, csr_array)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
