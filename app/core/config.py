"""
Core configuration module.
Loads all settings from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    HUGGINGFACE_API_KEY: str = ""
    LLM_MODEL: str = "meta-llama/Meta-Llama-3-8B-Instruct"

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./persona_ai.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    RATE_LIMIT: str = "60/minute"
    LOG_LEVEL: str = "INFO"

    # Memory
    SHORT_TERM_MEMORY_LIMIT: int = 20
    LONG_TERM_TOP_K: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
