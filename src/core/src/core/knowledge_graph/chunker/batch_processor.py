"""
Batch Processor for parallel chunking of multiple sections.

Handles batching of top-level sections and parallel processing
to maximize throughput while managing memory efficiently.
"""

import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

from loguru import logger

from core.knowledge_graph.chunker.page_merger import PageMerger
from core.knowledge_graph.chunker.paragraph_chunker import ParagraphChunker
from core.knowledge_graph.chunker.section_finder import SectionFinder
from core.knowledge_graph.chunker.section_processor import SectionProcessor
from core.knowledge_graph.models.chunk import Chunk, ChunkMetadata
from core.knowledge_graph.models.global_map import GlobalMap, SectionNode


class BatchProcessor:
    """
    Processes sections in batches for parallel chunking.

    This class orchestrates the chunking workflow by grouping top-level
    sections into batches and processing them in parallel using
    multiprocessing to maximize CPU utilization.
    """

    BATCH_SIZE = 8  # Process 8 chapters at a time

    def __init__(self, document_folder: str, global_map: GlobalMap):
        """
        Initialize BatchProcessor.

        Args:
            document_folder: Path to document folder containing pages
            global_map: GlobalMap instance for section lookup
        """
        self.document_folder = document_folder
        self.global_map = global_map
        self.section_finder = SectionFinder(global_map.structure)
        logger.info(f"BatchProcessor initialized (batch_size={self.BATCH_SIZE})")

    def _flatten_sections(self, sections: List[SectionNode]) -> List[SectionNode]:
        """
        Flatten section hierarchy to get all leaf sections.

        Recursively traverses the section tree and collects all leaf nodes
        (sections without children). These are the actual content sections
        that need to be chunked.

        Args:
            sections: List of top-level sections from global_map

        Returns:
            List of leaf sections (sections without children)
        """
        leaf_sections: List[SectionNode] = []

        def collect_leaves(section: SectionNode) -> None:
            if not section.children:
                # This is a leaf section
                leaf_sections.append(section)
            else:
                # Recurse into children
                for child in section.children:
                    collect_leaves(child)

        for section in sections:
            collect_leaves(section)

        return leaf_sections

    def process_all_sections(self, sections: List[SectionNode]) -> List[Chunk]:
        """
        Process all sections in batches.

        Flattens the section hierarchy to get leaf sections (chapters),
        then processes them in batches for parallel chunking.

        Args:
            sections: List of top-level sections from global_map

        Returns:
            List of all chunks from all sections
        """
        # Flatten hierarchy to get leaf sections
        leaf_sections = self._flatten_sections(sections)

        logger.info(
            f"Flattened {len(sections)} top-level sections "
            f"into {len(leaf_sections)} leaf sections"
        )

        all_chunks: List[Chunk] = []

        # Group sections into batches
        batches = [
            leaf_sections[i : i + self.BATCH_SIZE]
            for i in range(0, len(leaf_sections), self.BATCH_SIZE)
        ]

        logger.info(
            f"Processing {len(leaf_sections)} sections in {len(batches)} batches "
            f"(batch_size={self.BATCH_SIZE})"
        )

        # Process each batch
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}...")

            # Process sections in parallel within batch
            batch_chunks = self._process_batch_parallel(batch)
            all_chunks.extend(batch_chunks)

            logger.info(
                f"Batch {batch_idx + 1} complete: {len(batch_chunks)} chunks generated"
            )

        logger.info(f"All batches complete: {len(all_chunks)} total chunks")
        return all_chunks

    def _process_batch_parallel(self, batch: List[SectionNode]) -> List[Chunk]:
        """
        Process a batch of sections in parallel using multiprocessing.

        Args:
            batch: List of sections to process in parallel

        Returns:
            List of chunks from all sections in batch
        """
        chunks: List[Chunk] = []

        # Use ProcessPoolExecutor for CPU-bound work
        with ProcessPoolExecutor(max_workers=self.BATCH_SIZE) as executor:
            # Submit all sections in batch
            futures = {
                executor.submit(self._process_single_section, section): section
                for section in batch
            }

            # Collect results as they complete
            for future in as_completed(futures):
                section = futures[future]
                try:
                    section_chunks = future.result()
                    chunks.extend(section_chunks)
                    logger.debug(
                        f"Section '{section.title}': {len(section_chunks)} chunks"
                    )
                except Exception as e:
                    logger.error(f"Error processing section '{section.title}': {e}")

        return chunks

    def _process_single_section(self, section: SectionNode) -> List[Chunk]:
        """
        Process a single section (called in separate process).

        Args:
            section: Section to process

        Returns:
            List of chunks from this section
        """
        # Initialize components (each process needs its own instances)
        page_merger = PageMerger(self.document_folder)
        section_processor = SectionProcessor(page_merger)
        paragraph_chunker = ParagraphChunker()
        section_finder = SectionFinder(self.global_map.structure)

        # Get document metadata (cached after first call)
        doc_metadata = page_merger.get_document_metadata()

        # Extract section content
        content, offset_map = section_processor.extract_section_content(section)

        # Chunk content
        chunk_texts = paragraph_chunker.chunk_content(content)

        # Create Chunk objects with metadata
        chunks: List[Chunk] = []
        current_offset = 0

        for chunk_text in chunk_texts:
            # Track offset sequentially instead of searching
            # (RecursiveCharacterTextSplitter may modify text)
            chunk_start = current_offset
            chunk_end = current_offset + len(chunk_text)

            # Determine pages based on offset
            pages = page_merger.get_pages_for_chunk(chunk_start, chunk_end, offset_map)

            # Find most specific section for these pages
            section_info = section_finder.find_section_for_pages(pages)

            # Use specific section if found, otherwise fall back to current section
            if section_info:
                source, section_summary = section_info
            else:
                source = section.title
                section_summary = section.summary_context

            # Create chunk with metadata
            chunk = Chunk(
                chunk_id=str(uuid.uuid4()),
                content=chunk_text,
                metadata=ChunkMetadata(
                    source=source,
                    original_document=doc_metadata["title"],
                    author=doc_metadata["author"],
                    pages=pages,
                    section_summary=section_summary,
                    word_count=len(chunk_text.split()),
                ),
            )
            chunks.append(chunk)

            # Update offset for next chunk (account for separator)
            current_offset = chunk_end + 2  # +2 for "\n\n" separator

        return chunks
