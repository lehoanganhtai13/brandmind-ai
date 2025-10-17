import os
from dotenv import load_dotenv
from loguru import logger


class Settings:
    """Settings for the system configuration."""
    def __init__(self):

        # Load environment variables
        env_file = os.getenv("ENVIRONMENT_FILE", "environments/.env")
        status = load_dotenv(env_file)
        if not status:
            logger.warning(f"Failed to load environment variables from {env_file}")
        
        # MinIO settings
        self.MINIO_ACCESS_KEY_ID = os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin")
        self.MINIO_SECRET_ACCESS_KEY = os.getenv("MINIO_SECRET_ACCESS_KEY", "minioadmin")

        # Model serving settings
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))

        # Agent settings
        self.SCRAPELESS_API_KEY = os.getenv("SCRAPELESS_API_KEY", "")
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

SETTINGS = Settings()
