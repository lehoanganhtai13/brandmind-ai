"""
Knowledge Graph Post-Processing - Clean up data inconsistencies.

This module handles LLM-induced data quality issues:
1. Entity label casing variants (e.g., MarketingConcept vs Marketingconcept)
2. Duplicate/orphan relations in Vector DB

Usage in CLI:
    python src/cli/build_knowledge_graph.py \
        --folder FOLDER --stage post-process --dry-run
"""

from collections import defaultdict
from typing import Dict, List, Set

from loguru import logger

from core.knowledge_graph.curator.entity_resolver import merge_descriptions
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.graph_database.falkordb.utils import (
    sanitize_label,
    sanitize_relation_type,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder


def is_pascal_case(label: str) -> bool:
    """Check if label is in PascalCase (has uppercase letter after first char)."""
    if not label or len(label) < 2:
        return False
    return any(c.isupper() for c in label[1:])


async def cleanup_duplicate_entities(
    graph_db: BaseGraphDatabase,
    vector_db: BaseVectorDatabase,
    embedder: BaseEmbedder,
    entity_collection_name: str = "EntityDescriptions",
    dry_run: bool = True,
) -> Dict:
    """
    Merge duplicate entities with same ID but different label casing.

    For nodes with same ID but different label casing
    (e.g., MarketingConcept vs Marketingconcept):
    1. Merge descriptions using LLM
    2. Update the "good" node with merged description
    3. Migrate all edges from "bad" node to "good" node
    4. Delete "bad" node
    5. Update Vector DB entity record with new description embedding

    Args:
        graph_db: Graph database client
        vector_db: Vector database client
        embedder: Embedder for re-embedding merged descriptions
        entity_collection_name: Entity collection name in Vector DB
        dry_run: If True, only report what would be done

    Returns:
        Stats dict with counts of entities cleaned
    """
    stats = {
        "duplicates_found": 0,
        "nodes_merged": 0,
        "edges_migrated": 0,
        "descriptions_merged": 0,
    }

    logger.info("Scanning for duplicate entity IDs in Graph DB...")

    # 1. Find all nodes with their ID and labels
    result = await graph_db.async_execute_query(
        """
        MATCH (n)
        WHERE n.id IS NOT NULL
        RETURN n.id as id, labels(n) as labels, n.name as name,
               n.description as desc, id(n) as internal_id
        """
    )

    # Group by UUID
    id_to_nodes: Dict[str, List[Dict]] = defaultdict(list)
    for record in result.result_set:
        node_id = record[0]
        labels = record[1] or []
        name = record[2]
        desc = record[3] or ""
        internal_id = record[4]
        if node_id and labels:
            id_to_nodes[node_id].append(
                {
                    "label": labels[0],
                    "name": name,
                    "description": desc,
                    "internal_id": internal_id,
                }
            )

    # Find duplicates (same UUID, different labels)
    duplicates = {id: nodes for id, nodes in id_to_nodes.items() if len(nodes) > 1}
    stats["duplicates_found"] = len(duplicates)

    if not duplicates:
        logger.info("No duplicate entity IDs found!")
        return stats

    logger.info(f"Found {len(duplicates)} IDs with duplicate nodes (different labels)")

    # Show sample duplicates
    sample = list(duplicates.items())[:5]
    for node_id, nodes in sample:
        labels = [n["label"] for n in nodes]
        logger.info(f"  ID {node_id[:8]}...: {labels}")

    if dry_run:
        logger.info("DRY RUN - no changes will be made")
        return stats

    # 2. Process each duplicate
    for node_id, nodes in duplicates.items():
        # Get unique labels
        unique_labels = set(n["label"] for n in nodes)

        # Skip if all nodes have the same label (nothing to merge)
        if len(unique_labels) == 1:
            logger.debug(
                f"ID {node_id[:8]}...: Skipping - all {len(nodes)} nodes "
                f"have same label '{nodes[0]['label']}'"
            )
            continue

        # Sort by quality - prefer PascalCase (has uppercase after first char)
        sorted_nodes = sorted(
            nodes, key=lambda x: (not is_pascal_case(x["label"]), x["label"])
        )
        keep_node = sorted_nodes[0]
        delete_nodes = sorted_nodes[1:]

        keep_label = sanitize_label(keep_node["label"])

        # Log with more detail
        logger.info(
            f"ID {node_id[:8]}...: Keep '{keep_node['label']}' "
            f"(PascalCase={is_pascal_case(keep_node['label'])}), "
            f"delete {[n['label'] for n in delete_nodes]}"
        )

        for del_node in delete_nodes:
            del_label = sanitize_label(del_node["label"])

            try:
                # Step 1: Merge descriptions if different
                if (
                    keep_node["description"]
                    and del_node["description"]
                    and keep_node["description"] != del_node["description"]
                ):
                    logger.info(f"Merging descriptions for {node_id[:8]}...")
                    merged_desc = await merge_descriptions(
                        existing_desc=keep_node["description"],
                        new_desc=del_node["description"],
                    )
                    stats["descriptions_merged"] += 1

                    # Update good node with merged description
                    await graph_db.async_execute_query(
                        f"""
                        MATCH (n:{keep_label} {{id: $node_id}})
                        SET n.description = $desc
                        """,
                        {"node_id": node_id, "desc": merged_desc},
                    )

                    # Update Vector DB with new embedding
                    desc_emb = await embedder.aget_text_embedding(merged_desc)
                    await vector_db.async_upsert_vectors(
                        data=[
                            {
                                "id": node_id,
                                "description": merged_desc,
                                "description_embedding": desc_emb,
                            }
                        ],
                        collection_name=entity_collection_name,
                        partial_update=True,
                    )

                    # Update keep_node for next iteration
                    keep_node["description"] = merged_desc

                # Step 2: Get all relationship types from bad node
                out_edges_result = await graph_db.async_execute_query(
                    f"""
                    MATCH (bad:{del_label} {{id: $node_id}})-[r]->()
                    RETURN DISTINCT type(r) as rel_type
                    """,
                    {"node_id": node_id},
                )
                out_edge_types = [r[0] for r in out_edges_result.result_set if r[0]]

                in_edges_result = await graph_db.async_execute_query(
                    f"""
                    MATCH ()-[r]->(bad:{del_label} {{id: $node_id}})
                    RETURN DISTINCT type(r) as rel_type
                    """,
                    {"node_id": node_id},
                )
                in_edge_types = [r[0] for r in in_edges_result.result_set if r[0]]

                # Step 3: Migrate outgoing edges (per relationship type)
                for rel_type in out_edge_types:
                    safe_rel = sanitize_relation_type(rel_type)
                    migrate_query = f"""
                    MATCH (bad:{del_label} {{id: $node_id}})-[r:{safe_rel}]->(target)
                    MATCH (good:{keep_label} {{id: $node_id}})
                    CREATE (good)-[r2:{safe_rel}]->(target)
                    SET r2 = properties(r)
                    DELETE r
                    RETURN count(r) as migrated
                    """
                    result = await graph_db.async_execute_query(
                        migrate_query, {"node_id": node_id}
                    )
                    if result.result_set:
                        stats["edges_migrated"] += result.result_set[0][0] or 0

                # Step 4: Migrate incoming edges (per relationship type)
                for rel_type in in_edge_types:
                    safe_rel = sanitize_relation_type(rel_type)
                    migrate_query = f"""
                    MATCH (source)-[r:{safe_rel}]->(bad:{del_label} {{id: $node_id}})
                    MATCH (good:{keep_label} {{id: $node_id}})
                    CREATE (source)-[r2:{safe_rel}]->(good)
                    SET r2 = properties(r)
                    DELETE r
                    RETURN count(r) as migrated
                    """
                    result = await graph_db.async_execute_query(
                        migrate_query, {"node_id": node_id}
                    )
                    if result.result_set:
                        stats["edges_migrated"] += result.result_set[0][0] or 0

                # Step 5: Delete the now-orphaned bad node
                delete_query = f"""
                MATCH (n:{del_label} {{id: $node_id}})
                DELETE n
                RETURN count(n) as deleted
                """
                result = await graph_db.async_execute_query(
                    delete_query, {"node_id": node_id}
                )
                if result.result_set and result.result_set[0][0] > 0:
                    stats["nodes_merged"] += 1
                    logger.debug(f"Merged and deleted {del_label} {node_id[:8]}...")

            except Exception as e:
                logger.warning(f"Failed to process {del_label} {node_id[:8]}...: {e}")

    logger.info(f"Merged {stats['nodes_merged']} duplicate nodes")
    logger.info(f"Migrated {stats['edges_migrated']} edges")
    logger.info(f"Merged {stats['descriptions_merged']} descriptions")
    return stats


async def cleanup_duplicate_relations(
    graph_db: BaseGraphDatabase,
    vector_db: BaseVectorDatabase,
    relation_collection_name: str = "RelationDescriptions",
    dry_run: bool = True,
) -> Dict:
    """
    Delete orphan relation records from Vector DB.

    Orphans = records in Vector DB without corresponding edge in Graph DB.
    This happens when:
    - Same relation extracted from multiple chunks
    - Graph MERGE deduplicates, but Vector INSERT created multiple records
    - After changing to UPSERT, this cleans up existing orphans

    Args:
        graph_db: Graph database client
        vector_db: Vector database client
        relation_collection_name: Name of relation collection
        dry_run: If True, only report what would be done

    Returns:
        Stats dict with counts of relations cleaned
    """
    stats = {
        "valid_relations": 0,
        "total_vector_records": 0,
        "orphans_found": 0,
        "orphans_deleted": 0,
    }

    logger.info("Analyzing relation consistency between Graph DB and Vector DB...")

    # 1. Get all valid relation IDs from Graph DB edges
    logger.info("Getting valid relation IDs from Graph DB...")
    result = await graph_db.async_execute_query(
        """
        MATCH ()-[r]->()
        WHERE r.vector_db_ref_id IS NOT NULL
        RETURN DISTINCT r.vector_db_ref_id as ref_id
        """
    )

    valid_ids: Set[str] = set()
    for record in result.result_set:
        if record[0]:
            valid_ids.add(record[0])

    stats["valid_relations"] = len(valid_ids)
    logger.info(f"Found {len(valid_ids)} valid relation IDs in Graph DB")

    # 2. Get all relation IDs from Vector DB
    logger.info("Getting all relation IDs from Vector DB (this may take a while)...")
    try:
        all_vector_records = await vector_db.async_get_all_items(
            collection_name=relation_collection_name,
            output_fields=["id"],
        )
        vector_ids: Set[str] = {r["id"] for r in all_vector_records if r.get("id")}
        stats["total_vector_records"] = len(vector_ids)
        logger.info(f"Found {len(vector_ids)} records in Vector DB")
    except Exception as e:
        logger.error(f"Failed to get Vector DB records: {e}")
        return stats

    # 3. Find orphans
    orphan_ids = vector_ids - valid_ids
    stats["orphans_found"] = len(orphan_ids)

    logger.info(f"Found {len(orphan_ids)} orphan records (in Vector but not in Graph)")

    if not orphan_ids:
        logger.info("No orphan relations found!")
        return stats

    if dry_run:
        logger.info("DRY RUN - no changes will be made")
        logger.info(f"Would delete {len(orphan_ids)} orphan records")
        return stats

    # 4. Delete orphans in batches
    logger.info(f"Deleting {len(orphan_ids)} orphan records...")
    batch_size = 1000
    orphan_list = list(orphan_ids)

    for i in range(0, len(orphan_list), batch_size):
        batch = orphan_list[i : i + batch_size]
        try:
            await vector_db.async_delete_vectors(
                ids=batch,
                collection_name=relation_collection_name,
            )
            stats["orphans_deleted"] += len(batch)
            logger.debug(f"Deleted batch {i // batch_size + 1}")
        except Exception as e:
            logger.warning(f"Failed to delete batch: {e}")

    logger.info(f"Deleted {stats['orphans_deleted']} orphan relation records")
    return stats


async def run_post_processing(
    graph_db: BaseGraphDatabase,
    vector_db: BaseVectorDatabase,
    embedder: BaseEmbedder,
    entity_collection_name: str = "EntityDescriptions",
    relation_collection_name: str = "RelationDescriptions",
    dry_run: bool = True,
) -> Dict:
    """
    Run all post-processing cleanup tasks.

    Args:
        graph_db: Graph database client
        vector_db: Vector database client
        embedder: Embedder for re-embedding merged descriptions
        entity_collection_name: Entity collection name
        relation_collection_name: Relation collection name
        dry_run: If True, only report issues without fixing

    Returns:
        Combined stats from all cleanup tasks
    """
    logger.info("=" * 60)
    logger.info("POST-PROCESSING: Knowledge Graph Data Cleanup")
    logger.info(
        f"Mode: {'DRY RUN (report only)' if dry_run else 'LIVE (apply changes)'}"
    )
    logger.info("=" * 60)

    all_stats = {}

    # 1. Clean up duplicate entities
    logger.info("\n[1/2] Cleaning duplicate entities (label casing issues)...")
    entity_stats = await cleanup_duplicate_entities(
        graph_db=graph_db,
        vector_db=vector_db,
        embedder=embedder,
        entity_collection_name=entity_collection_name,
        dry_run=dry_run,
    )
    all_stats["entities"] = entity_stats

    # 2. Clean up orphan relations
    logger.info("\n[2/2] Cleaning orphan relations...")
    relation_stats = await cleanup_duplicate_relations(
        graph_db=graph_db,
        vector_db=vector_db,
        relation_collection_name=relation_collection_name,
        dry_run=dry_run,
    )
    all_stats["relations"] = relation_stats

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("POST-PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Duplicate entity IDs found: {entity_stats['duplicates_found']}")
    logger.info(f"Valid relations in Graph DB: {relation_stats['valid_relations']}")
    logger.info(
        f"Total relations in Vector DB: {relation_stats['total_vector_records']}"
    )
    logger.info(f"Orphan relations found: {relation_stats['orphans_found']}")

    if not dry_run:
        logger.info(f"Entities merged: {entity_stats['nodes_merged']}")
        logger.info(f"Edges migrated: {entity_stats['edges_migrated']}")
        logger.info(f"Descriptions merged: {entity_stats['descriptions_merged']}")
        logger.info(f"Orphan relations deleted: {relation_stats['orphans_deleted']}")

    return all_stats
