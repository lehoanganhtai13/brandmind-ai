"""
FalkorDB Graph Restore - Import nodes and edges from CSV backup.

Expected Input:
    ./backups/falkordb/
    ├── nodes.csv           # All nodes with id (UUID), labels, properties
    ├── edges.csv           # All edges with type, from_id, to_id (UUIDs), properties
    └── metadata.json       # Backup statistics

Usage:
    python scripts/migration/falkordb_restore.py \
        --backup-dir ./backups/falkordb \
        --graph knowledge_graph \
        --host localhost --port 6380 \
        --username brandmind --password password
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from shared.database_clients.graph_database.falkordb import (
    FalkorDBClient,
    FalkorDBConfig,
)
from shared.database_clients.graph_database.falkordb.utils import (
    sanitize_label,
    sanitize_relation_type,
)


def restore_graph(
    backup_dir: Path,
    graph_name: str,
    host: str = "localhost",
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    overwrite: bool = False,
) -> dict:
    """
    Restore FalkorDB graph from nodes.csv and edges.csv backup.

    Uses the 'id' property (UUID) to match nodes when creating edges.
    Supports label-based edge matching for accurate restoration.

    Args:
        backup_dir: Directory containing CSV backup files.
        graph_name: Target graph name to restore into.
        host: FalkorDB host address.
        port: FalkorDB port number.
        username: Optional username for authentication.
        password: Optional password for authentication.
        overwrite: If True, clear existing graph before restore.

    Returns:
        Restore statistics showing counts of restored nodes and edges.
    """
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")

    logger.info(f"Connecting to FalkorDB at {host}:{port}, graph: {graph_name}")

    config = FalkorDBConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        graph_name=graph_name,
    )
    client = FalkorDBClient(config)

    # Clear existing graph if overwrite mode
    if overwrite:
        logger.info("🗑️ Overwrite mode: Clearing existing graph...")
        try:
            client.execute_query("MATCH (n) DETACH DELETE n")
            logger.info("  ✅ Existing data cleared")
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to clear graph: {e}")

    stats = {"nodes_restored": 0, "edges_restored": 0, "edges_failed": 0}

    # Load backup metadata if available
    metadata = {}
    metadata_file = backup_dir / "metadata.json"
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
        logger.info(f"Restoring backup from: {metadata.get('backup_time', 'unknown')}")
        logger.info(f"Expected: {metadata.get('total_nodes', '?')} nodes, {metadata.get('total_edges', '?')} edges")

    # Restore nodes from nodes.csv
    nodes_file = backup_dir / "nodes.csv"
    if nodes_file.exists():
        logger.info("Restoring nodes from nodes.csv...")
        df = pd.read_csv(nodes_file)
        
        for _, row in df.iterrows():
            props = row.to_dict()
            
            # Remove NaN values
            props = {k: v for k, v in props.items() if pd.notna(v)}
            
            # Get label (each entity has exactly 1 label)
            label = props.pop("label", "Entity")
            label = sanitize_label(label) if label else "Entity"
            
            node_id = props.get("id")
            if not node_id:
                continue
            
            match_props = {"id": node_id}
            update_props = {k: v for k, v in props.items() if k != "id"}
            client.merge_node(label, match_props, update_props)
            stats["nodes_restored"] += 1

        logger.info(f"  ✅ Restored {stats['nodes_restored']} nodes")
    else:
        logger.warning("nodes.csv not found, skipping node restore")

    # Restore edges from edges.csv
    edges_file = backup_dir / "edges.csv"
    if edges_file.exists():
        logger.info("Restoring edges from edges.csv...")
        df = pd.read_csv(edges_file)

        # Check if new format with labels
        has_labels = "from_label" in df.columns and "to_label" in df.columns
        if has_labels:
            logger.info("  📋 Detected new format with labels - using label matching")
        else:
            logger.info("  ⚠️ Old format without labels - matching by ID only")

        for _, row in df.iterrows():
            edge_type = row.get("type")
            from_id = row.get("from_id")
            to_id = row.get("to_id")
            vector_db_ref_id = row.get("vector_db_ref_id")

            # Skip if missing required fields
            if pd.isna(edge_type) or pd.isna(from_id) or pd.isna(to_id):
                continue

            # Edge properties (exclude internal fields and label fields)
            excluded = {"type", "from_id", "to_id", "from_label", "to_label", "vector_db_ref_id"}
            props = {
                k: v for k, v in row.to_dict().items() if k not in excluded and pd.notna(v)
            }

            # Sanitize relationship type
            rel_type = sanitize_relation_type(str(edge_type))

            # Build SET clause for other properties (description, created_at, etc.)
            set_clause = ""
            if props:
                prop_sets = ", ".join([f"r.{k} = $r_{k}" for k in props.keys()])
                set_clause = f"SET {prop_sets}"

            # Use vector_db_ref_id as unique identifier for MERGE to support parallel edges
            # This ensures edges with different vector_db_ref_ids are created as separate edges
            merge_props = ""
            if pd.notna(vector_db_ref_id):
                merge_props = " {vector_db_ref_id: $ref_id}"

            # Use labels if available for accurate matching
            if has_labels and pd.notna(row.get("from_label")) and pd.notna(row.get("to_label")):
                from_label = sanitize_label(str(row.get("from_label")))
                to_label = sanitize_label(str(row.get("to_label")))
                query = f"""
                MATCH (s:{from_label} {{id: $from_id}})
                MATCH (t:{to_label} {{id: $to_id}})
                MERGE (s)-[r:{rel_type}{merge_props}]->(t)
                {set_clause}
                RETURN r
                """
            else:
                # Old format fallback - match by ID only
                query = f"""
                MATCH (s {{id: $from_id}})
                MATCH (t {{id: $to_id}})
                MERGE (s)-[r:{rel_type}{merge_props}]->(t)
                {set_clause}
                RETURN r
                """

            params = {
                "from_id": str(from_id),
                "to_id": str(to_id),
            }
            if pd.notna(vector_db_ref_id):
                params["ref_id"] = str(vector_db_ref_id)
            if props:
                params.update({f"r_{k}": v for k, v in props.items()})

            try:
                result = client.execute_query(query, params)
                if result.result_set:
                    stats["edges_restored"] += 1
                else:
                    stats["edges_failed"] += 1
            except Exception as e:
                logger.debug(f"Failed to create edge {from_id} -> {to_id}: {e}")
                stats["edges_failed"] += 1

        logger.info(f"  ✅ Restored {stats['edges_restored']} edges")
        if stats["edges_failed"] > 0:
            logger.warning(f"  ⚠️ {stats['edges_failed']} edges failed (nodes may not exist)")
    else:
        logger.warning("edges.csv not found, skipping edge restore")

    # === Verification Step ===
    logger.info("")
    logger.info("🔍 Verifying restore...")
    
    # Get actual counts from Graph DB
    try:
        node_result = client.execute_query("MATCH (n) RETURN count(n) as cnt")
        db_node_count = node_result.result_set[0][0] if node_result.result_set else 0
        
        edge_result = client.execute_query("MATCH ()-[r]->() RETURN count(r) as cnt")
        db_edge_count = edge_result.result_set[0][0] if edge_result.result_set else 0
    except Exception as e:
        logger.warning(f"  ⚠️ Could not verify counts: {e}")
        db_node_count = None
        db_edge_count = None
    
    # Compare with backup metadata
    expected_nodes = metadata.get("total_nodes") if metadata else None
    expected_edges = metadata.get("total_edges") if metadata else None
    
    # Verification results
    stats["verified"] = True
    verification_issues = []
    
    if expected_nodes is not None and db_node_count is not None:
        if db_node_count != expected_nodes:
            verification_issues.append(f"Node count mismatch: DB={db_node_count}, expected={expected_nodes}")
            stats["verified"] = False
    
    if expected_edges is not None and db_edge_count is not None:
        if db_edge_count != expected_edges:
            verification_issues.append(f"Edge count mismatch: DB={db_edge_count}, expected={expected_edges}")
            stats["verified"] = False
    
    # Check for edge failures
    if stats["edges_failed"] > 0:
        verification_issues.append(f"{stats['edges_failed']} edges failed to restore")
        stats["verified"] = False

    logger.info("")
    logger.info("📊 Restore Summary:")
    logger.info(f"   Nodes: {stats['nodes_restored']} restored" + 
                (f", {db_node_count} in DB" if db_node_count is not None else ""))
    logger.info(f"   Edges: {stats['edges_restored']} restored" +
                (f", {db_edge_count} in DB" if db_edge_count is not None else ""))
    if stats["edges_failed"] > 0:
        logger.info(f"   Edges failed: {stats['edges_failed']}")
    
    # Verification status
    if stats["verified"]:
        logger.info("")
        logger.info("✅ VERIFICATION PASSED - Restore matches backup!")
    else:
        logger.warning("")
        logger.warning("⚠️ VERIFICATION ISSUES:")
        for issue in verification_issues:
            logger.warning(f"   - {issue}")

    return stats


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Restore FalkorDB graph from nodes.csv and edges.csv backup files."
    )
    parser.add_argument(
        "--backup-dir", "-b",
        type=Path,
        default=Path("./backups/falkordb"),
        help="Directory containing backup CSV files (default: ./backups/falkordb)",
    )
    parser.add_argument("--graph", "-g", required=True, help="Target graph name to restore into")
    parser.add_argument("--host", default="localhost", help="FalkorDB host (default: localhost)")
    parser.add_argument("--port", type=int, default=6380, help="FalkorDB port (default: 6380)")
    parser.add_argument("--username", default=None, help="FalkorDB username (optional)")
    parser.add_argument("--password", default=None, help="FalkorDB password (optional)")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Clear existing graph before restore (like clean restore)",
    )

    args = parser.parse_args()

    try:
        restore_graph(
            backup_dir=args.backup_dir,
            graph_name=args.graph,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            overwrite=args.overwrite,
        )
        logger.info("✅ Restore completed successfully!")
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
