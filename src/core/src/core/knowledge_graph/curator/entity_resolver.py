"""
Entity resolution logic for Knowledge Graph curation.

This module provides hybrid search-based entity matching and LLM-powered merge
decisions for duplicate entity detection and resolution.
"""

import json
import traceback
from typing import Dict, List, Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field

from prompts.knowledge_graph.description_synthesis_instruction import (
    DESCRIPTION_SYNTHESIS_INSTRUCTION,
)
from prompts.knowledge_graph.description_synthesis_task_prompt import (
    DESCRIPTION_SYNTHESIS_TASK_PROMPT,
)
from prompts.knowledge_graph.entity_merge_decision_instruction import (
    ENTITY_MERGE_DECISION_INSTRUCTION,
)
from prompts.knowledge_graph.entity_merge_task_prompt import ENTITY_MERGE_TASK_PROMPT
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
from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig

# Constants
SIMILARITY_THRESHOLD = 0.85
MAX_DESCRIPTION_LENGTH = 1000  # Characters
CONDENSE_TARGET = 667  # ~2/3 of max (TARGET_LENGTH placeholder)


class EntityMergeDecision(BaseModel):
    """Structured response for entity merge decision."""

    decision: str = Field(..., description="Either 'MERGE' or 'NEW'")
    canonical_name: str = Field(
        ..., description="Selected canonical name for the entity"
    )
    reasoning: str = Field(..., description="Brief explanation of the decision")


class DescriptionSynthesisResponse(BaseModel):
    """Structured response for description synthesis."""

    synthesized_description: str = Field(..., description="The final merged text")


def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors using numpy."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    a = np.array(v1)
    b = np.array(v2)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


async def find_similar_entity(
    entity_name: str,
    entity_type: str,
    name_embedding: List[float],  # Pre-computed from batch
    vector_db: BaseVectorDatabase,
    collection_name: str = "EntityDescriptions",
) -> Optional[Dict]:
    """
    Find most similar existing entity using hybrid search.

    Uses pre-computed name embedding from batch processing combined with
    BM25 sparse search to find potential duplicate entities. Only returns
    candidates above similarity threshold to avoid false matches.

    Note: This function is called PER ENTITY during resolution, but uses
    pre-computed embeddings from batch processing to optimize costs.

    Args:
        entity_name: Name of entity to find matches for
        entity_type: Type of entity for filtering (e.g., "MarketingConcept")
        name_embedding: Pre-computed dense embedding for entity name
        vector_db: Vector database client for hybrid search
        collection_name: Name of entity descriptions collection

    Returns:
        Top matching entity dict with id, name, description, type if found
    """
    # Prepare hybrid search with pre-computed embedding
    embedding_data = [
        # Dense search on pre-computed name embedding
        EmbeddingData(
            embedding_type=EmbeddingType.DENSE,
            embeddings=name_embedding,
            field_name="name_embedding",
            filtering_expr=f'type == "{entity_type}"',
        ),
        # Sparse BM25 search on name text
        EmbeddingData(
            embedding_type=EmbeddingType.SPARSE,
            query=entity_name,
            field_name="name_sparse",
            filtering_expr=f'type == "{entity_type}"',
        ),
    ]

    results = await vector_db.async_hybrid_search_vectors(
        embedding_data=embedding_data,
        output_fields=[
            "id",
            "graph_id",
            "name",
            "description",
            "type",
            "name_embedding",
        ],
        top_k=1,
        collection_name=collection_name,
        metric_type=MetricType.COSINE,
        index_type=IndexType.HNSW,
    )

    if results:
        candidate = results[0]
        retrieved_embedding = candidate.get("name_embedding")

        if retrieved_embedding:
            similarity = calculate_cosine_similarity(
                name_embedding, retrieved_embedding
            )
            logger.info(
                f"Similarity score for '{entity_name}' vs "
                f"'{candidate.get('name')}': {similarity:.2f}"
            )

            if similarity > SIMILARITY_THRESHOLD:
                # Update score to reflect the true similarity
                candidate["_score"] = similarity
                return candidate

    return None


async def decide_entity_merge(
    existing_entity: Dict,
    new_entity: Dict,
) -> Dict:
    """
    Use LLM to decide whether to merge two entities.

    Creates GoogleAIClientLLM instance with entity merge instruction prompt
    and uses response_schema for structured JSON output. The LLM analyzes
    entity types and descriptions to determine semantic equivalence.

    Args:
        existing_entity: Dict with name, type, description of existing entity
        new_entity: Dict with name, type, description of new entity

    Returns:
        Decision dict with "decision" (MERGE/NEW), "canonical_name", "reasoning"
    """
    try:
        from config.system_config import SETTINGS

        # Create LLM with instruction as system_instruction
        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-3-flash-preview",
                api_key=SETTINGS.GEMINI_API_KEY,
                system_instruction=ENTITY_MERGE_DECISION_INSTRUCTION,
                temperature=1.0,
                thinking_level="low",
                max_tokens=2000,
                response_mime_type="application/json",
                response_schema=EntityMergeDecision,
            )
        )

        # Build task prompt from template (using {{placeholder}} format)
        task_prompt = (
            ENTITY_MERGE_TASK_PROMPT.replace(
                "{{EXISTING_NAME}}", existing_entity["name"]
            )
            .replace("{{EXISTING_TYPE}}", existing_entity.get("type", "Unknown"))
            .replace("{{EXISTING_DESC}}", existing_entity.get("description", ""))
            .replace("{{NEW_NAME}}", new_entity["name"])
            .replace("{{NEW_TYPE}}", new_entity.get("type", "Unknown"))
            .replace("{{NEW_DESC}}", new_entity.get("description", ""))
        )

        # Get structured response
        response = llm.complete(task_prompt).text
        decision = json.loads(response)

        return decision
    except Exception as e:
        logger.error(f"Error merging entities: {e}")
        logger.error(traceback.format_exc())

        # Fallback to NEW decision to be safe
        return {
            "decision": "NEW",
            "canonical_name": new_entity["name"],
            "reasoning": "JSON parse error from LLM",
        }


async def merge_descriptions(
    existing_desc: str,
    new_desc: str,
) -> str:
    """
    Merge two entity descriptions, condensing if needed.

    Combines both descriptions using GoogleAIClientLLM with synthesis instruction.
    Uses response_schema for structured output. Always condenses to target length
    for consistency, preserving most important information.

    Args:
        existing_desc: Current entity description
        new_desc: New description to merge in

    Returns:
        Merged and condensed description
    """
    try:
        from config.system_config import SETTINGS

        # Create LLM with instruction as system_instruction
        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-3-flash-preview",
                api_key=SETTINGS.GEMINI_API_KEY,
                system_instruction=DESCRIPTION_SYNTHESIS_INSTRUCTION,
                temperature=1.0,
                thinking_level="low",
                max_tokens=3000,
                response_mime_type="application/json",
                response_schema=DescriptionSynthesisResponse,
            )
        )

        # Build task prompt from template (using {{placeholder}} format)
        task_prompt = (
            DESCRIPTION_SYNTHESIS_TASK_PROMPT.replace(
                "{{TARGET_LENGTH}}", str(CONDENSE_TARGET)
            )
            .replace("{{EXISTING_DESC}}", existing_desc)
            .replace("{{NEW_DESC}}", new_desc)
        )

        # Get structured response
        response = llm.complete(task_prompt).text
        result = json.loads(response)

        return result["synthesized_description"]
    except Exception as e:
        logger.error(f"Error merging descriptions: {e}")
        logger.error(traceback.format_exc())

        # Fallback to NEW decision to be safe
        return existing_desc
