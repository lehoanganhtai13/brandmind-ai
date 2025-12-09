from enum import Enum
from typing import Optional

from shared.model_clients.embedder.base_class import EmbedderBackend, EmbedderConfig


class EmbeddingMode(str, Enum):
    """
    Embedding mode determines how task types are applied.

    RETRIEVAL: Optimized for retrieval tasks (document library)
        - get_text_embedding → RETRIEVAL_DOCUMENT
        - get_query_embedding → RETRIEVAL_QUERY

    SEMANTIC: Optimized for similarity matching (knowledge graph)
        - get_text_embedding → SEMANTIC_SIMILARITY
        - get_query_embedding → SEMANTIC_SIMILARITY
    """

    RETRIEVAL = "RETRIEVAL"
    SEMANTIC = "SEMANTIC"


class GeminiEmbedderConfig(EmbedderConfig):
    """
    Configuration for Gemini embedder.

    Attributes:
        model_name: Gemini embedding model name (default: gemini-embedding-001)
        mode: Embedding mode (RETRIEVAL or SEMANTIC)
        output_dimensionality: Output dimension (768, 1536, or 3072)
        api_key: Google API key (fallback to GOOGLE_API_KEY env)
    """

    def __init__(
        self,
        model_name: str = "gemini-embedding-001",
        mode: EmbeddingMode = EmbeddingMode.SEMANTIC,
        output_dimensionality: int = 1536,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(EmbedderBackend.GEMINI, **kwargs)
        from config.system_config import SETTINGS

        self.model_name = model_name
        self.mode = mode
        self.output_dimensionality = output_dimensionality
        self.api_key = api_key or SETTINGS.GEMINI_API_KEY
