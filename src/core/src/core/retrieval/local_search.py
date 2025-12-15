"""
Local semantic search using Personalized PageRank with Dijkstra traceback.

This module provides the LocalSearcher class for multi-hop knowledge graph
traversal. It finds semantically related concepts by exploring the graph
neighborhood around entity matches and ranking paths by importance.
"""

import asyncio
from typing import Dict, List, Optional

import networkx as nx
from loguru import logger
from pydantic import BaseModel, Field

from core.retrieval.edge_scorer import EdgeScorer
from core.retrieval.models import GraphEdge, GraphNode, SeedNode, SubgraphData
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.vector_database.base_class import (
    EmbeddingData,
    EmbeddingType,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.database_clients.vector_database.milvus.utils import (
    IndexType,
    MetricType,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder


class SemanticPath(BaseModel):
    """
    Represents a semantic path from a seed node to a high-PPR destination.

    Contains all nodes and edges along the path, plus scoring information
    for ranking and context assembly.
    """

    source_node: GraphNode = Field(..., description="Starting node (seed)")
    destination_node: GraphNode = Field(..., description="High-PPR destination node")
    intermediate_nodes: List[GraphNode] = Field(
        default_factory=list,
        description="Bridge nodes connecting source to destination",
    )
    edges: List[GraphEdge] = Field(
        default_factory=list, description="Edges along the path with properties"
    )
    ppr_score: float = Field(..., description="PPR score of the destination node")
    path_semantic_score: float = Field(
        default=0.0, description="Average semantic similarity of edges in path"
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
        max_neighbors_per_node: int = 50,
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
        edge_scores = await self._score_all_edges(query_embedding, subgraph_data.edges)

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
        self, local_queries: List[str], max_seeds: int
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
                output_fields=["id", "graph_id", "name", "type", "description"],
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
                        name=s.get("name", ""),
                        type=s.get("type", ""),
                        description=s.get("description", ""),
                        score=s.get("_score", 0.0),
                    )
                )

        return unique[:max_seeds]

    async def _extract_subgraph(
        self, seed_nodes: List[SeedNode], max_hops: int, max_neighbors: int
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
                    # Use raw Cypher to get neighbors WITH edge properties
                    # Use WHERE id(n) for internal FalkorDB node ID (not property)
                    query = """
                    MATCH (n)-[r]-(neighbor)
                    WHERE id(n) = $node_id
                    RETURN neighbor, id(neighbor) as neighbor_id,
                           type(r) as rel_type, properties(r) as rel_props
                    LIMIT $max_neighbors
                    """
                    result = await self.graph_db.async_execute_query(
                        query, {"node_id": int(node.id), "max_neighbors": max_neighbors}
                    )

                    if not result or not hasattr(result, "result_set"):
                        logger.debug(f"No result returned for node {node.id}")
                        continue

                    neighbors_data = result.result_set
                    for record in neighbors_data:
                        neighbor_node_obj = record[0]
                        neighbor_id = str(record[1])
                        rel_type = record[2]
                        rel_props = record[3] if len(record) > 3 else {}

                        if neighbor_id:
                            # Store neighbor node
                            if neighbor_id not in all_nodes:
                                neighbor_node = GraphNode(
                                    id=neighbor_id,
                                    type=(
                                        neighbor_node_obj.labels[0]
                                        if neighbor_node_obj.labels
                                        else "Unknown"
                                    ),
                                    name=neighbor_node_obj.properties.get("name", ""),
                                    properties=neighbor_node_obj.properties,
                                )
                                all_nodes[neighbor_id] = neighbor_node
                                next_frontier.append(neighbor_node)

                            # Store edge WITH properties including description
                            source_chunks = (
                                rel_props.get("source_chunks") if rel_props else None
                            )
                            edge = GraphEdge(
                                source_id=node.id,
                                target_id=neighbor_id,
                                relation_type=rel_type or "RELATED_TO",
                                description=(
                                    rel_props.get("description", "")
                                    if rel_props
                                    else ""
                                ),
                                vector_db_ref_id=(
                                    rel_props.get("vector_db_ref_id")
                                    if rel_props
                                    else None
                                ),
                                source_chunk=(
                                    source_chunks[0]
                                    if source_chunks
                                    and isinstance(source_chunks, list)
                                    and len(source_chunks) > 0
                                    else None
                                ),
                            )
                            all_edges.append(edge)
                except Exception as e:
                    logger.warning(f"Error getting neighbors for node {node.id}: {e}")
                    continue

            frontier = next_frontier

        logger.info(
            f"Extracted sub-graph: {len(all_nodes)} nodes, {len(all_edges)} edges"
        )
        return SubgraphData(nodes=all_nodes, edges=all_edges)

    async def _score_all_edges(
        self, query_embedding: List[float], edges: List[GraphEdge]
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
        self, subgraph_data: SubgraphData, edge_scores: Dict[str, float]
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
            # Exclude 'name' and 'type' from properties to avoid duplicate kwargs
            props = {
                k: v for k, v in node.properties.items() if k not in ("name", "type")
            }
            G.add_node(node_id, type=node.type, name=node.name, **props)

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
                    dijkstra_weight=(1.0 - semantic_weight + 0.01),
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
                weight="weight",
            )
            return ppr_scores
        except Exception as e:
            logger.error(f"PPR computation failed: {e}")
            return {}

    def _get_top_destinations(
        self, ppr_scores: Dict[str, float], seed_ids: List[str], top_k: int
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
        edge_scores: Dict[str, float],
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

            if best_path and best_seed and len(best_path) >= 2:
                path_obj = self._build_semantic_path(
                    G,
                    best_path,
                    best_seed,
                    dest_id,
                    ppr_score,
                    subgraph_data,
                    edge_scores,
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
        edge_scores: Dict[str, float],
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
        source_node = nodes_data.get(seed_id) or GraphNode(id=seed_id, type="Unknown")
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

                if edge.vector_db_ref_id and edge.vector_db_ref_id in edge_scores:
                    semantic_scores.append(edge_scores[edge.vector_db_ref_id])

        avg_semantic = (
            sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0.0
        )

        return SemanticPath(
            source_node=source_node,
            destination_node=destination_node,
            intermediate_nodes=intermediate_nodes,
            edges=edges,
            ppr_score=ppr_score,
            path_semantic_score=avg_semantic,
        )
