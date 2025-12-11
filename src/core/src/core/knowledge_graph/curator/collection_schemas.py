"""
Collection schema definitions for Knowledge Graph dual storage.

Defines Milvus collection schemas for entity descriptions and relation descriptions
with BM25 sparse vector support for hybrid search.
"""

from config.system_config import SETTINGS
from shared.database_clients.vector_database.milvus.utils import (
    DataType,
    IndexConfig,
    IndexType,
    MetricType,
    SchemaField,
)

# BM25 Function Configuration for EntityDescriptions
# Maps sparse_field_name -> text_field_name
ENTITY_BM25_CONFIG = {
    "description_sparse": "description",
    "name_sparse": "name",
}

# Entity Descriptions Schema
ENTITY_DESCRIPTIONS_SCHEMA = [
    SchemaField(
        field_name="id",
        field_type=DataType.STRING,
        is_primary=True,
        field_description="Entity UUID",
    ),
    SchemaField(
        field_name="graph_id",
        field_type=DataType.STRING,
        field_description="Reference ID in Graph DB",
    ),
    SchemaField(
        field_name="name",
        field_type=DataType.STRING,
        field_description="Entity name",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="type",
        field_type=DataType.STRING,
        field_description="Entity type for filtering",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="description",
        field_type=DataType.STRING,
        field_description="Entity description text",
    ),
    SchemaField(
        field_name="description_embedding",
        field_type=DataType.DENSE_VECTOR,
        dimension=SETTINGS.EMBEDDING_DIM,
        field_description="Description semantic embedding",
        index_config=IndexConfig(
            index=True, index_type=IndexType.HNSW, metric_type=MetricType.COSINE
        ),
    ),
    SchemaField(
        field_name="description_sparse",
        field_type=DataType.SPARSE_VECTOR,
        field_description="BM25 sparse for description",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="name_embedding",
        field_type=DataType.DENSE_VECTOR,
        dimension=SETTINGS.EMBEDDING_DIM,
        field_description="Name semantic embedding",
        index_config=IndexConfig(
            index=True, index_type=IndexType.HNSW, metric_type=MetricType.COSINE
        ),
    ),
    SchemaField(
        field_name="name_sparse",
        field_type=DataType.SPARSE_VECTOR,
        field_description="BM25 sparse for name",
        index_config=IndexConfig(index=True),
    ),
]


# BM25 Function Configuration for RelationDescriptions
RELATION_BM25_CONFIG = {
    "description_sparse": "description",
}

# Relation Descriptions Schema
RELATION_DESCRIPTIONS_SCHEMA = [
    SchemaField(
        field_name="id",
        field_type=DataType.STRING,
        is_primary=True,
        field_description="Relation UUID",
    ),
    SchemaField(
        field_name="source_entity_id",
        field_type=DataType.STRING,
        field_description="Source entity ID",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="target_entity_id",
        field_type=DataType.STRING,
        field_description="Target entity ID",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="relation_type",
        field_type=DataType.STRING,
        field_description="Type of relation",
        index_config=IndexConfig(index=True),
    ),
    SchemaField(
        field_name="description",
        field_type=DataType.STRING,
        field_description="Relation description",
    ),
    SchemaField(
        field_name="description_embedding",
        field_type=DataType.DENSE_VECTOR,
        dimension=SETTINGS.EMBEDDING_DIM,
        field_description="Semantic embedding",
        index_config=IndexConfig(
            index=True, index_type=IndexType.HNSW, metric_type=MetricType.COSINE
        ),
    ),
    SchemaField(
        field_name="description_sparse",
        field_type=DataType.SPARSE_VECTOR,
        field_description="BM25 sparse for description",
        index_config=IndexConfig(index=True),
    ),
]
