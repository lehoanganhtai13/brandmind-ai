# Task 17: Gemini Embedder + Document Library Builder

## 📌 Metadata

- **Epic**: Knowledge Graph Pipeline - Stage 4
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: [stage_4.md](../docs/brainstorm/stage_4.md), [task_16.md](./task_16.md)
- **Blocking**: Task 18
- **Blocked by**: Task 16 (Completed)

### ✅ Progress Checklist

- [ ] 🎯 [Context & Goals](#🎯-context--goals)
- [ ] 🛠 [Solution Design](#🛠-solution-design)
- [ ] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [ ] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ⏳ [Component 1: Gemini Embedder](#component-1-gemini-embedder) - Completed
    - [x] ⏳ [Component 2: Document Library Builder](#component-2-document-library-builder) - Completed
    - [x] ⏳ [Component 3: Milvus Module Updates](#component-3-milvus-module-updates-for-bm25-support) - Completed
    - [x] ⏳ [Component 4: Module Integration](#component-4-module-integration) - Completed
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **Reference Module**: `src/shared/src/shared/model_clients/embedder/openai/`
- **Google GenAI SDK**: https://github.com/googleapis/python-genai
- **Milvus Module**: `src/shared/src/shared/database_clients/vector_database/milvus/`

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Stage 4 cần embed chunks và entity descriptions để lưu vào Vector DB
- Cần Gemini embedder để thay thế/bổ sung OpenAI embedder (giảm cost, tăng flexibility)
- Document Library Builder (Stream A) cần được implement để xử lý chunks từ Stage 2

### Mục tiêu

1. **Part A**: Xây dựng Gemini Embedder module theo pattern OpenAI Embedder đã có
2. **Part B**: Xây dựng Document Library Builder để embed và upsert chunks vào Vector DB

### Success Metrics / Acceptance Criteria

- **Functionality**: Gemini embedder hoạt động với cả RETRIEVAL và SEMANTIC modes
- **Pattern Consistency**: Module structure giống với OpenAI embedder
- **Integration**: Document Library Builder hoạt động với Milvus
- **Scale**: Xử lý được ~1400 chunks với batch processing và progress resume

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Part A - Gemini Embedder**:
- Implement `GeminiEmbedder` theo `BaseEmbedder` interface
- Support 2 modes: `RETRIEVAL` (for documents) và `SEMANTIC` (for knowledge graph)
- Manual normalization cho non-default dimensions

**Part B - Document Library Builder**:
- Process `chunks.json` → embed → upsert to Vector DB
- Batch processing với progress checkpoint
- Use base class interfaces (không bind cụ thể Milvus/Gemini)

### Stack công nghệ

- **google-genai**: Official Google GenAI SDK
- **numpy**: Vector normalization
- **Milvus**: Vector DB (đã có module)

### Issues & Solutions

1. **Dimension Normalization** → Manual normalize khi không dùng default 3072
2. **Task Type Mapping** → EmbeddingMode enum để map `RETRIEVAL_DOCUMENT`/`RETRIEVAL_QUERY` vs `SEMANTIC_SIMILARITY`
3. **Resume Processing** → Save progress to JSON checkpoint file

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Gemini Embedder Module**
1. **Config & Enums**
   - Create `EmbeddingMode` enum (RETRIEVAL, SEMANTIC)
   - Create `GeminiEmbedderConfig` extending `EmbedderConfig`
   
2. **Embedder Implementation**
   - Implement sync methods: `get_text_embedding`, `get_text_embeddings`, `get_query_embedding`
   - Implement async wrappers via `asyncio.to_thread()`
   - Add normalization logic for non-default dimensions

3. **Testing**
   - Unit test với mock
   - Integration test với real API

### **Phase 2: Document Library Builder**
1. **Core Implementation**
   - Load chunks from JSON
   - Batch embed với progress tracking
   - Upsert to Vector DB (DocumentChunks collection)

2. **Integration**
   - CLI entry point
   - Progress resume capability

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> - **Absolute Imports**: Use `from shared.model_clients.embedder...` pattern
> - **Comprehensive Docstrings**: All functions must have detailed docstrings in English
> - **Type Hints**: Use Python type hints for all function signatures
> - **Consistent String Quoting**: Use double quotes `"` consistently

### Component 1: Gemini Embedder

#### Requirement 1 - EmbeddingMode Enum & Config
- **Requirement**: Define embedding mode và config cho Gemini
- **Implementation**:
  - `src/shared/src/shared/model_clients/embedder/gemini/config.py`
  ```python
  from enum import Enum
  from typing import Optional

  from shared.model_clients.embedder.base_class import EmbedderBackend, EmbedderConfig


  class EmbeddingMode(str, Enum):
      """
      Embedding mode determines how task types are applied.

      RETRIEVAL: Optimized for retrieval tasks (document library)
          - get_text_embedding → RETRIEVAL_DOCUMENT
          - get_query_embedding → RETRIEVAL_QUERY

      SEMANTIC: Optimized for similarity matching (knowledge graph)
          - get_text_embedding → SEMANTIC_SIMILARITY
          - get_query_embedding → SEMANTIC_SIMILARITY
      """

      RETRIEVAL = "RETRIEVAL"
      SEMANTIC = "SEMANTIC"


  class GeminiEmbedderConfig(EmbedderConfig):
      """
      Configuration for Gemini embedder.

      Attributes:
          model_name: Gemini embedding model name (default: gemini-embedding-001)
          mode: Embedding mode (RETRIEVAL or SEMANTIC)
          output_dimensionality: Output dimension (768, 1536, or 3072)
          api_key: Google API key (fallback to GOOGLE_API_KEY env)
      """

      def __init__(
          self,
          model_name: str = "gemini-embedding-001",
          mode: EmbeddingMode = EmbeddingMode.SEMANTIC,
          output_dimensionality: int = 1536,
          api_key: Optional[str] = None,
          **kwargs,
      ):
          super().__init__(EmbedderBackend.GEMINI, **kwargs)
          from config.system_config import SETTINGS

          self.model_name = model_name
          self.mode = mode
          self.output_dimensionality = output_dimensionality
          self.api_key = api_key or SETTINGS.GEMINI_API_KEY
  ```
- **Acceptance Criteria**:
  - [x] EmbeddingMode enum với RETRIEVAL và SEMANTIC
  - [x] GeminiEmbedderConfig với đủ parameters

#### Requirement 2 - Update EmbedderBackend Enum
- **Requirement**: Add GEMINI to EmbedderBackend enum
- **Implementation**:
  - `src/shared/src/shared/model_clients/embedder/base_class.py`
  ```python
  class EmbedderBackend(Enum):
      """Enum for different embedder backends."""

      OPENAI = "openai"
      GEMINI = "gemini"  # Add this
      LOCAL = "local"
  ```

#### Requirement 3 - Gemini Embedder Implementation
- **Requirement**: Full implementation theo BaseEmbedder interface
- **Implementation**:
  - `src/shared/src/shared/model_clients/embedder/gemini/embedder.py`
  ```python
  import asyncio
  from typing import Any, List

  import numpy as np
  from numpy.linalg import norm

  from google import genai
  from google.genai import types

  from shared.model_clients.embedder.base_embedder import BaseEmbedder
  from shared.model_clients.embedder.gemini.config import (
      EmbeddingMode,
      GeminiEmbedderConfig,
  )
  from shared.utils.base_class import DenseEmbedding


  class GeminiEmbedder(BaseEmbedder):
      """
      Gemini implementation for text embedding.

      Task type is determined by config.mode:
      - RETRIEVAL mode: text→RETRIEVAL_DOCUMENT, query→RETRIEVAL_QUERY
      - SEMANTIC mode: both→SEMANTIC_SIMILARITY

      Note: For non-default dimensions (not 3072), embeddings are manually
      normalized as per Google's recommendation.
      """

      # Default dimension where embeddings are pre-normalized
      DEFAULT_DIMENSION = 3072

      def _initialize_embedder(self, **kwargs) -> None:
          """Initialize Gemini client."""
          self._config: GeminiEmbedderConfig = self.config
          self.client = genai.Client(api_key=self._config.api_key)

      def _get_task_type_for_text(self) -> str:
          """Get Gemini task type for text/document embedding."""
          if self._config.mode == EmbeddingMode.RETRIEVAL:
              return "RETRIEVAL_DOCUMENT"
          return "SEMANTIC_SIMILARITY"

      def _get_task_type_for_query(self) -> str:
          """Get Gemini task type for query embedding."""
          if self._config.mode == EmbeddingMode.RETRIEVAL:
              return "RETRIEVAL_QUERY"
          return "SEMANTIC_SIMILARITY"

      def _normalize_embedding(self, values: List[float]) -> List[float]:
          """
          Normalize embedding vector if using non-default dimension.

          Google's gemini-embedding-001 only returns pre-normalized embeddings
          at the default dimension (3072). For other dimensions, manual
          normalization is required.
          """
          if self._config.output_dimensionality == self.DEFAULT_DIMENSION:
              return values

          embedding_np = np.array(values)
          normed = embedding_np / norm(embedding_np)
          return normed.tolist()

      def get_text_embedding(self, text: str, **kwargs: Any) -> DenseEmbedding:
          """Get embedding for text/document."""
          result = self.client.models.embed_content(
              model=self._config.model_name,
              contents=text,
              config=types.EmbedContentConfig(
                  task_type=self._get_task_type_for_text(),
                  output_dimensionality=self._config.output_dimensionality,
              ),
          )
          values = self._normalize_embedding(result.embeddings[0].values)
          return DenseEmbedding(values=values)

      def get_text_embeddings(
          self, texts: List[str], **kwargs: Any
      ) -> List[DenseEmbedding]:
          """Batch embedding for multiple texts."""
          result = self.client.models.embed_content(
              model=self._config.model_name,
              contents=texts,
              config=types.EmbedContentConfig(
                  task_type=self._get_task_type_for_text(),
                  output_dimensionality=self._config.output_dimensionality,
              ),
          )
          return [
              DenseEmbedding(values=self._normalize_embedding(emb.values))
              for emb in result.embeddings
          ]

      def get_query_embedding(self, query: str, **kwargs: Any) -> DenseEmbedding:
          """Get embedding for search query."""
          result = self.client.models.embed_content(
              model=self._config.model_name,
              contents=query,
              config=types.EmbedContentConfig(
                  task_type=self._get_task_type_for_query(),
                  output_dimensionality=self._config.output_dimensionality,
              ),
          )
          values = self._normalize_embedding(result.embeddings[0].values)
          return DenseEmbedding(values=values)

      # Async versions using asyncio.to_thread
      async def aget_text_embedding(
          self, text: str, **kwargs: Any
      ) -> DenseEmbedding:
          return await asyncio.to_thread(self.get_text_embedding, text, **kwargs)

      async def aget_text_embeddings(
          self, texts: List[str], **kwargs: Any
      ) -> List[DenseEmbedding]:
          return await asyncio.to_thread(self.get_text_embeddings, texts, **kwargs)

      async def aget_query_embedding(
          self, query: str, **kwargs: Any
      ) -> DenseEmbedding:
          return await asyncio.to_thread(self.get_query_embedding, query, **kwargs)
  ```
- **Acceptance Criteria**:
  - [x] Implements all BaseEmbedder abstract methods
  - [x] Normalizes embeddings for non-3072 dimensions
  - [x] Async methods work correctly

### Component 2: Document Library Builder

#### Requirement 1 - DocumentChunks Collection Schema with BM25 Function
- **Requirement**: Define Vector DB collection schema using Milvus built-in BM25
- **Schema Definition**:
  
  **Fields:**
  | Field Name | Type | Description |
  |------------|------|-------------|
  | `id` | VARCHAR (primary) | Chunk UUID from chunks.json |
  | `content` | VARCHAR | Original text content (with `enable_analyzer=True` for BM25) |
  | `content_embedding` | FLOAT_VECTOR(1536) | Dense embedding of chunk content |
  | `content_sparse` | SPARSE_FLOAT_VECTOR | BM25 sparse vector (auto-generated by Function) |
  | `source` | VARCHAR | Source hierarchy path for filtering |
  | `original_document` | VARCHAR | Document name |
  | `author` | VARCHAR | Author(s) |
  | `pages` | ARRAY[VARCHAR] | List of page files |
  | `word_count` | INT64 | Word count metadata |

  **BM25 Function Definition:**
  Milvus 2.5+ có built-in BM25 function tự động convert VARCHAR field → SPARSE_FLOAT_VECTOR:
  
  ```python
  from config.system_config import SETTINGS
  from shared.database_clients.vector_database.milvus.utils import (
      SchemaField,
      DataType,
      IndexConfig,
      ElementType,
  )

  DOCUMENT_CHUNKS_SCHEMA = [
      SchemaField(
          field_name="id",
          field_type=DataType.STRING,
          is_primary=True,
          field_description="Unique chunk ID"
      ),
      SchemaField(
          field_name="content",
          field_type=DataType.STRING,
          field_description="Original chunk text content (for BM25)",
          # NOTE: enable_analyzer and full_text_search flags are handled
          # internally by MilvusVectorDatabase._create_schema_and_index
          # when DataType.STRING is used with BM25 function
      ),
      SchemaField(
          field_name="content_embedding",
          field_type=DataType.DENSE_VECTOR,
          dimension=SETTINGS.EMBEDDING_DIM,
          field_description="Dense embedding for semantic search",
          index_config=IndexConfig(
              index=True,
              index_type=IndexType.HNSW,
              metric_type=MetricType.COSINE,
          ),
      ),
      SchemaField(
          field_name="content_sparse",
          field_type=DataType.SPARSE_VECTOR,
          field_description="BM25 sparse vector (auto-generated)",
          # NOTE: This field is populated by BM25 Function
          # Function links: content (VARCHAR) → content_sparse (SPARSE)
      ),
      SchemaField(
          field_name="source",
          field_type=DataType.STRING,
          field_description="Source hierarchy for filtering"
      ),
      SchemaField(
          field_name="original_document",
          field_type=DataType.STRING,
          field_description="Original document name"
      ),
      SchemaField(
          field_name="author",
          field_type=DataType.STRING,
          field_description="Author(s)"
      ),
      SchemaField(
          field_name="pages",
          field_type=DataType.ARRAY,
          element_type=ElementType.STRING,
          field_description="List of page files"
      ),
      SchemaField(
          field_name="word_count",
          field_type=DataType.INT,
          field_description="Word count metadata"
      ),
  ]

  # BM25 Function Configuration (to be added to Milvus module)
  # This defines the transformation: content (VARCHAR) → content_sparse (SPARSE)
  BM25_FUNCTION_CONFIG = {
      "name": "document_bm25",
      "type": "BM25",  # Function type
      "input_field": "content",   # VARCHAR field
      "output_field": "content_sparse"  # SPARSE_FLOAT_VECTOR field
  }
  ```

> **⚠️ IMPORTANT - Milvus Module Updates Required:**
>
> Để support BM25 function, cần update 2 functions trong `src/shared/src/shared/database_clients/vector_database/milvus/database.py`:
>
> 1. **`_create_schema_and_index()`**: 
>    - Khi field type là `STRING` và có BM25 function config, cần set:
>      - `enable_analyzer=True`
>      - `enable_match=True` (for full-text search)
>      - `analyzer_params` với tokenizer settings
>    - Add support cho defining BM25 Functions trong collection schema
>
> 2. **`build_hybrid_search_requests()` trong `hybrid_search_vectors()`**:
>    - Khi `embedding_type == SPARSE` và `query` field có giá trị:
>      - Dùng `query` text cho BM25 full-text search
>      - KHÔNG dùng manual sparse embeddings
>
> **Reference Documentation**:
> - Milvus Full-Text Search: https://milvus.io/docs/full-text-search.md
> - Milvus BM25 Function: https://milvus.io/docs/manage-collections.md (Functions section)
> - Multi-Vector Search: https://milvus.io/docs/multi-vector-search.md

- **Acceptance Criteria**:
  - [ ] Schema với BM25 function definition
  - [ ] Milvus module updated để support BM25 functions
  - [ ] Hybrid search supports text query for BM25

#### Requirement 2 - Document Library Builder
- **Requirement**: Process chunks.json → embed → upsert to Vector DB
- **Implementation**:
  - `src/core/src/core/knowledge_graph/curator/document_library.py`
  ```python
  import json
  from pathlib import Path
  from typing import Optional, List, Dict, Any

  from loguru import logger

  from shared.database_clients.vector_database.base_vector_database import (
      BaseVectorDatabase,
  )
  from shared.model_clients.embedder.base_embedder import BaseEmbedder


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
      chunks_to_process = [
          c for c in chunks if c["id"] not in processed_ids
      ]
      logger.info(f"Processing {len(chunks_to_process)} remaining chunks")

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
                  upsert_data.append({
                      "id": chunk["id"],
                      "content_embedding": emb.values,
                      "source": metadata.get("source", ""),
                      "original_document": metadata.get("original_document", ""),
                      "author": metadata.get("author", ""),
                      "pages": metadata.get("pages", []),
                      "word_count": metadata.get("word_count", 0),
                      "content": chunk["content"],
                  })

              # Upsert to Vector DB
              vector_db.upsert_data(
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
  ```
- **Acceptance Criteria**:
  - [x] Loads chunks from JSON
  - [x] Batch embeds with progress tracking
  - [x] Upserts to Vector DB
  - [x] Resumes from checkpoint

### Component 3: Milvus Module Updates for BM25 Support

> **Context**: Milvus 2.5+ có built-in BM25 function, nhưng current Milvus module chưa support. Cần update để enable BM25 full-text search.

#### Requirement 1 - Support BM25 Function in Schema Creation
- **Requirement**: Update `_create_schema_and_index()` để support BM25 Functions
- **Implementation**:
  - `src/shared/src/shared/database_clients/vector_database/milvus/database.py`
  - Cần add parameter `bm25_function_config` vào `_create_schema_and_index()`
  - Khi có BM25 function config:
    - VARCHAR input field: set `enable_analyzer=True`, `enable_match=True`
    - Define BM25 Function trong schema
- **Acceptance Criteria**:
  - [x] Collections can be created with BM25 functions
  - [x] VARCHAR fields with BM25 have proper analyzer settings
  - [x] BM25 function config uses `Dict[sparse_field → text_field]` format
  - [x] Sparse index uses `params={"inverted_index_algo": "DAAT_MAXSCORE"}`
  - [x] Conditional index creation based on `index_config.index` flag

#### Requirement 2 - Support BM25 Text Query in Hybrid Search
- **Requirement**: Update `build_hybrid_search_requests()` để support text query for BM25
- **Implementation**:
  - `src/shared/src/shared/database_clients/vector_database/milvus/database.py`
  - Trong `hybrid_search_vectors()`, khi build search requests:
    - Nếu `embedding_type == SPARSE` và `query` field có giá trị:
      - Dùng `AnnSearchRequest` với `data=[query_text]` (text search)
      - KHÔNG dùng manual sparse embeddings
- **Acceptance Criteria**:
  - [x] Hybrid search supports text query for BM25 sparse fields
  - [x] Can search with combination of dense + BM25 sparse
  - [x] Text query uses `drop_ratio_search: 0.2` param
  - [x] Manual sparse vectors use empty params with IP metric

### Component 4: Module Integration

#### Requirement 1 - Gemini Module Exports
- **Implementation**:
  - `src/shared/src/shared/model_clients/embedder/gemini/__init__.py`
  ```python
  from shared.model_clients.embedder.gemini.config import (
      EmbeddingMode,
      GeminiEmbedderConfig,
  )
  from shared.model_clients.embedder.gemini.embedder import GeminiEmbedder

  __all__ = ["GeminiEmbedder", "GeminiEmbedderConfig", "EmbeddingMode"]
  ```

#### Requirement 2 - Curator Module Exports
- **Implementation**:
  - `src/core/src/core/knowledge_graph/curator/__init__.py`
  ```python
  from core.knowledge_graph.curator.document_library import build_document_library

  __all__ = ["build_document_library"]
  ```

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Gemini Embedder - Single Text
- **Purpose**: Verify single text embedding
- **Steps**:
  1. Create GeminiEmbedder with SEMANTIC mode
  2. Call `get_text_embedding("test text")`
  3. Verify result is DenseEmbedding with correct dimension
- **Expected Result**: Returns 1536-dim vector
- **Status**: ✅ Passed (Integration test)

### Test Case 2: Gemini Embedder - Batch Texts
- **Purpose**: Verify batch embedding
- **Steps**:
  1. Create GeminiEmbedder with RETRIEVAL mode
  2. Call `get_text_embeddings(["text1", "text2", "text3"])`
  3. Verify 3 embeddings returned
- **Expected Result**: Returns list of 3 DenseEmbeddings
- **Status**: ✅ Passed (Integration test)

### Test Case 3: Gemini Embedder - Query vs Text Task Types
- **Purpose**: Verify correct task types are used
- **Steps**:
  1. RETRIEVAL mode: text → RETRIEVAL_DOCUMENT, query → RETRIEVAL_QUERY
  2. SEMANTIC mode: both → SEMANTIC_SIMILARITY
- **Status**: ✅ Passed (Integration test)

### Test Case 4: Document Library Builder - Full Flow
- **Purpose**: Verify end-to-end document library building
- **Steps**:
  1. Prepare sample chunks.json
  2. Call `build_document_library()`
  3. Verify data in Vector DB
- **Expected Result**: All chunks embedded and stored
- **Status**: ⏳ Pending

### Test Case 5: Document Library Builder - Resume
- **Purpose**: Verify progress resume
- **Steps**:
  1. Process 50% of chunks, then interrupt
  2. Resume processing
  3. Verify only remaining chunks are processed
- **Expected Result**: No duplicate processing
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [x] Gemini Embedder: Full implementation with RETRIEVAL/SEMANTIC modes
- [x] Document Library Builder: Batch processing with resume
- [x] Milvus BM25 Support: Full-text search with conditional indexing
- [x] Module Integration: Proper exports and imports
- [x] Validation: DENSE_VECTOR requires index_config, SPARSE_VECTOR requires index enabled

**Files Created/Modified**:
```
src/shared/src/shared/model_clients/embedder/
├── base_class.py               # Add GEMINI to backend enum
└── gemini/
    ├── __init__.py
    ├── config.py               # GeminiEmbedderConfig
    └── embedder.py             # GeminiEmbedder

src/core/src/core/knowledge_graph/curator/
├── __init__.py
└── document_library.py         # Document Library Builder
```

**Key Features Delivered**:
1. **Gemini Embedder**: API-compatible with OpenAI embedder
2. **Dual Mode Support**: RETRIEVAL for docs, SEMANTIC for KG
3. **Batch Processing**: Efficient batch embedding with progress

### **Deployment Notes**
- Requires `google-genai` package
- Requires `GEMINI_API_KEY` in SETTINGS (from environments/.env)
- Milvus 2.5+ must be running with BM25 function support
- FalkorDB must be running (port 6380) for Knowledge Graph
