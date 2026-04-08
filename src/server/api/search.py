"""Stateless search endpoints — no session required."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(tags=["search"])


@router.get("/search/kg")
async def search_knowledge_graph(
    q: str = Query(..., description="Conceptual query"),
    max_results: int = Query(10, ge=1, le=50, description="Max results"),
) -> dict[str, str]:
    """Search the Knowledge Graph for marketing concepts.

    Stateless — no session needed. Calls the KG search tool directly.
    """
    from shared.agent_tools.retrieval import (
        search_knowledge_graph as kg_search,
    )

    result = await kg_search(query=q, max_results=max_results)
    return {"result": result}


@router.get("/search/docs")
async def search_document_library(
    q: str = Query(..., description="Text to search for"),
    book: str | None = Query(None, description="Filter by book"),
    chapter: str | None = Query(None, description="Filter by chapter"),
    author: str | None = Query(None, description="Filter by author"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
) -> dict[str, str]:
    """Search the Document Library with optional filters.

    Stateless — no session needed. Calls the doc search tool directly.
    """
    from shared.agent_tools.retrieval import (
        search_document_library as doc_search,
    )

    result = await doc_search(
        query=q,
        filter_by_book=book,
        filter_by_chapter=chapter,
        filter_by_author=author,
        top_k=top_k,
    )
    return {"result": result}
