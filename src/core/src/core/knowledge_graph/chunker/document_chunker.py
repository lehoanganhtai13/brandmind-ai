"""
Document Chunker orchestrator for Stage 2 (Semantic Chunking).

Coordinates the chunking workflow from loading global_map.json
to generating chunks.json output.
"""

import os
from pathlib import Path

from loguru import logger

from core.knowledge_graph.chunker.batch_processor import BatchProcessor
from core.knowledge_graph.models.chunk import ChunkingResult
from core.knowledge_graph.models.global_map import GlobalMap


class DocumentChunker:
    """
    Orchestrates the document chunking workflow.

    This class manages the end-to-end chunking process including
    loading the global map, processing sections in batches, and
    generating the final chunking result.
    """

    def __init__(self, document_folder: str, global_map_path: str):
        """
        Initialize DocumentChunker.

        Args:
            document_folder: Path to folder containing page files
            global_map_path: Path to global_map.json from Stage 1
        """
        self.document_folder = Path(document_folder)
        self.global_map_path = Path(global_map_path)

        logger.info(f"DocumentChunker initialized for: {document_folder}")

    def chunk_document(self) -> ChunkingResult:
        """
        Execute the chunking workflow.

        Returns:
            ChunkingResult with all generated chunks and statistics
        """
        # Load global_map
        global_map_path = os.path.join(self.document_folder, "global_map.json")
        if not os.path.exists(global_map_path):
            raise FileNotFoundError(
                f"global_map.json not found in {self.document_folder}. "
                "Please run Stage 1 (mapping) first."
            )

        global_map = GlobalMap.from_json_file(global_map_path)
        logger.info(
            f"Loaded global_map with {len(global_map.structure)} top-level sections"
        )

        # Initialize batch processor with global_map
        batch_processor = BatchProcessor(str(self.document_folder), global_map)

        # Process all sections
        logger.info("Starting chunking process...")
        chunks = batch_processor.process_all_sections(global_map.structure)

        # Calculate statistics
        total_chunks = len(chunks)
        avg_chunk_size = (
            sum(chunk.metadata.word_count for chunk in chunks) / total_chunks
            if total_chunks > 0
            else 0.0
        )

        result = ChunkingResult(
            chunks=chunks, total_chunks=total_chunks, avg_chunk_size=avg_chunk_size
        )

        logger.info(
            f"Chunking complete: {total_chunks} chunks, "
            f"avg {avg_chunk_size:.0f} words/chunk"
        )

        return result
