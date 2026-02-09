"""
Entity Name Normalization Post-Processing Module.

This module provides functionality to detect and normalize PascalCase entity names
in the Knowledge Graph. It scans entities from Vector DB, uses LLM to convert
PascalCase names to natural language format, and updates both Vector DB and
Graph DB with the normalized names.

The normalization process:
1. Scans EntityDescriptions collection for PascalCase patterns
2. Batches entities for LLM processing (Gemini 3 Flash)
3. Updates both Milvus (Vector DB) and FalkorDB (Graph DB) atomically

Example:
    >>> result = await normalize_entity_names(
    ...     vector_db=milvus_client,
    ...     graph_db=falkordb_client,
    ...     embedder=gemini_embedder,
    ...     dry_run=True,
    ... )
    >>> print(f"Would normalize {result.normalized_count} entities")
"""

import json
import re
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from prompts.knowledge_graph.name_normalization_instruction import (
    NAME_NORMALIZATION_INSTRUCTION,
)
from prompts.knowledge_graph.name_normalization_task_prompt import (
    NAME_NORMALIZATION_TASK_PROMPT,
)
from shared.database_clients.graph_database.base_graph_database import (
    BaseGraphDatabase,
)
from shared.database_clients.vector_database.base_vector_database import (
    BaseVectorDatabase,
)
from shared.model_clients.embedder.base_embedder import BaseEmbedder
from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig

# =============================================================================
# CONSTANTS
# =============================================================================

# Pattern to detect PascalCase names without spaces
# Matches: BrandEquity, ConsumerBehavior, StrategicBrandManagement
# Does NOT match: Brand, Google, iPhone, AI (single words or special cases)
PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][a-z]+([A-Z][a-z]+)+$")


# =============================================================================
# DATA MODELS
# =============================================================================


class EntityToNormalize(BaseModel):
    """
    Represents an entity that needs name normalization.

    This model captures the essential information needed to identify
    and update an entity across both Vector DB and Graph DB.

    Attributes:
        entity_id: Unique identifier of the entity (UUID)
        entity_type: Type label used in Graph DB (e.g., "MarketingConcept")
        current_name: The current PascalCase name to be normalized
        description: Entity description for context in LLM normalization
    """

    entity_id: str = Field(..., description="UUID of the entity")
    entity_type: str = Field(..., description="Entity type (Graph DB label)")
    current_name: str = Field(..., description="Current PascalCase name")
    description: Optional[str] = Field(None, description="Entity description")


class NormalizationResult(BaseModel):
    """
    Encapsulates the result of entity name normalization operation.

    Tracks the mapping from old names to new names, along with
    statistics about the normalization process.

    Attributes:
        normalized_count: Number of entities successfully normalized
        skipped_count: Number of entities skipped (LLM decided to keep as-is)
        failed_count: Number of entities that failed to normalize
        name_mapping: Dict mapping old_name -> new_name for updated entities
        skipped_names: List of names that were kept as-is
        errors: List of error messages for failed normalizations
    """

    normalized_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    name_mapping: Dict[str, str] = Field(default_factory=dict)
    skipped_names: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


# =============================================================================
# LLM RESPONSE SCHEMAS
# =============================================================================


class NormalizedName(BaseModel):
    """Schema for a single normalized name result from LLM."""

    original: str = Field(..., description="Original PascalCase name")
    normalized: str = Field(..., description="Normalized name with spaces")
    keep_original: bool = Field(
        default=False, description="True if name should stay as-is"
    )


class NormalizationResponse(BaseModel):
    """Schema for LLM response containing batch of normalized names."""

    names: List[NormalizedName] = Field(default_factory=list)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def detect_pascal_case_entities(
    vector_db: BaseVectorDatabase,
    collection_name: str = "EntityDescriptions",
) -> List[EntityToNormalize]:
    """
    Scan EntityDescriptions collection and detect entities with PascalCase names.

    Fetches all entities from the Vector DB, then filters using regex pattern
    to identify names that are PascalCase without spaces.

    Args:
        vector_db (BaseVectorDatabase): Vector database client
        collection_name (str): Name of entity collection

    Returns:
        List[EntityToNormalize]: Entities needing normalization
    """
    logger.info(f"Scanning collection '{collection_name}' for PascalCase entities...")

    # Fetch all entities from Vector DB using iterator pattern for large datasets
    all_entities = vector_db.get_all_items(
        collection_name=collection_name,
        output_fields=["id", "name", "type", "description"],
    )

    logger.info(f"Found {len(all_entities)} total entities")

    # Filter entities with PascalCase names using regex pattern
    pascal_case_entities: List[EntityToNormalize] = []
    for entity in all_entities:
        name = entity.get("name", "")
        if PASCAL_CASE_PATTERN.match(name):
            pascal_case_entities.append(
                EntityToNormalize(
                    entity_id=entity["id"],
                    entity_type=entity.get("type", "Entity"),
                    current_name=name,
                    description=entity.get("description"),
                )
            )

    logger.info(f"Detected {len(pascal_case_entities)} entities with PascalCase names")
    return pascal_case_entities


async def batch_normalize_names(
    entities: List[EntityToNormalize],
    batch_size: int = 50,
    max_concurrent: int = 10,
) -> Dict[str, str]:
    """
    Send batches of entity names to LLM for normalization in parallel.

    Uses LLM with structured output for consistent results.
    Processes entities in parallel batches with semaphore to respect API limits.

    Args:
        entities (List[EntityToNormalize]): Entities with PascalCase names
        batch_size (int): Number of entities per batch (default: 50)
        max_concurrent (int): Max concurrent LLM requests (default: 10)

    Returns:
        Dict[str, str]: Mapping original_name -> normalized_name
    """
    import asyncio

    # Initialize LLM with low thinking level for simple task
    llm_config = GoogleAIClientLLMConfig(
        model="gemini-3-flash-preview",
        thinking_level="low",
    )
    llm = GoogleAIClientLLM(config=llm_config)

    # Semaphore to limit concurrent API requests (respect rate limits)
    semaphore = asyncio.Semaphore(max_concurrent)

    # Split entities into batches
    batches: List[List[EntityToNormalize]] = []
    for i in range(0, len(entities), batch_size):
        batches.append(entities[i : i + batch_size])

    total_batches = len(batches)
    logger.info(
        f"Processing {total_batches} batches with max {max_concurrent} concurrent"
    )

    async def process_single_batch(
        batch: List[EntityToNormalize], batch_num: int
    ) -> Dict[str, str]:
        """Process a single batch with semaphore control."""
        async with semaphore:
            batch_names = [e.current_name for e in batch]
            batch_mapping: Dict[str, str] = {}

            logger.info(
                f"Normalizing batch {batch_num}/{total_batches}: {len(batch)} names"
            )

            task_prompt = NAME_NORMALIZATION_TASK_PROMPT.replace(
                "{{NAMES_JSON}}", json.dumps(batch_names, indent=2)
            )

            try:
                response = await llm.acomplete(
                    prompt=task_prompt,
                    system_instruction=NAME_NORMALIZATION_INSTRUCTION,
                    response_schema=NormalizationResponse,
                )

                # Parse response and build mapping for changed names
                result = NormalizationResponse.model_validate_json(response.text)
                for item in result.names:
                    if not item.keep_original and item.original != item.normalized:
                        batch_mapping[item.original] = item.normalized
                        logger.debug(f"  {item.original} -> {item.normalized}")

            except Exception as e:
                logger.error(f"Failed to normalize batch {batch_num}: {e}")

            return batch_mapping

    # Run all batches in parallel with semaphore limiting concurrency
    tasks = [process_single_batch(batch, idx + 1) for idx, batch in enumerate(batches)]
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all batch results into single mapping
    name_mapping: Dict[str, str] = {}
    for result in batch_results:
        if isinstance(result, dict):
            name_mapping.update(result)
        elif isinstance(result, Exception):
            logger.error(f"Batch failed with exception: {result}")

    logger.info(f"Normalized {len(name_mapping)} entity names")
    return name_mapping


async def update_entity_names(
    entities: List[EntityToNormalize],
    name_mapping: Dict[str, str],
    vector_db: BaseVectorDatabase,
    graph_db: BaseGraphDatabase,
    embedder: BaseEmbedder,
    collection_name: str = "EntityDescriptions",
    dry_run: bool = False,
) -> NormalizationResult:
    """
    Update entity names in both Vector DB and Graph DB.

    For each entity in name_mapping:
    1. Re-embed the new name using embedder
    2. Update Vector DB using async_upsert_vectors with partial_update
    3. Update Graph DB using async_update_node

    Args:
        entities (List[EntityToNormalize]): Original entities with metadata
        name_mapping (Dict[str, str]): old_name -> new_name mappings
        vector_db (BaseVectorDatabase): Vector database client
        graph_db (BaseGraphDatabase): Graph database client
        embedder (BaseEmbedder): Embedder for re-embedding new names
        collection_name (str): Vector DB collection name
        dry_run (bool): If True, only log without updating

    Returns:
        NormalizationResult: Statistics about the normalization operation
    """
    result = NormalizationResult(name_mapping=name_mapping)

    # Build lookup from current name to entity for quick access
    entity_lookup = {e.current_name: e for e in entities}

    for old_name, new_name in name_mapping.items():
        entity = entity_lookup.get(old_name)
        if not entity:
            result.errors.append(f"Entity not found for name: {old_name}")
            result.failed_count += 1
            continue

        if dry_run:
            logger.info(f"[DRY RUN] Would update: {old_name} -> {new_name}")
            result.normalized_count += 1
            continue

        try:
            # Step 1: Re-embed the new name
            name_embedding = await embedder.aget_text_embedding(new_name)

            # Step 2: Update Vector DB (partial update - only name and embedding)
            vector_data = {
                "id": entity.entity_id,
                "name": new_name,
                "name_embedding": name_embedding,
            }
            await vector_db.async_upsert_vectors(
                data=[vector_data],
                collection_name=collection_name,
                partial_update=True,
            )

            # Step 3: Update Graph DB node
            await graph_db.async_update_node(
                label=entity.entity_type,
                match_properties={"id": entity.entity_id},
                update_properties={"name": new_name},
            )

            logger.info(f"Updated: {old_name} -> {new_name}")
            result.normalized_count += 1

        except Exception as e:
            logger.error(f"Failed to update {old_name}: {e}")
            result.errors.append(f"{old_name}: {str(e)}")
            result.failed_count += 1

    # Track skipped entities (those not in name_mapping)
    for entity in entities:
        if entity.current_name not in name_mapping:
            result.skipped_names.append(entity.current_name)
            result.skipped_count += 1

    return result


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


async def normalize_entity_names(
    vector_db: BaseVectorDatabase,
    graph_db: BaseGraphDatabase,
    embedder: BaseEmbedder,
    collection_name: str = "EntityDescriptions",
    batch_size: int = 50,
    dry_run: bool = False,
) -> NormalizationResult:
    """
    Main entry point for entity name normalization post-processing.

    Orchestrates the full pipeline:
    1. Scan Vector DB for entities with PascalCase names
    2. Batch send to LLM for normalization
    3. Update both Vector DB and Graph DB

    This function is designed to be called from the KG build pipeline
    or directly from CLI for one-time cleanup operations.

    Args:
        vector_db (BaseVectorDatabase): Vector database client
        graph_db (BaseGraphDatabase): Graph database client
        embedder (BaseEmbedder): Embedder for re-embedding normalized names
        collection_name (str): Entity collection name
        batch_size (int): LLM batch size (default: 50)
        dry_run (bool): If True, only detect and log without updating

    Returns:
        NormalizationResult: Full statistics about the operation

    Example:
        >>> result = await normalize_entity_names(
        ...     vector_db=milvus_client,
        ...     graph_db=falkordb_client,
        ...     embedder=gemini_embedder,
        ...     dry_run=True,
        ... )
        >>> print(f"Would normalize {result.normalized_count} entities")
    """
    logger.info("=" * 60)
    logger.info("Starting Entity Name Normalization Post-Processing")
    logger.info("=" * 60)

    # Step 1: Detect PascalCase entities from Vector DB
    entities = detect_pascal_case_entities(vector_db, collection_name)

    if not entities:
        logger.info("No PascalCase entities found. Nothing to normalize.")
        return NormalizationResult()

    # Step 2: Batch normalize names via LLM
    name_mapping = await batch_normalize_names(entities, batch_size)

    if not name_mapping:
        logger.info("LLM decided all names should remain as-is.")
        return NormalizationResult(
            skipped_count=len(entities),
            skipped_names=[e.current_name for e in entities],
        )

    # Step 3: Update both databases with normalized names
    result = await update_entity_names(
        entities=entities,
        name_mapping=name_mapping,
        vector_db=vector_db,
        graph_db=graph_db,
        embedder=embedder,
        collection_name=collection_name,
        dry_run=dry_run,
    )

    # Log final summary
    logger.info("=" * 60)
    logger.info("Normalization Complete!")
    logger.info(f"  Normalized: {result.normalized_count}")
    logger.info(f"  Skipped: {result.skipped_count}")
    logger.info(f"  Failed: {result.failed_count}")
    logger.info("=" * 60)

    return result
