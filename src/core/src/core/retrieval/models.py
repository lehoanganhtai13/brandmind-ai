"""
Data models for retrieval module.

All search results use typed Pydantic models instead of Dict to ensure
type safety and clear API contracts.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentChunkResult(BaseModel):
    """
    Search result from Document Library.

    Represents a single document chunk returned from hybrid search,
    containing the text content and source metadata for agent context.

    Attributes:
        id: Unique chunk identifier (UUID)
        content: Text content of the chunk
        source: Source hierarchy (e.g., "Chapter 9 > Section 3 > Page 245")
        original_document: Name of the source book/document
        author: Author(s) of the document
        score: Search relevance score from RRF ranking
    """

    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Text content of the chunk")
    source: str = Field(..., description="Source hierarchy (chapter/section/page)")
    original_document: str = Field(..., description="Name of the source book/document")
    author: str = Field(default="", description="Author(s) of the document")
    score: float = Field(default=0.0, description="Search relevance score")


class SeedNode(BaseModel):
    """
    Entity node found via EntityDescriptions search.

    Used as starting point for local search PPR traversal.
    """

    id: str = Field(..., description="Entity UUID in Vector DB")
    graph_id: str = Field(..., description="Node ID in Graph DB")
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (e.g., MarketingConcept)")
    description: str = Field(default="", description="Entity description")
    score: float = Field(default=0.0, description="Search relevance score")


class GraphNode(BaseModel):
    """
    Node in the knowledge graph sub-graph.

    Extracted from FalkorDB during K-hop traversal.
    """

    id: str = Field(..., description="Node ID in Graph DB")
    type: str = Field(..., description="Node label/type")
    name: str = Field(default="", description="Node name property")
    properties: dict = Field(
        default_factory=dict, description="Additional node properties"
    )


class GraphEdge(BaseModel):
    """
    Edge in the knowledge graph sub-graph.

    Contains relation metadata and reference to vector DB embedding.
    """

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relation_type: str = Field(..., description="Relation type (e.g., RELATES_TO)")
    description: str = Field(
        default="", description="Relation description text from Graph DB"
    )
    vector_db_ref_id: Optional[str] = Field(
        default=None, description="Reference ID in RelationDescriptions collection"
    )
    source_chunk: Optional[str] = Field(
        default=None, description="Source chunk ID for provenance"
    )


class SubgraphData(BaseModel):
    """
    Extracted K-hop sub-graph from graph database.

    Contains all nodes and edges discovered during BFS traversal
    from seed nodes. Used as input for PPR computation.
    """

    nodes: Dict[str, GraphNode] = Field(
        default_factory=dict, description="Node ID -> GraphNode mapping"
    )
    edges: List[GraphEdge] = Field(
        default_factory=list, description="All edges in sub-graph"
    )


class GlobalRelation(BaseModel):
    """
    Relation found via RelationDescriptions search with enriched entity data.

    Contains complete source and target entity information (not just IDs)
    to enable meaningful verbalization and context assembly. Also includes
    source_chunk for provenance tracking back to original documents.
    """

    id: str = Field(..., description="Relation UUID in Vector DB")
    source_entity: GraphNode = Field(
        ..., description="Source entity with full metadata"
    )
    target_entity: GraphNode = Field(
        ..., description="Target entity with full metadata"
    )
    relation_type: str = Field(..., description="Relation type")
    description: str = Field(..., description="Relation description text")
    source_chunk: Optional[str] = Field(
        default=None, description="Source chunk ID for provenance tracking"
    )
    score: float = Field(default=0.0, description="Search relevance score")


class SourceMetadata(BaseModel):
    """
    Source document metadata from DocumentChunks.

    Provides provenance information for knowledge tracing.
    """

    source: str = Field(..., description="Source hierarchy (chapter/section/page)")
    original_document: str = Field(..., description="Book/document name")
    author: str = Field(default="", description="Author(s)")


class VerbalizedFact(BaseModel):
    """
    Verbalized knowledge fact for agent consumption.

    Combines path/relation data with human-readable text representation.
    """

    type: str = Field(..., description="Fact type: 'local' or 'global'")
    text: str = Field(..., description="Human-readable fact representation")
    source_chunk_ids: List[str] = Field(
        default_factory=list, description="Chunk IDs for provenance lookup"
    )
    source_metadata: List[SourceMetadata] = Field(
        default_factory=list, description="Enriched source metadata"
    )
    # Local path fields
    source_node: Optional[GraphNode] = Field(default=None, description="Starting node")
    destination_node: Optional[GraphNode] = Field(default=None, description="End node")
    intermediate_nodes: List[GraphNode] = Field(
        default_factory=list, description="Bridge nodes"
    )
    edges: List[GraphEdge] = Field(default_factory=list, description="Path edges")
    ppr_score: float = Field(default=0.0, description="PPR ranking score")
    semantic_score: float = Field(default=0.0, description="Path semantic score")
    # Global relation fields
    relation: Optional[GlobalRelation] = Field(
        default=None, description="Global relation (for type='global')"
    )
