"""
Central configuration for the RAG system.

This module:
- Loads environment variables from .env
- Exposes them via a frozen Settings dataclass
- Performs basic validation on required configuration

All other modules should import settings from here
instead of reading environment variables directly.
"""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    """
     Immutable application configuration.

     Values are read once from environment variables at startup
     and should be treated as read-only throughout the program.
     """

    ntnu_api_key: str = os.getenv("NTNU_API_KEY", "")
    ntnu_base_url: str = os.getenv("NTNU_BASE_URL", "")

    chat_model: str = os.getenv("CHAT_MODEL", "gpt-oss-120b")
    embed_model: str = os.getenv("EMBED_MODEL", "Qwen3-Embedding-8B")

    data_dir: str = os.getenv("DATA_DIR", "./data")
    vectorstore_dir: str = os.getenv("VECTORSTORE_DIR", "./vectorstore")

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    top_k: int = int(os.getenv("TOP_K", "5"))

settings = Settings()

def validate_settings() -> None:
    """
        Validate that required configuration values are present.

        Raises:
            ValueError: If a required environment variable is missing.
        """
    if not settings.ntnu_api_key:
        raise ValueError("Missing NTNU_API_KEY in .env")
    if not settings.ntnu_base_url:
        raise ValueError("Missing NTNU_BASE_URL in .env")
