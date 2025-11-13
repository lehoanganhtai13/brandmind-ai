"""LLM-powered table summarizer."""

import time
from typing import List

from loguru import logger

from core.document_processing.models import TableInfo, TableSummary
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)


class TableSummarizer:
    """
    LLM-powered table summarizer for converting HTML tables to readable summaries.
    """

    def __init__(self):
        """Initializes the TableSummarizer with a Google AI LLM client."""
        from config.system_config import SETTINGS
        from prompts.document_processing.summarize_table import SUMMARIZE_TABLE_PROMPT
        self.llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-2.5-flash-lite",
                api_key=SETTINGS.GEMINI_API_KEY,
                temperature=0.1,
                thinking_budget=0,
                response_mime_type="text/plain",
                system_instruction=SUMMARIZE_TABLE_PROMPT,
            )
        )

    async def summarize_table(self, table: TableInfo) -> TableSummary:
        """
        Summarizes a single HTML table using the configured LLM.

        Args:
            table (TableInfo): An object containing the table's HTML content and metadata.

        Returns:
            TableSummary: An object containing the original HTML and the generated summary.
        """
        start_time = time.time()
        try:
            content = (
                f"The table content from page {table.page_number} is:\n{table.html_content}"
            )
            result = self.llm.complete(content, temperature=0.1).text
            summary = result.strip()
            processing_time = time.time() - start_time

            logger.debug(
                f"Table summary generated for page {table.page_number} in {processing_time:.2f}s"
            )

            return TableSummary(
                original_table_html=table.html_content,
                summary_markdown=summary,
                page_number=table.page_number,
                processing_time=processing_time,
            )
        except Exception as e:
            logger.error(
                f"Failed to summarize table on page {table.page_number}: {e}, using fallback"
            )
            return TableSummary(
                original_table_html=table.html_content,
                summary_markdown=self._fallback_summary(table.html_content),
                page_number=table.page_number,
                processing_time=time.time() - start_time,
            )

    async def summarize_tables_batch(
        self,
        tables: List[TableInfo]
    ) -> List[TableSummary]:
        """
        Summarizes multiple tables sequentially with a progress bar.

        Args:
            tables (List[TableInfo]): A list of TableInfo objects to be summarized.

        Returns:
            List[TableSummary]: A list of summarization results.
        """
        from tqdm import tqdm

        summaries = []
        with tqdm(total=len(tables), desc="Summarizing tables") as pbar:
            for table in tables:
                try:
                    summary = await self.summarize_table(table)
                    summaries.append(summary)
                    pbar.set_description(f"Page {table.page_number}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(
                        f"Failed to summarize table on page {table.page_number}: {e}"
                    )
                    pbar.update(1)
                    continue
        logger.info(f"Table summarization completed: {len(summaries)} successful")
        return summaries

    def _fallback_summary(self, html_table: str) -> str:
        """
        Provides a basic fallback summary by extracting raw text from HTML.

        Args:
            html_table (str): The HTML content of the table.

        Returns:
            str: A simple, truncated text summary.
        """
        import re

        text_content = re.sub(r"<[^>]+>", " ", html_table)
        text_content = re.sub(r"\s+", " ", text_content).strip()

        if len(text_content) > 200:
            return text_content[:200] + "..."
        return text_content
