"""
Collection initialization utilities for Stage 4 indexing.

Handles creation of Milvus collections with proper schemas
and BM25 function configurations. Provides idempotent collection
creation that can be safely called multiple times.
"""

from typing import Dict, List, Optional

from loguru import logger

from shared.database_clients.vector_database.milvus.database import (
    MilvusVectorDatabase,
)
from shared.database_clients.vector_database.milvus.utils import SchemaField


async def ensure_collection_exists(
    client: MilvusVectorDatabase,
    collection_name: str,
    schema: List[SchemaField],
    bm25_config: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Ensure a Milvus collection exists, creating it if necessary.

    This function provides idempotent collection creation, checking for
    existence before attempting to create. It gracefully skips creation
    if the collection already exists.

    Args:
        client: Milvus vector database client instance
        collection_name: Name of the collection to create or verify
        schema: List of SchemaField definitions for collection structure
        bm25_config: Optional BM25 function configuration mapping sparse field
            names to text field names for full-text search

    Returns:
        True if collection was newly created, False if already existed
    """
    if await client.async_has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists, skipping creation")
        return False

    logger.info(f"Creating collection '{collection_name}'...")
    await client.async_create_collection(
        collection_name=collection_name,
        collection_structure=schema,
        bm25_function_config=bm25_config,
    )
    logger.info(f"✅ Collection '{collection_name}' created successfully")
    return True
