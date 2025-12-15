"""
Global semantic search for knowledge graph relations.

This module provides the GlobalSearcher class which performs hybrid search
on the RelationDescriptions collection to find relevant relationships
regardless of graph structure. Results are enriched with full entity metadata
from the graph database for meaningful verbalization.
"""

import asyncio
from typing import Dict, List, Optional

from loguru import logger

from core.retrieval.models import GlobalRelation, GraphNode
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.graph_database.falkordb.utils import (
    sanitize_relation_type,
)
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


class GlobalSearcher:
    """
    Global semantic search via relation descriptions.

    Searches the RelationDescriptions collection to find relationships
    that are semantically similar to the query, regardless of graph
    structure. Complements local search by finding relevant concepts
    that may not be directly connected to seed nodes.
    """

    def __init__(
        self,
        vector_db: BaseVectorDatabase,
        graph_db: BaseGraphDatabase,
        embedder: BaseEmbedder,
        collection_name: str = "RelationDescriptions",
    ):
        """
        Initialize the global searcher.

        Args:
            vector_db: Vector database client for hybrid search
            graph_db: Graph database client for entity enrichment
            embedder: Embedder client for query embedding
            collection_name: Collection containing relation embeddings
        """
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.embedder = embedder
        self.collection_name = collection_name

    async def search(
        self, queries: List[str], top_k_per_query: int = 5
    ) -> List[GlobalRelation]:
        """
        Search for relevant relations using global sub-queries.

        Args:
            queries: List of global sub-queries (from query decomposition)
            top_k_per_query: Number of results per query

        Returns:
            List of unique GlobalRelation objects with enriched entity data
        """
        if not queries:
            return []

        # Search all queries in parallel
        async def search_single_query(query: str) -> List[Dict]:
            query_embedding = await self.embedder.aget_query_embedding(query)

            embedding_data = [
                EmbeddingData(
                    embedding_type=EmbeddingType.DENSE,
                    embeddings=query_embedding,
                    field_name="description_embedding",
                ),
                EmbeddingData(
                    embedding_type=EmbeddingType.SPARSE,
                    query=query,
                    field_name="description_sparse",
                ),
            ]

            results = await self.vector_db.async_hybrid_search_vectors(
                embedding_data=embedding_data,
                output_fields=[
                    "id",
                    "source_entity_id",
                    "target_entity_id",
                    "relation_type",
                    "description",
                ],
                top_k=top_k_per_query,
                collection_name=self.collection_name,
                metric_type=MetricType.COSINE,
                index_type=IndexType.HNSW,
            )
            return results

        # Execute all queries in parallel
        results_per_query = await asyncio.gather(
            *[search_single_query(q) for q in queries]
        )

        # Flatten results
        all_results = []
        for results in results_per_query:
            all_results.extend(results)

        # Deduplicate by relation ID
        seen_ids = set()
        unique_results = []
        for r in all_results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                unique_results.append(r)

        # Enrich with entity data and source_chunk from GraphDB
        enriched_relations = await self._enrich_relations(unique_results)

        return enriched_relations

    async def _enrich_relations(self, raw_results: List[Dict]) -> List[GlobalRelation]:
        """
        Enrich relation results with entity metadata from graph database.

        Fetches source and target entity nodes from GraphDB to get
        complete entity information (name, type, properties). Also
        retrieves source_chunk from the relationship edge properties.

        Args:
            raw_results: Raw search results from vector database

        Returns:
            List of GlobalRelation objects with full entity data
        """
        # Collect unique entity IDs to fetch
        entity_ids = set()
        for r in raw_results:
            entity_ids.add(r.get("source_entity_id", ""))
            entity_ids.add(r.get("target_entity_id", ""))
        entity_ids.discard("")  # Remove empty strings

        # Batch fetch entity data from GraphDB
        entity_cache: Dict[str, GraphNode] = {}
        for entity_id in entity_ids:
            try:
                # Query across multiple possible labels
                # Since we don't know the entity type, try common patterns
                node_data = await self._fetch_entity_by_id(entity_id)
                if node_data:
                    entity_cache[entity_id] = node_data
            except Exception as e:
                logger.warning(f"Failed to fetch entity {entity_id}: {e}")

        # Build enriched GlobalRelation objects
        enriched = []
        for r in raw_results:
            source_id = r.get("source_entity_id", "")
            target_id = r.get("target_entity_id", "")

            # Get entity data from cache or create minimal node
            source_entity = entity_cache.get(source_id) or GraphNode(
                id=source_id, type="Unknown", name=source_id
            )
            target_entity = entity_cache.get(target_id) or GraphNode(
                id=target_id, type="Unknown", name=target_id
            )

            # Fetch source_chunk from graph edge properties
            source_chunk = await self._get_relation_source_chunk(
                source_id, target_id, r.get("relation_type", "")
            )

            enriched.append(
                GlobalRelation(
                    id=r.get("id", ""),
                    source_entity=source_entity,
                    target_entity=target_entity,
                    relation_type=r.get("relation_type", ""),
                    description=r.get("description", ""),
                    source_chunk=source_chunk,
                    score=r.get("_score", 0.0),
                )
            )

        return enriched

    async def _fetch_entity_by_id(self, entity_id: str) -> Optional[GraphNode]:
        """
        Fetch entity node from graph database by ID.

        Queries EntityDescriptions collection to find entity type, then
        fetches full node data from graph database.

        Args:
            entity_id: Entity UUID

        Returns:
            GraphNode with entity metadata, or None if not found
        """
        # First, try to get entity type from EntityDescriptions collection
        try:
            entity_data = await self.vector_db.async_get_items(
                ids=[entity_id],
                collection_name="EntityDescriptions",
            )

            if entity_data:
                entity = entity_data[0]
                return GraphNode(
                    id=entity_id,
                    type=entity.get("type", "Unknown"),
                    name=entity.get("name", ""),
                    properties={
                        "description": entity.get("description", ""),
                    },
                )
        except Exception as e:
            logger.debug(f"Could not fetch entity from VectorDB: {e}")

        return None

    async def _get_relation_source_chunk(
        self, source_id: str, target_id: str, relation_type: str
    ) -> Optional[str]:
        """
        Get source_chunk from relationship edge in graph database.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship

        Returns:
            Source chunk ID if found, None otherwise
        """
        try:
            # Sanitize relation type to match how it was inserted
            # (e.g., "must gain" -> "MUST_GAIN")
            sanitized_rel_type = sanitize_relation_type(relation_type)

            # Query the edge properties from GraphDB
            query = f"""
                MATCH (s)-[r:{sanitized_rel_type}]->(t)
                WHERE s.id = $source_id AND t.id = $target_id
                RETURN r.source_chunk
                LIMIT 1
            """
            result = await self.graph_db.async_execute_query(
                query, {"source_id": source_id, "target_id": target_id}
            )

            # FalkorDB returns result with result_set attribute
            # result_set is List[List] where each row is a list of column values
            if result and hasattr(result, "result_set") and result.result_set:
                source_chunk = result.result_set[0][0]
                return source_chunk if source_chunk else None
        except Exception as e:
            logger.debug(f"Could not fetch source_chunk: {e}")

        return None
