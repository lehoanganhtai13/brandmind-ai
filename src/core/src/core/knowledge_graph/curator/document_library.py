import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from config.system_config import SETTINGS
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.database_clients.vector_database.milvus.utils import (
    DataType,
    ElementType,
    IndexConfig,
    IndexType,
    MetricType,
    SchemaField,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder

# BM25 Function Configuration
# Maps sparse_field_name -> text_field_name
# Each sparse field can have its own BM25 function
BM25_FUNCTION_CONFIG = {
    "content_sparse": "content",  # content (VARCHAR) -> content_sparse (SPARSE)
}

# Document Chunks Schema
DOCUMENT_CHUNKS_SCHEMA = [
    SchemaField(
        field_name="id",
        field_type=DataType.STRING,
        is_primary=True,
        field_description="Unique chunk ID",
    ),
    SchemaField(
        field_name="content",
        field_type=DataType.STRING,
        field_description="Original chunk text content",
    ),
    SchemaField(
        field_name="content_embedding",
        field_type=DataType.DENSE_VECTOR,
        dimension=SETTINGS.EMBEDDING_DIM,
        field_description="Dense embedding of chunk content",
        index_config=IndexConfig(
            index=True,
            index_type=IndexType.HNSW,
            metric_type=MetricType.COSINE,
        ),
    ),
    SchemaField(
        field_name="content_sparse",
        field_type=DataType.SPARSE_VECTOR,
        field_description="BM25 sparse vector of chunk content",
        index_config=IndexConfig(
            index=True,
            # index_type and metric_type are auto-determined
        ),
    ),
    SchemaField(
        field_name="source",
        field_type=DataType.STRING,
        field_description="Source hierarchy for filtering",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="original_document",
        field_type=DataType.STRING,
        field_description="Original document name",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="author",
        field_type=DataType.STRING,
        field_description="Author(s)",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="pages",
        field_type=DataType.ARRAY,
        element_type=ElementType.STRING,
        field_description="List of page files",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="word_count",
        field_type=DataType.INT,
        field_description="Word count metadata",
    ),
]


async def build_document_library(
    chunks_path: Path,
    vector_db: BaseVectorDatabase,
    embedder: BaseEmbedder,
    collection_name: str = "DocumentChunks",
    batch_size: int = 50,
    progress_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Build document library from chunks.

    Process:
    1. Load chunks from JSON
    2. Create/verify collection schema
    3. For each batch:
       a. Embed chunk contents
       b. Prepare data with metadata
       c. Upsert to Vector DB
       d. Save progress

    Args:
        chunks_path: Path to chunks.json
        vector_db: Vector database client
        embedder: Embedder client
        collection_name: Name of the collection
        batch_size: Number of chunks per batch
        progress_path: Path to save progress checkpoint

    Returns:
        Summary dict with processed count and stats
    """
    # Load chunks
    with open(chunks_path, "r") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    total_chunks = len(chunks)
    logger.info(f"Loaded {total_chunks} chunks from {chunks_path}")

    # Load progress if exists
    processed_ids = set()
    if progress_path and progress_path.exists():
        with open(progress_path, "r") as f:
            progress = json.load(f)
            processed_ids = set(progress.get("processed_ids", []))
        logger.info(f"Resuming from {len(processed_ids)} processed chunks")

    # Filter unprocessed chunks
    chunks_to_process = [c for c in chunks if c["id"] not in processed_ids]
    logger.info(f"Processing {len(chunks_to_process)} remaining chunks")

    # Create collection if needed
    # Note: We use create_collection which handles schema creation
    # If collection exists, we assume schema is correct or user handles it.
    # But for initial build, we might want to ensure it exists with correct schema.
    if not await vector_db.async_has_collection(collection_name):
        logger.info(f"Creating collection {collection_name}...")
        await vector_db.async_create_collection(
            collection_name=collection_name,
            collection_structure=DOCUMENT_CHUNKS_SCHEMA,
            bm25_function_config=BM25_FUNCTION_CONFIG,
        )

    # Process in batches
    stats = {"embedded": 0, "upserted": 0, "errors": 0}

    for i in range(0, len(chunks_to_process), batch_size):
        batch = chunks_to_process[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(chunks_to_process) + batch_size - 1) // batch_size

        try:
            # Extract contents for embedding
            contents = [c["content"] for c in batch]

            # Embed contents
            embeddings = await embedder.aget_text_embeddings(contents)
            stats["embedded"] += len(embeddings)

            # Prepare data for upsert
            upsert_data = []
            for chunk, emb in zip(batch, embeddings):
                metadata = chunk.get("metadata", {})
                upsert_data.append(
                    {
                        "id": chunk["id"],
                        "content_embedding": emb,  # emb is List[float] now
                        "source": metadata.get("source", ""),
                        "original_document": metadata.get("original_document", ""),
                        "author": metadata.get("author", ""),
                        "pages": metadata.get("pages", []),
                        "word_count": metadata.get("word_count", 0),
                        "content": chunk["content"],
                        # content_sparse is auto-generated by Milvus
                    }
                )

            # Upsert to Vector DB
            await vector_db.async_insert_vectors(
                data=upsert_data,
                collection_name=collection_name,
            )
            stats["upserted"] += len(upsert_data)

            # Update progress
            for chunk in batch:
                processed_ids.add(chunk["id"])

            if progress_path:
                with open(progress_path, "w") as f:
                    json.dump({"processed_ids": list(processed_ids)}, f)

            logger.info(
                f"Batch {batch_num}/{total_batches}: "
                f"Embedded {len(embeddings)}, Upserted {len(upsert_data)}"
            )

        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            stats["errors"] += 1

    logger.info(f"Document library build complete: {stats}")
    return stats
