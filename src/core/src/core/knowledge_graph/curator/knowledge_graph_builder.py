"""Knowledge Graph Builder with Entity Resolution."""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from loguru import logger

from core.knowledge_graph.curator.entity_resolver import (
    decide_entity_merge,
    find_similar_entity,
    merge_descriptions,
)
from core.knowledge_graph.curator.storage_manager import StorageManager
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder


async def build_knowledge_graph(
    triples_path: Path,
    graph_db: BaseGraphDatabase,
    vector_db: BaseVectorDatabase,
    embedder: BaseEmbedder,
    entity_collection_name: str = "EntityDescriptions",
    relation_collection_name: str = "RelationDescriptions",
    progress_path: Optional[Path] = None,
) -> Dict:
    """
    Build knowledge graph from extracted triples with entity resolution.

    Uses batch embedding to optimize API costs: embeds all entity names and
    descriptions per chunk. Individual re-embedding still happens when needed
    (e.g., merged descriptions). Processes chunks sequentially to maintain
    entity consistency.

    Args:
        triples_path: Path to triples.json from Stage 3
        graph_db: Graph database client (FalkorDB)
        vector_db: Vector database client (Milvus)
        embedder: Embedder client (Gemini in SEMANTIC mode)
        entity_collection_name: Name of entity descriptions collection
            (default: "EntityDescriptions")
        relation_collection_name: Name of relation descriptions collection
            (default: "RelationDescriptions")
        progress_path: Path to save progress checkpoint

    Returns:
        Stats dict with entity/relation counts and processing time
    """
    # Load triples
    with open(triples_path) as f:
        data = json.load(f)

    # Load progress
    processed_chunks = set()
    if progress_path and progress_path.exists():
        with open(progress_path) as f:
            progress = json.load(f)
            processed_chunks = set(progress.get("processed_chunks", []))

    storage_mgr = StorageManager(
        graph_db=graph_db,
        vector_db=vector_db,
        embedder=embedder,
        entity_collection_name=entity_collection_name,
        relation_collection_name=relation_collection_name,
    )
    stats = {"entities_created": 0, "entities_merged": 0, "relations_created": 0}

    # Process chunks sequentially
    for chunk_data in data["extractions"]:
        chunk_id = chunk_data["chunk_id"]
        if chunk_id in processed_chunks:
            continue

        # Extract entities and relations from nested structure
        extraction = chunk_data["extraction"]
        entities = extraction["entities"]
        relationships = extraction["relationships"]

        # Filter invalid entities (empty names)
        valid_entities = [e for e in entities if e.get("name") and e["name"].strip()]
        if len(valid_entities) < len(entities):
            logger.warning(
                f"Skipped {len(entities) - len(valid_entities)} entities with "
                f"empty names in chunk {chunk_id}"
            )
        entities = valid_entities

        # Collect all names and descriptions for batch processing
        entity_names = [e["name"] for e in entities]

        # Sanitize descriptions - Embedder fails on empty strings
        entity_descs = [
            e["description"] if e.get("description", "").strip() else "No description"
            for e in entities
        ]
        relation_descs = [
            (
                r.get("description", "")
                if r.get("description", "").strip()
                else "No description"
            )
            for r in relationships
        ]

        # Batch embed
        # Ensure names are not empty (already filtered, but extra safety check for API)
        # Note: name_embeddings alignment matches 'entities' list
        if not entity_names:
            name_embeddings = []
            desc_embeddings = []
        else:
            name_embeddings = await embedder.aget_text_embeddings(entity_names)
            desc_embeddings = await embedder.aget_text_embeddings(entity_descs)

        rel_embeddings = (
            await embedder.aget_text_embeddings(relation_descs)
            if relationships  # Always embed if there are relations (sanitized)
            else []
        )

        # Entity mapping: name -> (entity_id, entity_type)
        entity_map: Dict[str, Tuple[str, str]] = {}

        # 1. Process entities in parallel (safe within same chunk - no duplicates)
        async def process_entity(i: int, entity: Dict) -> Dict:
            """Process single entity: search, resolve, create/merge."""
            # Search with pre-computed name embedding
            similar = await find_similar_entity(
                entity_name=entity["name"],
                entity_type=entity["type"],
                name_embedding=name_embeddings[i],
                vector_db=vector_db,
                collection_name=entity_collection_name,
            )

            if similar:
                # Check for exact name match (optimization to skip LLM call)
                if similar["name"] == entity["name"]:
                    # Exact match - auto-merge without LLM decision
                    logger.info(
                        f"Exact name match found: '{entity['name']}' - auto-merging"
                    )
                    return {
                        "action": "merged",
                        "name": entity["name"],
                        "entity_id": similar["id"],
                        "entity_type": entity["type"],
                    }

                # LLM decision (creates own GoogleAIClientLLM instance)
                decision = await decide_entity_merge(
                    existing_entity=similar, new_entity=entity
                )

                logger.info("Entity resolution decision:")
                logger.info(f"  [+] Merge decision: {decision['decision']}")
                logger.info(f"  [+] Canonical Name: {decision['canonical_name']}")
                logger.info(f"  [+] Reasoning: {decision['reasoning']}")

                if decision["decision"] == "MERGE":
                    # Merge descriptions (creates own GoogleAIClientLLM instance)
                    merged_desc = await merge_descriptions(
                        existing_desc=similar["description"],
                        new_desc=entity["description"],
                    )

                    # Update entity (will re-embed merged description individually)
                    await storage_mgr.update_entity(
                        entity_id=similar["id"],
                        entity_type=similar["type"],
                        name=decision["canonical_name"],
                        description=merged_desc,
                        source_chunk_id=chunk_id,
                    )

                    return {
                        "action": "merged",
                        "name": entity["name"],
                        "entity_id": similar["id"],
                        "entity_type": similar["type"],
                    }

            # Create new entity with pre-computed embeddings
            result = await storage_mgr.create_entity(
                name=entity["name"],
                entity_type=entity["type"],
                description=entity["description"],
                name_embedding=name_embeddings[i],
                desc_embedding=desc_embeddings[i],
                source_chunk_id=chunk_id,
            )
            return {
                "action": "created",
                "name": entity["name"],
                "entity_id": result["entity_id"],
                "entity_type": entity["type"],
            }

        # Process all entities in parallel
        entity_results = await asyncio.gather(
            *[process_entity(i, entity) for i, entity in enumerate(entities)]
        )

        # Build entity map and update stats
        for result in entity_results:
            entity_map[result["name"]] = (result["entity_id"], result["entity_type"])
            if result["action"] == "created":
                stats["entities_created"] += 1
            elif result["action"] == "merged":
                stats["entities_merged"] += 1

        # 2. Process relations in parallel (safe - just lookup + insert)
        async def process_relation(i: int, relation: Dict) -> bool:
            """Process single relation: lookup entities and create relation."""
            source_data = entity_map.get(relation["source"])
            target_data = entity_map.get(relation["target"])

            if source_data and target_data:
                source_id, source_type = source_data
                target_id, target_type = target_data

                await storage_mgr.create_relation(
                    source_entity_id=source_id,
                    source_entity_type=source_type,
                    target_entity_id=target_id,
                    target_entity_type=target_type,
                    relation_type=relation["relation_type"],
                    description=relation.get("description", ""),
                    desc_embedding=(
                        rel_embeddings[i] if i < len(rel_embeddings) else []
                    ),
                    source_chunk_id=chunk_id,
                )
                return True  # Created
            return False  # Skipped (missing entities)

        # Process all relations in parallel
        relation_results = await asyncio.gather(
            *[process_relation(i, relation) for i, relation in enumerate(relationships)]
        )

        # Update stats
        stats["relations_created"] += sum(relation_results)

        # Save progress
        processed_chunks.add(chunk_id)
        if progress_path:
            with open(progress_path, "w") as f:
                json.dump({"processed_chunks": list(processed_chunks)}, f)

        logger.info(
            f"Processed chunk {chunk_id}: +{len(entity_map)} entities, "
            f"+{len(relationships)} relations"
        )

    return stats
