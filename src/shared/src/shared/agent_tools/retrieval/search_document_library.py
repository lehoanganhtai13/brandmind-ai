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
from core.retrieval.models import DocumentChunkResult
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
CONTENT_PREVIEW_CHAR_LIMIT = 3200
DIRECT_EVIDENCE_RESULT_LIMIT = 3
NEIGHBOR_PREVIEW_CHAR_LIMIT = 450
OPENING_EVIDENCE_CHAR_LIMIT = 360
NO_RESULTS_MESSAGE = "No results found."
QUERY_EXPANSION_ALIASES = {
    "chiến lược marketing hướng tới giá trị khách hàng": (
        "customer value-driven marketing strategy customer-driven marketing "
        "strategy segmentation targeting differentiation positioning value "
        "proposition"
    ),
    "chủ nghĩa môi trường": "environmentalism environmental sustainability",
    "chủ nghĩa tiêu dùng": "consumerism organized social movement",
    "cấu trúc gia đình tại mỹ": (
        "The Changing American Family market segmentation lifestyle life stage "
        "common values age-specific segments birth date"
    ),
    "customer value-driven marketing": (
        "customer-driven marketing strategy segmentation targeting "
        "differentiation positioning value proposition"
    ),
    "family structure": (
        "The Changing American Family market segmentation lifestyle life stage "
        "common values age-specific segments birth date"
    ),
    "changing family dynamics": (
        "The Changing American Family market segmentation lifestyle life stage "
        "common values age-specific segments birth date"
    ),
    "family dynamics": (
        "The Changing American Family market segmentation lifestyle life stage "
        "common values age-specific segments birth date"
    ),
    "fast-moving bank": "United Jersey fast-moving bank positioning",
    "quy trình thiết kế": (
        "designing customer-driven marketing strategy segmentation targeting "
        "differentiation positioning value proposition"
    ),
    "bốn bước": (
        "segmentation targeting differentiation positioning value proposition"
    ),
    "sustainable marketing": (
        "sustainable marketing principles consumer-oriented marketing customer "
        "value marketing innovative marketing sense-of-mission marketing "
        "societal marketing"
    ),
    "tiếp thị bền vững": (
        "sustainable marketing principles consumer-oriented marketing customer "
        "value marketing innovative marketing sense-of-mission marketing "
        "societal marketing"
    ),
}


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
    source_chunk_id: Optional[str] = None,
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
        source_chunk_id: Exact DocumentChunks ID copied from Knowledge Graph output.
            Use this when KG provides a source chunk pointer for a follow-up read.
        top_k: Number of results to return. Default 10.

    Returns:
        Formatted text with relevant passages and their sources.
        Each result includes: source location, book name, and content preview.
    """
    retriever = _get_retriever()

    if source_chunk_id:
        chunk_ids = parse_source_chunk_ids(source_chunk_id)
        results = await retriever.get_chunks_by_ids(chunk_ids)
        if not results:
            return (
                f"{NO_RESULTS_MESSAGE}\n"
                "Next step: copy source_chunk_id exactly from the Knowledge Graph "
                "evidence map, or retry with a scoped book/chapter search."
            )
        return format_document_chunks(results, lookup_mode="source_chunk_id")

    expanded_query = expand_document_query(query)
    results = await retriever.search(
        query=expanded_query,
        top_k=top_k,
        filter_by_book=filter_by_book,
        filter_by_chapter=filter_by_chapter,
        filter_by_author=filter_by_author,
    )

    if not results:
        return (
            f"{NO_RESULTS_MESSAGE}\n"
            "Next step: remove over-specific filters, use exact metadata from the "
            "Knowledge Graph evidence map, or broaden the query within the same "
            "book/chapter."
        )

    return format_document_chunks(results, lookup_mode="ranked_search")


def parse_source_chunk_ids(source_chunk_id: str) -> list[str]:
    """
    Parse one or more source chunk IDs supplied as a comma-separated string.

    Args:
        source_chunk_id: Exact chunk ID or comma-separated chunk IDs.

    Returns:
        Ordered unique chunk IDs.
    """
    chunk_ids: list[str] = []
    seen: set[str] = set()
    for raw_chunk_id in source_chunk_id.split(","):
        chunk_id = raw_chunk_id.strip()
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        chunk_ids.append(chunk_id)
    return chunk_ids


def expand_document_query(query: str) -> str:
    """
    Add compact English corpus terms for common Vietnamese marketing queries.

    Args:
        query: User or agent-generated document-search query.

    Returns:
        Query enriched with source-language terms when a known concept appears.
    """
    folded_query = query.casefold()
    expansions: list[str] = []
    for trigger, expansion in QUERY_EXPANSION_ALIASES.items():
        if trigger in folded_query and expansion.casefold() not in folded_query:
            expansions.append(expansion)
    if not expansions:
        return query
    return f"{query} {' '.join(expansions)}"


def format_document_chunks(
    results: list[DocumentChunkResult],
    *,
    lookup_mode: str,
) -> str:
    """
    Format document chunks for agent consumption.

    Args:
        results: Retrieved or directly fetched document chunks.

    Returns:
        Text with source metadata and enough passage context for answer synthesis.
    """
    # Format results for agent consumption
    output = [format_document_lookup_hint(lookup_mode)]
    for i, chunk in enumerate(results, 1):
        if lookup_mode == "ranked_search" and i == DIRECT_EVIDENCE_RESULT_LIMIT + 1:
            output.append(
                "### Lower-ranked neighboring passages\n"
                "Use these only when they directly answer the question. Treat them "
                "as exploratory context, not as permission to add broader claims."
            )
        output.append(f"[{i}] Source: {chunk.source}")
        output.append(f"    Book: {chunk.original_document}")
        output.append(f"    Source chunk ID: {chunk.id}")
        preview_limit = CONTENT_PREVIEW_CHAR_LIMIT
        if lookup_mode == "ranked_search" and i > DIRECT_EVIDENCE_RESULT_LIMIT:
            preview_limit = NEIGHBOR_PREVIEW_CHAR_LIMIT
        if lookup_mode == "ranked_search" and i <= DIRECT_EVIDENCE_RESULT_LIMIT:
            opening_evidence = extract_opening_evidence(chunk.content)
            if opening_evidence:
                output.append(f"    Opening evidence: {opening_evidence}")
        content_preview = chunk.content[:preview_limit]
        if len(chunk.content) > preview_limit:
            content_preview += "..."
        output.append(f"    Content: {content_preview}")
        output.append("")  # Empty line between results

    return "\n".join(output)


def extract_opening_evidence(content: str) -> str:
    """
    Return a compact opening cue from a high-ranked passage.

    Args:
        content: Full document chunk content.

    Returns:
        The opening sentence or a bounded prefix for passages without punctuation.
    """
    stripped = " ".join(content.strip().split())
    if not stripped:
        return ""
    first_sentence_end = stripped.find(". ")
    if 0 <= first_sentence_end < OPENING_EVIDENCE_CHAR_LIMIT:
        return stripped[: first_sentence_end + 1]
    preview = stripped[:OPENING_EVIDENCE_CHAR_LIMIT]
    if len(stripped) > OPENING_EVIDENCE_CHAR_LIMIT:
        preview += "..."
    return preview


def format_document_lookup_hint(lookup_mode: str) -> str:
    """
    Return a compact next-step hint for the current document lookup mode.

    Args:
        lookup_mode: Either exact source lookup or ranked passage search.

    Returns:
        Agent-facing context guidance for using the returned passages.
    """
    if lookup_mode == "source_chunk_id":
        return (
            "Context hint: exact source_chunk_id lookup. Use this passage to "
            "verify the KG fact; if the answer needs neighboring evidence, run "
            "a scoped search with the same book/chapter and no source_chunk_id.\n"
        )
    return (
        "Context hint: ranked document search. Use these passages as surrounding "
        "evidence. Prioritize the highest-ranked passages that directly answer "
        "the question; lower-ranked passages may be neighboring context or noise. "
        "If a KG fact needs exact verification, use its source_chunk_id.\n"
    )
