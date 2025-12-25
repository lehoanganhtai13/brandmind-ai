"""
FalkorDB Graph Restore - Import nodes and edges from CSV backup.

Expected Input:
    ./backups/falkordb/
    ├── nodes.csv           # All nodes with id, labels, properties
    ├── edges.csv           # All edges with id, type, from_id, to_id, properties
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


def restore_graph(
    backup_dir: Path,
    graph_name: str,
    host: str = "localhost",
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
) -> dict:
    """
    Restore FalkorDB graph from nodes.csv and edges.csv backup.

    Uses MERGE operations to upsert nodes and relationships (idempotent).
    Nodes are matched by their 'name' property as the unique identifier.

    Args:
        backup_dir: Directory containing CSV backup files.
        graph_name: Target graph name to restore into.
        host: FalkorDB host address.
        port: FalkorDB port number.
        username: Optional username for authentication.
        password: Optional password for authentication.

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

    stats = {"nodes_restored": 0, "edges_restored": 0}

    # Load backup metadata if available
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
            
            # Get labels (may be comma-separated)
            labels_str = props.pop("labels", "Entity")
            label = labels_str.split(",")[0] if labels_str else "Entity"
            
            # Remove internal id (will use name as match key)
            props.pop("id", None)
            
            # Use 'name' as the unique match key
            if "name" in props:
                match_props = {"name": props["name"]}
                update_props = {k: v for k, v in props.items() if k != "name"}
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
        
        for _, row in df.iterrows():
            edge_type = row.get("type")
            from_name = row.get("from_name")
            to_name = row.get("to_name")
            
            # Skip if missing required fields
            if pd.isna(edge_type) or pd.isna(from_name) or pd.isna(to_name):
                continue
            
            # Edge properties (exclude internal fields)
            excluded = {"id", "type", "from_id", "to_id", "from_name", "to_name"}
            props = {k: v for k, v in row.to_dict().items() if k not in excluded and pd.notna(v)}
            
            client.merge_relationship(
                source_label="Entity",  # Default label, actual label determined by MERGE
                source_match={"name": str(from_name)},
                target_label="Entity",
                target_match={"name": str(to_name)},
                relation_type=str(edge_type),
                properties=props if props else None,
            )
            stats["edges_restored"] += 1

        logger.info(f"  ✅ Restored {stats['edges_restored']} edges")
    else:
        logger.warning("edges.csv not found, skipping edge restore")

    logger.info("")
    logger.info("📊 Restore Summary:")
    logger.info(f"   Total nodes restored: {stats['nodes_restored']}")
    logger.info(f"   Total edges restored: {stats['edges_restored']}")

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

    args = parser.parse_args()

    try:
        restore_graph(
            backup_dir=args.backup_dir,
            graph_name=args.graph,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
        )
        logger.info("✅ Restore completed successfully!")
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
