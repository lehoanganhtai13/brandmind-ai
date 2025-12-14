# Task 20: Document Library Search Tool

## 📌 Metadata

- **Epic**: Stage 5 - The Retriever
- **Priority**: High
- **Estimated Effort**: 0.5 days
- **Team**: Backend
- **Related Tasks**: [Stage 5 Planning](../docs/brainstorm/stage_5.md)
- **Blocking**: Task 21 (KG Search), Task 22 (KG Retriever)
- **Blocked by**: Stage 4 completion (DocumentChunks indexed)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1-data-models) - Data models
    - [x] ✅ [Component 2](#component-2-documentretriever-class) - DocumentRetriever class
    - [x] ✅ [Component 3](#component-3-agent-tool-wrapper) - Agent tool wrapper
- [x] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **Stage 5 Spec**: [docs/brainstorm/stage_5.md](../docs/brainstorm/stage_5.md)
- **Existing Module**: [document_library.py](../src/core/src/core/knowledge_graph/curator/document_library.py) - Schema reference

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Agent cần một công cụ để tìm kiếm trong "Kho Sách" (Document Library) - nơi chứa các đoạn text gốc từ sách marketing
- DocumentChunks collection đã được indexed với dense vector + BM25 sparse vector trong Stage 4
- Cần hybrid search để tận dụng cả semantic matching (dense) và keyword matching (BM25)

### Mục tiêu

Xây dựng `DocumentRetriever` class và `search_document_library` tool wrapper cho agent, hỗ trợ hybrid search với metadata filtering để agent có thể tìm kiếm targeted, controlled thông tin từ sách.

### Success Metrics / Acceptance Criteria

- **Performance**: Latency < 500ms cho mỗi search request
- **Functionality**: Hybrid search (dense + BM25) hoạt động chính xác
- **Filtering**: Filter by book, chapter, author hoạt động đúng
- **Integration**: Tool wrapper có thể được gọi bởi agent

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Hybrid Search với RRF**: Sử dụng `async_hybrid_search_vectors` của Milvus với built-in RRFRanker để kết hợp dense vector search và BM25 sparse search.

### Stack công nghệ

- **Milvus**: Vector database, async hybrid search với RRF ranking
- **GeminiEmbedder**: Query embedding với RETRIEVAL mode
- **BaseVectorDatabase/BaseEmbedder**: Type hints sử dụng base classes cho extensibility
- **Pydantic BaseModel**: Typed return models thay vì Dict

### Issues & Solutions

1. **Filter expression syntax** → Sử dụng Milvus filter expression format: `field == "value"` hoặc `field like "%pattern%"`
2. **Query embedding mode** → Sử dụng `EmbeddingMode.RETRIEVAL` cho query embedding, khác với document embedding
3. **Type safety** → Sử dụng `DocumentChunkResult` BaseModel thay vì `Dict` để đảm bảo type safety

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Core Implementation**
1. **Data Models**
   - Tạo `src/core/src/core/retrieval/models.py`
   - Define `DocumentChunkResult` BaseModel

2. **DocumentRetriever Class**
   - Tạo `src/core/src/core/retrieval/` directory structure
   - Implement `DocumentRetriever` class với hybrid search logic
   - *Decision Point: Verify filter expression syntax works with Milvus*

3. **Agent Tool Wrapper**
   - Create tool wrapper với lazy initialization pattern
   - Format output cho agent consumption

### **Phase 2: Testing & Validation**
1. **Integration Testing**
   - Test hybrid search với existing DocumentChunks data
   - Test filter combinations
   - Verify output format

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards**:
>
> - **Comprehensive Docstrings**: Every module, class, and function must have detailed docstrings in English
> - **Type Hints**: Use Python type hints for all function signatures
> - **Pydantic Models**: Use BaseModel for all stable return types (NOT Dict)
> - **Consistent String Quoting**: Use double quotes `"` consistently
> - **Line Length**: Max 100 characters

### Component 1: Data Models

#### Requirement 1 - Create retrieval module structure
- **Requirement**: Create `src/core/src/core/retrieval/` directory with `__init__.py` and `models.py`
- **Implementation**:
  - `src/core/src/core/retrieval/__init__.py`
  ```python
  """
  Retrieval module for document and knowledge graph search.
  
  This module provides search tools for the agent to query:
  - Document Library (raw text passages from books)
  - Knowledge Graph (semantic entities and relationships)
  """
  
  from core.retrieval.models import DocumentChunkResult
  from core.retrieval.document_retriever import DocumentRetriever
  
  __all__ = ["DocumentChunkResult", "DocumentRetriever"]
  ```
  - `src/core/src/core/retrieval/models.py`
  ```python
  """
  Data models for retrieval module.
  
  All search results use typed Pydantic models instead of Dict to ensure
  type safety and clear API contracts.
  """
  
  from typing import List, Optional
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
  ```
- **Acceptance Criteria**:
  - [x] Directory created with `__init__.py`
  - [x] `models.py` exports `DocumentChunkResult`
  - [x] All fields have descriptions

### Component 2: DocumentRetriever Class

#### Requirement 1 - Implement DocumentRetriever
- **Requirement**: Hybrid search retriever class with filter support
- **Implementation**:
  - `src/core/src/core/retrieval/document_retriever.py`
  ```python
  """
  Document retriever for hybrid search on Document Library.
  
  This module provides the DocumentRetriever class which combines dense vector
  search with BM25 sparse search using Milvus's built-in RRF ranking.
  """
  
  from typing import List, Optional
  
  from shared.database_clients.vector_database.base_vector_database import (
      BaseVectorDatabase,
  )
  from shared.database_clients.vector_database.base_class import (
      EmbeddingData,
      EmbeddingType,
  )
  from shared.database_clients.vector_database.milvus.utils import (
      MetricType,
      IndexType,
  )
  from shared.model_clients.embedder.base_embedder import BaseEmbedder
  from core.retrieval.models import DocumentChunkResult
  
  
  class DocumentRetriever:
      """
      Hybrid search retriever for the Document Library.
      
      This retriever performs combined dense vector + BM25 sparse search
      on the DocumentChunks collection using Milvus's built-in RRF (Reciprocal
      Rank Fusion) for result fusion.
      
      Features:
          - Hybrid search combining semantic (dense) and keyword (BM25) matching
          - Metadata filtering by book, chapter, and author
          - Automatic query embedding using the configured embedder
          - Returns typed DocumentChunkResult objects
      
      Example:
          >>> retriever = DocumentRetriever(vector_db=milvus, embedder=gemini)
          >>> results = await retriever.search("marketing strategy", top_k=5)
          >>> for chunk in results:
          ...     print(f"{chunk.source}: {chunk.content[:100]}")
      """
      
      def __init__(
          self,
          vector_db: BaseVectorDatabase,
          embedder: BaseEmbedder,
          collection_name: str = "DocumentChunks"
      ):
          """
          Initialize the document retriever.
          
          Args:
              vector_db: Vector database client implementing BaseVectorDatabase.
                  Should be configured with run_async=True for async operations.
              embedder: Embedder client implementing BaseEmbedder.
                  Should use EmbeddingMode.RETRIEVAL for query embedding.
              collection_name: Name of the document chunks collection in Milvus.
                  Defaults to "DocumentChunks" as created by Stage 4.
          """
          self.vector_db = vector_db
          self.embedder = embedder
          self.collection_name = collection_name
      
      async def search(
          self,
          query: str,
          top_k: int = 10,
          filter_by_book: Optional[str] = None,
          filter_by_chapter: Optional[str] = None,
          filter_by_author: Optional[str] = None,
      ) -> List[DocumentChunkResult]:
          """
          Perform hybrid search on document chunks.
          
          Executes a combined dense vector + BM25 sparse search with RRF fusion.
          Optionally filters by book, chapter, or author metadata.
          
          Args:
              query: Search query text. Will be embedded using the configured embedder.
              top_k: Maximum number of results to return. Default 10.
              filter_by_book: Filter by exact book/document name match.
                  Example: "Kotler Marketing Management"
              filter_by_chapter: Filter by partial chapter/section match.
                  Example: "Chapter 9" will match "Chapter 9 > Section 3"
              filter_by_author: Filter by exact author name match.
                  Example: "Philip Kotler"
          
          Returns:
              List of DocumentChunkResult objects ordered by relevance score.
              Each result contains content, source metadata, and score.
          """
          # 1. Embed query using retrieval mode
          query_embedding = await self.embedder.aget_query_embedding(query)
          
          # 2. Build Milvus filter expression
          filter_parts = []
          if filter_by_book:
              # Exact match on original_document field
              filter_parts.append(f'original_document == "{filter_by_book}"')
          if filter_by_chapter:
              # Partial match on source field using LIKE
              filter_parts.append(f'source like "%{filter_by_chapter}%"')
          if filter_by_author:
              # Exact match on author field
              filter_parts.append(f'author == "{filter_by_author}"')
          filter_expr = " and ".join(filter_parts) if filter_parts else ""
          
          # 3. Prepare hybrid search data (dense + sparse)
          embedding_data = [
              EmbeddingData(
                  embedding_type=EmbeddingType.DENSE,
                  embeddings=query_embedding,
                  field_name="content_embedding",
                  filtering_expr=filter_expr,
              ),
              EmbeddingData(
                  embedding_type=EmbeddingType.SPARSE,
                  query=query,
                  field_name="content_sparse",
                  filtering_expr=filter_expr,
              ),
          ]
          
          # 4. Execute hybrid search with RRF fusion
          raw_results = await self.vector_db.async_hybrid_search_vectors(
              embedding_data=embedding_data,
              output_fields=["id", "content", "source", "original_document", "author"],
              top_k=top_k,
              collection_name=self.collection_name,
              metric_type=MetricType.COSINE,
              index_type=IndexType.HNSW,
          )
          
          # 5. Convert raw dict results to typed DocumentChunkResult objects
          results = [
              DocumentChunkResult(
                  id=r.get("id", ""),
                  content=r.get("content", ""),
                  source=r.get("source", ""),
                  original_document=r.get("original_document", ""),
                  author=r.get("author", ""),
                  score=r.get("_score", 0.0),
              )
              for r in raw_results
          ]
          
          return results
  ```
- **Acceptance Criteria**:
  - [x] Class uses base class type hints (`BaseVectorDatabase`, `BaseEmbedder`)
  - [x] `search()` method returns `List[DocumentChunkResult]` (NOT Dict)
  - [x] Supports filter_by_book (exact match), filter_by_chapter (partial match), filter_by_author (exact match)
  - [x] Uses `async_hybrid_search_vectors` for hybrid search
  - [x] Comprehensive docstrings on all methods

### Component 3: Agent Tool Wrapper

#### Requirement 1 - Create agent_tools retrieval module
- **Requirement**: Create `src/shared/src/shared/agent_tools/retrieval/` directory
- **Implementation**:
  - `src/shared/src/shared/agent_tools/retrieval/__init__.py`
  ```python
  """
  Retrieval tools for agent use.
  
  Provides search tools for the agent to query document library and knowledge graph.
  """
  
  from shared.agent_tools.retrieval.search_document_library import (
      search_document_library,
  )
  
  __all__ = ["search_document_library"]
  ```
- **Acceptance Criteria**:
  - [x] Directory created
  - [x] `__init__.py` exports `search_document_library`

#### Requirement 2 - Implement search_document_library tool
- **Requirement**: Async tool function with lazy initialization
- **Implementation**:
  - `src/shared/src/shared/agent_tools/retrieval/search_document_library.py`
  ```python
  """
  Document Library search tool for agent use.
  
  This tool provides the agent with access to raw text passages from marketing books.
  It uses hybrid search (dense + BM25) with optional metadata filtering.
  
  Best Practices for Agent:
  - Use Knowledge Graph first to understand concepts
  - Then use this tool with targeted filters for detailed passages
  - Use filter_by_chapter when you know the specific section
  """
  
  from typing import Optional
  
  from config.system_config import SETTINGS
  from shared.database_clients.vector_database.milvus.database import (
      MilvusVectorDatabase,
  )
  from shared.database_clients.vector_database.milvus.config import MilvusConfig
  from shared.model_clients.embedder.gemini import GeminiEmbedder
  from shared.model_clients.embedder.gemini.config import (
      GeminiEmbedderConfig,
      EmbeddingMode,
  )
  from core.retrieval.document_retriever import DocumentRetriever
  
  # Singleton retriever instance
  _retriever: Optional[DocumentRetriever] = None
  
  
  def _get_retriever() -> DocumentRetriever:
      """
      Lazy initialization of retriever singleton.
      
      Creates MilvusVectorDatabase and GeminiEmbedder instances using
      settings from SETTINGS configuration. Reuses the same instance
      for all subsequent calls.
      
      Returns:
          Initialized DocumentRetriever instance
      """
      global _retriever
      if _retriever is None:
          # Initialize Milvus client with async support
          vector_db = MilvusVectorDatabase(
              config=MilvusConfig(
                  host=SETTINGS.MILVUS_HOST,
                  port=SETTINGS.MILVUS_PORT,
                  user="root",
                  password=SETTINGS.MILVUS_ROOT_PASSWORD,
                  run_async=True,
              )
          )
          
          # Initialize Gemini embedder with retrieval mode
          embedder = GeminiEmbedder(
              config=GeminiEmbedderConfig(
                  mode=EmbeddingMode.RETRIEVAL,
                  output_dimensionality=SETTINGS.EMBEDDING_DIM,
                  api_key=SETTINGS.GEMINI_API_KEY,
              )
          )
          
          _retriever = DocumentRetriever(vector_db=vector_db, embedder=embedder)
      return _retriever
  
  
  async def search_document_library(
      query: str,
      filter_by_book: Optional[str] = None,
      filter_by_chapter: Optional[str] = None,
      filter_by_author: Optional[str] = None,
      top_k: int = 10
  ) -> str:
      """
      Search the document library for relevant text passages.
      
      Use this tool when you need:
      - Exact quotes or citations from books
      - Specific passages about a topic
      - Fact-checking or verification
      - Detailed explanations after understanding concepts from Knowledge Graph
      
      Strategy:
      1. First use search_knowledge_graph to understand concepts and find relevant sections
      2. Then use this tool with filter_by_chapter to get detailed passages
      
      Args:
          query: What to search for. Be specific for better results.
          filter_by_book: Limit to specific book name (exact match).
              Example: "Kotler Marketing Management"
          filter_by_chapter: Limit to specific chapter/section (partial match).
              Example: "Chapter 9" or "Pricing Strategy"
          filter_by_author: Limit to specific author (exact match).
              Example: "Philip Kotler"
          top_k: Number of results to return. Default 10.
      
      Returns:
          Formatted text with relevant passages and their sources.
          Each result includes: source location, book name, and content preview.
      """
      retriever = _get_retriever()
      
      results = await retriever.search(
          query=query,
          top_k=top_k,
          filter_by_book=filter_by_book,
          filter_by_chapter=filter_by_chapter,
          filter_by_author=filter_by_author,
      )
      
      if not results:
          return "No results found."
      
      # Format results for agent consumption
      output = []
      for i, chunk in enumerate(results, 1):
          output.append(f"[{i}] Source: {chunk.source}")
          output.append(f"    Book: {chunk.original_document}")
          # Truncate content to 500 chars for readability
          content_preview = chunk.content[:500]
          if len(chunk.content) > 500:
              content_preview += "..."
          output.append(f"    Content: {content_preview}")
          output.append("")  # Empty line between results
      
      return "\n".join(output)
  ```
- **Acceptance Criteria**:
  - [x] Uses singleton pattern with lazy initialization
  - [x] Returns formatted string for agent consumption
  - [x] Docstring describes when and how to use the tool
  - [x] Uses `DocumentChunkResult` BaseModel attributes (not dict access)

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Basic Hybrid Search
- **Purpose**: Verify hybrid search returns relevant results
- **Steps**:
  1. Call `search_document_library("marketing mix")` without filters
  2. Verify results contain chunks about 4Ps, marketing mix concepts
  3. Check that returned chunks have valid metadata (source, original_document)
- **Expected Result**: Returns up to 10 chunks with relevant marketing content
- **Status**: ✅ **PASSED** - Returned 5 relevant results with scores and metadata

### Test Case 2: Filter by Book
- **Purpose**: Verify book filter works correctly
- **Steps**:
  1. Call `search_document_library("pricing", filter_by_book="Principles of Marketing 17th Edition")`
  2. Verify all returned chunks have correct `original_document`
- **Expected Result**: Only chunks from specified book returned
- **Status**: ✅ **PASSED** - All 3 results from correct book (pricing chapters)

### Test Case 3: Filter by Chapter
- **Purpose**: Verify chapter filter with partial matching
- **Steps**:
  1. Call `search_document_library("value", filter_by_chapter="Chapter 9")`
  2. Verify all returned chunks have `source` containing "Chapter 9"
- **Expected Result**: Only chunks from Chapter 9 returned
- **Status**: ✅ **PASSED** - All 3 results from Chapter 9

### Test Case 4: Low Relevance Query
- **Purpose**: Verify handling of nonsense queries
- **Steps**:
  1. Call `search_document_library("xyzabc123nonexistent")`
  2. Check return behavior
- **Expected Result**: Returns low-relevance results (hybrid search behavior)
- **Status**: ✅ **PASSED** - Returned index entries (expected for hybrid search)
- **Note**: Hybrid search always tries to return something, even for nonsense queries

### Test Case 5: Combined Filters
- **Purpose**: Verify multiple filters work together
- **Steps**:
  1. Call with both `filter_by_book="Principles of Marketing 17th Edition"` and `filter_by_chapter="Chapter"`
  2. Verify results match both conditions
- **Expected Result**: Results filtered by both criteria
- **Status**: ✅ **PASSED** - All 3 results matched both filters

------------------------------------------------------------------------

## 📝 Task Summary

> **✅ Task Completed**: All components implemented and typecheck passed.

### What Was Implemented

**Components Completed**:
- [x] [Component 1]: Data models (`DocumentChunkResult`)
- [x] [Component 2]: DocumentRetriever class with hybrid search
- [x] [Component 3]: search_document_library agent tool wrapper

**Files Created/Modified**:
```
src/core/src/core/retrieval/
├── __init__.py                   # Module exports
├── models.py                     # DocumentChunkResult model
└── document_retriever.py         # Hybrid search retriever class

src/shared/src/shared/agent_tools/retrieval/
├── __init__.py                   # Module exports
└── search_document_library.py    # Agent tool wrapper

tests/integration/
└── test_document_library_search.py  # Integration tests (5 test cases)
```

**Key Features Delivered**:
1. **Typed Models**: `DocumentChunkResult` BaseModel for type safety
2. **Hybrid Search**: Combined dense vector + BM25 search with RRF ranking
3. **Metadata Filtering**: Filter by book (exact), chapter (partial), author (exact)
4. **Agent Integration**: Tool wrapper with clear usage documentation

### Technical Highlights

**Architecture Decisions**:
- Base class type hints (`BaseVectorDatabase`, `BaseEmbedder`) for extensibility
- `DocumentChunkResult` BaseModel instead of Dict for type safety
- Lazy initialization singleton pattern for tool wrapper
- Separated models into `models.py` for reuse

**Documentation Added**:
- [x] All functions have comprehensive docstrings
- [x] Complex business logic is well-commented
- [x] Module-level documentation explains purpose
- [x] Type hints are complete and accurate

### Validation Results

**Code Quality**:
- [x] Typecheck passed (ruff, black, mypy)
- [x] All acceptance criteria met
- [x] Follows enterprise-level Python standards
- [x] Line length < 88 characters

**Test Coverage**:
- [x] Integration test created with 5 test cases:
  - ✅ Test Case 1: Basic hybrid search - PASSED
  - ✅ Test Case 2: Filter by book - PASSED
  - ✅ Test Case 3: Filter by chapter - PASSED
  - ✅ Test Case 4: Low relevance query - PASSED
  - ✅ Test Case 5: Combined filters - PASSED
- ✅ **All tests executed successfully with Milvus running**

**Test Results Summary**:
- All 5 test cases passed
- Hybrid search correctly combines dense + BM25
- Metadata filters work as expected (exact and partial matching)
- Tool wrapper formats output correctly for agent consumption
- Handles edge cases appropriately (low-relevance queries)

**Deployment Notes**:
- Requires Stage 4 completion (DocumentChunks collection populated)
- Uses existing SETTINGS configuration for Milvus and Gemini
- No database migrations needed

------------------------------------------------------------------------
