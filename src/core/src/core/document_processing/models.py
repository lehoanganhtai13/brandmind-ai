"""Pydantic models for the document processing pipeline."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TableInfo(BaseModel):
    """Information about an extracted table."""

    html_content: str = Field(
        ..., description="Raw table content (HTML or markdown format)"
    )
    table_format: Literal["html", "markdown"] = Field(
        ..., description="Format of the table: 'html' or 'markdown'"
    )
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


class TableChain(BaseModel):
    """
    Represents a chain of consecutive tables that may be fragments of a single
    logical table.

    A chain is formed when multiple tables appear consecutively with only
    whitespace or newlines between them (no text content). Chains can span
    multiple pages:
    - Within same page: table_A → table_B (no text between)
    - Cross-page: last table of page N → first table of page N+1 (no text at boundaries)
    - Multi-page: page1_A → page2_B → page2_C → page3_D (transitive closure)

    This structure enables LLM analysis to determine if fragments should be merged.

    Attributes:
        chain_id (str): Unique identifier (includes "_cross" suffix if spans pages)
        page_number (int): Starting page number (first table's page)
        tables (List[TableInfo]): Ordered list of consecutive fragments (may span pages)
        has_gap_content (bool): Whether non-whitespace content exists between any tables
    """

    chain_id: str = Field(..., description="Unique chain identifier")
    page_number: int = Field(..., description="Starting page number")
    tables: List[TableInfo] = Field(..., description="Ordered table fragments")
    has_gap_content: bool = Field(
        default=False, description="True if text content exists between tables"
    )


class TableMergeDecision(BaseModel):
    """
    Result of LLM table assembly analysis.

    This model captures the LLM's analysis output from the Expert Table Assembly AI,
    which determines if fragments belong together and provides merged result if
    applicable. The model maps directly to the JSON structure returned by the LLM.

    Attributes:
        chain_id (str): Identifier of the analyzed chain
        status (str): "SUCCESS" if merged, "NO_MERGE" if fragments are separate tables
        analysis (Dict[str, Any]): Analysis metadata including total fragments,
            indices merged, and reasoning for the decision
        final_merged_html (Optional[str]): Complete merged table if status=SUCCESS
        processing_time (float): Time taken for LLM analysis
    """

    chain_id: str = Field(..., description="Chain identifier")
    status: str = Field(..., description="SUCCESS or NO_MERGE")
    analysis: Dict[str, Any] = Field(
        ...,
        description=(
            "Analysis metadata: total_fragments_received, fragments_merged, reasoning"
        ),
    )
    final_merged_html: Optional[str] = Field(
        None, description="Merged table HTML if status=SUCCESS"
    )
    processing_time: float = Field(..., description="Processing time in seconds")


class TableMergeReport(BaseModel):
    """
    Detailed report for a single table chain assembly operation.

    This report provides complete traceability for debugging and analysis, capturing
    all input table fragments (including cross-page fragments), LLM assembly analysis,
    and the final merged result if applicable.

    Attributes:
        chain_id (str): Identifier of the processed chain (includes "_cross" if
            spans pages)
        page_number (int): Starting page number (first table's page)
        fragment_count (int): Number of table fragments in the chain
        fragments_info (List[Dict[str, Any]]): Metadata for each fragment including page
        is_cross_page (bool): Whether this chain spans multiple pages
        page_range (str): Page range covered by chain (e.g., "1-3")
        merge_decision (TableMergeDecision): LLM's assembly decision and analysis
        timestamp (str): ISO timestamp of processing
    """

    chain_id: str = Field(..., description="Chain identifier")
    page_number: int = Field(..., description="Starting page number")
    fragment_count: int = Field(..., description="Number of fragments in chain")
    fragments_info: List[Dict[str, Any]] = Field(
        ...,
        description="Metadata for each fragment (position, size, page number)",
    )
    is_cross_page: bool = Field(
        default=False, description="True if chain spans multiple pages"
    )
    page_range: str = Field(..., description="Page range (e.g., '1', '1-2', '1-3')")
    merge_decision: TableMergeDecision = Field(..., description="LLM assembly decision")
    timestamp: str = Field(..., description="Processing timestamp ISO format")


class TableSummarizationReport(BaseModel):
    """
    Report for table summarization operation with full context.

    This report captures the original table content, its location metadata, and the
    generated summary for complete traceability of the summarization process.

    Attributes:
        table_id (str): Unique identifier for this table
        page_number (int): Page number where table is located
        original_table_html (str): Original HTML table content
        summary_markdown (str): Generated summary text
        processing_time (float): Time taken for summarization
        was_merged (bool): Whether this table resulted from a merge operation
        source_chain_id (Optional[str]): Chain ID if table was merged
        timestamp (str): ISO timestamp of processing
    """

    table_id: str = Field(..., description="Unique table identifier")
    page_number: int = Field(..., description="Page number")
    original_table_html: str = Field(..., description="Original table HTML")
    summary_markdown: str = Field(..., description="Generated summary")
    processing_time: float = Field(..., description="Processing time in seconds")
    was_merged: bool = Field(
        default=False, description="Whether this resulted from merge"
    )
    source_chain_id: Optional[str] = Field(
        None, description="Chain ID if table was merged"
    )
    timestamp: str = Field(..., description="Processing timestamp ISO format")
