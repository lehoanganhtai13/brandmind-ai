"""
Knowledge Graph search tool for agent use.

This tool provides the agent with semantic reasoning over marketing
concepts and their relationships. It combines local graph traversal
(PPR) with global relation matching to discover connected knowledge.

Best Practices for Agent:
- Use this tool first to understand concepts and relationships
- Note the source metadata (books, chapters) in the output
- Then use search_document_library for specific passages if needed
- Query should be natural language questions about marketing
"""

from typing import Optional

from config.system_config import SETTINGS
from core.retrieval.kg_retriever import KGRetriever
from shared.database_clients.graph_database.falkordb.client import FalkorDBClient
from shared.database_clients.graph_database.falkordb.config import FalkorDBConfig
from shared.database_clients.vector_database.milvus.config import MilvusConfig
from shared.database_clients.vector_database.milvus.database import (
    MilvusVectorDatabase,
)
from shared.model_clients.embedder.gemini import GeminiEmbedder
from shared.model_clients.embedder.gemini.config import (
    EmbeddingMode,
    GeminiEmbedderConfig,
)

# Singleton retriever instance
_retriever: Optional[KGRetriever] = None


def _get_retriever() -> KGRetriever:
    """
    Lazy initialization of retriever singleton.

    Creates MilvusVectorDatabase, FalkorDBClient, and GeminiEmbedder
    instances using settings from SETTINGS configuration. Reuses the
    same KGRetriever instance for all subsequent calls.

    Returns:
        Initialized KGRetriever instance
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

        # Initialize FalkorDB client
        graph_db = FalkorDBClient(
            config=FalkorDBConfig(
                host=SETTINGS.FALKORDB_HOST,
                port=SETTINGS.FALKORDB_PORT,
                username=SETTINGS.FALKORDB_USERNAME,
                password=SETTINGS.FALKORDB_PASSWORD,
                graph_name=SETTINGS.FALKORDB_GRAPH_NAME,
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

        _retriever = KGRetriever(
            graph_db=graph_db,
            vector_db=vector_db,
            embedder=embedder,
        )
    return _retriever


async def search_knowledge_graph(
    query: str,
    max_results: int = 10,
) -> str:
    """
    Search the Knowledge Graph for concepts and relationships.

    Use this tool when you need:
    - Understanding of marketing concepts and their relationships
    - Multi-hop reasoning about how ideas connect
    - Discovery of related concepts and techniques
    - Identification of relevant book sections before deep-dive

    Strategy:
    1. Use this tool first to understand the topic landscape
    2. Review the entities, relationships, and their descriptions
    3. Note the source metadata (books, chapters) for follow-up
    4. Use search_document_library for detailed passages if needed

    Args:
        query: Natural language question about marketing concepts.
            Examples:
            - "How does pricing strategy affect customer value?"
            - "What is market segmentation?"
            - "Relationship between brand positioning and differentiation"
        max_results: Maximum facts to return. Default 10.

    Returns:
        Structured Markdown with:
        - Entities section: Discovered concepts with their types
        - Relationships section: Paths and connections with descriptions
        - Source metadata: Book and chapter references for each fact
    """
    retriever = _get_retriever()
    return await retriever.search(query=query, max_results=max_results)
