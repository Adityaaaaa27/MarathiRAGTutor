"""Query Service Orchestrator.

Provides a high-level interface for querying the RAG system.
Handles initialization of all required services and delegates
to the RAG chain for question answering.
"""

from typing import Any, Optional

from app.chains.rag_chain import QueryResult, RAGChain
from app.config.settings import Settings, get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.llm.mistral_service import MistralService
from app.prompts.rag_prompt import PromptService
from app.retrieval.retriever import RetrieverService
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)


class QueryService:
    """High-level query interface for the Marathi RAG tutor.

    Manages the lifecycle of all required services and provides
    a simple ``ask()`` method for question answering.

    Args:
        settings: Application settings. Injected for testability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._rag_chain: Optional[RAGChain] = None
        self._chroma_service: Optional[ChromaService] = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """Check whether all services have been initialized."""
        return self._initialized

    def initialize(self) -> None:
        """Initialize all required services for querying.

        Creates and wires together:
        - EmbeddingService
        - ChromaService
        - RetrieverService
        - MistralService
        - PromptService
        - RAGChain

        Raises:
            ValueError: If Mistral API key is missing.
            RuntimeError: If any service fails to initialize.
        """
        logger.info("Initializing query service...")

        # 1. Embedding service
        embedding_service = EmbeddingService(settings=self._settings)
        embedding_service.initialize()

        # 2. ChromaDB service (connect to existing store)
        self._chroma_service = ChromaService(
            embedding_service=embedding_service,
            settings=self._settings,
        )
        self._chroma_service.create()
        chroma_service = self._chroma_service

        # Verify documents exist
        doc_count = chroma_service.document_count
        if doc_count == 0:
            raise RuntimeError(
                "No documents found in ChromaDB. "
                "Run ingestion first: python -m app.cli.ingest"
            )
        logger.info(
            "ChromaDB contains [cyan]%d documents[/cyan]",
            doc_count,
            extra={"markup": True},
        )

        # 3. Retriever service
        retriever_service = RetrieverService(
            chroma_service=chroma_service,
            settings=self._settings,
        )

        # 4. LLM service (Gemini or Mistral based on settings.llm_provider)
        llm_service: Any
        if self._settings.llm_provider.lower() == "gemini":
            from app.llm.gemini_service import GeminiService
            llm_service = GeminiService(settings=self._settings)
            llm_service.initialize()
        else:
            mistral_service = MistralService(settings=self._settings)
            mistral_service.initialize()
            llm_service = mistral_service

        # 5. Prompt service
        prompt_service = PromptService()

        # 6. RAG chain
        self._rag_chain = RAGChain(
            retriever_service=retriever_service,
            prompt_service=prompt_service,
            mistral_service=llm_service,
            chroma_service=chroma_service,
        )

        self._initialized = True
        logger.info("✅ Query service initialized successfully")

    def ask(
        self,
        question: str,
        standard: Optional[int | str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> QueryResult:
        """Ask a question and get a textbook-grounded answer.

        Args:
            question: User question in Marathi or English.
            standard: Selected grade/standard (6, 7, 8, 9, 10, or 'all'/None).
            filters: Optional metadata filters for retrieval.

        Returns:
            ``QueryResult`` with answer, retrieved chunks, and metadata.

        Raises:
            RuntimeError: If the service has not been initialized.
            Exception: If the RAG pipeline fails.
        """
        if not self._initialized or self._rag_chain is None:
            raise RuntimeError(
                "QueryService not initialized. Call initialize() first."
            )

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        logger.info("Question received: %s (Standard: %s)", question[:100], standard or "all")

        try:
            result = self._rag_chain.invoke(
                question=question,
                standard=standard,
                filters=filters,
            )
            return result
        except Exception as exc:
            logger.error("Query failed: %s", exc)
            raise

    def get_standards_info(self) -> list[dict[str, Any]]:
        """Get summary info and chunk counts for all supported standards."""
        from app.config.constants import AVAILABLE_STANDARDS
        standards_list = []
        for std, info in AVAILABLE_STANDARDS.items():
            count = 0
            if self._initialized and self._chroma_service and self._chroma_service._vectorstore:
                try:
                    collection = self._chroma_service._vectorstore._collection
                    res = collection.get(where={"standard": std})
                    count = len(res["ids"]) if res and "ids" in res else 0
                except Exception as e:
                    logger.warning("Error getting count for standard %d: %s", std, e)
                    count = 0

            standards_list.append({
                "standard": std,
                "name": info["name"],
                "title": info["title"],
                "chunk_count": count,
                "is_indexed": count > 0,
            })
        return standards_list

    @property
    def is_initialized(self) -> bool:
        """Check if the query service is ready."""
        return self._initialized
