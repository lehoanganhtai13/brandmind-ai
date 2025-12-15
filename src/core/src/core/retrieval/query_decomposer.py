"""
LLM-based query decomposition for dual-level knowledge graph search.

This module provides the decompose_query function which uses Gemini LLM
to analyze a user query and split it into:
- Global queries: For searching relation descriptions (concepts, themes)
- Local queries: For entity linking and graph traversal
"""

import json
from typing import List

from loguru import logger
from pydantic import BaseModel, Field

from config.system_config import SETTINGS
from prompts.knowledge_graph.query_decompose_instruction import (
    QUERY_DECOMPOSE_INSTRUCTION,
)
from prompts.knowledge_graph.query_decompose_task_prompt import (
    QUERY_DECOMPOSE_TASK_PROMPT,
)
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)


class DecomposedQuery(BaseModel):
    """
    Structured response for query decomposition.

    Splits a user query into global (conceptual) and local (entity-specific)
    sub-queries for dual-level knowledge graph search.
    """

    global_queries: List[str] = Field(..., description="Broad thematic questions")
    local_queries: List[str] = Field(..., description="Specific entity questions")


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
