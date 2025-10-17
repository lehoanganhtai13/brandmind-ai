from typing import Optional

from enum import Enum
from pydantic import BaseModel

from shared.utils.base_class import (
    DenseEmbedding, BinaryEmbedding, SparseEmbedding
)


class EmbeddingType(Enum):
    """Enum for different types of embeddings."""
    DENSE = "dense"
    SPARSE = "sparse"
    BINARY = "binary"


class EmbeddingData(BaseModel):
    """
    Data structure for embedding data used for searching in a vector database.
    
    Args:
        field_name (str): Name of the field in the JSON object.
        embeddings (Optional[DenseEmbedding | BinaryEmbedding | SparseEmbedding]): embedding (dense, sparse, or binary).
        query (Optional[str]): Query string for full-text search.
        filtering_expr (Optional[str]): Filtering expression for the embeddings.
        embedding_type (Optional[EmbeddingType]): Type of the embedding (dense, sparse, or binary).
    """
    field_name: str
    embeddings: Optional[DenseEmbedding | BinaryEmbedding | SparseEmbedding] = None
    query: Optional[str] = None
    filtering_expr: Optional[str] = None
    embedding_type: Optional[EmbeddingType] = EmbeddingType.DENSE

    class Config:
        arbitrary_types_allowed = True


class VectorDBBackend(Enum):
    """Enum for different vector database backends."""
    MILVUS = "milvus"
    LANCEDB = "lancedb"


class VectorDBConfig:
    """Base configuration for vector database."""
    def __init__(self, backend: VectorDBBackend, **kwargs):
        self.backend = backend
        self.config = kwargs
