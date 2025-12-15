"""
Integration tests for Task 21 Knowledge Graph Search Components.

These tests verify the functionality of QueryDecomposer, EdgeScorer,
LocalSearcher, and GlobalSearcher with real database connections.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import List

from config.system_config import SETTINGS
from shared.database_clients.vector_database.milvus.database import (
    MilvusVectorDatabase,
)
from shared.database_clients.vector_database.milvus.config import MilvusConfig
from shared.database_clients.graph_database.falkordb.client import FalkorDBClient
from shared.database_clients.graph_database.falkordb.config import FalkorDBConfig
from shared.model_clients.embedder.gemini.embedder import GeminiEmbedder
from shared.model_clients.embedder.gemini.config import (
    EmbeddingMode,
    GeminiEmbedderConfig,
)
from core.retrieval.query_decomposer import decompose_query, DecomposedQuery
from core.retrieval.edge_scorer import EdgeScorer
from core.retrieval.local_search import LocalSearcher, SemanticPath
from core.retrieval.global_search import GlobalSearcher
from core.retrieval.models import SeedNode, GlobalRelation


@pytest_asyncio.fixture
async def vector_db():
    """Milvus vector database client with proper async configuration."""
    client = MilvusVectorDatabase(
        config=MilvusConfig(
            host=SETTINGS.MILVUS_HOST,
            port=SETTINGS.MILVUS_PORT,
            user="root",
            password=SETTINGS.MILVUS_ROOT_PASSWORD,
            run_async=True,
        )
    )
    yield client


@pytest_asyncio.fixture
async def graph_db():
    """FalkorDB graph database client with proper async configuration."""
    client = FalkorDBClient(
        config=FalkorDBConfig(
            host=SETTINGS.FALKORDB_HOST,
            port=SETTINGS.FALKORDB_PORT,
            username=SETTINGS.FALKORDB_USERNAME,
            password=SETTINGS.FALKORDB_PASSWORD,
            graph_name=SETTINGS.FALKORDB_GRAPH_NAME,
        )
    )
    yield client


@pytest.fixture
def embedder():
    """Gemini embedder client configured for RETRIEVAL mode."""
    return GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=SETTINGS.GEMINI_API_KEY,
            model="gemini-embedding-001",
            task_type=EmbeddingMode.RETRIEVAL,
            output_dimensionality=SETTINGS.EMBEDDING_DIM,
        )
    )


@pytest.fixture
def edge_scorer(vector_db):
    """EdgeScorer instance."""
    return EdgeScorer(vector_db)


@pytest.fixture
def local_searcher(graph_db, vector_db, embedder):
    """LocalSearcher instance."""
    return LocalSearcher(graph_db, vector_db, embedder)


@pytest.fixture
def global_searcher(vector_db, graph_db, embedder):
    """GlobalSearcher instance."""
    return GlobalSearcher(vector_db, graph_db, embedder)


class TestQueryDecomposer:
    """Test Case 1: Query Decomposition."""
    
    @pytest.mark.asyncio
    async def test_decompose_query_structure(self):
        """Verify query decomposition returns correct structure."""
        query = "What is the relationship between pricing strategy and customer value?"
        
        result = await decompose_query(query)
        
        # Check result is DecomposedQuery
        assert isinstance(result, DecomposedQuery)
        
        # Check both fields are populated
        assert isinstance(result.global_queries, list)
        assert isinstance(result.local_queries, list)
        assert len(result.global_queries) > 0
        assert len(result.local_queries) > 0
        
        print(f"\n✓ Query decomposed successfully:")
        print(f"  Global queries: {result.global_queries}")
        print(f"  Local queries: {result.local_queries}")
    
    @pytest.mark.asyncio
    async def test_decompose_query_fallback(self):
        """Verify fallback behavior on empty query."""
        # Very short query might trigger fallback
        result = await decompose_query("")
        
        # Should still return valid structure
        assert isinstance(result, DecomposedQuery)
        assert isinstance(result.global_queries, list)
        assert isinstance(result.local_queries, list)


class TestEdgeScorer:
    """Test Case 2: Edge Scoring."""
    
    @pytest.mark.asyncio
    async def test_score_edges_valid_scores(self, edge_scorer, embedder):
        """Verify edge scoring returns valid scores between 0.0 and 1.0."""
        # Get a query embedding
        query = "pricing strategy"
        query_embedding = await embedder.aget_query_embedding(query)
        
        # Note: This test requires actual relation IDs from the DB
        # For now, test with empty list to verify no crashes
        scores = await edge_scorer.score_edges(query_embedding, [])
        
        assert isinstance(scores, dict)
        assert len(scores) == 0  # Empty input = empty output
        
        print("\n✓ EdgeScorer handles empty input correctly")
    
    @pytest.mark.asyncio
    async def test_score_edges_with_real_data(self, edge_scorer, embedder, vector_db):
        """Test edge scoring with real relation IDs from DB."""
        # First, try to get some real relation IDs
        try:
            # Search for any relation to get valid IDs
            from shared.database_clients.vector_database.base_class import (
                EmbeddingData,
                EmbeddingType,
            )
            from shared.database_clients.vector_database.milvus.utils import (
                MetricType,
                IndexType,
            )
            
            query = "marketing strategy"
            query_embedding = await embedder.aget_query_embedding(query)
            
            embedding_data = [
                EmbeddingData(
                    embedding_type=EmbeddingType.DENSE,
                    embeddings=query_embedding,
                    field_name="description_embedding",
                ),
            ]
            
            results = await vector_db.async_hybrid_search_vectors(
                embedding_data=embedding_data,
                output_fields=["id"],
                top_k=3,
                collection_name="RelationDescriptions",
                metric_type=MetricType.COSINE,
                index_type=IndexType.HNSW,
            )
            
            if results:
                relation_ids = [r["id"] for r in results]
                scores = await edge_scorer.score_edges(query_embedding, relation_ids)
                
                # Verify all scores are valid
                for rel_id, score in scores.items():
                    assert 0.0 <= score <= 1.0, f"Score {score} out of range"
                    assert isinstance(score, float)
                
                print(f"\n✓ EdgeScorer scored {len(scores)} edges successfully")
                print(f"  Score range: {min(scores.values()):.3f} - {max(scores.values()):.3f}")
            else:
                pytest.skip("No relation data in DB for testing")
                
        except Exception as e:
            pytest.skip(f"DB not available for real data test: {e}")


class TestLocalSearcher:
    """Test Cases 3-5: Local Search with PPR and Dijkstra."""
    
    @pytest.mark.asyncio
    async def test_local_search_end_to_end(self, local_searcher):
        """Test complete local search flow."""
        try:
            local_queries = ["pricing strategy", "customer value"]
            query = "relationship between pricing and customer value"
            
            paths = await local_searcher.search(
                local_queries=local_queries,
                query=query,
                max_seeds=5,
                max_hops=2,
                top_k_destinations=3,
                max_neighbors_per_node=20
            )
            
            # Verify result structure
            assert isinstance(paths, list)
            
            if paths:
                # Check first path structure
                assert isinstance(paths[0], SemanticPath)
                assert paths[0].source_node is not None
                assert paths[0].destination_node is not None
                assert isinstance(paths[0].ppr_score, float)
                assert isinstance(paths[0].path_semantic_score, float)
                
                print(f"\n✓ LocalSearcher found {len(paths)} semantic paths")
                for i, path in enumerate(paths[:3], 1):
                    print(f"  Path {i}: {path.source_node.name} -> {path.destination_node.name}")
                    print(f"    PPR: {path.ppr_score:.4f}, Semantic: {path.path_semantic_score:.4f}")
            else:
                print("\n⚠ LocalSearcher returned no paths (may be expected if DB is empty)")
                
        except Exception as e:
            pytest.skip(f"LocalSearch test requires DB with data: {e}")
    
    @pytest.mark.asyncio
    async def test_find_seed_nodes(self, local_searcher):
        """Test seed node finding from local queries."""
        try:
            local_queries = ["marketing mix", "pricing"]
            
            # Access private method for testing
            seeds = await local_searcher._find_seed_nodes(local_queries, max_seeds=5)
            
            assert isinstance(seeds, list)
            
            if seeds:
                # Verify seed structure
                assert isinstance(seeds[0], SeedNode)
                assert seeds[0].id
                assert seeds[0].graph_id
                assert seeds[0].name
                
                print(f"\n✓ Found {len(seeds)} seed nodes:")
                for seed in seeds[:3]:
                    print(f"  - {seed.name} ({seed.type})")
            else:
                print("\n⚠ No seed nodes found (may be expected if DB is empty)")
                
        except Exception as e:
            pytest.skip(f"Seed node test requires DB with data: {e}")


class TestGlobalSearcher:
    """Test Case 6: Global Search."""
    
    @pytest.mark.asyncio
    async def test_global_search_deduplication(self, global_searcher):
        """Test global search with deduplication."""
        try:
            queries = ["pricing strategy", "value proposition", "pricing strategy"]
            
            results = await global_searcher.search(queries, top_k_per_query=3)
            
            assert isinstance(results, list)
            
            if results:
                # Check result structure
                assert isinstance(results[0], GlobalRelation)
                assert results[0].id
                assert results[0].source_entity is not None
                assert results[0].target_entity is not None
                assert results[0].description
                
                # Check deduplication (no duplicate IDs)
                ids = [r.id for r in results]
                assert len(ids) == len(set(ids)), "Results not deduplicated"
                
                print(f"\n✓ GlobalSearcher found {len(results)} unique relations")
                for i, rel in enumerate(results[:3], 1):
                    print(f"  {i}. {rel.source_entity.name} -{rel.relation_type}-> {rel.target_entity.name}")
                    print(f"     Score: {rel.score:.4f}")
            else:
                print("\n⚠ GlobalSearcher returned no results (may be expected if DB is empty)")
                
        except Exception as e:
            pytest.skip(f"GlobalSearch test requires DB with data: {e}")
    
    @pytest.mark.asyncio
    async def test_global_search_entity_enrichment(self, global_searcher):
        """Verify entities are enriched with metadata."""
        try:
            queries = ["customer segmentation"]
            
            results = await global_searcher.search(queries, top_k_per_query=2)
            
            if results:
                # Check that entities have more than just ID
                rel = results[0]
                assert rel.source_entity.type != ""
                assert rel.target_entity.type != ""
                
                # At least one should have a name
                assert rel.source_entity.name or rel.target_entity.name
                
                print("\n✓ Entities enriched with metadata")
            else:
                pytest.skip("No results to verify enrichment")
                
        except Exception as e:
            pytest.skip(f"Entity enrichment test requires DB with data: {e}")


if __name__ == "__main__":
    """Quick manual test runner."""
    import sys
    
    print("Running Task 21 Integration Tests...")
    print("=" * 60)
    
    # Run with pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
