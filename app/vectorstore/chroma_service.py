"""ChromaDB Vector Store Service.

Provides a managed wrapper around ChromaDB for storing, searching,
and managing textbook document embeddings. All vector store operations
in the application go through this service.
"""

from typing import Any, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config.settings import Settings, get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.utils.helpers import timer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchResult:
    """Represents a single search result with score.

    Attributes:
        document: The retrieved LangChain Document.
        score: Similarity score (lower is more similar for L2 distance).
    """

    def __init__(self, document: Document, score: float) -> None:
        self.document = document
        self.score = score

    @property
    def page_content(self) -> str:
        """Shortcut to the document's text content."""
        return self.document.page_content

    @property
    def metadata(self) -> dict[str, Any]:
        """Shortcut to the document's metadata."""
        return self.document.metadata

    def __repr__(self) -> str:
        preview = self.page_content[:80].replace("\n", " ")
        return f"SearchResult(score={self.score:.4f}, preview='{preview}…')"


class ChromaService:
    """Managed ChromaDB vector store service.

    Wraps ``langchain_chroma.Chroma`` and provides standardized methods
    for CRUD operations on the vector store. Accepts an ``EmbeddingService``
    via dependency injection.

    Args:
        embedding_service: Initialized ``EmbeddingService`` instance.
        settings: Application settings. Injected for testability.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        settings: Optional[Settings] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._embedding_service = embedding_service
        self._vectorstore: Optional[Chroma] = None

    def reset_collection(self) -> None:
        """Reset or delete the existing collection to guarantee a fresh index."""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self._settings.chroma_persist_dir))
            try:
                client.delete_collection(self._settings.collection_name)
                logger.info("Deleted existing ChromaDB collection: %s", self._settings.collection_name)
            except Exception:
                pass
            self._vectorstore = None
        except Exception as exc:
            logger.warning("Could not reset ChromaDB collection: %s", exc)

    def create(self) -> Chroma:
        """Create or connect to a persistent ChromaDB collection.

        Returns:
            The ``Chroma`` vector store instance.
        """
        if self._vectorstore is not None:
            logger.debug("ChromaDB collection already created, reusing.")
            return self._vectorstore

        logger.info(
            "Creating ChromaDB collection: [bold]%s[/bold] at [cyan]%s[/cyan]",
            self._settings.collection_name,
            self._settings.chroma_persist_dir,
            extra={"markup": True},
        )

        self._vectorstore = Chroma(
            collection_name=self._settings.collection_name,
            embedding_function=self._embedding_service.get_embeddings(),
            persist_directory=str(self._settings.chroma_persist_dir),
        )

        logger.info("✅ ChromaDB collection ready")
        return self._vectorstore

    @timer
    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents with embeddings to the vector store.

        Args:
            documents: List of LangChain ``Document`` objects to store.

        Returns:
            List of document IDs assigned by ChromaDB.

        Raises:
            RuntimeError: If the collection has not been created.
        """
        store = self._ensure_store()

        logger.info(
            "Adding [cyan]%d documents[/cyan] to ChromaDB...",
            len(documents),
            extra={"markup": True},
        )

        ids = store.add_documents(documents)

        logger.info(
            "✅ Added [green]%d documents[/green] to ChromaDB",
            len(ids),
            extra={"markup": True},
        )
        return ids

    def search(
        self,
        query: str,
        k: Optional[int] = None,
        filter_dict: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Search for similar documents by query text.

        Args:
            query: Search query text.
            k: Number of results to return. Defaults to ``retriever_top_k``.
            filter_dict: Optional metadata filter (e.g., ``{"textbook_id": "..."}``)

        Returns:
            List of ``SearchResult`` objects sorted by relevance.

        Raises:
            RuntimeError: If the collection has not been created.
        """
        store = self._ensure_store()
        top_k = k or self._settings.retriever_top_k

        logger.debug("Searching ChromaDB: query='%s', k=%d, filters=%s", query[:50], top_k, filter_dict)

        kwargs: dict[str, Any] = {"k": top_k}
        if filter_dict:
            cleaned_filters = {k: v for k, v in filter_dict.items() if v is not None}
            if len(cleaned_filters) > 1:
                kwargs["filter"] = {"$and": [{k: v} for k, v in cleaned_filters.items()]}
            elif len(cleaned_filters) == 1:
                kwargs["filter"] = cleaned_filters

        results = store.similarity_search_with_score(query, **kwargs)

        search_results = [
            SearchResult(document=doc, score=score)
            for doc, score in results
        ]

        logger.info(
            "Search returned [cyan]%d results[/cyan]",
            len(search_results),
            extra={"markup": True},
        )

        return search_results

    def delete(self, ids: list[str]) -> None:
        """Delete documents from the vector store by ID.

        Args:
            ids: List of document IDs to delete.

        Raises:
            RuntimeError: If the collection has not been created.
        """
        store = self._ensure_store()
        collection = store._collection
        collection.delete(ids=ids)
        logger.info("Deleted %d documents from ChromaDB", len(ids))

    def reset(self) -> None:
        """Delete all documents from the current collection.

        Drops and recreates the collection, effectively clearing all data.

        Raises:
            RuntimeError: If the collection has not been created.
        """
        store = self._ensure_store()
        store.reset_collection()
        logger.warning("⚠️ ChromaDB collection reset — all documents deleted")

    def persist(self) -> None:
        """Persist vector store data to disk.

        Note: ChromaDB with persistent directory auto-persists,
        but this method is kept for explicit lifecycle management.
        """
        if self._vectorstore is not None:
            logger.info("ChromaDB data persisted to %s", self._settings.chroma_persist_dir)

    @property
    def document_count(self) -> int:
        """Return the number of documents currently in the collection."""
        if self._vectorstore is None:
            return 0
        try:
            collection = self._vectorstore._collection
            return collection.count()
        except Exception:
            return 0

    def get_vectorstore(self) -> Chroma:
        """Return the underlying Chroma instance.

        Returns:
            The ``Chroma`` vector store.

        Raises:
            RuntimeError: If the collection has not been created.
        """
        return self._ensure_store()

    def _ensure_store(self) -> Chroma:
        """Ensure the vector store has been created.

        Returns:
            The ``Chroma`` instance.

        Raises:
            RuntimeError: If ``create()`` has not been called.
        """
        if self._vectorstore is None:
            raise RuntimeError(
                "ChromaService not initialized. Call create() first."
            )
        return self._vectorstore
