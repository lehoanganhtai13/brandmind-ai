import asyncio
from typing import Any, List

import numpy as np
from google import genai
from google.genai import types
from numpy.linalg import norm

from shared.model_clients.embedder.base_embedder import BaseEmbedder
from shared.model_clients.embedder.gemini.config import (
    EmbeddingMode,
    GeminiEmbedderConfig,
)
from shared.utils.base_class import DenseEmbedding


class GeminiEmbedder(BaseEmbedder):
    """
    Gemini implementation for text embedding.

    Task type is determined by config.mode:
    - RETRIEVAL mode: text→RETRIEVAL_DOCUMENT, query→RETRIEVAL_QUERY
    - SEMANTIC mode: both→SEMANTIC_SIMILARITY

    Note: For non-default dimensions (not 3072), embeddings are manually
    normalized as per Google's recommendation.
    """

    # Default dimension where embeddings are pre-normalized
    DEFAULT_DIMENSION = 3072

    def _initialize_embedder(self, **kwargs) -> None:
        """Initialize Gemini client."""
        assert isinstance(self.config, GeminiEmbedderConfig)
        self._config: GeminiEmbedderConfig = self.config
        self.client = genai.Client(api_key=self._config.api_key)

    def _get_task_type_for_text(self) -> str:
        """Get Gemini task type for text/document embedding."""
        if self._config.mode == EmbeddingMode.RETRIEVAL:
            return "RETRIEVAL_DOCUMENT"
        return "SEMANTIC_SIMILARITY"

    def _get_task_type_for_query(self) -> str:
        """Get Gemini task type for query embedding."""
        if self._config.mode == EmbeddingMode.RETRIEVAL:
            return "RETRIEVAL_QUERY"
        return "SEMANTIC_SIMILARITY"

    def _normalize_embedding(self, values: List[float]) -> List[float]:
        """
        Normalize embedding vector if using non-default dimension.

        Google's gemini-embedding-001 only returns pre-normalized embeddings
        at the default dimension (3072). For other dimensions, manual
        normalization is required.
        """
        if self._config.output_dimensionality == self.DEFAULT_DIMENSION:
            return values

        embedding_np = np.array(values)
        normed = embedding_np / norm(embedding_np)
        return normed.tolist()

    def get_text_embedding(self, text: str, **kwargs: Any) -> DenseEmbedding:
        """Get embedding for text/document."""
        result = self.client.models.embed_content(
            model=self._config.model_name,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=self._get_task_type_for_text(),
                output_dimensionality=self._config.output_dimensionality,
            ),
        )
        if result.embeddings is None or len(result.embeddings) == 0:
            raise ValueError("No embeddings returned from Gemini API")

        emb_values = result.embeddings[0].values
        if emb_values is None:
            raise ValueError("Embedding values are None")

        values = self._normalize_embedding(list(emb_values))
        return values

    def get_text_embeddings(
        self, texts: List[str], **kwargs: Any
    ) -> List[DenseEmbedding]:
        """Batch embedding for multiple texts."""
        result = self.client.models.embed_content(
            model=self._config.model_name,
            contents=texts,  # type: ignore[arg-type]
            config=types.EmbedContentConfig(
                task_type=self._get_task_type_for_text(),
                output_dimensionality=self._config.output_dimensionality,
            ),
        )
        if result.embeddings is None:
            raise ValueError("No embeddings returned from Gemini API")

        embeddings = []
        for emb in result.embeddings:
            if emb.values is None:
                raise ValueError("Embedding values are None")
            embeddings.append(self._normalize_embedding(list(emb.values)))

        return embeddings

    def get_query_embedding(self, query: str, **kwargs: Any) -> DenseEmbedding:
        """Get embedding for search query."""
        result = self.client.models.embed_content(
            model=self._config.model_name,
            contents=query,
            config=types.EmbedContentConfig(
                task_type=self._get_task_type_for_query(),
                output_dimensionality=self._config.output_dimensionality,
            ),
        )
        if result.embeddings is None or len(result.embeddings) == 0:
            raise ValueError("No embeddings returned from Gemini API")

        emb_values = result.embeddings[0].values
        if emb_values is None:
            raise ValueError("Embedding values are None")

        values = self._normalize_embedding(list(emb_values))
        return values

    # Async versions using asyncio.to_thread
    async def aget_text_embedding(self, text: str, **kwargs: Any) -> DenseEmbedding:
        return await asyncio.to_thread(self.get_text_embedding, text, **kwargs)

    async def aget_text_embeddings(
        self, texts: List[str], **kwargs: Any
    ) -> List[DenseEmbedding]:
        return await asyncio.to_thread(self.get_text_embeddings, texts, **kwargs)

    async def aget_query_embedding(self, query: str, **kwargs: Any) -> DenseEmbedding:
        return await asyncio.to_thread(self.get_query_embedding, query, **kwargs)
