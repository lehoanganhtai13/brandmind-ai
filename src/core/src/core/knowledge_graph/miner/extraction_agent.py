"""Deep Agent-based extraction agent for knowledge graph triple extraction.

This module provides the ExtractionAgent class which wraps a Deep Agent
for extracting knowledge triples from document chunks with validation.
"""

from langchain_core.messages import HumanMessage
from loguru import logger

from core.knowledge_graph.miner.agent_config import create_miner_agent
from core.knowledge_graph.models.chunk import Chunk
from core.knowledge_graph.models.triple import (
    ChunkExtractionResult,
    ExtractionResult,
    ValidationResult,
)
from prompts.knowledge_graph.miner_system_prompt import SPECIALIZED_DOMAIN
from prompts.knowledge_graph.miner_task_prompt import MINER_TASK_PROMPT_TEMPLATE


class ExtractionAgent:
    """Agent for extracting knowledge triples from chunks using Deep Agent.

    This class manages the interaction with the Deep Agent, formatting
    task prompts and parsing agent responses into structured extraction results.

    The agent has access to:
    - write_todos: Optional planning tool for complex extractions
    - validate_triples: Mandatory validation tool for quality assurance

    Attributes:
        agent: Configured Deep Agent instance
        model: LLM model instance
    """

    def __init__(self):
        """Initialize extraction agent with Deep Agent configuration.

        Creates a new Deep Agent instance with TodoWrite middleware
        and ValidateTriples tool configured for knowledge extraction.
        """
        self.agent, self.model = create_miner_agent()
        logger.debug("ExtractionAgent initialized with Deep Agent")

    async def extract_knowledge(self, chunk: Chunk) -> ChunkExtractionResult:
        """Extract knowledge triples from a chunk using Deep Agent.

        The agent follows a three-phase workflow:
        1. Conceptual Distillation: Extract entities with PascalCase types
        2. Mechanics Mapping: Extract relationships with lowerCamelCase verbs
        3. Validation: Validate extraction using validate_triples tool
        4. Refinement: Refine if validation fails (agent decides)

        The agent receives:
        - Domain context (marketing) via system prompt
        - Section summary for disambiguation via task prompt
        - Chunk content as the source text via task prompt

        Args:
            chunk: Chunk to extract knowledge from, containing content and metadata

        Returns:
            ChunkExtractionResult with entities, relations, validation feedback,
            and source metadata for traceability

        Raises:
            Exception: If agent invocation fails or response cannot be parsed
        """
        try:
            # Prepare task prompt with section summary and chunk content
            task_prompt = (
                MINER_TASK_PROMPT_TEMPLATE.replace("{{domain}}", SPECIALIZED_DOMAIN)
                .replace("{{section_summary}}", chunk.metadata.section_summary)
                .replace("{{chunk_content}}", chunk.content)
            )

            # Invoke agent with task prompt (async)
            logger.debug(f"Invoking agent for chunk {chunk.chunk_id[:8]}...")
            result = await self.agent.ainvoke(  # type: ignore[attr-defined]
                {"messages": [HumanMessage(content=task_prompt)]},
                {"recursion_limit": 100},  # Lower limit for extraction task
            )

            logger.debug(
                f"Agent completed extraction for chunk {chunk.chunk_id[:8]}..."
            )

            # Parse agent output - extract JSON from final message
            # Cannot use response_format due to tool calling conflicts
            messages = result.get("messages", [])
            if not messages:
                raise ValueError("Agent returned no messages")

            # Get last AI message
            final_message = messages[-1]

            # Handle content - can be string or list
            if hasattr(final_message, "text"):
                content = final_message.text
            else:
                content = str(final_message)

            # Extract JSON from content (may be wrapped in ```json blocks)
            import json
            import re

            # Try to find JSON block in markdown
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError(
                        f"No JSON found in agent response: {content[:200]}"
                    )

            # Parse JSON into ExtractionResult
            extraction_data = json.loads(json_str)
            extraction = ExtractionResult(**extraction_data)

            # Create result with validation
            result_obj = ChunkExtractionResult(
                chunk_id=chunk.chunk_id,
                source_hierarchy=chunk.metadata.source,
                extraction=extraction,
                validation=ValidationResult(
                    status="VALID",
                    critique="Extraction completed and validated by agent",
                    required_actions=[],
                ),
                metadata={
                    "pages": chunk.metadata.pages,
                    "word_count": chunk.metadata.word_count,
                },
            )

            logger.info(
                f"✅ Extracted {len(extraction.entities)} entities, "
                f"{len(extraction.relationships)} relations from chunk "
                f"{chunk.chunk_id[:8]}"
            )

            return result_obj

        except Exception as e:
            logger.error(f"Extraction failed for chunk {chunk.chunk_id}: {e}")
            raise
