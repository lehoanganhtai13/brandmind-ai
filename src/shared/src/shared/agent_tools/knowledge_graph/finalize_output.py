"""FinalizeOutput tool for Knowledge Miner agent.

This tool validates JSON structure before the agent returns its final output,
catching truncation and syntax errors early to prevent chunk loss.
"""

import json
from typing import Any

from loguru import logger


def finalize_output(output_json: str) -> str:
    """Validate JSON structure before returning final extraction result.

    This tool performs lightweight validation (no LLM cost) to catch:
    - Truncated JSON (from hitting max_output_tokens limit)
    - Syntax errors (missing brackets, trailing commas, unquoted strings)
    - Missing required keys (entities, relationships)

    The agent MUST call this tool before returning its final JSON output.
    If validation fails, the agent should reduce output size or fix syntax.

    Args:
        output_json: The JSON string to validate

    Returns:
        Validation result as a human-readable string:
        - "[VALID] ..." if valid
        - "[ERROR] ..." with specific issues if invalid
    """
    try:
        logger.debug("Validating final output JSON...")

        # Step 1: Check JSON syntax
        try:
            data = json.loads(output_json)
        except json.JSONDecodeError as e:
            error_context = _get_error_context(output_json, e.pos)
            return (
                f"[ERROR] JSON SYNTAX ERROR at position {e.pos}\n\n"
                f"Error: {e.msg}\n"
                f"Context: ...{error_context}...\n\n"
                f"Common fixes:\n"
                f"- Check for unclosed brackets {{ }} or [ ]\n"
                f"- Check for trailing commas before }} or ]\n"
                f"- Check for missing quotes around strings\n"
                f"- If output is too long, reduce number of entities/relationships"
            )

        # Step 2: Check required structure
        errors = []

        if not isinstance(data, dict):
            errors.append("Output must be a JSON object (dict), not " + type(data).__name__)
        else:
            if "entities" not in data:
                errors.append("Missing required key: 'entities'")
            elif not isinstance(data["entities"], list):
                errors.append("'entities' must be a list")

            if "relationships" not in data:
                errors.append("Missing required key: 'relationships'")
            elif not isinstance(data["relationships"], list):
                errors.append("'relationships' must be a list")

        if errors:
            return (
                f"[ERROR] STRUCTURE ERROR\n\n"
                f"Issues found:\n"
                + "\n".join(f"- {e}" for e in errors)
                + "\n\nPlease fix and call finalize_output again."
            )

        # Step 3: Check entity structure
        entity_errors = []
        for i, entity in enumerate(data.get("entities", [])):
            if not isinstance(entity, dict):
                entity_errors.append(f"Entity {i}: must be an object")
                continue
            if "name" not in entity:
                entity_errors.append(f"Entity {i}: missing 'name'")
            if "type" not in entity:
                entity_errors.append(f"Entity {i}: missing 'type'")
            if "description" not in entity:
                entity_errors.append(f"Entity {i}: missing 'description'")

        if entity_errors:
            return (
                f"[ERROR] ENTITY STRUCTURE ERROR\n\n"
                f"Issues found:\n"
                + "\n".join(f"- {e}" for e in entity_errors[:5])  # Limit to 5
                + ("\n- ... and more" if len(entity_errors) > 5 else "")
                + "\n\nPlease fix and call finalize_output again."
            )

        # Step 4: Check relationship structure
        rel_errors = []
        for i, rel in enumerate(data.get("relationships", [])):
            if not isinstance(rel, dict):
                rel_errors.append(f"Relationship {i}: must be an object")
                continue
            if "source" not in rel:
                rel_errors.append(f"Relationship {i}: missing 'source'")
            if "target" not in rel:
                rel_errors.append(f"Relationship {i}: missing 'target'")
            if "relation_type" not in rel:
                rel_errors.append(f"Relationship {i}: missing 'relation_type'")

        if rel_errors:
            return (
                f"[ERROR] RELATIONSHIP STRUCTURE ERROR\n\n"
                f"Issues found:\n"
                + "\n".join(f"- {e}" for e in rel_errors[:5])
                + ("\n- ... and more" if len(rel_errors) > 5 else "")
                + "\n\nPlease fix and call finalize_output again."
            )

        # All checks passed
        entity_count = len(data.get("entities", []))
        rel_count = len(data.get("relationships", []))
        logger.debug(f"Output valid: {entity_count} entities, {rel_count} relationships")

        return (
            f"[VALID] OUTPUT VERIFIED\n\n"
            f"Structure verified: {entity_count} entities, {rel_count} relationships.\n"
            f"You may now return this JSON as your final answer."
        )

    except Exception as e:
        logger.error(f"Finalize output error: {e}")
        return (
            f"[WARNING] VALIDATION ERROR\n\n"
            f"An unexpected error occurred: {str(e)}\n"
            f"Please check your JSON format and try again."
        )


def _get_error_context(json_str: str, pos: int, context_size: int = 30) -> str:
    """Extract context around JSON error position."""
    start = max(0, pos - context_size)
    end = min(len(json_str), pos + context_size)
    context = json_str[start:end]
    # Mark error position
    marker_pos = min(pos - start, len(context))
    return context[:marker_pos] + "<<<HERE>>>" + context[marker_pos:]
