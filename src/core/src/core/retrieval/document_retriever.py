"""
Document retriever for hybrid search on Document Library.

This module provides the DocumentRetriever class which combines dense vector
search with BM25 sparse search using Milvus's built-in RRF ranking.
"""

from typing import List, Optional

from core.retrieval.models import DocumentChunkResult
from shared.database_clients.vector_database.base_class import (
    EmbeddingData,
    EmbeddingType,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.database_clients.vector_database.milvus.utils import (
    IndexType,
    MetricType,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder


class DocumentRetriever:
    """
    Hybrid search retriever for the Document Library.

    This retriever performs combined dense vector + BM25 sparse search
    on the DocumentChunks collection using Milvus's built-in RRF (Reciprocal
    Rank Fusion) for result fusion.

    Features:
        - Hybrid search combining semantic (dense) and keyword (BM25) matching
        - Metadata filtering by book, chapter, and author
        - Automatic query embedding using the configured embedder
        - Returns typed DocumentChunkResult objects

    Example:
        >>> retriever = DocumentRetriever(vector_db=milvus, embedder=gemini)
        >>> results = await retriever.search("marketing strategy", top_k=5)
        >>> for chunk in results:
        ...     print(f"{chunk.source}: {chunk.content[:100]}")
    """

    def __init__(
        self,
        vector_db: BaseVectorDatabase,
        embedder: BaseEmbedder,
        collection_name: str = "DocumentChunks",
    ):
        """
        Initialize the document retriever.

        Args:
            vector_db: Vector database client implementing BaseVectorDatabase.
                Should be configured with run_async=True for async operations.
            embedder: Embedder client implementing BaseEmbedder.
                Should use EmbeddingMode.RETRIEVAL for query embedding.
            collection_name: Name of the document chunks collection in Milvus.
                Defaults to "DocumentChunks" as created by Stage 4.
        """
        self.vector_db = vector_db
        self.embedder = embedder
        self.collection_name = collection_name

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_by_book: Optional[str] = None,
        filter_by_chapter: Optional[str] = None,
        filter_by_author: Optional[str] = None,
    ) -> List[DocumentChunkResult]:
        """
        Perform hybrid search on document chunks.

        Executes a combined dense vector + BM25 sparse search with RRF fusion.
        Optionally filters by book, chapter, or author metadata.

        Args:
            query: Search query text. Will be embedded using the configured embedder.
            top_k: Maximum number of results to return. Default 10.
            filter_by_book: Filter by exact book/document name match.
                Example: "Kotler Marketing Management"
            filter_by_chapter: Filter by partial chapter/section match.
                Example: "Chapter 9" will match "Chapter 9 > Section 3"
            filter_by_author: Filter by exact author name match.
                Example: "Philip Kotler"

        Returns:
            List of DocumentChunkResult objects ordered by relevance score.
            Each result contains content, source metadata, and score.
        """
        # 1. Embed query using retrieval mode
        query_embedding = await self.embedder.aget_query_embedding(query)

        # 2. Build Milvus filter expression
        filter_parts = []
        if filter_by_book:
            # Exact match on original_document field
            filter_parts.append(f'original_document == "{filter_by_book}"')
        if filter_by_chapter:
            # Partial match on source field using LIKE
            filter_parts.append(f'source like "%{filter_by_chapter}%"')
        if filter_by_author:
            # Exact match on author field
            filter_parts.append(f'author == "{filter_by_author}"')
        filter_expr = " and ".join(filter_parts) if filter_parts else ""

        # 3. Prepare hybrid search data (dense + sparse)
        embedding_data = [
            EmbeddingData(
                embedding_type=EmbeddingType.DENSE,
                embeddings=query_embedding,
                field_name="content_embedding",
                filtering_expr=filter_expr,
            ),
            EmbeddingData(
                embedding_type=EmbeddingType.SPARSE,
                query=query,
                field_name="content_sparse",
                filtering_expr=filter_expr,
            ),
        ]

        # 4. Execute hybrid search with RRF fusion
        raw_results = await self.vector_db.async_hybrid_search_vectors(
            embedding_data=embedding_data,
            output_fields=["id", "content", "source", "original_document", "author"],
            top_k=top_k,
            collection_name=self.collection_name,
            metric_type=MetricType.COSINE,
            index_type=IndexType.HNSW,
        )

        # 5. Convert raw dict results to typed DocumentChunkResult objects
        results = [
            DocumentChunkResult(
                id=r.get("id", ""),
                content=r.get("content", ""),
                source=r.get("source", ""),
                original_document=r.get("original_document", ""),
                author=r.get("author", ""),
                score=r.get("_score", 0.0),
            )
            for r in raw_results
        ]

        return results
