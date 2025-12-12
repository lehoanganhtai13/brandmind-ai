"""
Storage manager for dual storage coordination between Graph DB and Vector DB.

This module ensures atomic operations across both databases with rollback
capability. Uses entity types as Graph DB node labels for efficient filtering.
"""

import uuid
from typing import Dict, List

from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.graph_database.falkordb.utils import sanitize_label
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder


class StorageManager:
    """
    Manages coordinated storage of entities across Graph DB and Vector DB.

    Ensures dual storage where entity nodes in Graph DB (with entity_type as label)
    have corresponding description embeddings in Vector DB. Designed for batch
    operations to optimize performance.
    """

    def __init__(
        self,
        graph_db: BaseGraphDatabase,
        vector_db: BaseVectorDatabase,
        embedder: BaseEmbedder,
        entity_collection_name: str = "EntityDescriptions",
        relation_collection_name: str = "RelationDescriptions",
    ):
        self.graph_db = graph_db
        self.vector_db = vector_db
        self.embedder = embedder
        self.entity_collection_name = entity_collection_name
        self.relation_collection_name = relation_collection_name

    async def create_entity(
        self,
        name: str,
        entity_type: str,
        description: str,
        name_embedding: List[float],  # Pre-computed
        desc_embedding: List[float],  # Pre-computed
        source_chunk_id: str,
    ) -> Dict:
        """
        Create new entity in both Graph DB and Vector DB.

        Creates entity node in Graph DB using entity_type as label for efficient
        indexing. Stores pre-computed embeddings in Vector DB. Uses dual storage
        pattern for consistency.

        Args:
            name: Entity name
            entity_type: Entity type used as Graph DB label (e.g., "MarketingConcept")
            description: Entity description
            name_embedding: Pre-computed dense embedding for name
            desc_embedding: Pre-computed dense embedding for description
            source_chunk_id: ID of source chunk

        Returns:
            Dict with entity_id, graph_id
        """
        entity_id = str(uuid.uuid4())

        try:
            # 1. Create in Graph DB with entity_type AS LABEL
            graph_id = await self.graph_db.async_merge_node(
                label=entity_type,  # Use entity type as label!
                match_properties={"name": name},
                update_properties={
                    "id": entity_id,
                    "description": description,
                    "source_chunks": [source_chunk_id],
                },
            )

            # 2. Insert to Vector DB with pre-computed embeddings
            vector_data = {
                "id": entity_id,
                "graph_id": graph_id,
                "name": name,
                "type": entity_type,  # Store type as property for filtering
                "description": description,
                "description_embedding": desc_embedding,
                "name_embedding": name_embedding,
            }
            await self.vector_db.async_insert_vectors(
                data=[vector_data], collection_name=self.entity_collection_name
            )

            return {"entity_id": entity_id, "graph_id": graph_id}

        except Exception:
            # Rollback: delete from Graph DB if created
            await self._rollback_entity(entity_id, entity_type)
            raise

    async def _rollback_entity(self, entity_id: str, entity_type: str) -> None:
        """Rollback entity creation on error."""
        try:
            await self.graph_db.async_delete_node(
                label=entity_type, match_properties={"id": entity_id}, detach=True
            )
        except Exception:
            pass  # Best effort cleanup

    async def update_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        description: str,
        source_chunk_id: str,
    ) -> None:
        """
        Update existing entity in both Graph DB and Vector DB.

        Updates entity node with merged description in Graph DB and re-embeds
        the merged description for Vector DB.

        Args:
            entity_id: Entity ID
            entity_type: Entity type (Graph DB label)
            name: Updated entity name (possibly canonical)
            description: Merged/condensed description (NEW content)
            source_chunk_id: New source chunk to add
        """
        # 1. Update Graph DB (entity_type as label)
        await self.graph_db.async_merge_node(
            label=entity_type,
            match_properties={"id": entity_id},
            update_properties={
                "name": name,
                "description": description,
            },
        )

        # 2. Append to source_chunks array using Cypher
        # Use proper Cypher list concatenation
        label = sanitize_label(entity_type)
        query = f"""
        MATCH (n:{label} {{id: $entity_id}})
        SET n.source_chunks = CASE
            WHEN n.source_chunks IS NULL THEN [$new_chunk]
            ELSE n.source_chunks + [$new_chunk]
        END
        """
        params = {"entity_id": entity_id, "new_chunk": source_chunk_id}
        await self.graph_db.async_execute_query(query, params)

        # 3. Re-embed merged description
        desc_emb = await self.embedder.aget_text_embedding(description)
        name_emb = await self.embedder.aget_text_embedding(name)

        # 3. Update Vector DB with new embeddings using upsert
        vector_data = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "description": description,
            "description_embedding": desc_emb,
            "name_embedding": name_emb,
        }
        await self.vector_db.async_upsert_vectors(
            data=[vector_data],
            collection_name=self.entity_collection_name,
            partial_update=True,
        )

    async def create_relation(
        self,
        source_entity_id: str,
        source_entity_type: str,
        target_entity_id: str,
        target_entity_type: str,
        relation_type: str,
        description: str,
        desc_embedding: List[float],  # Pre-computed
        source_chunk_id: str,
    ) -> Dict:
        """
        Create relation edge in Graph DB with description in Vector DB.

        Creates directed edge between entities in Graph DB using entity types
        as node labels. Stores relation description embedding in Vector DB for
        semantic search.

        Args:
            source_entity_id: Source entity ID
            source_entity_type: Source entity type (Graph DB label)
            target_entity_id: Target entity ID
            target_entity_type: Target entity type (Graph DB label)
            relation_type: Type of relation (e.g., "employsStrategy")
            description: Relation description
            desc_embedding: Pre-computed dense embedding for description
            source_chunk_id: ID of source chunk

        Returns:
            Dict with relation_id
        """
        relation_id = str(uuid.uuid4())

        # 1. Create edge in Graph DB (entity types as labels)
        await self.graph_db.async_merge_relationship(
            source_label=source_entity_type,
            source_match={"id": source_entity_id},
            target_label=target_entity_type,
            target_match={"id": target_entity_id},
            relation_type=relation_type,
            properties={
                "description": description,
                "vector_db_ref_id": relation_id,
                "source_chunk": source_chunk_id,
            },
        )

        # 2. Insert to Vector DB with pre-computed embedding
        vector_data = {
            "id": relation_id,
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "relation_type": relation_type,
            "description": description,
            "description_embedding": desc_embedding,
        }
        await self.vector_db.async_insert_vectors(
            data=[vector_data], collection_name=self.relation_collection_name
        )

        return {"relation_id": relation_id}
