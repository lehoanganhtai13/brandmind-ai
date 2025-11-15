"""Pydantic models for the document processing pipeline."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TableInfo(BaseModel):
    """Information about an extracted table."""

    html_content: str = Field(..., description="Raw HTML table content")
    start_pos: int = Field(..., description="Position in markdown content")
    end_pos: int = Field(..., description="End position in markdown content")
    page_number: int = Field(..., description="Page number where table was found")
    page_file: Optional[str] = Field(None, description="Path to page markdown file")


class PDFParseResult(BaseModel):
    """Result of PDF parsing with file-based storage metadata."""

    content: str = Field(..., description="Markdown content for table processing")
    pages: int = Field(..., description="Number of pages processed")
    tables_extracted: int = Field(default=0, description="Number of tables found")
    processing_time: float = Field(..., description="Processing time in seconds")
    file_path: str = Field(..., description="Original file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    output_directory: str = Field(
        ..., description="Directory where page files were saved"
    )
    page_files: List[str] = Field(
        default_factory=list, description="List of page file paths"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional metadata"
    )


class TableSummary(BaseModel):
    """Result of table summarization."""

    original_table_html: str = Field(..., description="Original HTML table")
    summary_markdown: str = Field(..., description="Generated summary")
    page_number: int = Field(..., description="Page number of original table")
    processing_time: Optional[float] = Field(
        None, description="Time to generate summary"
    )
