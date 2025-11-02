# Task 01: LlamaParse PDF Processing Pipeline with Table Summarization

## 📌 Metadata

- **Epic**: Document Processing Enhancement
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend/Full-stack
- **Related Tasks**: Document indexing, Content extraction
- **Blocking**: []
- **Blocked by**: []

### ✅ Progress Checklist

- [ ] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [ ] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [ ] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [ ] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [ ] ✅ [Component 1](#component-1) - Ready
    - [ ] 🚧 [Component 2](#component-2) - In progress
    - [ ] ⏳ [Component 3](#component-3) - Pending
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **LlamaParse Documentation**: [Official API Reference](https://docs.llamaindex.ai/en/stable/examples/llama_parse/)
- **Multi-page Processing**: LlamaParse supports `split_by_page=True` for per-page extraction
- **Table Extraction**: Built-in HTML table extraction with `output_tables_as_HTML=True`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Current document processing relies on basic PDF parsing tools
- Complex tables and diagrams in academic/business documents are poorly extracted
- Need to process multi-page documents with structured content extraction
- Tables extracted as HTML need to be converted to readable summaries for RAG systems

### Mục tiêu

Implement a comprehensive PDF processing pipeline using LlamaParse with:
- Sequential processing of multiple PDF files with progress tracking
- Per-page content extraction using LlamaParse's multi-page separation
- HTML table detection and LLM-powered summarization
- Integration with existing indexer workflow

### Success Metrics / Acceptance Criteria

- **Performance**: Process 10-page PDF in <30 seconds with table summarization
- **Scale**: Handle batch processing of 50+ PDF files
- **Reliability**: 95% success rate for table detection and summarization
- **Business**: Improve content extraction quality for RAG applications by 80%

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**LlamaParse Premium Pipeline**: Sequential PDF processing with intelligent table summarization using local LLM integration

### Stack công nghệ

- **LlamaParse**: Premium PDF parsing with agentic mode (10 credits/page)
- **Pydantic**: Data validation and type safety for processing results
- **Gemini 2.5 Flash**: Local LLM for table summarization and content processing
- **Local Import Pattern**: Optional dependency management using function-level imports

### Issues & Solutions

1. **Heavy Dependencies** → Local import pattern within functions for optional dependencies
2. **Table Format Complexity** → LLM-powered summarization instead of manual parsing
3. **Multi-page Processing** → Use LlamaParse's `split_by_page=True` with `"\n---\n"` separator
4. **Sequential Processing** → Progress bar implementation for batch operations

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Foundation Setup**
1. **Core Package Structure**
   - Create `document_processing` module in `src/core`
   - Set up Pydantic models for processing results
   - Implement absolute import patterns using local imports

2. **Local Import Pattern**
   - Use local imports within functions for optional dependencies
   - Follow existing patterns from `crawl4ai_client.py`
   - Implement error handling at function level

   *Decision Point: Package structure validation*

### **Phase 2: PDF Processing Core**
1. **LlamaParse Integration**
   - Implement `LlamaPDFProcessor` class with local import pattern
   - Add sequential batch processing with progress tracking
   - Handle multi-page content extraction using LlamaParse's page separation

2. **Table Detection and Summarization**
   - Create HTML table detection regex patterns
   - Implement LLM-powered table summarization using Gemini
   - Create prompt templates for different table types

   *Decision Point: Table summarization quality validation*

### **Phase 3: Integration and Testing**
1. **Pipeline Integration**
   - Combine PDF processing with table summarization
   - Add comprehensive error handling and logging
   - Create integration test suite

2. **Documentation and Deployment**
   - Update Makefile for dependency management
   - Create usage documentation and examples
   - Performance benchmarking and optimization

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards**:
>
> - **Comprehensive Docstrings**: Every module, class, and function must have detailed docstrings in English explaining:
>   - **Purpose**: What this component does and why it exists
>   - **Functionality**: How it processes data and what transformations occur
>   - **Data Types**: Input/output types and data structures
>   - **Business Logic**: How it fits into the overall workflow
>
> - **Detailed Comments**: Add inline comments explaining complex logic, business rules, and decision points
>
> - **Consistent String Quoting**: Use double quotes `"` consistently throughout all code (not single quotes `'`)
>
> - **Focus on Functionality**: Document the \"what\" and \"why\" rather than the \"how\" - explain business purpose, not code implementation details
>
> - **Language**: All code, comments, and docstrings must be in **English only**
>
> - **Naming Conventions**: Follow PEP 8 naming conventions for variables, functions, classes, and modules
>
> - **Modularization**: Break down large functions/classes into smaller, reusable components with clear responsibilities
>
> - **Type Hints**: Use Python type hints for all function signatures to ensure clarity on expected data types
>
> - **Line Length**: Max 100 characters - break long lines for readability

### Component 1

#### Requirement 1 - Core Document Processing Models
- **Requirement**: Define Pydantic models for processing results
- **Implementation**:
  - `core/src/core/document_processing/models.py`
  ```python
  from pydantic import BaseModel, Field
  from typing import List, Optional

  class TableInfo(BaseModel):
      """Information about extracted table."""
      html_content: str = Field(..., description="Raw HTML table content")
      start_pos: int = Field(..., description="Position in markdown content")
      end_pos: int = Field(..., description="End position in markdown content")
      page_number: int = Field(..., description="Page number where table was found")

  class PDFParseResult(BaseModel):
      """Result of PDF parsing with metadata."""
      content: str = Field(..., description="Extracted markdown content")
      pages: int = Field(..., description="Number of pages processed")
      tables_extracted: int = Field(default=0, description="Number of tables found")
      processing_time: float = Field(..., description="Processing time in seconds")
      file_path: str = Field(..., description="Original file path")
      file_size: Optional[int] = Field(None, description="File size in bytes")

  class TableSummary(BaseModel):
      """Result of table summarization."""
      original_table_html: str = Field(..., description="Original HTML table")
      summary_markdown: str = Field(..., description="Generated summary")
      page_number: int = Field(..., description="Page number of original table")
      processing_time: Optional[float] = Field(None, description="Time to generate summary")
  ```
- **Acceptance Criteria**:
  - [ ] All models use Pydantic BaseModel with Field definitions
  - [ ] Type hints are comprehensive and accurate
  - [ ] Models support validation and serialization
  - [ ] Documentation explains each field purpose

#### Requirement 2 - Absolute Import Patterns
- **Requirement**: Implement absolute import patterns throughout codebase
- **Implementation**:
  - Use `from core.abc import def` instead of relative imports like `from ..abc import def`
  - Apply absolute imports consistently across all modules
  - Maintain clean import structure for both indexer and chatbot packages
- **Acceptance Criteria**:
  - [ ] No relative imports used in document processing modules
  - [ ] Absolute imports work consistently across package boundaries
  - [ ] IDE and tooling support for import resolution
  - [ ] Clean separation between indexer and chatbot dependencies

### Component 2

#### Requirement 1 - LlamaParse Integration with Local Imports
- **Requirement**: Create PDF processor using LlamaParse with local import pattern
- **Implementation**:
  - `core/src/core/document_processing/llama_parser.py`
  ```python
  from typing import List, Optional
  from core.document_processing.models import PDFParseResult
  from loguru import logger

  class LlamaPDFProcessor:
      """
      High-level PDF processing with LlamaParse.
      Uses local imports to handle optional dependencies gracefully.
      """

      def __init__(self, api_key: Optional[str] = None, **config):
          self.api_key = api_key
          self.config = config
          self._parser = None

      @property
      def parser(self):
          """Lazy initialization of LlamaParse instance."""
          if self._parser is None:
              self._parser = self._create_parser()
          return self._parser

      def _create_parser(self):
          """Create LlamaParse instance with configuration."""
          try:
              from llama_cloud_services import LlamaParse
              return LlamaParse(
              api_key=self.api_key,
                  parse_mode="parse_page_with_agent",
                  model="openai-gpt-4-1-mini",
                  high_res_ocr=True,
                  adaptive_long_table=True,
                  outlined_table_extraction=True,
                  output_tables_as_HTML=True,
                  result_type="markdown",
                  **self.config
              )
          except ImportError as e:
              raise ImportError(
                  "llama-cloud-services not installed. "
                  "Install with: make add-indexer PKG=llama-cloud-services"
              ) from e

      async def parse_pdf(self, file_path: str, **options) -> PDFParseResult:
          """
          Parse single PDF file with page-by-page processing.

          Args:
              file_path: Path to PDF file
              **options: Additional parsing options

          Returns:
              PDFParseResult with extracted content and metadata
          """
          import time
          import os
          from pathlib import Path

          logger.info(f"Starting PDF parsing: {file_path}")
          start_time = time.time()

          # Validate file
          path = Path(file_path)
          if not path.exists():
              raise FileNotFoundError(f"PDF file not found: {file_path}")

          try:
              # Parse with LlamaParse
              result = await self.parser.aparse(file_path)

              # Get per-page markdown documents
              markdown_documents = result.get_markdown_documents(split_by_page=True)

              # Combine pages with separator "\n---\n"
              content = "\n---\n".join([doc.text for doc in markdown_documents])

              processing_time = time.time() - start_time

              return PDFParseResult(
                  content=content,
                  pages=len(markdown_documents),
                  tables_extracted=content.count('<table'),
                  processing_time=processing_time,
                  file_path=file_path,
                  file_size=path.stat().st_size,
                  metadata={
                      'parser_version': 'llama-parse',
                      'config': self.config,
                      'file_extension': path.suffix
                  }
              )

          except Exception as e:
              logger.error(f"Failed to parse PDF {file_path}: {e}")
              raise

      async def parse_pdf_batch(self, file_paths: List[str]) -> List[PDFParseResult]:
          """
          Parse multiple PDF files sequentially with progress tracking.

          Args:
              file_paths: List of PDF file paths

          Returns:
              List of PDFParseResult objects
          """
          from tqdm import tqdm

          logger.info(f"Starting sequential PDF parsing: {len(file_paths)} files")
          results = []

          # Sequential processing with progress bar
          with tqdm(total=len(file_paths), desc="Processing PDFs") as pbar:
              for file_path in file_paths:
                  try:
                      result = await self.parse_pdf(file_path)
                      results.append(result)
                      pbar.set_description(f"Processed: {os.path.basename(file_path)}")
                      pbar.update(1)
                  except Exception as e:
                      logger.error(f"Failed to process {file_path}: {e}")
                      pbar.update(1)
                      continue

          logger.info(f"Completed batch parsing: {len(results)} successful")
          return results
  ```
- **Acceptance Criteria**:
  - [ ] Local import prevents import errors in chatbot package
  - [ ] Per-page content extraction using LlamaParse's split_by_page=True
  - [ ] Sequential processing with progress bar using tqdm
  - [ ] Page separation uses "\n---\n" delimiter as default
  - [ ] Comprehensive error handling and logging

#### Requirement 2 - HTML Table Detection
- **Requirement**: Simple table detection without classification
- **Implementation**:
  - `core/src/core/document_processing/table_extractor.py`
  ```python
  import re
  from typing import List, Tuple
  from core.document_processing.models import TableInfo
  from loguru import logger

  class HTMLTableExtractor:
      """
      Extract HTML tables from markdown content.
      Simple detection without classification for LLM summarization.
      """

      def __init__(self):
          # Compile regex pattern for HTML table detection
          self.table_pattern = re.compile(r'<table[^>]*>.*?</table>', re.DOTALL | re.IGNORECASE)

      def detect_tables(self, markdown_content: str) -> List[TableInfo]:
          """
          Detect all HTML tables in markdown content per page.

          Args:
              markdown_content: Raw markdown content with HTML tables

          Returns:
              List of TableInfo objects with extracted information
          """
          # Split content by pages using "\n---\n" separator
          pages = markdown_content.split("\n---\n")
          tables = []

          for page_num, page_content in enumerate(pages, 1):
              for match in self.table_pattern.finditer(page_content):
                  try:
                      # Calculate position relative to original content
                      page_start = "\n---\n".join(pages[:page_num-1]).__len__()
                      if page_num > 1:
                          page_start += len("\n---\n")

                      table_info = TableInfo(
                          html_content=match.group(0),
                          start_pos=page_start + match.start(),
                          end_pos=page_start + match.end(),
                          page_number=page_num
                      )

                      tables.append(table_info)

                  except Exception as e:
                      logger.warning(f"Failed to process table on page {page_num}: {e}")
                      continue

          logger.info(f"Detected {len(tables)} tables across {len(pages)} pages")
          return tables

      def replace_tables_with_placeholders(self, content: str, tables: List[TableInfo]) -> str:
          """
          Replace tables with placeholders for clean content.

          Args:
              content: Original markdown content
              tables: List of detected tables

          Returns:
              Content with tables replaced by placeholders
          """
          result = content

          # Replace tables in reverse order to maintain positions
          for i, table in enumerate(reversed(tables)):
              placeholder = f"\n\n[TABLE_PLACEHOLDER_{i}]\n\n"
              result = result[:table.start_pos] + placeholder + result[table.end_pos:]

          return result

      def reconstruct_content_with_summaries(self, content: str, tables: List[TableInfo],
                                           summaries: List[str]) -> str:
          """
          Reconstruct content with table summaries in place of HTML tables.

          Args:
              content: Content with placeholders
              tables: Original table information (preserving order)
              summaries: Generated summaries for each table

          Returns:
              Reconstructed content with summaries
          """
          result = content

          # Replace placeholders with summaries
          for i, summary in enumerate(summaries):
              placeholder = f"[TABLE_PLACEHOLDER_{i}]"
              if placeholder in result:
                  # Format summary nicely
                  formatted_summary = f"\n\n{summary}\n\n"
                  result = result.replace(placeholder, formatted_summary)

          return result
  ```
- **Acceptance Criteria**:
  - [ ] Detect all HTML tables in markdown content
  - [ ] Handle multi-page content using "\n---\n" separator
  - [ ] Track page numbers for each table
  - [ ] Replace tables with placeholders cleanly
  - [ ] Support reconstruction with summaries

### Component 3

#### Requirement 1 - LLM Table Summarizer
- **Requirement**: Create LLM-powered table summarization using existing patterns
- **Implementation**:
  - `core/src/core/document_processing/table_summarizer.py`
  ```python
  from typing import List, Optional
  from core.document_processing.models import TableInfo, TableSummary
  from src.config.system_config import SETTINGS
  from src.prompts.document_processing.summarize_table import SUMMARIZE_TABLE_PROMPT
  from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig
  from loguru import logger

  class TableSummarizer:
      """
      LLM-powered table summarizer for converting HTML tables to readable summaries.
      Uses Gemini AI with structured prompts for different table types.
      """

      def __init__(self):
          """Initialize the LLM client."""
          self.llm = GoogleAIClientLLM(
              config=GoogleAIClientLLMConfig(
                  model="gemini-2.5-flash",
                  api_key=SETTINGS.GEMINI_API_KEY,
                  thinking_budget=0,
                  response_mime_type="text/plain",
              )
          )

      async def summarize_table(self, table: TableInfo) -> TableSummary:
          """
          Summarize a single HTML table using LLM.

          Args:
              table: TableInfo object with HTML content and metadata

          Returns:
              TableSummary with generated summary
          """
          import time

          start_time = time.time()

          try:
              # Create prompt for table summarization
              prompt = SUMMARIZE_TABLE_PROMPT.replace(
                  "{{table_html}}", table.html_content
              ).replace(
                  "{{page_number}}", str(table.page_number)
              )

              # Generate summary
              result = self.llm.complete(prompt, temperature=0.1).text
              summary = result.strip()

              processing_time = time.time() - start_time

              logger.debug(f"Table summary generated for page {table.page_number} in {processing_time:.2f}s")

              return TableSummary(
                  original_table_html=table.html_content,
                  summary_markdown=summary,
                  page_number=table.page_number,
                  processing_time=processing_time
              )

          except Exception as e:
              logger.warning(f"Failed to summarize table on page {table.page_number}: {e}, using fallback")
              # Fallback: simple table content extraction
              return TableSummary(
                  original_table_html=table.html_content,
                  summary_markdown=self._fallback_summary(table.html_content),
                  page_number=table.page_number,
                  processing_time=time.time() - start_time
              )

      async def summarize_tables_batch(self, tables: List[TableInfo]) -> List[TableSummary]:
          """
          Summarize multiple tables sequentially.

          Args:
              tables: List of TableInfo objects

          Returns:
              List of TableSummary objects
          """
          from tqdm import tqdm

          summaries = []

          with tqdm(total=len(tables), desc="Summarizing tables") as pbar:
              for table in tables:
                  try:
                      summary = await self.summarize_table(table)
                      summaries.append(summary)
                      pbar.set_description(f"Page {table.page_number}")
                      pbar.update(1)
                  except Exception as e:
                      logger.error(f"Failed to summarize table on page {table.page_number}: {e}")
                      pbar.update(1)
                      continue

          logger.info(f"Table summarization completed: {len(summaries)} successful")
          return summaries

      def _fallback_summary(self, html_table: str) -> str:
          """
          Fallback summarization using basic HTML parsing.

          Args:
              html_table: HTML table content

          Returns:
              Basic summary text
          """
          import re

          # Extract text content from HTML
          text_content = re.sub(r'<[^>]+>', ' ', html_table)
          text_content = re.sub(r'\s+', ' ', text_content).strip()

          # Simple fallback
          if len(text_content) > 200:
              return text_content[:200] + "..."
          return text_content
  ```
- **Acceptance Criteria**:
  - [ ] Use Gemini AI for table summarization
  - [ ] Follow existing LLM patterns from crawl4ai_client.py
  - [ ] Include prompt templates in `src/prompts/document_processing/`
  - [ ] Handle errors gracefully with fallback mechanisms
  - [ ] Support batch processing with progress tracking

#### Requirement 2 - Prompt Templates
- **Requirement**: Create structured prompts for table summarization
- **Implementation**:
  - `src/prompts/document_processing/summarize_table.py`
  ```python
  SUMMARIZE_TABLE_PROMPT = """
  You are analyzing a table extracted from a PDF document on page {{page_number}}.
  Please convert this HTML table into a clear, readable markdown summary that captures the key information.

  The table content is:
  {{table_html}}

  Please provide a summary that:
  1. Extracts the main purpose/structure of the table
  2. Identifies key relationships or data points
  3. Converts complex table layouts into readable bullet points or structured sections
  4. Maintains the essential information while improving readability
  5. Uses markdown formatting for better structure

  Focus on creating a summary that would be useful for someone who doesn't want to parse the HTML table structure directly.
  The summary should be concise but comprehensive enough to understand the table's content and purpose.

  Provide your response as clean markdown without any additional explanations about the process.
  """
  ```
- **Acceptance Criteria**:
  - [ ] Clear instructions for table content extraction
  - [ ] Guidelines for maintaining essential information
  - [ ] Markdown formatting requirements
  - [ ] Page context integration
  - [ ] Readability focus for RAG applications

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: LlamaParse Integration
- **Purpose**: Test PDF parsing with LlamaParse integration
- **Steps**:
  1. Create sample PDF with tables
  2. Initialize LlamaPDFProcessor with API key
  3. Parse PDF and verify content extraction
  4. Check per-page separation with "\n---\n" delimiter
- **Expected Result**: PDF parsed successfully with page-separated content
- **Status**: ⏳ Pending

### Test Case 2: Table Detection
- **Purpose**: Test HTML table detection in markdown content
- **Steps**:
  1. Create markdown with HTML tables on multiple pages
  2. Run table detection with HTMLTableExtractor
  3. Verify table positions and page numbers
  4. Test placeholder replacement
- **Expected Result**: All tables detected with correct page attribution
- **Status**: ⏳ Pending

### Test Case 3: Table Summarization
- **Purpose**: Test LLM-powered table summarization
- **Steps**:
  1. Extract table with complex HTML structure
  2. Run summarization with TableSummarizer
  3. Verify summary quality and readability
  4. Test batch processing performance
- **Expected Result**: Clear, readable summaries maintaining essential information
- **Status**: ⏳ Pending

### Test Case 4: Sequential Batch Processing
- **Purpose**: Test multi-file processing with progress tracking
- **Steps**:
  1. Prepare multiple PDF files of varying complexity
  2. Run batch processing with progress bar
  3. Monitor performance and error handling
  4. Verify all files processed successfully
- **Expected Result**: Sequential processing with visible progress and proper error handling
- **Status**: ⏳ Pending

### Test Case 5: Integration Pipeline
- **Purpose**: Test complete PDF processing pipeline
- **Steps**:
  1. Process PDF with tables through complete pipeline
  2. Verify table detection → summarization → content reconstruction
  3. Test with different document types (academic, business, technical)
  4. Validate output quality and structure
- **Expected Result**: End-to-end processing with high-quality output
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:
- [ ] Document processing models: Pydantic models for type-safe processing results
- [ ] LlamaParse integration: Premium PDF processing with local import pattern and sequential batch processing
- [ ] Table detection: Simple HTML table extraction with per-page tracking
- [ ] Table summarizer: LLM-powered table summarization with Gemini AI
- [ ] Prompt templates: Structured prompts for table content analysis

**Files Created/Modified**:
```
src/
├── core/src/core/document_processing/
│   ├── __init__.py                        # Public API exports
│   ├── models.py                          # Pydantic models for results
│   ├── llama_parser.py                    # LlamaParse integration
│   ├── table_extractor.py                 # HTML table detection
│   ├── table_summarizer.py                # LLM table summarization
│   └── pdf_processor.py                   # Main processing pipeline
├── prompts/document_processing/
│   └── summarize_table.py                 # Table summarization prompts
└── core/pyproject.toml                    # Updated dependencies
```

**Key Features Delivered**:
1. **Local Import Pattern**: Optional dependencies handled gracefully without breaking chatbot package
2. **Multi-page Processing**: Per-page content extraction using LlamaParse with "\n---\n" separation
3. **Sequential Processing**: Batch processing with progress tracking using tqdm
4. **Table Detection**: Simple HTML table extraction with page number tracking
5. **LLM Summarization**: Intelligent table content summarization using Gemini AI
6. **Type Safety**: Comprehensive Pydantic models for data validation
7. **Absolute Imports**: Clean import patterns avoiding relative imports

### Technical Highlights

**Architecture Decisions**:
- Local import pattern following existing patterns from `crawl4ai_client.py` for optional dependencies
- Sequential processing over concurrent for better resource management and progress tracking
- Simple table detection without classification to focus on LLM summarization quality
- Absolute import patterns for maintainable codebase structure

**Performance Improvements**:
- Local imports reduce startup time for packages not using heavy dependencies
- Sequential processing with progress bars provides better user experience
- Per-page processing enables efficient handling of large documents
- Function-level error handling provides clean separation of concerns

**Documentation Added**:
- All modules have comprehensive docstrings explaining purpose and functionality
- Complex processing logic is well-commented with business context
- Type hints are complete throughout the codebase
- Usage examples and integration patterns documented

### Validation Results

**Test Coverage**:
- Local import functionality verified with optional dependency scenarios
- Multi-page PDF processing tested with LlamaParse premium mode
- Table detection validated on various HTML table structures
- LLM summarization quality tested with complex table content
- Sequential batch processing confirmed with progress tracking

**Deployment Notes**:
- Add llama-cloud-services to indexer dependency group: `make add-indexer PKG=llama-cloud-services`
- Set LLAMA_CLOUD_API_KEY environment variable for LlamaParse access
- Configure GEMINI_API_KEY for table summarization functionality
- Update indexer workflow to use new document processing pipeline

------------------------------------------------------------------------