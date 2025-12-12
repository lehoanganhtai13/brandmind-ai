import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


class Settings:
    """Settings for the system configuration."""

    def __init__(self):
        # Load environment variables
        # Get project root (2 levels up from this file: src/config/system_config.py)
        project_root = Path(__file__).parent.parent.parent
        default_env_file = project_root / "environments" / ".env"
        env_file = os.getenv("ENVIRONMENT_FILE", str(default_env_file))

        if not os.path.exists(env_file):
            logger.warning(f"Environment file not found: {env_file}")
        else:
            status = load_dotenv(env_file, override=False)
            if not status:
                logger.warning(f"Failed to load environment variables from {env_file}")

        # MinIO settings
        self.MINIO_ACCESS_KEY_ID = os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin")
        self.MINIO_SECRET_ACCESS_KEY = os.getenv(
            "MINIO_SECRET_ACCESS_KEY", "minioadmin"
        )

        # Model serving settings
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))

        # Parsing service settings
        self.LLAMA_PARSE_API_KEY = os.getenv("LLAMA_PARSE_API_KEY", "")

        # Database settings
        self.MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
        self.MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
        self.MILVUS_ROOT_PASSWORD = os.getenv("MILVUS_ROOT_PASSWORD", "")

        self.FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
        self.FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", 6380))
        self.FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME", "")
        self.FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD", "")
        self.FALKORDB_GRAPH_NAME = os.getenv("FALKORDB_GRAPH_NAME", "knowledge_graph")

        # Vector Database Collection Names
        self.COLLECTION_DOCUMENT_CHUNKS = os.getenv(
            "COLLECTION_DOCUMENT_CHUNKS", "DocumentChunks"
        )
        self.COLLECTION_ENTITY_DESCRIPTIONS = os.getenv(
            "COLLECTION_ENTITY_DESCRIPTIONS", "EntityDescriptions"
        )
        self.COLLECTION_RELATION_DESCRIPTIONS = os.getenv(
            "COLLECTION_RELATION_DESCRIPTIONS", "RelationDescriptions"
        )


SETTINGS = Settings()
