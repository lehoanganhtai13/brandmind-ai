"""
Knowledge Graph Retriever orchestrator.

This module provides the KGRetriever class which coordinates local search
(PPR-based graph traversal) and global search (relation description matching)
to provide comprehensive semantic context for knowledge graph queries.
"""

import asyncio
import json
from typing import Dict, List

from loguru import logger
from pydantic import BaseModel, Field

from config.system_config import SETTINGS
from core.retrieval.global_search import GlobalSearcher
from core.retrieval.local_search import LocalSearcher, SemanticPath
from core.retrieval.models import (
    GlobalRelation,
    GraphNode,
    SourceMetadata,
    VerbalizedFact,
)
from core.retrieval.query_decomposer import decompose_query
from prompts.knowledge_graph.rerank_diversity_instruction import (
    RERANK_DIVERSITY_INSTRUCTION,
)
from prompts.knowledge_graph.rerank_diversity_task_prompt import (
    RERANK_DIVERSITY_TASK_PROMPT,
)
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder
from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig


class RerankResponse(BaseModel):
    """
    Structured response from LLM reranking.

    Used to parse JSON output from reranking LLM call, ensuring
    valid index references to the original fact list.
    """

    top_ranked_ids: List[int] = Field(
        ..., description="Ordered list of selected fact indices (0-based)"
    )


class KGRetriever:
    """
    Knowledge Graph Retriever with dual-level search and LLM reranking.

    Orchestrates local search (PPR-based graph traversal) and global search
    (relation description matching) to provide comprehensive context for
    knowledge graph queries.

    Args:
        graph_db: Graph database client for local search
        vector_db: Vector database client for entity/relation search
        embedder: Embedder client for query embedding
        document_chunks_collection: Collection name for source metadata lookup
    """

    def __init__(
        self,
        graph_db: BaseGraphDatabase,
        vector_db: BaseVectorDatabase,
        embedder: BaseEmbedder,
        document_chunks_collection: str = "DocumentChunks",
    ):
        self.graph_db = graph_db
        self.vector_db = vector_db
        self.embedder = embedder
        self.document_chunks_collection = document_chunks_collection

        # Initialize searchers with shared clients
        self.local_searcher = LocalSearcher(
            graph_db=graph_db,
            vector_db=vector_db,
            embedder=embedder,
        )
        self.global_searcher = GlobalSearcher(
            vector_db=vector_db,
            graph_db=graph_db,
            embedder=embedder,
        )

    async def search(
        self,
        query: str,
        max_results: int = 10,
        max_seed_nodes: int = 10,
        max_hops: int = 2,
        top_k_destinations: int = 5,
    ) -> str:
        """
        Perform comprehensive knowledge graph search.

        Executes a 7-step pipeline: decomposition → parallel search →
        verbalization → enrichment → reranking → formatting.

        Args:
            query: User query (natural language question)
            max_results: Maximum facts to return after reranking
            max_seed_nodes: Maximum seed nodes for local search
            max_hops: Graph traversal depth
            top_k_destinations: Number of PPR destinations to trace

        Returns:
            Structured Markdown context for LLM consumption
        """
        # Step 1: Decompose query into local and global sub-queries
        decomposed = await decompose_query(query)
        logger.info(
            f"Decomposed: {len(decomposed.local_queries)} local, "
            f"{len(decomposed.global_queries)} global"
        )

        # Step 2: Execute local and global search in parallel
        local_task = self.local_searcher.search(
            local_queries=decomposed.local_queries,
            query=query,
            max_seeds=max_seed_nodes,
            max_hops=max_hops,
            top_k_destinations=top_k_destinations,
        )
        global_task = self.global_searcher.search(
            queries=decomposed.global_queries,
            top_k_per_query=5,
        )

        local_paths, global_relations = await asyncio.gather(local_task, global_task)

        logger.info(
            f"Search results: {len(local_paths)} local paths, "
            f"{len(global_relations)} global relations"
        )

        # Step 3: Verbalize results (convert to human-readable facts)
        all_facts = self._verbalize_results(local_paths, global_relations)

        if not all_facts:
            return "No relevant knowledge found for this query."

        # Step 4: Enrich with source metadata
        all_facts = await self._enrich_with_source_metadata(all_facts)

        # Step 5: Rerank if too many results
        if len(all_facts) > max_results:
            all_facts = await self._rerank(query, all_facts, max_results)

        # Step 6: Format output as Markdown
        return self._format_output(all_facts)

    def _verbalize_results(
        self,
        local_paths: List[SemanticPath],
        global_relations: List[GlobalRelation],
    ) -> List[VerbalizedFact]:
        """
        Convert search results to verbalized facts with descriptions.

        Args:
            local_paths: Semantic paths from LocalSearcher
            global_relations: Relations from GlobalSearcher

        Returns:
            List of VerbalizedFact objects ready for reranking
        """
        facts: List[VerbalizedFact] = []

        # Verbalize local paths WITH edge descriptions
        for path in local_paths:
            # Build path string with descriptions
            path_parts = [path.source_node.name]
            for edge in path.edges:
                # Include description if available
                if edge.description:
                    path_parts.append(
                        f"--[{edge.relation_type}: {edge.description}]-->"
                    )
                else:
                    path_parts.append(f"--[{edge.relation_type}]-->")
            path_parts.append(path.destination_node.name)
            path_str = " ".join(path_parts)

            # Collect source_chunk IDs from edges for provenance
            chunk_ids = [edge.source_chunk for edge in path.edges if edge.source_chunk]

            facts.append(
                VerbalizedFact(
                    type="local",
                    text=path_str,
                    source_chunk_ids=chunk_ids,
                    source_node=path.source_node,
                    destination_node=path.destination_node,
                    intermediate_nodes=path.intermediate_nodes,
                    edges=path.edges,
                    ppr_score=path.ppr_score,
                    semantic_score=path.path_semantic_score,
                )
            )

        # Verbalize global relations (already have descriptions)
        for rel in global_relations:
            text = (
                f"{rel.source_entity.name} "
                f"--[{rel.relation_type}]--> "
                f"{rel.target_entity.name}: "
                f"{rel.description}"
            )

            # Global relations may have source_chunk from edge properties
            chunk_ids = [rel.source_chunk] if rel.source_chunk else []

            facts.append(
                VerbalizedFact(
                    type="global",
                    text=text,
                    source_chunk_ids=chunk_ids,
                    relation=rel,
                )
            )

        return facts

    async def _enrich_with_source_metadata(
        self,
        facts: List[VerbalizedFact],
    ) -> List[VerbalizedFact]:
        """
        Enrich facts with source document metadata.

        Fetches source/original_document from DocumentChunks collection
        using chunk IDs stored in edge properties. Enables agent to know
        WHERE each piece of knowledge came from.

        Args:
            facts: List of VerbalizedFact with source_chunk_ids

        Returns:
            Facts enriched with source_metadata (SourceMetadata objects)
        """
        # Collect all unique chunk IDs
        all_chunk_ids = set()
        for fact in facts:
            all_chunk_ids.update(fact.source_chunk_ids)

        if not all_chunk_ids:
            return facts

        try:
            # Batch fetch chunk metadata from DocumentChunks
            chunk_records = await self.vector_db.async_get_items(
                ids=list(all_chunk_ids),
                collection_name=self.document_chunks_collection,
            )

            # Build lookup map: chunk_id -> metadata
            chunk_metadata: Dict[str, SourceMetadata] = {}
            for record in chunk_records:
                chunk_id = record.get("id")
                if chunk_id:
                    chunk_metadata[chunk_id] = SourceMetadata(
                        source=record.get("source", ""),
                        original_document=record.get("original_document", ""),
                        author=record.get("author", ""),
                    )

            # Enrich each fact with source metadata
            enriched_facts: List[VerbalizedFact] = []
            for fact in facts:
                sources = [
                    chunk_metadata[cid]
                    for cid in fact.source_chunk_ids
                    if cid in chunk_metadata
                ]

                # Deduplicate sources by (source, original_document)
                unique_sources: List[SourceMetadata] = []
                seen = set()
                for s in sources:
                    key = (s.source, s.original_document)
                    if key not in seen:
                        seen.add(key)
                        unique_sources.append(s)

                # Create updated fact with source_metadata
                enriched_facts.append(
                    fact.model_copy(update={"source_metadata": unique_sources})
                )

            return enriched_facts

        except Exception as e:
            logger.warning(f"Failed to enrich source metadata: {e}")
            # Gracefully return facts without enrichment
            return facts

    async def _rerank(
        self,
        query: str,
        facts: List[VerbalizedFact],
        top_k: int,
    ) -> List[VerbalizedFact]:
        """
        Use LLM to rerank and select diverse facts.

        Args:
            query: Original user query
            facts: All candidate facts
            top_k: Number of facts to select

        Returns:
            Top-K diverse facts selected by LLM
        """
        try:
            llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model="gemini-2.5-flash-lite",
                    api_key=SETTINGS.GEMINI_API_KEY,
                    system_instruction=RERANK_DIVERSITY_INSTRUCTION,
                    temperature=0.1,
                    max_tokens=4000,
                    thinking_budget=2000,
                    response_mime_type="application/json",
                    response_schema=RerankResponse,
                )
            )

            # Build candidates list with indices
            candidates_text = "\n".join(
                [f"[{i}] {fact.text}" for i, fact in enumerate(facts)]
            )

            # Replace placeholders in task prompt
            task_prompt = (
                RERANK_DIVERSITY_TASK_PROMPT.replace("{{QUERY}}", query)
                .replace("{{CANDIDATES_LIST}}", candidates_text)
                .replace("{{TOP_K}}", str(top_k))
            )

            response = llm.complete(task_prompt).text
            result = json.loads(response)

            # Extract selected facts by indices
            selected = [facts[i] for i in result["top_ranked_ids"] if i < len(facts)]

            logger.info(f"Reranked: {len(facts)} -> {len(selected)} facts")
            return selected

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return first top_k facts
            return facts[:top_k]

    def _format_output(self, facts: List[VerbalizedFact]) -> str:
        """
        Format facts as structured Markdown for agent consumption.

        Args:
            facts: Reranked list of VerbalizedFact

        Returns:
            Markdown string with entities, relationships, and sources
        """
        output = ["## Retrieved Knowledge from Knowledge Graph\n"]

        # Collect unique entities from all facts
        entities: Dict[str, GraphNode] = {}
        for f in facts:
            if f.source_node:
                entities[f.source_node.id] = f.source_node
            if f.destination_node:
                entities[f.destination_node.id] = f.destination_node
            for node in f.intermediate_nodes:
                entities[node.id] = node
            # Add entities from global relations
            if f.relation:
                entities[f.relation.source_entity.id] = f.relation.source_entity
                entities[f.relation.target_entity.id] = f.relation.target_entity

        # Entities section
        if entities:
            output.append("### Entities\n")
            for e in entities.values():
                output.append(f"* **{e.name}** ({e.type})")
                desc = e.properties.get("description", "")
                if desc:
                    # Truncate long descriptions
                    output.append(f"  * {desc[:200]}")

        # Relationships & Paths section
        output.append("\n### Relationships & Paths\n")
        for f in facts:
            output.append(f"* {f.text}")

            # Include source metadata for provenance
            if f.source_metadata:
                for src in f.source_metadata:
                    output.append(
                        f"  * 📚 Source: {src.source} | Document: {src.original_document}"
                    )

        return "\n".join(output)
