"""ValidateTriples tool for Knowledge Miner agent.

This tool provides LLM-based validation of extracted knowledge graph triples,
checking for accuracy, significance, and completeness against the source text.
"""

import json
import time

from loguru import logger

from config.system_config import SETTINGS
from core.knowledge_graph.models.triple import ValidationResult
from prompts.knowledge_graph.miner_system_prompt import SPECIALIZED_DOMAIN
from prompts.knowledge_graph.miner_validation_prompt import VALIDATION_PROMPT_TEMPLATE
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)


def validate_triples(
    extracted_graph_json: str,
    chunk_content: str,
    section_summary: str,
) -> str:
    """Validate extracted knowledge graph triples for accuracy and completeness.

    This tool uses an LLM to check the extracted triples against the source text,
    identifying hallucinations, missing concepts, and weak descriptions. The
    validation provides structured feedback that the agent can use to refine
    its extraction.

    Args:
        extracted_graph_json: JSON string of extracted entities and relationships
        chunk_content: Original chunk text (ground truth)
        section_summary: Section context summary for disambiguation

    Returns:
        Formatted validation result with status and required actions as a
        human-readable string for the agent to interpret
    """
    try:
        logger.debug("Validating triples...")

        # Initialize LLM client with thinking budget for validation
        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-3-flash-preview",
                api_key=SETTINGS.GEMINI_API_KEY,
                thinking_level="low",  # Validation is simple task, use low
                max_tokens=30000,
                response_mime_type="application/json",
                response_schema=ValidationResult,
            )
        )

        # Generate validation prompt
        prompt = (
            VALIDATION_PROMPT_TEMPLATE.replace("{{domain}}", SPECIALIZED_DOMAIN)
            .replace("{{section_summary}}", section_summary)
            .replace("{{chunk_content}}", chunk_content)
            .replace("{{input_graph_json}}", extracted_graph_json)
        )

        # Call LLM for validation with retry logic
        validation_result = None
        last_error = None

        MAX_ATTEMPTS = 3
        for attempt in range(MAX_ATTEMPTS):
            try:
                result = llm.complete(prompt, temperature=1.0).text  # Gemini 3 default

                # Parse JSON response (handle markdown code blocks)
                if result.startswith("```json"):
                    result = result.replace("```json", "").replace("```", "").strip()

                validation_data = json.loads(result)
                validation_result = ValidationResult(**validation_data)
                break  # Success - exit retry loop

            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                if attempt < (MAX_ATTEMPTS - 1):  # Not last attempt
                    logger.warning(
                        f"Validation attempt {attempt + 1} failed: {e}, "
                        f"retrying in 1 second..."
                    )
                    time.sleep(1)
                else:  # Last attempt - will raise to outer try-except
                    logger.error(f"Validation failed after {attempt + 1} attempts: {e}")
                    raise

        if validation_result is None:
            raise last_error or Exception("Validation failed with unknown error")

        # Format result for agent consumption
        if validation_result.status == "VALID":
            return f"✅ VALIDATION PASSED\n\n{validation_result.critique}"

        elif validation_result.status == "MINOR_ISSUES":
            actions_str = "\n".join(
                [
                    f"  - {action.type}: {action.target_name or 'N/A'}\n"
                    f"    Reason: {action.reason}\n"
                    f"    Suggestion: {action.suggestion}"
                    for action in validation_result.required_actions
                ]
            )
            return (
                f"⚠️ VALIDATION: MINOR ISSUES\n\n"
                f"Critique: {validation_result.critique}\n\n"
                f"Suggested improvements:\n{actions_str}\n\n"
                f"You may proceed, but consider refining based on feedback."
            )

        else:  # MAJOR_ISSUES
            actions_str = "\n".join(
                [
                    f"  - {action.type}: {action.target_name or 'N/A'}\n"
                    f"    Reason: {action.reason}\n"
                    f"    Suggestion: {action.suggestion}"
                    for action in validation_result.required_actions
                ]
            )
            return (
                f"❌ VALIDATION FAILED: MAJOR ISSUES\n\n"
                f"Critique: {validation_result.critique}\n\n"
                f"Required actions:\n{actions_str}\n\n"
                f"Please refine your extraction and validate again."
            )

    except Exception as e:
        logger.error(f"Validation tool error: {e}")
        return (
            f"⚠️ VALIDATION ERROR\n\n"
            f"An error occurred during validation: {str(e)}\n\n"
            f"You may proceed, but manual review is recommended."
        )
