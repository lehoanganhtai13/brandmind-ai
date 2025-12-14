"""
Data models for retrieval module.

All search results use typed Pydantic models instead of Dict to ensure
type safety and clear API contracts.
"""

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
