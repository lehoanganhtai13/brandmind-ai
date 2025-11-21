"""LLM-powered table assembly service for reconstructing fragmented tables."""

import json
import time
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from core.document_processing.models import TableChain, TableMergeDecision
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)


class RepairsPerformed(BaseModel):
    """Details about repairs performed on table fragments."""

    collapsed_columns_fixed: bool = Field(
        ..., description="Whether collapsed column errors were fixed"
    )
    description: str = Field(
        ..., description="Brief description of rowspan cell splitting performed"
    )


class TableAssemblyAnalysis(BaseModel):
    """Analysis metadata from table assembly and repair operation."""

    fragments_received: int = Field(
        ..., description="Number of fragments received for assembly"
    )
    repairs_performed: RepairsPerformed = Field(
        ..., description="Details about structural repairs applied to fragments"
    )
    reasoning: str = Field(
        ..., description="Explanation of why fragments belong together"
    )


class TableAssemblyResponse(BaseModel):
    """Structured response from LLM table assembly and repair."""

    analysis: TableAssemblyAnalysis = Field(
        ..., description="Analysis metadata for repair and merge operations"
    )
    status: str = Field(
        ..., description="SUCCESS if merged, NO_MERGE if fragments are separate"
    )
    final_merged_html: Optional[str] = Field(
        None,
        description=(
            "Complete repaired and merged table HTML (only if status=SUCCESS, "
            "else null)"
        ),
    )


class TableAssembler:
    """
    Expert Table Assembly AI for reconstructing fragmented tables.

    This service analyzes chains of consecutive table fragments using an LLM with
    column fingerprinting logic to determine if they belong to a single logical
    table. The LLM reconstructs the complete table by identifying the master header,
    processing body fragments, and handling ghost headers and formatting issues.
    """

    def __init__(self):
        """Initialize the table assembler with LLM client and task prompt."""
        from config.system_config import SETTINGS
        from prompts.document_processing.assemble_table_fragments import (
            ASSEMBLE_TABLE_FRAGMENTS_PROMPT,
        )

        self.llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-2.5-flash-lite",
                api_key=SETTINGS.GEMINI_API_KEY,
                temperature=0.1,
                thinking_budget=0,
                max_tokens=10000,
                response_mime_type="application/json",
                response_schema=TableAssemblyResponse,
            )
        )
        self.task_prompt = ASSEMBLE_TABLE_FRAGMENTS_PROMPT

    async def analyze_chain(self, chain: TableChain) -> TableMergeDecision:
        """
        Analyze a chain of table fragments and assemble if they belong together.

        This method normalizes all table formats to HTML before sending to the LLM,
        which performs column fingerprinting analysis to determine if fragments
        represent a single table. If yes, returns status=SUCCESS with merged HTML;
        otherwise NO_MERGE.

        Args:
            chain (TableChain): Chain of consecutive table fragments to analyze

        Returns:
            decision (TableMergeDecision): Assembly decision with analysis and result
        """
        start_time = time.time()

        try:
            # Convert all tables to HTML format for LLM processing
            from core.document_processing.markdown_table_converter import (
                MarkdownTableConverter,
            )

            converter = MarkdownTableConverter()
            table_list = []

            for table in chain.tables:
                if table.table_format == "html":
                    table_list.append(table.html_content)
                elif table.table_format == "markdown":
                    # Convert markdown to HTML
                    html_table = converter.convert_to_html(table.html_content)
                    table_list.append(html_table)
                else:
                    logger.warning(
                        f"Unknown table format: {table.table_format}, skipping"
                    )

            # Create the task prompt with input data
            content = (
                f"{self.task_prompt}\n\n"
                f"---\n"
                f"**Input Table List:**\n"
                f"{json.dumps(table_list, ensure_ascii=False)}"
            )

            # Get LLM response
            response = self.llm.complete(content, temperature=0.1).text
            result = json.loads(response)

            processing_time = time.time() - start_time

            # Map LLM response to our model
            decision = TableMergeDecision(
                chain_id=chain.chain_id,
                status=result["status"],
                analysis=result["analysis"],
                final_merged_html=result.get("final_merged_html"),
                processing_time=processing_time,
            )

            logger.debug(
                f"Chain {chain.chain_id}: Assembly status = {decision.status} "
                f"({result['analysis']['fragments_received']} fragments, "
                f"repairs: {result['analysis']['repairs_performed']['collapsed_columns_fixed']}) "
                f"in {processing_time:.2f}s"
            )

            return decision

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM response for chain {chain.chain_id}: {e}"
            )
            # Fallback: return NO_MERGE on parsing errors
            return self._create_fallback_decision(chain, start_time)

        except Exception as e:
            logger.error(f"Failed to analyze chain {chain.chain_id}: {e}")
            return self._create_fallback_decision(chain, start_time)

    async def analyze_chains_batch(
        self, chains: List[TableChain]
    ) -> List[TableMergeDecision]:
        """
        Analyze multiple table chains sequentially with progress tracking.

        This method processes each chain independently, maintaining a clear audit
        trail of assembly decisions across the entire document.

        Args:
            chains (List[TableChain]): List of all table chains to analyze

        Returns:
            decisions (List[TableMergeDecision]): Assembly decisions for all chains
        """
        from tqdm import tqdm

        decisions = []

        with tqdm(total=len(chains), desc="Assembling table chains") as pbar:
            for chain in chains:
                try:
                    decision = await self.analyze_chain(chain)
                    decisions.append(decision)
                    pbar.set_description(f"Chain {chain.chain_id} ({decision.status})")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Failed to analyze chain {chain.chain_id}: {e}")
                    pbar.update(1)
                    continue

        success_count = sum(1 for d in decisions if d.status == "SUCCESS")
        logger.info(
            f"Chain assembly completed: {success_count}/{len(decisions)} chains "
            f"successfully merged"
        )

        return decisions

    def _create_fallback_decision(
        self, chain: TableChain, start_time: float
    ) -> TableMergeDecision:
        """
        Create a conservative fallback decision when LLM analysis fails.

        Args:
            chain (TableChain): The chain that failed analysis
            start_time (float): Processing start timestamp

        Returns:
            decision (TableMergeDecision): Conservative NO_MERGE decision
        """
        return TableMergeDecision(
            chain_id=chain.chain_id,
            status="NO_MERGE",
            analysis={
                "fragments_received": len(chain.tables),
                "repairs_performed": {
                    "collapsed_columns_fixed": False,
                    "description": "No repairs attempted due to analysis failure",
                },
                "reasoning": "LLM analysis failed; defaulting to NO_MERGE for safety",
            },
            final_merged_html=None,
            processing_time=time.time() - start_time,
        )
