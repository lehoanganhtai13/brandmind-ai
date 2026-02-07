"""Batch processor for knowledge extraction.

This module handles concurrent async processing of document chunks through
the extraction agent, with progress tracking and resume capabilities.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List

from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from core.knowledge_graph.miner.extraction_agent import ExtractionAgent
from core.knowledge_graph.models.chunk import Chunk
from core.knowledge_graph.models.triple import ChunkExtractionResult


def _log_retry_attempt(retry_state):
    """Custom retry callback for loguru compatibility.

    Args:
        retry_state: Tenacity retry state object
    """
    logger.warning(
        f"Retrying {retry_state.fn.__name__} after {retry_state.outcome.exception()}"
    )


class BatchProcessor:
    """Processes chunks in batches for parallel extraction.

    This class manages the batch processing workflow, including:
    - Loading chunks from chunks.json
    - Grouping into batches for parallel processing
    - Concurrency control with ThreadPoolExecutor
    - Retry logic with tenacity for API errors
    - Progress checkpointing for resume capability

    Attributes:
        document_folder: Path to document folder containing chunks.json
        progress_file: Path to progress checkpoint
        BATCH_SIZE: Number of chunks to process in each batch
        MAX_CONCURRENT: Maximum number of concurrent extraction agents (Semaphore limit)
    """

    BATCH_SIZE = 20  # Process 20 chunks at a time
    MAX_CONCURRENT = 20  # Max concurrent agents (controlled by Semaphore)

    def __init__(self, document_folder: str):
        """Initialize batch processor.

        Args:
            document_folder: Path to document folder containing chunks.json
        """
        self.document_folder = Path(document_folder)
        self.progress_file = self.document_folder / "extraction_progress.json"
        logger.info(f"BatchProcessor initialized (batch_size={self.BATCH_SIZE})")

    def load_chunks(self) -> List[Chunk]:
        """Load chunks from chunks.json.

        Returns:
            List of Chunk objects loaded from chunks.json

        Raises:
            FileNotFoundError: If chunks.json does not exist
        """
        chunks_file = self.document_folder / "chunks.json"

        if not chunks_file.exists():
            raise FileNotFoundError(
                f"chunks.json not found in {self.document_folder}. "
                "Please run Stage 2 (chunking) first."
            )

        with open(chunks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = [Chunk(**chunk_data) for chunk_data in data["chunks"]]
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")

        return chunks

    def load_progress(self) -> dict:
        """Load extraction progress from checkpoint."""
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_batch_idx": -1,
            "completed_chunk_ids": [],
            "failed_chunk_ids": [],
        }

    def save_progress(
        self,
        batch_idx: int,
        completed_chunk_ids: List[str],
        failed_chunk_ids: List[str],
    ):
        """Save extraction progress to checkpoint.

        Args:
            batch_idx: Index of last completed batch
            completed_chunk_ids: List of successfully processed chunk IDs
            failed_chunk_ids: List of failed chunk IDs (after max retries)
        """
        progress = {
            "last_batch_idx": batch_idx,
            "completed_chunk_ids": completed_chunk_ids,
            "failed_chunk_ids": failed_chunk_ids,
        }
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)

    def save_incremental_results(self, all_results: List[ChunkExtractionResult]):
        """Save incremental extraction results to triples.json.

        This ensures results are persisted after each batch, preventing data loss
        if the process is interrupted.

        Args:
            all_results: All extraction results accumulated so far
        """
        output_file = self.document_folder / "triples.json"
        output_data = {
            "total_chunks": len(all_results),
            "total_entities": sum(len(r.extraction.entities) for r in all_results),
            "total_relations": sum(
                len(r.extraction.relationships) for r in all_results
            ),
            "extractions": [r.model_dump() for r in all_results],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.debug(
            f"Saved incremental results: {len(all_results)} chunks, "
            f"{output_data['total_entities']} entities, "
            f"{output_data['total_relations']} relations"
        )

    def load_existing_results(self) -> List[ChunkExtractionResult]:
        """Load existing extraction results from triples.json if it exists.

        Used when resuming to preserve previously extracted results.

        Returns:
            List of existing ChunkExtractionResult objects, or empty
            list if file doesn't exist
        """
        output_file = self.document_folder / "triples.json"

        if not output_file.exists():
            return []

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert back to ChunkExtractionResult objects
            existing_results = [
                ChunkExtractionResult(**extraction)
                for extraction in data.get("extractions", [])
            ]

            logger.info(
                f"Loaded {len(existing_results)} existing results from {output_file}"
            )
            return existing_results

        except Exception as e:
            logger.warning(f"Failed to load existing results: {e}")
            return []

    async def process_all_chunks(
        self, resume: bool = False, retry_failed: bool = False
    ) -> List[ChunkExtractionResult]:
        """Process all chunks with batch processing and async concurrency.

        Args:
            resume: Resume from last checkpoint (skip completed chunks)
            retry_failed: Retry only previously failed chunks

        Returns:
            List of extraction results for all chunks
        """
        chunks = self.load_chunks()

        # Load progress if resuming or retrying failed
        progress = (
            self.load_progress()
            if (resume or retry_failed)
            else {
                "last_batch_idx": -1,
                "completed_chunk_ids": [],
                "failed_chunk_ids": [],
            }
        )
        start_batch_idx = progress["last_batch_idx"] + 1

        # Filter chunks based on mode
        if retry_failed:
            # Retry ONLY failed chunks
            failed_ids = set(progress.get("failed_chunk_ids", []))
            if not failed_ids:
                logger.info("No failed chunks to retry!")
                return []

            chunks = [c for c in chunks if c.chunk_id in failed_ids]
            logger.info(f"Retrying {len(chunks)} previously failed chunks")
            # Reset start_batch_idx for retry mode
            start_batch_idx = 0

        elif resume:
            # Skip both completed and failed chunks
            completed_ids = set(progress["completed_chunk_ids"])
            failed_ids = set(progress.get("failed_chunk_ids", []))
            skip_ids = completed_ids | failed_ids  # Union of both sets

            chunks = [c for c in chunks if c.chunk_id not in skip_ids]

            if failed_ids:
                logger.warning(
                    f"Skipping {len(failed_ids)} previously failed chunks. "
                    f"Use --retry-failed to retry them."
                )

            logger.info(
                f"Resuming from batch {start_batch_idx}, "
                f"{len(chunks)} chunks remaining "
                f"({len(completed_ids)} completed, {len(failed_ids)} failed)"
            )

        # Group into batches
        batches = [
            chunks[i : i + self.BATCH_SIZE]
            for i in range(0, len(chunks), self.BATCH_SIZE)
        ]

        logger.info(
            f"Processing {len(chunks)} chunks in {len(batches)} batches "
            f"(batch_size={self.BATCH_SIZE}, max_concurrent={self.MAX_CONCURRENT})"
        )

        # Load existing results if resuming (prevents overwrite)
        if resume:
            all_results = self.load_existing_results()
            logger.info(
                f"Starting with {len(all_results)} existing results from previous run"
            )
        else:
            all_results = []

        # Process each batch
        start_time = time.time()
        for new_batch_idx, batch in enumerate(batches):
            # Calculate original batch index for progress tracking
            original_batch_idx = start_batch_idx + new_batch_idx

            logger.info(
                f"Processing batch {original_batch_idx + 1} "
                f"({new_batch_idx + 1}/{len(batches)} remaining)..."
            )

            # Process batch with async concurrency
            batch_results, failed_chunks = await self._process_batch_async(batch)
            all_results.extend(batch_results)

            # Save progress checkpoint (including failed chunks)
            completed_ids = progress.get("completed_chunk_ids", [])
            completed_ids.extend([r.chunk_id for r in batch_results])

            failed_ids = progress.get("failed_chunk_ids", [])
            failed_ids.extend(failed_chunks)

            self.save_progress(original_batch_idx, completed_ids, failed_ids)

            # Save incremental results (prevents data loss on interruption)
            self.save_incremental_results(all_results)

            if failed_chunks:
                logger.warning(
                    f"Batch {original_batch_idx + 1}: "
                    f"{len(failed_chunks)} chunks failed after max retries"
                )

            logger.info(
                f"Batch {original_batch_idx + 1} complete: "
                f"{len(batch_results)} extractions, "
                f"{len(all_results)} total so far"
            )

        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"All batches complete: {len(all_results)} total extractions "
            f"in {duration:.2f} seconds"
        )
        return all_results

    async def _process_batch_async(
        self, batch: List[Chunk]
    ) -> tuple[List[ChunkExtractionResult], List[str]]:
        """Process a batch of chunks with async concurrent processing.

        Uses Semaphore to limit concurrent agents and prevent overwhelming the API.
        Each chunk gets its own extraction agent running concurrently.

        Args:
            batch: List of chunks to process

        Returns:
            Tuple of (successful results, failed chunk IDs)
        """
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        async def process_with_limit(chunk: Chunk):
            """Process single chunk with semaphore rate limiting."""
            async with semaphore:  # Acquire semaphore (blocks if limit reached)
                try:
                    result = await self._process_single_chunk_async(chunk)
                    logger.debug(
                        f"Chunk '{chunk.chunk_id[:8]}...': "
                        f"{len(result.extraction.entities)} entities, "
                        f"{len(result.extraction.relationships)} relations"
                    )
                    return (result, None)  # (result, no error)
                except Exception as e:
                    logger.error(
                        f"Chunk '{chunk.chunk_id}' failed after max retries: {e}"
                    )
                    return (None, chunk.chunk_id)  # (no result, failed chunk ID)

        # Run all chunks concurrently (limited by semaphore)
        results = await asyncio.gather(
            *[process_with_limit(chunk) for chunk in batch],
            return_exceptions=False,  # Exceptions handled in process_with_limit
        )

        # Separate successful results and failed chunk IDs
        successful_results = [r for r, _ in results if r is not None]
        failed_chunk_ids = [chunk_id for _, chunk_id in results if chunk_id is not None]

        return successful_results, failed_chunk_ids

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),  # Fixed 1 second delay between retries
        retry=retry_if_exception_type(Exception),
        before_sleep=_log_retry_attempt,  # Custom callback for loguru
    )
    async def _process_single_chunk_async(self, chunk: Chunk) -> ChunkExtractionResult:
        """Process a single chunk with extraction agent (async).

        Includes retry logic for API errors using tenacity decorator.
        Retries up to 3 times with 1 second delay between attempts.

        Args:
            chunk: Chunk to process

        Returns:
            Extraction result with validation

        Raises:
            Exception: If extraction fails after all retries
        """
        # Create agent and run extraction (pure async, no asyncio.run)
        agent = ExtractionAgent()
        return await agent.extract_knowledge(chunk)
