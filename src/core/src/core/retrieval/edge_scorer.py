"""
Edge scorer for semantic similarity-based graph weighting.

This module provides the EdgeScorer class which computes semantic similarity
scores between a query embedding and relation embeddings from the vector DB.
These scores are used as edge weights in the PPR computation.
"""

from typing import Dict, List

import numpy as np

from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)


class EdgeScorer:
    """
    Scores graph edges based on semantic similarity to a query.

    Uses pre-embedded relation descriptions from the RelationDescriptions
    collection in Milvus. Edge scores determine flow weights during PPR
    computation and path selection during Dijkstra traceback.

    Higher scores indicate edges whose descriptions are more semantically
    relevant to the user's query.

    Example:
        >>> scorer = EdgeScorer(vector_db=milvus)
        >>> scores = await scorer.score_edges(query_embedding, relation_ids)
        >>> # scores = {"rel_123": 0.85, "rel_456": 0.42, ...}
    """

    def __init__(
        self,
        vector_db: BaseVectorDatabase,
        collection_name: str = "RelationDescriptions",
    ):
        """
        Initialize the edge scorer.

        Args:
            vector_db: Vector database client for fetching embeddings
            collection_name: Collection containing relation description embeddings
        """
        self.vector_db = vector_db
        self.collection_name = collection_name

    async def score_edges(
        self, query_embedding: List[float], relation_ids: List[str]
    ) -> Dict[str, float]:
        """
        Compute semantic similarity scores for multiple edges.

        Fetches relation embeddings by ID from the vector database,
        then calculates cosine similarity with the query embedding.

        Args:
            query_embedding: Embedded query vector
            relation_ids: List of relation IDs (vector_db_ref_id from FalkorDB)

        Returns:
            Dictionary mapping relation_id to similarity score (0.0 to 1.0)
        """
        if not relation_ids:
            return {}

        # Fetch relation embeddings from vector DB
        results = await self.vector_db.async_get_items(
            ids=relation_ids,
            collection_name=self.collection_name,
        )

        if not results:
            return {}

        # Prepare data for vectorized computation
        query_np = np.array(query_embedding, dtype=np.float32)

        valid_ids = []
        embeddings_list = []

        for result in results:
            rel_id = result.get("id")
            rel_embedding = result.get("description_embedding")

            if rel_id and rel_embedding:
                valid_ids.append(rel_id)
                embeddings_list.append(rel_embedding)

        if not embeddings_list:
            return {}

        # Vectorized cosine similarity computation
        # Shape: (n_relations, embedding_dim)
        rel_matrix = np.array(embeddings_list, dtype=np.float32)

        # Compute norms
        query_norm = np.linalg.norm(query_np)
        rel_norms = np.linalg.norm(rel_matrix, axis=1)

        # Avoid division by zero
        if query_norm == 0:
            return {rel_id: 0.0 for rel_id in valid_ids}

        # Vectorized dot product: (n_relations,)
        dot_products = np.dot(rel_matrix, query_np)

        # Vectorized cosine similarity
        similarities = dot_products / (rel_norms * query_norm)

        # Handle any NaN or inf values
        similarities = np.nan_to_num(similarities, nan=0.0, posinf=0.0, neginf=0.0)

        # Build result dictionary
        scores = {rel_id: float(sim) for rel_id, sim in zip(valid_ids, similarities)}

        return scores
