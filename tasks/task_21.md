# Task 21: Knowledge Graph Search Components

## 📌 Metadata

- **Epic**: Stage 5 - The Retriever
- **Priority**: High
- **Estimated Effort**: 1.5 days
- **Team**: Backend
- **Related Tasks**: [Stage 5 Planning](../docs/brainstorm/stage_5.md), [Task 20](./task_20.md)
- **Blocking**: Task 22 (KG Retriever Integration)
- **Blocked by**: Task 20 (Document Library Search - completed)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1-data-models) - Data models for KG search
    - [x] ✅ [Component 2](#component-2-query-decomposer) - LLM-based query decomposition
    - [x] ✅ [Component 3](#component-3-edge-scorer) - Semantic edge scoring
    - [x] ✅ [Component 4](#component-4-local-searcher) - Local search with PPR + Dijkstra
    - [x] ✅ [Component 5](#component-5-global-searcher) - Global relation search
- [x] 🐛 [Debugging & Bug Fixes](#🐛-debugging--bug-fixes) - Critical issues found and resolved
- [x] 🧪 [Test Cases](#🧪-test-cases) - All 8/8 tests passing with real data
- [x] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **Stage 5 Spec**: [docs/brainstorm/stage_5.md](../docs/brainstorm/stage_5.md) - Sub-Task 21 section
- **Task 20 Reference**: [tasks/task_20.md](./task_20.md) - Pattern for models.py extension

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Agent cần một công cụ để tìm kiếm trong "Kho Tri Thức" (Knowledge Graph) - nơi chứa entities và relationships được trích xuất từ sách marketing
- Knowledge Graph đã được indexed trong Stage 4:
  - Milvus `EntityDescriptions`: ~25,000+ entity embeddings
  - Milvus `RelationDescriptions`: ~23,000+ relation embeddings
  - FalkorDB Graph: Entity nodes + Relationship edges
- Cần multi-hop reasoning với semantic PPR để tìm related concepts

### Mục tiêu

Xây dựng 4 core components cho Knowledge Graph Search:
1. **QueryDecomposer**: Phân tách query thành local/global sub-queries
2. **EdgeScorer**: Scoring edges dựa trên semantic similarity
3. **LocalSearcher**: Local semantic PPR với Dijkstra traceback
4. **GlobalSearcher**: Global relation search trên RelationDescriptions

### Success Metrics / Acceptance Criteria

- **Performance**: Edge scoring batch < 500ms, PPR computation < 1s
- **Quality**: Top-5 PPR paths có semantic coherence cao
- **Coverage**: Hỗ trợ multi-hop traversal (2-3 hops)
- **Integration**: Tất cả components ready cho Task 22 orchestration

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Local Semantic PPR with Dijkstra Traceback**: Sử dụng NetworkX để build in-memory graph với semantic edge weights, chạy PageRank để tìm important nodes, sau đó trace back paths bằng Dijkstra với inverted weights.

### Stack công nghệ

- **NetworkX**: In-memory graph operations, PPR, Dijkstra
- **Milvus**: Vector DB cho entity/relation embeddings
- **FalkorDB**: Graph DB cho sub-graph extraction
- **Gemini LLM**: Query decomposition với structured output
- **Pydantic BaseModel**: Typed data models

### Issues & Solutions

1. **Super-node explosion** → Limit `max_neighbors_per_node` during BFS expansion
2. **False negatives from greedy pruning** → Use PPR to detect "convergence hubs" where multiple weak paths meet
3. **Path coherence** → Dijkstra with inverted semantic weights ensures most relevant paths

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Data Models & Prompts**
1. **Data Models**
   - Extend `models.py` with: `SeedNode`, `GraphNode`, `GraphEdge`, `SubgraphData`, `GlobalRelation`, `SourceMetadata`, `VerbalizedFact`

2. **Prompt Files**
   - Verify `query_decompose_instruction.py` and `query_decompose_task_prompt.py` exist (already created)

### **Phase 2: Core Components**
1. **QueryDecomposer**
   - LLM-based query analysis with structured JSON output
   - *Decision Point: Verify Gemini response_schema works correctly*

2. **EdgeScorer**
   - Batch fetch relation embeddings from Milvus
   - Compute cosine similarity scores

3. **LocalSearcher (most complex)**
   - K-hop sub-graph extraction via async_get_neighbors
   - NetworkX graph construction with semantic weights
   - nx.pagerank() with seed personalization
   - Dijkstra traceback for path reconstruction

4. **GlobalSearcher**
   - Hybrid search on RelationDescriptions
   - Deduplication across sub-queries

### **Phase 3: Testing & Validation**
1. **Unit Tests**
   - Test each component in isolation
   - Mock database responses

2. **Integration Tests**
   - Test with real FalkorDB and Milvus data
   - Verify end-to-end flow

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
> - **Line Length**: Max 88 characters (ruff default)

### Component 1: Data Models

#### Requirement 1 - Extend models.py
- **Requirement**: Add all KG search data models to `src/core/src/core/retrieval/models.py`
- **Implementation**:
  - `src/core/src/core/retrieval/models.py`
  ```python
  # Add to existing models.py (after DocumentChunkResult)

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
      source_node: Optional[GraphNode] = Field(
          default=None, description="Starting node"
      )
      destination_node: Optional[GraphNode] = Field(
          default=None, description="End node"
      )
      intermediate_nodes: List[GraphNode] = Field(
          default_factory=list, description="Bridge nodes"
      )
      edges: List[GraphEdge] = Field(
          default_factory=list, description="Path edges"
      )
      ppr_score: float = Field(default=0.0, description="PPR ranking score")
      semantic_score: float = Field(default=0.0, description="Path semantic score")
      # Global relation fields
      relation: Optional[GlobalRelation] = Field(
          default=None, description="Global relation (for type='global')"
      )
  ```
- **Acceptance Criteria**:
  - [ ] All 7 new models added to `models.py`
  - [ ] All models have comprehensive docstrings
  - [ ] All fields have type hints and descriptions
  - [ ] `__init__.py` updated with new exports

### Component 2: Query Decomposer

#### Requirement 1 - Implement QueryDecomposer
- **Requirement**: LLM-based query decomposition into local/global sub-queries
- **Implementation**:
  - `src/core/src/core/retrieval/query_decomposer.py`
  ```python
  """
  LLM-based query decomposition for dual-level knowledge graph search.

  This module provides the decompose_query function which uses Gemini LLM
  to analyze a user query and split it into:
  - Global queries: For searching relation descriptions (concepts, themes)
  - Local queries: For entity linking and graph traversal
  """

  import json
  from typing import List
  from pydantic import BaseModel, Field
  from loguru import logger

  from config.system_config import SETTINGS
  from shared.model_clients.llm.google import (
      GoogleAIClientLLM,
      GoogleAIClientLLMConfig,
  )
  from prompts.knowledge_graph.query_decompose_instruction import (
      QUERY_DECOMPOSE_INSTRUCTION,
  )
  from prompts.knowledge_graph.query_decompose_task_prompt import (
      QUERY_DECOMPOSE_TASK_PROMPT,
  )


  class DecomposedQuery(BaseModel):
      """
      Structured response for query decomposition.
      
      Splits a user query into global (conceptual) and local (entity-specific)
      sub-queries for dual-level knowledge graph search.
      """
      global_queries: List[str] = Field(
          ..., description="Broad thematic questions"
      )
      local_queries: List[str] = Field(
          ..., description="Specific entity questions"
      )


  async def decompose_query(query: str) -> DecomposedQuery:
      """
      Decompose user query into local and global sub-queries.
      
      Uses an LLM to analyze the query and split it into:
      - Global queries: For searching relation descriptions (concepts, themes)
      - Local queries: For entity linking and graph traversal
      
      Args:
          query: The original user query
      
      Returns:
          DecomposedQuery with global_queries and local_queries lists
      """
      try:
          llm = GoogleAIClientLLM(
              config=GoogleAIClientLLMConfig(
                  model="gemini-2.5-flash-lite",
                  api_key=SETTINGS.GEMINI_API_KEY,
                  system_instruction=QUERY_DECOMPOSE_INSTRUCTION,
                  temperature=0.1,
                  thinking_budget=2000,
                  max_tokens=4000,
                  response_mime_type="application/json",
                  response_schema=DecomposedQuery,
              )
          )
          
          task_prompt = QUERY_DECOMPOSE_TASK_PROMPT.replace("{{QUERY}}", query)
          response = llm.complete(task_prompt).text
          result = json.loads(response)
          
          return DecomposedQuery(**result)
      except Exception as e:
          logger.error(f"Error decomposing query: {e}")
          # Fallback: use original query for both
          return DecomposedQuery(global_queries=[query], local_queries=[query])
  ```
- **Acceptance Criteria**:
  - [ ] `DecomposedQuery` model defined with global_queries and local_queries
  - [ ] Uses Gemini LLM with structured JSON output
  - [ ] Fallback behavior on error (returns original query for both)
  - [ ] Comprehensive docstrings

### Component 3: Edge Scorer

#### Requirement 1 - Implement EdgeScorer
- **Requirement**: Batch semantic scoring for graph edges
- **Implementation**:
  - `src/core/src/core/retrieval/edge_scorer.py`
  ```python
  """
  Edge scorer for semantic similarity-based graph weighting.

  This module provides the EdgeScorer class which computes semantic similarity
  scores between a query embedding and relation embeddings from the vector DB.
  These scores are used as edge weights in the PPR computation.
  """

  import numpy as np
  from typing import List, Dict
  from shared.database_clients.vector_database.base_vector_database import (
      BaseVectorDatabase,
  )


  class EdgeScorer:
      """
      Scores graph edges based on semantic similarity to a query.
      
      Uses pre-embedded relation descriptions from the RelationDescriptions
      collection in Milvus. Edge scores determine flow weights during PPR
      computation and path selection during Dijkstra traceback.
      
      Higher scores indicate edges whose descriptions are more semantically
      relevant to the user's query.
      
      Example:
          >>> scorer = EdgeScorer(vector_db=milvus)
          >>> scores = await scorer.score_edges(query_embedding, relation_ids)
          >>> # scores = {"rel_123": 0.85, "rel_456": 0.42, ...}
      """
      
      def __init__(
          self,
          vector_db: BaseVectorDatabase,
          collection_name: str = "RelationDescriptions"
      ):
          """
          Initialize the edge scorer.
          
          Args:
              vector_db: Vector database client for fetching embeddings
              collection_name: Collection containing relation description embeddings
          """
          self.vector_db = vector_db
          self.collection_name = collection_name
      
      async def score_edges(
          self,
          query_embedding: List[float],
          relation_ids: List[str]
      ) -> Dict[str, float]:
          """
          Compute semantic similarity scores for multiple edges.
          
          Fetches relation embeddings by ID from the vector database,
          then calculates cosine similarity with the query embedding.
          
          Args:
              query_embedding: Embedded query vector
              relation_ids: List of relation IDs (vector_db_ref_id from FalkorDB)
          
          Returns:
              Dictionary mapping relation_id to similarity score (0.0 to 1.0)
          """
          if not relation_ids:
              return {}
          
          # Fetch relation embeddings from vector DB
          results = await self.vector_db.async_get_items(
              ids=relation_ids,
              collection_name=self.collection_name,
          )
          
          if not results:
              return {}
          
          # Prepare data for vectorized computation
          query_np = np.array(query_embedding, dtype=np.float32)
          
          valid_ids = []
          embeddings_list = []
          
          for result in results:
              rel_id = result.get("id")
              rel_embedding = result.get("description_embedding")
              
              if rel_id and rel_embedding:
                  valid_ids.append(rel_id)
                  embeddings_list.append(rel_embedding)
          
          if not embeddings_list:
              return {}
          
          # Vectorized cosine similarity computation
          # Shape: (n_relations, embedding_dim)
          rel_matrix = np.array(embeddings_list, dtype=np.float32)
          
          # Compute norms
          query_norm = np.linalg.norm(query_np)
          rel_norms = np.linalg.norm(rel_matrix, axis=1)
          
          # Avoid division by zero
          if query_norm == 0:
              return {rel_id: 0.0 for rel_id in valid_ids}
          
          # Vectorized dot product: (n_relations,)
          dot_products = np.dot(rel_matrix, query_np)
          
          # Vectorized cosine similarity
          similarities = dot_products / (rel_norms * query_norm)
          
          # Handle any NaN or inf values
          similarities = np.nan_to_num(similarities, nan=0.0, posinf=0.0, neginf=0.0)
          
          # Build result dictionary
          scores = {rel_id: float(sim) for rel_id, sim in zip(valid_ids, similarities)}
          
          return scores
  ```
- **Acceptance Criteria**:
  - [ ] Uses `async_get_items` to fetch embeddings by ID
  - [ ] Computes cosine similarity correctly
  - [ ] Handles empty relation_ids list
  - [ ] Returns Dict[str, float] with scores 0.0-1.0

### Component 4: Local Searcher

#### Requirement 1 - Implement LocalSearcher
- **Requirement**: Local semantic search with PPR and Dijkstra traceback
- **Implementation**:
  - `src/core/src/core/retrieval/local_search.py`
  ```python
  """
  Local semantic search using Personalized PageRank with Dijkstra traceback.

  This module provides the LocalSearcher class for multi-hop knowledge graph
  traversal. It finds semantically related concepts by exploring the graph
  neighborhood around entity matches and ranking paths by importance.
  """

  import asyncio
  import networkx as nx
  from typing import List, Optional, Dict
  from pydantic import BaseModel, Field
  from loguru import logger

  from shared.database_clients.graph_database.base_graph_database import (
      BaseGraphDatabase,
  )
  from shared.database_clients.graph_database.base_class import RelationDirection
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
  from core.retrieval.edge_scorer import EdgeScorer
  from core.retrieval.models import GraphNode, GraphEdge, SeedNode, SubgraphData


  class SemanticPath(BaseModel):
      """
      Represents a semantic path from a seed node to a high-PPR destination.
      
      Contains all nodes and edges along the path, plus scoring information
      for ranking and context assembly.
      """
      source_node: GraphNode = Field(..., description="Starting node (seed)")
      destination_node: GraphNode = Field(
          ..., description="High-PPR destination node"
      )
      intermediate_nodes: List[GraphNode] = Field(
          default_factory=list,
          description="Bridge nodes connecting source to destination"
      )
      edges: List[GraphEdge] = Field(
          default_factory=list,
          description="Edges along the path with properties"
      )
      ppr_score: float = Field(..., description="PPR score of the destination node")
      path_semantic_score: float = Field(
          default=0.0,
          description="Average semantic similarity of edges in path"
      )


  class LocalSearcher:
      """
      Local semantic search for entity-linked graph traversal.
      
      Discovers related concepts by finding entity matches from queries,
      then exploring their graph neighborhood to identify semantically
      important destinations. Provides coherent paths for LLM context
      rather than isolated nodes.
      
      Example:
          >>> searcher = LocalSearcher(graph_db, vector_db, embedder)
          >>> paths = await searcher.search(local_queries, query, max_hops=2)
      """
      
      DAMPING_FACTOR = 0.85  # Standard PPR damping
      MIN_EDGE_WEIGHT = 0.001  # Avoid zero weights in graph
      
      def __init__(
          self,
          graph_db: BaseGraphDatabase,
          vector_db: BaseVectorDatabase,
          embedder: BaseEmbedder,
      ):
          """
          Initialize the local searcher.
          
          Args:
              graph_db: Graph database client for sub-graph extraction
              vector_db: Vector database client for entity and edge scoring
              embedder: Embedder client for query embedding
          """
          self.graph_db = graph_db
          self.vector_db = vector_db
          self.edge_scorer = EdgeScorer(vector_db)
          self.embedder = embedder
      
      async def search(
          self,
          local_queries: List[str],
          query: str,
          max_seeds: int = 10,
          max_hops: int = 2,
          top_k_destinations: int = 5,
          max_neighbors_per_node: int = 50
      ) -> List[SemanticPath]:
          """
          Execute local semantic search from entity-focused queries.
          
          Finds relevant entities from local queries, explores their graph
          neighborhood, and traces semantically coherent paths to important
          related concepts.
          
          Args:
              local_queries: Entity-focused sub-queries for seed node finding
              query: Original user query for semantic weighting
              max_seeds: Maximum number of seed entities to start from
              max_hops: Depth of graph exploration
              top_k_destinations: Number of destination paths to return
              max_neighbors_per_node: Limit to prevent super-node explosion
          
          Returns:
              List of SemanticPath objects with complete path information
          """
          if not local_queries:
              return []
          
          # Step 1: Find seed nodes from local queries
          seed_nodes = await self._find_seed_nodes(local_queries, max_seeds)
          
          if not seed_nodes:
              logger.info("No seed nodes found for local search")
              return []
          
          logger.info(f"Starting local search with {len(seed_nodes)} seed nodes")
          
          # Step 2: Extract K-hop sub-graph
          subgraph_data = await self._extract_subgraph(
              seed_nodes, max_hops, max_neighbors_per_node
          )
          
          if not subgraph_data.edges:
              logger.warning("No edges found in sub-graph")
              return []
          
          # Step 3: Compute semantic edge weights
          query_embedding = await self.embedder.aget_query_embedding(query)
          edge_scores = await self._score_all_edges(
              query_embedding, subgraph_data.edges
          )
          
          # Step 4: Build NetworkX graph with semantic weights
          G = self._build_networkx_graph(subgraph_data, edge_scores)
          logger.info(
              f"Built graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
          )
          
          # Step 5: Run Personalized PageRank
          seed_ids = [n.graph_id for n in seed_nodes]
          ppr_scores = self._run_ppr(G, seed_ids)
          
          # Step 6: Get top destination nodes (excluding seeds)
          top_destinations = self._get_top_destinations(
              ppr_scores, seed_ids, top_k_destinations
          )
          logger.info(f"Top PPR destinations: {[d[0] for d in top_destinations]}")
          
          # Step 7: Trace paths using Dijkstra
          paths = self._trace_paths_dijkstra(
              G, seed_ids, top_destinations, subgraph_data, edge_scores
          )
          
          return paths
      
      async def _find_seed_nodes(
          self,
          local_queries: List[str],
          max_seeds: int
      ) -> List[SeedNode]:
          """
          Find seed entities from local queries via EntityDescriptions search.
          
          Args:
              local_queries: Entity-focused sub-queries
              max_seeds: Maximum number of seeds to return
          
          Returns:
              List of unique SeedNode objects
          """
          # Search all queries concurrently
          async def search_entities(lq: str) -> List[Dict]:
              query_embedding = await self.embedder.aget_query_embedding(lq)
              
              embedding_data = [
                  EmbeddingData(
                      embedding_type=EmbeddingType.DENSE,
                      embeddings=query_embedding,
                      field_name="name_embedding",
                  ),
                  EmbeddingData(
                      embedding_type=EmbeddingType.SPARSE,
                      query=lq,
                      field_name="name_sparse",
                  ),
              ]
              
              results = await self.vector_db.async_hybrid_search_vectors(
                  embedding_data=embedding_data,
                  output_fields=[
                      "id", "graph_id", "entity_name", "entity_type", "description"
                  ],
                  top_k=3,
                  collection_name="EntityDescriptions",
                  metric_type=MetricType.COSINE,
                  index_type=IndexType.HNSW,
              )
              return results
          
          results_per_query = await asyncio.gather(
              *[search_entities(q) for q in local_queries]
          )
          
          # Flatten and deduplicate
          all_seeds = []
          for results in results_per_query:
              all_seeds.extend(results)
          
          seen = set()
          unique: List[SeedNode] = []
          for s in all_seeds:
              if s["id"] not in seen:
                  seen.add(s["id"])
                  unique.append(
                      SeedNode(
                          id=s.get("id", ""),
                          graph_id=s.get("graph_id", ""),
                          name=s.get("entity_name", ""),
                          type=s.get("entity_type", ""),
                          description=s.get("description", ""),
                          score=s.get("_score", 0.0),
                      )
                  )
          
          return unique[:max_seeds]
      
      async def _extract_subgraph(
          self,
          seed_nodes: List[SeedNode],
          max_hops: int,
          max_neighbors: int
      ) -> SubgraphData:
          """
          Extract K-hop neighborhood sub-graph from seed nodes.
          
          Args:
              seed_nodes: Starting entities for traversal
              max_hops: Maximum depth of traversal
              max_neighbors: Limit neighbors per node
          
          Returns:
              SubgraphData with nodes and edges
          """
          all_nodes: Dict[str, GraphNode] = {}
          all_edges: List[GraphEdge] = []
          visited_ids: set = set()
          
          # Initialize with seed nodes
          frontier: List[GraphNode] = []
          for seed in seed_nodes:
              node = GraphNode(
                  id=seed.graph_id,
                  type=seed.type,
                  name=seed.name,
                  properties={"description": seed.description},
              )
              all_nodes[seed.graph_id] = node
              frontier.append(node)
          
          for hop in range(max_hops):
              next_frontier: List[GraphNode] = []
              
              for node in frontier:
                  if node.id in visited_ids:
                      continue
                  visited_ids.add(node.id)
                  
                  try:
                      neighbors = await self.graph_db.async_get_neighbors(
                          label=node.type,
                          match_properties={"id": node.id},
                          direction=RelationDirection.BOTH,
                      )
                      
                      # Limit neighbors to prevent explosion
                      neighbors = neighbors[:max_neighbors]
                      
                      for neighbor in neighbors:
                          neighbor_id = neighbor.get("id")
                          if neighbor_id:
                              # Store neighbor node
                              if neighbor_id not in all_nodes:
                                  neighbor_node = GraphNode(
                                      id=neighbor_id,
                                      type=neighbor.get("labels", ["Unknown"])[0]
                                      if neighbor.get("labels")
                                      else "Unknown",
                                      name=neighbor.get("properties", {}).get(
                                          "name", ""
                                      ),
                                      properties=neighbor.get("properties", {}),
                                  )
                                  all_nodes[neighbor_id] = neighbor_node
                                  next_frontier.append(neighbor_node)
                              
                              # Store edge
                              edge = GraphEdge(
                                  source_id=node.id,
                                  target_id=neighbor_id,
                                  relation_type=neighbor.get(
                                      "relation_type", "RELATED_TO"
                                  ),
                                  vector_db_ref_id=neighbor.get(
                                      "properties", {}
                                  ).get("vector_db_ref_id"),
                                  source_chunk=neighbor.get("properties", {}).get(
                                      "source_chunk"
                                  ),
                              )
                              all_edges.append(edge)
                  except Exception as e:
                      logger.warning(
                          f"Error getting neighbors for node {node.id}: {e}"
                      )
                      continue
              
              frontier = next_frontier
          
          logger.info(
              f"Extracted sub-graph: {len(all_nodes)} nodes, {len(all_edges)} edges"
          )
          return SubgraphData(nodes=all_nodes, edges=all_edges)
      
      async def _score_all_edges(
          self,
          query_embedding: List[float],
          edges: List[GraphEdge]
      ) -> Dict[str, float]:
          """
          Batch score all edges by semantic similarity.
          
          Args:
              query_embedding: Embedded query vector
              edges: All edges in the sub-graph
          
          Returns:
              Dictionary mapping vector_db_ref_id to similarity score
          """
          ref_ids = [e.vector_db_ref_id for e in edges if e.vector_db_ref_id]
          ref_ids = list(set(ref_ids))  # Deduplicate
          
          if not ref_ids:
              return {}
          
          return await self.edge_scorer.score_edges(query_embedding, ref_ids)
      
      def _build_networkx_graph(
          self,
          subgraph_data: SubgraphData,
          edge_scores: Dict[str, float]
      ) -> nx.DiGraph:
          """
          Build NetworkX DiGraph with semantic weights.
          
          Args:
              subgraph_data: Extracted sub-graph with nodes and edges
              edge_scores: Semantic similarity scores for edges
          
          Returns:
              NetworkX DiGraph with weighted edges for PPR and Dijkstra
          """
          G = nx.DiGraph()
          
          for node_id, node in subgraph_data.nodes.items():
              G.add_node(
                  node_id, type=node.type, name=node.name, **node.properties
              )
          
          for edge in subgraph_data.edges:
              if edge.source_id and edge.target_id:
                  # Semantic weight for PPR (higher = more flow)
                  semantic_weight = edge_scores.get(
                      edge.vector_db_ref_id or "", self.MIN_EDGE_WEIGHT
                  )
                  semantic_weight = max(semantic_weight, self.MIN_EDGE_WEIGHT)
                  
                  G.add_edge(
                      edge.source_id,
                      edge.target_id,
                      weight=semantic_weight,
                      dijkstra_weight=(1.0 - semantic_weight + 0.01), # High similarity = Low distance
                      relation_type=edge.relation_type,
                      vector_db_ref_id=edge.vector_db_ref_id,
                      source_chunk=edge.source_chunk,
                  )
          
          return G
      
      def _run_ppr(self, G: nx.DiGraph, seed_ids: List[str]) -> Dict[str, float]:
          """
          Run Personalized PageRank with seed personalization.
          
          Args:
              G: NetworkX DiGraph with semantic weights
              seed_ids: Node IDs of seed entities
          
          Returns:
              Dictionary mapping node_id to PPR score
          """
          personalization = {node: 0.0 for node in G.nodes()}
          valid_seeds = [s for s in seed_ids if s in G]
          
          if not valid_seeds:
              logger.warning("No valid seeds in graph for PPR")
              return {}
          
          for seed in valid_seeds:
              personalization[seed] = 1.0 / len(valid_seeds)
          
          try:
              ppr_scores = nx.pagerank(
                  G,
                  alpha=self.DAMPING_FACTOR,
                  personalization=personalization,
                  weight="weight"
              )
              return ppr_scores
          except Exception as e:
              logger.error(f"PPR computation failed: {e}")
              return {}
      
      def _get_top_destinations(
          self,
          ppr_scores: Dict[str, float],
          seed_ids: List[str],
          top_k: int
      ) -> List[tuple]:
          """
          Get top-K PPR nodes excluding seeds.
          
          Args:
              ppr_scores: PPR scores for all nodes
              seed_ids: Seed node IDs to exclude
              top_k: Number of destinations to return
          
          Returns:
              List of (node_id, score) tuples sorted by score descending
          """
          seed_set = set(seed_ids)
          destinations = [
              (node_id, score)
              for node_id, score in ppr_scores.items()
              if node_id not in seed_set and score > 0
          ]
          destinations.sort(key=lambda x: x[1], reverse=True)
          return destinations[:top_k]
      
      def _trace_paths_dijkstra(
          self,
          G: nx.DiGraph,
          seed_ids: List[str],
          top_destinations: List[tuple],
          subgraph_data: SubgraphData,
          edge_scores: Dict[str, float]
      ) -> List[SemanticPath]:
          """
          Trace semantic paths from seeds to destinations using Dijkstra.
          
          Args:
              G: NetworkX DiGraph with dijkstra_weight edges
              seed_ids: List of seed node IDs
              top_destinations: List of (dest_id, ppr_score) tuples
              subgraph_data: Original sub-graph data for node metadata
              edge_scores: Edge semantic scores for path scoring
          
          Returns:
              List of SemanticPath objects with complete path information
          """
          paths = []
          
          for dest_id, ppr_score in top_destinations:
              best_path = None
              best_cost = float("inf")
              best_seed = None
              
              for seed_id in seed_ids:
                  if seed_id not in G or dest_id not in G:
                      continue
                  
                  try:
                      path_nodes = nx.dijkstra_path(
                          G, seed_id, dest_id, weight="dijkstra_weight"
                      )
                      path_cost = nx.dijkstra_path_length(
                          G, seed_id, dest_id, weight="dijkstra_weight"
                      )
                      
                      if path_cost < best_cost:
                          best_cost = path_cost
                          best_path = path_nodes
                          best_seed = seed_id
                  except nx.NetworkXNoPath:
                      continue
              
              if best_path and len(best_path) >= 2:
                  path_obj = self._build_semantic_path(
                      G, best_path, best_seed, dest_id, ppr_score,
                      subgraph_data, edge_scores
                  )
                  if path_obj:
                      paths.append(path_obj)
          
          return paths
      
      def _build_semantic_path(
          self,
          G: nx.DiGraph,
          path_nodes: List[str],
          seed_id: str,
          dest_id: str,
          ppr_score: float,
          subgraph_data: SubgraphData,
          edge_scores: Dict[str, float]
      ) -> Optional[SemanticPath]:
          """
          Build SemanticPath object from path node list.
          
          Args:
              G: NetworkX DiGraph with edge metadata
              path_nodes: List of node IDs in path order
              seed_id: Starting seed node ID
              dest_id: Destination node ID
              ppr_score: PPR score of destination
              subgraph_data: Sub-graph data for node metadata lookup
              edge_scores: Edge semantic scores
          
          Returns:
              SemanticPath object with complete path information
          """
          nodes_data = subgraph_data.nodes
          source_node = nodes_data.get(seed_id) or GraphNode(
              id=seed_id, type="Unknown"
          )
          destination_node = nodes_data.get(dest_id) or GraphNode(
              id=dest_id, type="Unknown"
          )
          intermediate_nodes = [
              nodes_data.get(nid) or GraphNode(id=nid, type="Unknown")
              for nid in path_nodes[1:-1]
          ]
          
          edges: List[GraphEdge] = []
          semantic_scores = []
          
          for i in range(len(path_nodes) - 1):
              src, tgt = path_nodes[i], path_nodes[i + 1]
              if G.has_edge(src, tgt):
                  edge_data = G.edges[src, tgt]
                  
                  edge = GraphEdge(
                      source_id=src,
                      target_id=tgt,
                      relation_type=edge_data.get("relation_type", "RELATED_TO"),
                      vector_db_ref_id=edge_data.get("vector_db_ref_id"),
                      source_chunk=edge_data.get("source_chunk"),
                  )
                  edges.append(edge)
                  
                  if (
                      edge.vector_db_ref_id
                      and edge.vector_db_ref_id in edge_scores
                  ):
                      semantic_scores.append(edge_scores[edge.vector_db_ref_id])
          
          avg_semantic = (
              sum(semantic_scores) / len(semantic_scores)
              if semantic_scores
              else 0.0
          )
          
          return SemanticPath(
              source_node=source_node,
              destination_node=destination_node,
              intermediate_nodes=intermediate_nodes,
              edges=edges,
              ppr_score=ppr_score,
              path_semantic_score=avg_semantic
          )
  ```
- **Acceptance Criteria**:
  - [ ] Uses `networkx` for graph operations
  - [ ] `_extract_subgraph` uses `async_get_neighbors` with BFS
  - [ ] `_run_ppr` uses proper personalization dict
  - [ ] `_trace_paths_dijkstra` uses inverted weights (1.0 - score)
  - [ ] Returns `List[SemanticPath]` with all path information
  - [ ] Comprehensive docstrings on all methods

### Component 5: Global Searcher

#### Requirement 1 - Implement GlobalSearcher
- **Requirement**: Global semantic search on RelationDescriptions with entity enrichment
- **Implementation**:
  - `src/core/src/core/retrieval/global_search.py`
  ```python
  """
  Global semantic search for knowledge graph relations.

  This module provides the GlobalSearcher class which performs hybrid search
  on the RelationDescriptions collection to find relevant relationships
  regardless of graph structure. Results are enriched with full entity metadata
  from the graph database for meaningful verbalization.
  """

  import asyncio
  from typing import List, Dict, Optional
  from loguru import logger
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
  from shared.database_clients.graph_database.base_graph_database import (
      BaseGraphDatabase,
  )
  from shared.model_clients.embedder.base_embedder import BaseEmbedder
  from core.retrieval.models import GlobalRelation, GraphNode


  class GlobalSearcher:
      """
      Global semantic search via relation descriptions.
      
      Searches the RelationDescriptions collection to find relationships
      that are semantically similar to the query, regardless of graph
      structure. Complements local search by finding relevant concepts
      that may not be directly connected to seed nodes.
      """
      
      def __init__(
          self,
          vector_db: BaseVectorDatabase,
          graph_db: BaseGraphDatabase,
          embedder: BaseEmbedder,
          collection_name: str = "RelationDescriptions"
      ):
          """
          Initialize the global searcher.
          
          Args:
              vector_db: Vector database client for hybrid search
              graph_db: Graph database client for entity enrichment
              embedder: Embedder client for query embedding
              collection_name: Collection containing relation embeddings
          """
          self.vector_db = vector_db
          self.graph_db = graph_db
          self.embedder = embedder
          self.collection_name = collection_name
      
      async def search(
          self,
          queries: List[str],
          top_k_per_query: int = 5
      ) -> List[GlobalRelation]:
          """
          Search for relevant relations using global sub-queries.
          
          Args:
              queries: List of global sub-queries (from query decomposition)
              top_k_per_query: Number of results per query
          
          Returns:
              List of unique GlobalRelation objects with enriched entity data
          """
          if not queries:
              return []
          
          # Search all queries in parallel
          async def search_single_query(query: str) -> List[Dict]:
              query_embedding = await self.embedder.aget_query_embedding(query)
              
              embedding_data = [
                  EmbeddingData(
                      embedding_type=EmbeddingType.DENSE,
                      embeddings=query_embedding,
                      field_name="description_embedding",
                  ),
                  EmbeddingData(
                      embedding_type=EmbeddingType.SPARSE,
                      query=query,
                      field_name="description_sparse",
                  ),
              ]
              
              results = await self.vector_db.async_hybrid_search_vectors(
                  embedding_data=embedding_data,
                  output_fields=[
                      "id", "source_entity_id", "target_entity_id",
                      "relation_type", "description"
                  ],
                  top_k=top_k_per_query,
                  collection_name=self.collection_name,
                  metric_type=MetricType.COSINE,
                  index_type=IndexType.HNSW,
              )
              return results
          
          # Execute all queries in parallel
          results_per_query = await asyncio.gather(
              *[search_single_query(q) for q in queries]
          )
          
          # Flatten results
          all_results = []
          for results in results_per_query:
              all_results.extend(results)
          
          # Deduplicate by relation ID
          seen_ids = set()
          unique_results = []
          for r in all_results:
              if r["id"] not in seen_ids:
                  seen_ids.add(r["id"])
                  unique_results.append(r)
          
          # Enrich with entity data and source_chunk from GraphDB
          enriched_relations = await self._enrich_relations(unique_results)
          
          return enriched_relations
      
      async def _enrich_relations(
          self,
          raw_results: List[Dict]
      ) -> List[GlobalRelation]:
          """
          Enrich relation results with entity metadata from graph database.
          
          Fetches source and target entity nodes from GraphDB to get
          complete entity information (name, type, properties). Also
          retrieves source_chunk from the relationship edge properties.
          
          Args:
              raw_results: Raw search results from vector database
          
          Returns:
              List of GlobalRelation objects with full entity data
          """
          # Collect unique entity IDs to fetch
          entity_ids = set()
          for r in raw_results:
              entity_ids.add(r.get("source_entity_id", ""))
              entity_ids.add(r.get("target_entity_id", ""))
          entity_ids.discard("")  # Remove empty strings
          
          # Batch fetch entity data from GraphDB
          entity_cache: Dict[str, GraphNode] = {}
          for entity_id in entity_ids:
              try:
                  # Query across multiple possible labels
                  # Since we don't know the entity type, try common patterns
                  node_data = await self._fetch_entity_by_id(entity_id)
                  if node_data:
                      entity_cache[entity_id] = node_data
              except Exception as e:
                  logger.warning(f"Failed to fetch entity {entity_id}: {e}")
          
          # Build enriched GlobalRelation objects
          enriched = []
          for r in raw_results:
              source_id = r.get("source_entity_id", "")
              target_id = r.get("target_entity_id", "")
              
              # Get entity data from cache or create minimal node
              source_entity = entity_cache.get(source_id) or GraphNode(
                  id=source_id, type="Unknown", name=source_id
              )
              target_entity = entity_cache.get(target_id) or GraphNode(
                  id=target_id, type="Unknown", name=target_id
              )
              
              # Fetch source_chunk from graph edge properties
              source_chunk = await self._get_relation_source_chunk(
                  source_id, target_id, r.get("relation_type", "")
              )
              
              enriched.append(
                  GlobalRelation(
                      id=r.get("id", ""),
                      source_entity=source_entity,
                      target_entity=target_entity,
                      relation_type=r.get("relation_type", ""),
                      description=r.get("description", ""),
                      source_chunk=source_chunk,
                      score=r.get("_score", 0.0),
                  )
              )
          
          return enriched
      
      async def _fetch_entity_by_id(self, entity_id: str) -> Optional[GraphNode]:
          """
          Fetch entity node from graph database by ID.
          
          Queries EntityDescriptions collection to find entity type, then
          fetches full node data from graph database.
          
          Args:
              entity_id: Entity UUID
          
          Returns:
              GraphNode with entity metadata, or None if not found
          """
          # First, try to get entity type from EntityDescriptions collection
          try:
              entity_data = await self.vector_db.async_get_items(
                  ids=[entity_id],
                  collection_name="EntityDescriptions",
              )
              
              if entity_data:
                  entity = entity_data[0]
                  return GraphNode(
                      id=entity_id,
                      type=entity.get("entity_type", "Unknown"),
                      name=entity.get("entity_name", ""),
                      properties={
                          "description": entity.get("description", ""),
                      },
                  )
          except Exception as e:
              logger.debug(f"Could not fetch entity from VectorDB: {e}")
          
          return None
      
      async def _get_relation_source_chunk(
          self,
          source_id: str,
          target_id: str,
          relation_type: str
      ) -> Optional[str]:
          """
          Get source_chunk from relationship edge in graph database.
          
          Args:
              source_id: Source entity ID
              target_id: Target entity ID
              relation_type: Type of relationship
          
          Returns:
              Source chunk ID if found, None otherwise
          """
          try:
              # Query the edge properties from GraphDB
              query = f"""
                  MATCH (s)-[r:{relation_type}]->(t)
                  WHERE s.id = $source_id AND t.id = $target_id
                  RETURN r.source_chunk
                  LIMIT 1
              """
              result = await self.graph_db.async_execute_query(
                  query, {"source_id": source_id, "target_id": target_id}
              )
              
              # FalkorDB returns result with result_set attribute
              # result_set is List[List] where each row is a list of column values
              if result and hasattr(result, "result_set") and result.result_set:
                  source_chunk = result.result_set[0][0]
                  return source_chunk if source_chunk else None
          except Exception as e:
              logger.debug(f"Could not fetch source_chunk: {e}")
          
          return None
  ```
- **Acceptance Criteria**:
  - [ ] Uses hybrid search (dense + BM25)
  - [ ] Enriches results with entity metadata from GraphDB
  - [ ] Includes source_chunk for provenance tracking
  - [ ] Returns `List[GlobalRelation]` with full `GraphNode` entities
  - [ ] Deduplicates results across queries
  - [ ] Comprehensive docstrings

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Query Decomposition
- **Purpose**: Verify LLM correctly decomposes queries
- **Steps**:
  1. Call `decompose_query("What is the relationship between pricing strategy and customer value?")`
  2. Check `global_queries` contains thematic questions
  3. Check `local_queries` contains entity-focused questions
- **Expected Result**: Both lists populated with relevant sub-queries
- **Status**: ✅ PASSED - Integration test validates LLM decomposition with fallback handling

### Test Case 2: Edge Scoring
- **Purpose**: Verify edge scoring returns valid scores
- **Steps**:
  1. Create EdgeScorer with test Milvus connection
  2. Call `score_edges(query_embedding, sample_relation_ids)`
  3. Verify scores are between 0.0 and 1.0
- **Expected Result**: Dict with valid float scores
- **Status**: ✅ PASSED - Scores validated with real Milvus data, numpy vectorization working

### Test Case 3: Sub-graph Extraction
- **Purpose**: Verify K-hop BFS extracts correct sub-graph
- **Steps**:
  1. Create LocalSearcher with test connections
  2. Call `_extract_subgraph(seed_nodes, max_hops=2, max_neighbors=50)`
  3. Verify nodes and edges are populated
- **Expected Result**: SubgraphData with multiple nodes and edges
- **Status**: ✅ PASSED - Extracted 54 nodes, 64 edges from 5 seeds (2-hop traversal)

### Test Case 4: PPR Computation
- **Purpose**: Verify PageRank returns valid scores
- **Steps**:
  1. Build NetworkX graph from sub-graph
  2. Run `_run_ppr(G, seed_ids)`
  3. Verify non-seed nodes have positive scores
- **Expected Result**: Dict with PPR scores, destinations ranked
- **Status**: ✅ PASSED - PPR scores computed correctly, top destinations identified

### Test Case 5: Path Traceback
- **Purpose**: Verify Dijkstra traces coherent paths
- **Steps**:
  1. Get top PPR destinations
  2. Run `_trace_paths_dijkstra(...)`
  3. Verify paths connect seeds to destinations
- **Expected Result**: List of SemanticPath objects
- **Status**: ✅ PASSED - Dijkstra traced 3 semantic paths with valid scores

### Test Case 6: Global Search
- **Purpose**: Verify global relation search works
- **Steps**:
  1. Create GlobalSearcher
  2. Call `search(["pricing strategy", "value proposition"])`
  3. Verify results are deduplicated
- **Expected Result**: List of unique GlobalRelation objects
- **Status**: ✅ PASSED - Global search returns unique relations with entity enrichment


------------------------------------------------------------------------

## 🐛 Debugging & Bug Fixes

During integration testing with real production data, three critical bugs were discovered and fixed:

### Bug #1: FalkorDB Node ID Mismatch ❌ → ✅

**Problem**: 
- Cypher query used `WHERE n.id = $node_id` (looking for a property named 'id')
- But `graph_id` from Milvus EntityDescriptions is FalkorDB's internal node ID (integer)
- Query returned 0 neighbors despite graph having extensive data

**Root Cause**:
```python
# WRONG - tries to match property 'id'
MATCH (n)-[r]-(neighbor) WHERE n.id = $node_id

# CORRECT - uses internal ID function
MATCH (n)-[r]-(neighbor) WHERE id(n) = $node_id
```

**Fix Applied**:
- Changed query to use `id(n)` function instead of property lookup
- Cast node ID to `int(node.id)` for proper type matching
- **File**: `src/core/src/core/retrieval/local_search.py:295-296`

**Impact**: 
- Before: 0 edges extracted
- After: 54 nodes, 64 edges successfully extracted from 5 seed nodes

### Bug #2: NetworkX Duplicate Keyword Arguments ❌ → ✅

**Problem**:
```python
TypeError: networkx.classes.digraph.DiGraph.add_node() 
got multiple values for keyword argument 'name'
```

**Root Cause**:
```python
# WRONG - 'name' appears in both explicit args AND **node.properties
G.add_node(node_id, type=node.type, name=node.name, **node.properties)
```

**Fix Applied**:
```python
# Filter out 'name' and 'type' from properties dict before unpacking
props = {k: v for k, v in node.properties.items() if k not in ("name", "type")}
G.add_node(node_id, type=node.type, name=node.name, **props)
```

**File**: `src/core/src/core/retrieval/local_search.py:394-399`

**Impact**:
- Before: Crash immediately after subgraph extraction
- After: NetworkX graph built successfully, PPR computed

### Bug #3: Edge Property Array Handling ❌ → ✅

**Problem**:
- Code expected `source_chunk` (singular string)
- Actual DB schema has `source_chunks` (array of strings)

**Fix Applied**:
```python
# Handle source_chunks as array, take first element
source_chunks = rel_props.get("source_chunks") if rel_props else None
source_chunk = (
    source_chunks[0] 
    if source_chunks and isinstance(source_chunks, list) and len(source_chunks) > 0 
    else None
)
```

**File**: `src/core/src/core/retrieval/local_search.py:336-343`

### Debug Process

**Tools Used**:
1. Created standalone test script (`tests/manual/test_local_search_standalone.py`)
2. Added extensive debug logging to trace query execution
3. Inspected FalkorDB data directly via GUI to understand schema

**Key Learnings**:
- Always verify DB schema assumptions with actual data
- Internal IDs vs. properties require different Cypher syntax
- Standalone tests reveal errors that pytest might silence

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation to document what was actually accomplished.

### What Was Implemented

**Components Completed**:
- [x] ✅ [Component 1]: Data models (7 new models)
- [x] ✅ [Component 2]: QueryDecomposer
- [x] ✅ [Component 3]: EdgeScorer
- [x] ✅ [Component 4]: LocalSearcher (PPR + Dijkstra)
- [x] ✅ [Component 5]: GlobalSearcher

**Files Created/Modified**:
```
src/core/src/core/retrieval/
├── models.py                    # Extended with KG search models
├── query_decomposer.py          # LLM-based query decomposition
├── edge_scorer.py               # Semantic edge scoring
├── local_search.py              # Local PPR search
└── global_search.py             # Global relation search

tests/integration/
└── test_kg_search_components.py # Component tests
```

**Key Features Delivered**:
1. **Query Decomposition**: LLM splits queries into local/global
2. **Semantic PPR**: NetworkX-based PageRank with semantic weights
3. **Dijkstra Traceback**: Coherent path reconstruction
4. **Global Search**: Hybrid search on relations

### Technical Highlights

**Architecture Decisions**:
- NetworkX for in-memory graph ops (vs external graph algorithms)
- BaseModel types throughout (SeedNode, GraphNode, GraphEdge, etc.)
- Separation of concerns (EdgeScorer, LocalSearcher, GlobalSearcher)

**Documentation Added**:
- [ ] All functions have comprehensive docstrings
- [ ] Complex business logic is well-commented
- [ ] Module-level documentation explains purpose
- [ ] Type hints are complete and accurate

### Validation Results

**Test Coverage**:
- [x] ✅ **All 8/8 test cases PASSED** (100% success rate)
- [x] ✅ Real data validation with production DB
- [x] ✅ Edge cases handled (empty results, missing properties)
- [x] ✅ Error scenarios tested (connection errors, malformed data)

**Final Test Execution**:
```bash
pytest tests/integration/test_knowledge_graph_search.py -v
# Result: 8 passed, 3 warnings in 13.85s
```

**Component Breakdown**:
- QueryDecomposer: 2/2 tests ✅
- EdgeScorer: 2/2 tests ✅  
- LocalSearcher: 2/2 tests ✅ (PPR + Dijkstra fully working!)
- GlobalSearcher: 2/2 tests ✅

**Sample LocalSearcher Output** (with real data):
```
Query: "relationship between pricing and customer value"
→ Extracted sub-graph: 54 nodes, 64 edges (from 5 seeds)
→ Found 3 semantic paths:
   1. Customer Value → Products (PPR: 0.041, Semantic: 0.852)
   2. Pricing Strategy → Pricing Perception (PPR: 0.040, Semantic: 0.870)
   3. Customer Value → Marketing Process (PPR: 0.040, Semantic: 0.832)
```

**Deployment Notes**:
- Requires Stage 4 completion (EntityDescriptions, RelationDescriptions, FalkorDB populated)
- Uses existing SETTINGS configuration
- Requires `networkx` dependency (already in core[retrieval])

------------------------------------------------------------------------
