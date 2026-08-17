"""Retriever Service Module.

Provides a configurable LangChain retriever backed by ChromaDB.
Supports top-K tuning and metadata filtering for future
multi-textbook expansion.
"""

from typing import Any, Optional

from langchain_core.retrievers import BaseRetriever

from app.config.settings import Settings, get_settings
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)


class RetrieverService:
    """Configurable document retriever backed by ChromaDB.

    Creates LangChain-compatible retrievers from the vector store
    with support for metadata filtering (e.g., by textbook_id,
    standard, chapter) even when only one textbook exists today.

    Args:
        chroma_service: Initialized ``ChromaService`` instance.
        settings: Application settings. Injected for testability.
    """

    def __init__(
        self,
        chroma_service: ChromaService,
        settings: Optional[Settings] = None,
    ) -> None:
        self._chroma_service = chroma_service
        self._settings = settings or get_settings()

    def get_retriever(
        self,
        top_k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> BaseRetriever:
        """Create a LangChain retriever with optional metadata filtering.

        Args:
            top_k: Number of documents to retrieve. Defaults to settings value.
            filters: Optional ChromaDB metadata filter dict.
                Example: ``{"textbook_id": "mh_state_board_marathi_std_6"}``

        Returns:
            A LangChain ``BaseRetriever`` instance.

        Raises:
            RuntimeError: If the vector store has not been initialized.
        """
        k = top_k or self._settings.retriever_top_k

        search_kwargs: dict[str, Any] = {"k": k}

        if filters:
            search_kwargs["filter"] = filters
            logger.info(
                "Creating retriever with k=%d and filters: %s", k, filters
            )
        else:
            logger.info("Creating retriever with k=%d (no filters)", k)

        # Get the score threshold if configured
        if self._settings.retriever_score_threshold is not None:
            search_kwargs["score_threshold"] = self._settings.retriever_score_threshold
            search_type = "similarity_score_threshold"
            logger.info(
                "Score threshold set: %.4f",
                self._settings.retriever_score_threshold,
            )
        else:
            search_type = "similarity"

        vectorstore = self._chroma_service.get_vectorstore()

        retriever = vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

        logger.info(
            "✅ Retriever created: search_type=%s, k=%d",
            search_type,
            k,
        )

        return retriever
