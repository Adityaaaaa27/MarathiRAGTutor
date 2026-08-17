"""Application Settings Module.

Centralized configuration using Pydantic Settings.
Loads environment variables from .env with fallbacks and type validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.constants import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_MISTRAL_MODEL,
    FALLBACK_EMBEDDING_MODEL,
    PRIMARY_EMBEDDING_MODEL,
)

# Base directory of the marathi-rag project
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Global configuration settings for the Marathi RAG system."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # LLM Provider Configuration ('gemini' or 'mistral')
    # --------------------------------------------------------------------------
    llm_provider: str = Field(
        default="mistral",
        description="Active LLM provider for generation: 'gemini' or 'mistral'.",
    )

    # --------------------------------------------------------------------------
    # Google Gemini Settings (100% Free via Google AI Studio)
    # --------------------------------------------------------------------------
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key loaded from .env or environment.",
    )
    gemini_model_name: str = Field(
        default="gemini-3.7-flash",
        description="Gemini model identifier (e.g. gemini-3.7-flash, gemini-3-flash-preview).",
    )
    gemini_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for Gemini generation.",
    )
    gemini_max_tokens: int = Field(
        default=2048,
        gt=0,
        description="Maximum tokens for generated Gemini response.",
    )

    # --------------------------------------------------------------------------
    # Mistral AI Settings
    # --------------------------------------------------------------------------
    mistral_api_key: str = Field(
        default="",
        description="Mistral AI API key loaded from .env or environment.",
    )
    mistral_model_name: str = Field(
        default=DEFAULT_MISTRAL_MODEL,
        description="Mistral model identifier (e.g., mistral-large-latest, open-mistral-7b).",
    )
    mistral_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for generation (low for factual adherence).",
    )
    mistral_max_tokens: int = Field(
        default=2048,
        gt=0,
        description="Maximum tokens for generated response.",
    )
    mistral_timeout_seconds: int = Field(
        default=60,
        gt=0,
        description="API timeout in seconds.",
    )

    # --------------------------------------------------------------------------
    # Text Chunking Settings
    # --------------------------------------------------------------------------
    chunk_size: int = Field(
        default=800,
        gt=0,
        description="Token/character chunk size for splitting.",
    )
    chunk_overlap: int = Field(
        default=150,
        ge=0,
        description="Overlap between consecutive chunks to preserve context.",
    )

    # --------------------------------------------------------------------------
    # Embedding Model Settings
    # --------------------------------------------------------------------------
    hf_api_key: str = Field(
        default="",
        description="HuggingFace API key for Inference API embeddings.",
    )
    embedding_mode: str = Field(
        default="api",
        description="Embedding mode: 'api' (HuggingFace Inference API, no download) or 'local' (download model).",
    )
    embedding_model_name: str = Field(
        default=PRIMARY_EMBEDDING_MODEL,
        description="Primary HuggingFace embedding model name or path.",
    )
    fallback_embedding_model_name: str = Field(
        default=FALLBACK_EMBEDDING_MODEL,
        description="Fallback embedding model name if primary fails to load.",
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embeddings computation ('cpu', 'cuda', 'mps'). Only used in local mode.",
    )
    embedding_normalize: bool = Field(
        default=True,
        description="Normalize embeddings vectors for cosine similarity computation. Only used in local mode.",
    )

    # --------------------------------------------------------------------------
    # Vector Database (ChromaDB) Settings
    # --------------------------------------------------------------------------
    chroma_persist_dir: Path = Field(
        default=PROJECT_ROOT / "chroma",
        description="Filesystem directory for persistent ChromaDB storage.",
    )
    collection_name: str = Field(
        default=DEFAULT_COLLECTION_NAME,
        description="ChromaDB collection name for storing textbook embeddings.",
    )

    # --------------------------------------------------------------------------
    # Retrieval Settings
    # --------------------------------------------------------------------------
    retriever_top_k: int = Field(
        default=10,
        gt=0,
        description="Number of most relevant chunks to retrieve per query.",
    )
    retriever_score_threshold: Optional[float] = Field(
        default=None,
        description="Optional minimum similarity score threshold for retrieved chunks.",
    )

    # --------------------------------------------------------------------------
    # File Paths & Directories
    # --------------------------------------------------------------------------
    pdf_path: Path = Field(
        default=PROJECT_ROOT / "data" / "textbook.pdf",
        description="Path to the source Marathi textbook PDF.",
    )
    log_dir: Path = Field(
        default=PROJECT_ROOT / "logs",
        description="Directory for application log files.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is strictly less than chunk size."""
        chunk_size = info.data.get("chunk_size", 400)
        if v >= chunk_size:
            raise ValueError(f"chunk_overlap ({v}) must be strictly less than chunk_size ({chunk_size})")
        return v

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_path.parent.mkdir(parents=True, exist_ok=True)

    def validate_api_key(self) -> bool:
        """Check if an API key is configured for the active LLM provider."""
        if self.llm_provider.lower() == "gemini":
            return bool(self.gemini_api_key and self.gemini_api_key.strip() != "your_gemini_api_key_here")
        if not self.mistral_api_key or self.mistral_api_key.strip() == "your_mistral_api_key_here":
            return False
        return True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of application Settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
