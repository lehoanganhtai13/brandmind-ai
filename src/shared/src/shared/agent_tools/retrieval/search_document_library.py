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
from core.retrieval.document_retriever import DocumentRetriever
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
    top_k: int = 10,
) -> str:
    """
    Search the document library for relevant text passages.

    Use this tool when you need:
    - Exact quotes or citations from books
    - Specific passages about a topic
    - Fact-checking or verification
    - Detailed explanations after understanding concepts from Knowledge Graph

    Strategy:
    1. First use search_knowledge_graph to understand concepts and find
       relevant sections
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
