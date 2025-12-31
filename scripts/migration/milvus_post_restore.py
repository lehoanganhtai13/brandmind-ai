"""
Milvus Post-Restore - Recreate indexes and load collections.

After milvus-backup restore, indexes are NOT restored. This script:
1. Recreates indexes for all vector fields
2. Loads collections into memory

Usage:
    python scripts/migration/milvus_post_restore.py
"""

import os
import sys

from loguru import logger
from pymilvus import MilvusClient

# Index configurations for each collection
# Format: {collection_name: {field_name: {index_type, metric_type, params}}}
# Derived from collection_schemas.py and document_library.py
# - String fields: INVERTED index
# - Array fields: AUTOINDEX
# - Dense vectors: HNSW with COSINE
# - Sparse vectors: SPARSE_INVERTED_INDEX with BM25
INDEX_CONFIGS = {
    "DocumentChunks": {
        # Dense vector
        "content_embedding": {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 500},
        },
        # Sparse vector (BM25)
        "content_sparse": {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "BM25",
            "params": {"inverted_index_algo": "DAAT_MAXSCORE"},
        },
        # String fields - INVERTED index
        "source": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        "original_document": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        "author": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        # Array field - AUTOINDEX
        "pages": {
            "index_type": "AUTOINDEX",
            "metric_type": None,
            "params": {},
        },
    },
    "EntityDescriptions": {
        # Dense vectors
        "description_embedding": {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 500},
        },
        "name_embedding": {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 500},
        },
        # Sparse vectors (BM25)
        "description_sparse": {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "BM25",
            "params": {"inverted_index_algo": "DAAT_MAXSCORE"},
        },
        "name_sparse": {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "BM25",
            "params": {"inverted_index_algo": "DAAT_MAXSCORE"},
        },
        # String fields - INVERTED index
        "name": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        "type": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
    },
    "RelationDescriptions": {
        # Dense vector
        "description_embedding": {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 500},
        },
        # Sparse vector (BM25)
        "description_sparse": {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "BM25",
            "params": {"inverted_index_algo": "DAAT_MAXSCORE"},
        },
        # String fields - INVERTED index
        "source_entity_id": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        "target_entity_id": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
        "relation_type": {
            "index_type": "INVERTED",
            "metric_type": None,
            "params": {},
        },
    },
}


def create_indexes(client: MilvusClient, collection_name: str) -> int:
    """Create indexes for a collection."""
    if collection_name not in INDEX_CONFIGS:
        logger.warning(f"No index config for collection: {collection_name}")
        return 0

    configs = INDEX_CONFIGS[collection_name]
    created = 0

    for field_name, config in configs.items():
        try:
            logger.info(f"Creating index on {collection_name}.{field_name}...")

            index_params = client.prepare_index_params()
            
            # Build index params dict - metric_type only for vector fields
            index_kwargs = {
                "field_name": field_name,
                "index_type": config["index_type"],
            }
            if config.get("metric_type"):
                index_kwargs["metric_type"] = config["metric_type"]
            if config.get("params"):
                index_kwargs["params"] = config["params"]
            
            index_params.add_index(**index_kwargs)

            client.create_index(
                collection_name=collection_name,
                index_params=index_params,
            )
            logger.info(f"  ✅ Created {config['index_type']} index on {field_name}")
            created += 1

        except Exception as e:
            # Index might already exist
            if "already exist" in str(e).lower() or "already indexed" in str(e).lower():
                logger.info(f"  ⏭️ Index on {field_name} already exists")
            else:
                logger.error(f"  ❌ Failed to create index on {field_name}: {e}")

    return created


def load_collection(client: MilvusClient, collection_name: str) -> bool:
    """Load a collection into memory."""
    try:
        logger.info(f"Loading collection: {collection_name}...")
        client.load_collection(collection_name)
        logger.info(f"  ✅ Loaded {collection_name}")
        return True
    except Exception as e:
        logger.error(f"  ❌ Failed to load {collection_name}: {e}")
        return False


def main() -> None:
    """Main entry point."""
    # Milvus connection settings from environment
    milvus_host = os.getenv("MILVUS_HOST", "localhost")
    milvus_port = os.getenv("MILVUS_PORT", "19530")
    milvus_password = os.getenv("MILVUS_ROOT_PASSWORD", "")
    
    milvus_uri = f"http://{milvus_host}:{milvus_port}"
    
    logger.info(f"Connecting to Milvus at {milvus_uri} as user 'root'...")

    # Initialize Milvus client with authentication
    client = MilvusClient(
        uri=milvus_uri,
        user="root",
        password=milvus_password,
    )

    collections = list(INDEX_CONFIGS.keys())
    logger.info(f"Processing collections: {collections}")

    stats = {"indexes_created": 0, "collections_loaded": 0}

    for collection_name in collections:
        # Check if collection exists
        if not client.has_collection(collection_name):
            logger.warning(f"Collection {collection_name} does not exist, skipping")
            continue

        # Create indexes
        created = create_indexes(client, collection_name)
        stats["indexes_created"] += created

        # Load collection
        if load_collection(client, collection_name):
            stats["collections_loaded"] += 1

    logger.info("")
    logger.info("📊 Post-Restore Summary:")
    logger.info(f"   Indexes created: {stats['indexes_created']}")
    logger.info(f"   Collections loaded: {stats['collections_loaded']}")
    logger.info("✅ Post-restore complete!")


if __name__ == "__main__":
    main()
