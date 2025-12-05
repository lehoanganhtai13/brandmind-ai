"""Pydantic models for knowledge graph triples.

This module defines the data structures for representing extracted knowledge
from document chunks, including entities, relationships, validation results,
and complete extraction outputs.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """Represents a knowledge graph entity.

    An entity is a core concept, tool, person, or organization extracted from
    the text. Entities use PascalCase type naming convention for consistency.

    Attributes:
        name: Exact term from the source text
        type: Entity type in PascalCase (e.g., MarketingStrategy, SoftwareTool)
        description: Comprehensive definition of the entity's role and meaning
            within the domain context
    """

    name: str = Field(description="Exact term from text")
    type: str = Field(
        description="Entity type in PascalCase (e.g., MarketingStrategy, SoftwareTool)"
    )
    description: str = Field(
        description="Comprehensive definition of entity's role/meaning in domain"
    )


class Relation(BaseModel):
    """Represents a relationship between two entities.

    Relations describe how entities interact or relate to each other, using
    active verbs in lowerCamelCase for consistency.

    Attributes:
        source: Source entity name (must exist in entities list)
        target: Target entity name (must exist in entities list)
        relation_type: Relation type in lowerCamelCase active verb
            (e.g., improvesEfficiency, requiresSkill)
        description: Contextual explanation of the mechanic or logic connecting
            source and target entities
    """

    source: str = Field(description="Source entity name (must exist in entities list)")
    target: str = Field(description="Target entity name (must exist in entities list)")
    relation_type: str = Field(
        description=(
            "Relation type in lowerCamelCase active verb (e.g., improvesEfficiency)"
        )
    )
    description: str = Field(
        description=(
            "Contextual explanation of the mechanic/logic connecting source and target"
        )
    )


class ExtractionResult(BaseModel):
    """Result of knowledge extraction from a single chunk.

    Contains the normalized graph structure with entities defined once and
    referenced by name in relationships.

    Attributes:
        entities: List of extracted entities with unique names
        relationships: List of relationships referencing entity names
    """

    entities: List[Entity] = Field(description="List of extracted entities")
    relationships: List[Relation] = Field(description="List of extracted relationships")


class ValidationAction(BaseModel):
    """Represents a required action from validation.

    Validation actions provide specific feedback on how to improve the
    extracted knowledge graph.

    Attributes:
        type: Type of action required (REMOVE_ENTITY, ADD_ENTITY, etc.)
        target_name: Name of entity/relation to modify (if applicable)
        reason: Explanation for why this action is needed
        suggestion: Suggested fix or addition
    """

    type: Literal[
        "REMOVE_ENTITY", "ADD_ENTITY", "REWRITE_DESCRIPTION", "MODIFY_RELATION"
    ] = Field(description="Type of action required")
    target_name: str = Field(
        default="", description="Name of entity/relation to modify"
    )
    reason: str = Field(default="", description="Reason for this action")
    suggestion: str = Field(default="", description="Suggested fix or addition")


class ValidationResult(BaseModel):
    """Result of triple validation.

    Provides quality assessment of extracted triples, checking for accuracy,
    significance, and completeness.

    Attributes:
        status: Overall validation status (VALID, MINOR_ISSUES, MAJOR_ISSUES)
        critique: Brief overall assessment of extraction quality
        required_actions: List of required corrections or improvements
    """

    status: Literal["VALID", "MINOR_ISSUES", "MAJOR_ISSUES"] = Field(
        description="Overall validation status"
    )
    critique: str = Field(description="Brief overall assessment")
    required_actions: List[ValidationAction] = Field(
        default=[], description="List of required corrections"
    )


class ChunkExtractionResult(BaseModel):
    """Complete extraction result for a chunk including metadata.

    This is the final output structure that combines extraction results,
    validation feedback, and source metadata for traceability.

    Attributes:
        chunk_id: UUID of the source chunk
        source_hierarchy: Full hierarchy path (e.g., "Part 1 > Chapter 2")
        extraction: Extracted entities and relations
        validation: Validation result with feedback
        metadata: Additional metadata (pages, word_count, etc.)
    """

    chunk_id: str = Field(description="UUID of the chunk")
    source_hierarchy: str = Field(
        description="Full hierarchy path (e.g., 'Part 1 > Chapter 2')"
    )
    extraction: ExtractionResult = Field(description="Extracted entities and relations")
    validation: ValidationResult = Field(description="Validation result")
    metadata: dict = Field(
        default={}, description="Additional metadata (pages, word_count, etc.)"
    )
