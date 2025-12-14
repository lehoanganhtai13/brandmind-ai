"""
Retrieval module for document and knowledge graph search.

This module provides search tools for the agent to query:
- Document Library (raw text passages from books)
- Knowledge Graph (semantic entities and relationships)
"""

from core.retrieval.document_retriever import DocumentRetriever
from core.retrieval.models import DocumentChunkResult

__all__ = ["DocumentChunkResult", "DocumentRetriever"]
