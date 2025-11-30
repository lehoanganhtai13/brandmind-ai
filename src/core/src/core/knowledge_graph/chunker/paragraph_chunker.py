"""
Paragraph Chunker for adaptive structural chunking.

Implements paragraph-based aggregation with fallback to sentence
splitting for giant paragraphs. Uses zero overlap to prevent
duplicate triple extraction.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class ParagraphChunker:
    """
    Chunks text content using adaptive structural approach.

    This chunker respects paragraph boundaries and aggregates them
    up to a target size. For giant paragraphs exceeding max size,
    it falls back to recursive sentence splitting.
    """

    TARGET_CHUNK_SIZE = 400  # words
    MAX_CHUNK_SIZE = 700  # words

    def __init__(self) -> None:
        """Initialize ParagraphChunker."""
        # Fallback splitter for giant paragraphs
        # Approximate: 1 word ≈ 5-6 characters on average
        self.sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.TARGET_CHUNK_SIZE * 5,  # ~2000 chars for 400 words
            chunk_overlap=0,  # Zero overlap
            separators=[". ", "? ", "! ", "\n", " ", ""],
            length_function=self._count_words,
        )

        logger.info(
            f"ParagraphChunker initialized (target={self.TARGET_CHUNK_SIZE} words)"
        )

    def _count_words(self, text: str) -> int:
        """
        Count words in text using simple split.

        Args:
            text: Text to count words for

        Returns:
            Number of words
        """
        return len(text.split())

    def chunk_content(self, content: str) -> List[str]:
        """
        Chunk content using adaptive structural approach.

        Args:
            content: Section content to chunk

        Returns:
            List of chunk strings
        """
        # Split by paragraphs
        paragraphs = content.split("\n\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for para in paragraphs:
            para_words = self._count_words(para)

            # Case 1: Giant paragraph (> MAX_SIZE)
            if para_words > self.MAX_CHUNK_SIZE:
                # Commit current chunk if exists
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Split giant paragraph by sentences
                sub_chunks = self.sentence_splitter.split_text(para)
                chunks.extend(sub_chunks)

                logger.debug(
                    f"Split giant paragraph ({para_words} words) "
                    f"into {len(sub_chunks)} chunks"
                )
                continue

            # Case 2: Adding para would exceed target
            if current_length + para_words > self.TARGET_CHUNK_SIZE:
                # Commit current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))

                # Start new chunk with this paragraph
                current_chunk = [para]
                current_length = para_words

            # Case 3: Still room, add to current chunk
            else:
                current_chunk.append(para)
                current_length += para_words

        # Commit final chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        avg_size = (
            sum(self._count_words(c) for c in chunks) / len(chunks) if chunks else 0
        )
        logger.info(
            f"Chunked content: {len(chunks)} chunks, avg {avg_size:.0f} words/chunk"
        )

        return chunks
