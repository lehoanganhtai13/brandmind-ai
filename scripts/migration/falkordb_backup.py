"""
FalkorDB Graph Backup - Export all nodes and edges to CSV files.

Output:
    ./backups/falkordb/
    ├── nodes.csv           # All nodes with id, labels, properties
    ├── edges.csv           # All edges with id, type, from_id, to_id, properties
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
        "MATCH (n) RETURN ID(n) as id, labels(n) as labels, properties(n) as props"
    )

    nodes = []
    for record in nodes_result.result_set:
        node_id = record[0]
        labels = record[1] or []
        props = record[2] or {}
        
        node = {
            "id": node_id,
            "labels": ",".join(labels) if labels else "",
            **props
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
        RETURN ID(e) as id,
               TYPE(e) as type,
               ID(a) as from_id,
               ID(b) as to_id,
               properties(a).name as from_name,
               properties(b).name as to_name,
               properties(e) as props
        """
    )

    edges = []
    for record in edges_result.result_set:
        edge = {
            "id": record[0],
            "type": record[1],
            "from_id": record[2],
            "to_id": record[3],
            "from_name": record[4],
            "to_name": record[5],
            **(record[6] or {})
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
