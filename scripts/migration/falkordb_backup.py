"""
FalkorDB Graph Backup - Export all nodes and edges to CSV files.

Output:
    ./backups/falkordb/
    ├── nodes.csv           # All nodes with id (UUID from property), labels, properties
    ├── edges.csv           # All edges with from_id, to_id (UUIDs from node properties)
    └── metadata.json       # Backup statistics and timestamp

Usage:
    python scripts/migration/falkordb_backup.py knowledge_graph \
        --host localhost --port 6380 \
        --username brandmind --password password \
        --output ./backups/falkordb
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from shared.database_clients.graph_database.falkordb import (
    FalkorDBClient,
    FalkorDBConfig,
)


def backup_graph(
    graph_name: str,
    output_dir: Path,
    host: str = "localhost",
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
) -> dict:
    """
    Export FalkorDB graph to 2 CSV files: nodes.csv and edges.csv.
    
    Uses the 'id' property (UUID) from nodes as the primary identifier,
    NOT the internal FalkorDB node ID.

    Args:
        graph_name: Name of the graph to export.
        output_dir: Directory to save CSV files.
        host: FalkorDB host address.
        port: FalkorDB port number.
        username: Optional username for authentication.
        password: Optional password for authentication.

    Returns:
        Backup metadata dict containing statistics and timestamp.
    """
    logger.info(f"Connecting to FalkorDB at {host}:{port}, graph: {graph_name}")

    config = FalkorDBConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        graph_name=graph_name,
    )
    client = FalkorDBClient(config)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Backup output directory: {output_dir}")

    # Export all nodes to single file
    logger.info("Exporting nodes...")
    nodes_result = client.execute_query(
        "MATCH (n) RETURN labels(n) as labels, properties(n) as props"
    )

    nodes = []
    for record in nodes_result.result_set:
        labels = record[0] or []
        props = record[1] or {}
        
        node = {
            "id": props.get("id", ""),  # UUID from property
            "label": labels[0] if labels else "",  # Each entity has exactly 1 label
            **{k: v for k, v in props.items() if k != "id"}  # Other props, exclude id (already added)
        }
        nodes.append(node)

    nodes_file = output_dir / "nodes.csv"
    pd.DataFrame(nodes).to_csv(nodes_file, index=False)
    logger.info(f"  ✅ Exported {len(nodes)} nodes → nodes.csv")

    # Export all edges to single file
    logger.info("Exporting edges...")
    edges_result = client.execute_query(
        """
        MATCH (a)-[e]->(b)
        RETURN TYPE(e) as type,
               properties(a).id as from_id,
               labels(a)[0] as from_label,
               properties(b).id as to_id,
               labels(b)[0] as to_label,
               properties(e) as props
        """
    )

    edges = []
    for record in edges_result.result_set:
        edge = {
            "type": record[0],
            "from_id": record[1],       # UUID from source node property
            "from_label": record[2],    # Source node label
            "to_id": record[3],         # UUID from target node property
            "to_label": record[4],      # Target node label
            **(record[5] or {})         # Edge properties
        }
        edges.append(edge)

    edges_file = output_dir / "edges.csv"
    pd.DataFrame(edges).to_csv(edges_file, index=False)
    logger.info(f"  ✅ Exported {len(edges)} edges → edges.csv")

    # Save backup metadata
    metadata = {
        "graph_name": graph_name,
        "backup_time": datetime.now().isoformat(),
        "host": host,
        "port": port,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }
    metadata_file = output_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    logger.info(f"  ✅ Saved metadata → metadata.json")

    logger.info("")
    logger.info("📊 Backup Summary:")
    logger.info(f"   Total nodes: {metadata['total_nodes']}")
    logger.info(f"   Total edges: {metadata['total_edges']}")

    return metadata


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Export FalkorDB graph to nodes.csv and edges.csv files."
    )
    parser.add_argument("graph_name", help="Name of the graph to export")
    parser.add_argument("--host", default="localhost", help="FalkorDB host (default: localhost)")
    parser.add_argument("--port", type=int, default=6380, help="FalkorDB port (default: 6380)")
    parser.add_argument("--username", default=None, help="FalkorDB username (optional)")
    parser.add_argument("--password", default=None, help="FalkorDB password (optional)")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./backups/falkordb"),
        help="Output directory for backup files (default: ./backups/falkordb)",
    )

    args = parser.parse_args()

    try:
        backup_graph(
            graph_name=args.graph_name,
            output_dir=args.output,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
        )
        logger.info("✅ Backup completed successfully!")
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
