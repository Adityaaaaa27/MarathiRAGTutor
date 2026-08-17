"""Embedding Service Module.

Provides a centralized wrapper around HuggingFace embedding models.
Supports two modes:
  - API mode (default): Uses HuggingFace Inference API — no model download.
  - Local mode: Downloads and runs the model locally.

No other module in the application should directly instantiate
embedding models — all access goes through EmbeddingService.
"""

from typing import Any, Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpointEmbeddings,
)

from app.config.constants import FALLBACK_EMBEDDING_MODEL, PRIMARY_EMBEDDING_MODEL
from app.config.settings import Settings, get_settings
from app.utils.helpers import timer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Centralized embedding model provider.

    Supports two modes of operation:

    **API Mode** (default, recommended):
        Uses the HuggingFace Inference API. Requires a free ``HF_API_KEY``
        in ``.env``. No model download, no GPU, no disk space needed.

    **Local Mode**:
        Downloads the model (~2.3 GB) and runs it locally on CPU/GPU.
        Set ``EMBEDDING_MODE=local`` in ``.env`` to use this mode.

    Both modes present the same interface to the rest of the application
    via the ``Embeddings`` abstract class.

    Args:
        settings: Application settings. Injected for testability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._embeddings: Optional[Embeddings] = None
        self._model_name: str = self._settings.embedding_model_name

    @timer
    def initialize(self) -> None:
        """Initialize the embedding model (API or local).

        Attempts the primary model first, then falls back.

        Raises:
            RuntimeError: If both primary and fallback models fail to load.
        """
        mode = self._settings.embedding_mode
        primary = self._settings.embedding_model_name
        fallback = self._settings.fallback_embedding_model_name

        logger.info(
            "Initializing embeddings: mode=[bold]%s[/bold], model=[bold]%s[/bold]",
            mode,
            primary,
            extra={"markup": True},
        )

        # Try primary model
        try:
            if mode == "api":
                self._embeddings = self._create_api_embeddings(primary)
            else:
                self._embeddings = self._create_local_embeddings(primary)
            self._model_name = primary
            logger.info(
                "✅ Primary embedding model ready: [green]%s[/green] (mode=%s)",
                primary,
                mode,
                extra={"markup": True},
            )
            return
        except Exception as exc:
            logger.warning(
                "Primary model '%s' failed (%s): %s. Trying fallback...",
                primary,
                mode,
                exc,
            )

        # Try fallback model
        try:
            if mode == "api":
                self._embeddings = self._create_api_embeddings(fallback)
            else:
                self._embeddings = self._create_local_embeddings(fallback)
            self._model_name = fallback
            logger.info(
                "✅ Fallback embedding model ready: [green]%s[/green] (mode=%s)",
                fallback,
                mode,
                extra={"markup": True},
            )
            return
        except Exception as exc:
            logger.error("Fallback model '%s' also failed: %s", fallback, exc)
            raise RuntimeError(
                f"Failed to load both embedding models ({mode} mode): "
                f"primary='{primary}', fallback='{fallback}'. "
                f"Check your HF_API_KEY in .env if using API mode."
            ) from exc

    def _create_api_embeddings(self, model_name: str) -> HuggingFaceEndpointEmbeddings:
        """Create embeddings via HuggingFace Inference API.

        Args:
            model_name: HuggingFace model identifier.

        Returns:
            Configured ``HuggingFaceEndpointEmbeddings`` instance.

        Raises:
            ValueError: If HF_API_KEY is not configured.
        """
        api_key = self._settings.hf_api_key
        if not api_key or api_key == "your_hf_api_key_here":
            raise ValueError(
                "HF_API_KEY is required for API mode. "
                "Get a free key from: https://huggingface.co/settings/tokens "
                "and add it to your .env file."
            )

        logger.info("Connecting to HuggingFace Inference API for: %s", model_name)

        return HuggingFaceEndpointEmbeddings(
            model=model_name,
            huggingfacehub_api_token=api_key,
        )

    def _create_local_embeddings(self, model_name: str) -> HuggingFaceEmbeddings:
        """Create embeddings by downloading and running the model locally.

        Args:
            model_name: HuggingFace model identifier.

        Returns:
            Configured ``HuggingFaceEmbeddings`` instance.
        """
        model_kwargs: dict[str, Any] = {"device": self._settings.embedding_device}
        encode_kwargs: dict[str, Any] = {
            "normalize_embeddings": self._settings.embedding_normalize,
        }

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

    def get_embeddings(self) -> Embeddings:
        """Return the loaded embedding model instance.

        Returns:
            The active ``Embeddings`` instance (API or local).

        Raises:
            RuntimeError: If the service has not been initialized.
        """
        if self._embeddings is None:
            raise RuntimeError(
                "EmbeddingService not initialized. Call initialize() first."
            )
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding vector for a single query text.

        Args:
            text: Query text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            RuntimeError: If the service has not been initialized.
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple documents.

        Args:
            texts: List of document texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            RuntimeError: If the service has not been initialized.
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)

    @property
    def model_name(self) -> str:
        """Return the name of the currently loaded model."""
        return self._model_name

    @property
    def is_initialized(self) -> bool:
        """Check if the embedding model is loaded and ready."""
        return self._embeddings is not None
