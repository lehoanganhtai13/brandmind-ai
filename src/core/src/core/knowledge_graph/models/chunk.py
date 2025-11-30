"""Pydantic models for document chunks."""

from typing import List

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Metadata for a document chunk.

    This model stores all contextual information about a chunk including
    its source location in the document hierarchy, page references, and
    document attribution for downstream processing.
    """

    source: str = Field(
        description="Hierarchical source path (e.g., 'Chapter 1/Section 1.1')"
    )
    original_document: str = Field(description="Original document title")
    author: str = Field(description="Document author(s)")
    pages: List[str] = Field(
        description=(
            "List of page IDs this chunk spans (e.g., ['page_5.md', 'page_6.md'])"
        )
    )
    section_summary: str = Field(
        description=("Summary of the section containing this chunk (for context)")
    )
    word_count: int = Field(description="Number of words in chunk content")


class Chunk(BaseModel):
    """
    Represents a single document chunk.

    A chunk is a semantically coherent piece of text extracted from the
    document with complete metadata for tracking its origin and context.
    """

    chunk_id: str = Field(description="Unique identifier for this chunk (UUID)")
    content: str = Field(description="Text content of the chunk")
    metadata: ChunkMetadata = Field(description="Metadata for this chunk")


class ChunkingResult(BaseModel):
    """
    Result of chunking a document.

    Contains all chunks generated from the document along with
    aggregate statistics for validation and monitoring.
    """

    chunks: List[Chunk] = Field(description="List of all chunks generated")
    total_chunks: int = Field(description="Total number of chunks")
    avg_chunk_size: float = Field(description="Average chunk size in words")

    def to_json_file(self, filepath: str) -> None:
        """
        Save chunking result to JSON file with pretty formatting.

        Args:
            filepath: Path to output JSON file
        """
        import json
        from pathlib import Path

        Path(filepath).write_text(
            json.dumps(self.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
