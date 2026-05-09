"""LiteLLM integration helpers for running HippoRAG in BrandMind benchmarks.

The benchmark runs HippoRAG in a separate Python 3.10 conda environment while
BrandMind remains in its Python 3.12 uv workspace. HippoRAG can speak to any
OpenAI-compatible endpoint, so the local LiteLLM proxy is the bridge to Gemini
LLM and embedding models.

Business context:
    BrandMind uses 1536-dimensional Gemini embeddings in its Milvus/FalkorDB
    retrieval stack. LiteLLM returns 3072 dimensions for ``gemini-embedding-001``
    unless the OpenAI-compatible ``dimensions`` parameter is supplied. This
    module patches HippoRAG's OpenAI-compatible embedding adapter so HippoRAG and
    BrandMind are compared with the same embedding dimensionality.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np
from pydantic import BaseModel, Field

DEFAULT_LITELLM_BASE_URL = "http://localhost:4000/v1"
DEFAULT_LLM_MODEL = "gemini-2.5-flash-lite"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_DIMENSIONS = 1536


class EmbeddingResponseItem(Protocol):
    """Protocol for one OpenAI-compatible embedding response item."""

    embedding: list[float]


class EmbeddingResponse(Protocol):
    """Protocol for an OpenAI-compatible embedding response."""

    data: list[EmbeddingResponseItem]


class EmbeddingsClient(Protocol):
    """Protocol for an OpenAI-compatible embeddings client."""

    def create(
        self,
        *,
        input: list[str],
        model: str,
        dimensions: int,
    ) -> EmbeddingResponse:
        """Create embeddings for a batch of texts."""


class OpenAIClient(Protocol):
    """Protocol for the OpenAI client object owned by HippoRAG."""

    embeddings: EmbeddingsClient


class HippoRagOpenAIEmbeddingModel(Protocol):
    """Structural type for HippoRAG's OpenAI embedding model instances."""

    client: OpenAIClient
    embedding_model_name: str


class HippoRagLiteLLMConfig(BaseModel):
    """Configuration for the BrandMind HippoRAG LiteLLM bridge.

    Args:
        save_dir: Directory where HippoRAG stores indexes, OpenIE results, and
            local parquet embedding stores.
        llm_base_url: OpenAI-compatible LiteLLM base URL.
        embedding_base_url: OpenAI-compatible LiteLLM embedding base URL.
        llm_model_name: Gemini chat model exposed by LiteLLM.
        embedding_model_name: Gemini embedding model exposed by LiteLLM.
        embedding_dimensions: Embedding dimensionality used for fair comparison
            with BrandMind's retrieval stack.
        embedding_batch_size: Batch size used by HippoRAG embedding stores.
    """

    save_dir: str
    llm_base_url: str = DEFAULT_LITELLM_BASE_URL
    embedding_base_url: str = DEFAULT_LITELLM_BASE_URL
    llm_model_name: str = DEFAULT_LLM_MODEL
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    embedding_dimensions: int = Field(default=DEFAULT_EMBEDDING_DIMENSIONS, gt=0)
    embedding_batch_size: int = Field(default=16, gt=0)


def install_gemini_embedding_dimension_patch(
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
) -> None:
    """Patch HippoRAG's OpenAI embedding adapter to pass Gemini dimensions.

    Args:
        embedding_dimensions: The OpenAI-compatible ``dimensions`` value to send
            to LiteLLM for ``gemini-embedding-001`` calls.

    Raises:
        ValueError: If ``embedding_dimensions`` is not positive.
    """

    if embedding_dimensions <= 0:
        raise ValueError("embedding_dimensions must be a positive integer.")

    from hipporag.embedding_model.OpenAI import OpenAIEmbeddingModel

    def encode_with_dimensions(
        self: HippoRagOpenAIEmbeddingModel,
        texts: list[str],
    ) -> np.ndarray:
        """Encode texts with the configured Gemini embedding dimensionality."""

        sanitized_texts = [text.replace("\n", " ") if text else " " for text in texts]
        response = self.client.embeddings.create(
            input=sanitized_texts,
            model=self.embedding_model_name,
            dimensions=embedding_dimensions,
        )
        return np.array([item.embedding for item in response.data])

    OpenAIEmbeddingModel.encode = encode_with_dimensions


def build_hipporag_config(config: HippoRagLiteLLMConfig):
    """Build a HippoRAG ``BaseConfig`` for the local LiteLLM proxy.

    Args:
        config: Bridge configuration with model names, base URLs, save path, and
            embedding settings.

    Returns:
        A HippoRAG ``BaseConfig`` instance. The return type is intentionally not
        imported at module import time because this module may be imported from
        the BrandMind Python 3.12 environment where HippoRAG is not installed.
    """

    from hipporag.utils.config_utils import BaseConfig

    return BaseConfig(
        save_dir=config.save_dir,
        llm_name=config.llm_model_name,
        llm_base_url=config.llm_base_url,
        embedding_model_name=config.embedding_model_name,
        embedding_base_url=config.embedding_base_url,
        embedding_batch_size=config.embedding_batch_size,
    )


def build_hipporag(config: HippoRagLiteLLMConfig):
    """Create a HippoRAG instance configured for BrandMind's LiteLLM proxy.

    Args:
        config: Bridge configuration.

    Returns:
        A configured HippoRAG instance ready for indexing or retrieval.
    """

    install_gemini_embedding_dimension_patch(config.embedding_dimensions)

    from hipporag import HippoRAG

    return HippoRAG(global_config=build_hipporag_config(config))
