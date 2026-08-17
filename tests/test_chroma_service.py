"""Tests for ChromaDB Service Module.

Uses a temporary directory for ChromaDB storage to avoid
polluting the main data store.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from langchain_core.documents import Document

from app.config.settings import Settings
from app.vectorstore.chroma_service import ChromaService, SearchResult


class TestSearchResult:
    """Tests for the SearchResult class."""

    def test_search_result_properties(self):
        """Test SearchResult convenience properties."""
        doc = Document(
            page_content="मराठी मजकूर",
            metadata={"page_number": 1, "chapter": "unknown"},
        )
        result = SearchResult(document=doc, score=0.85)
        assert result.page_content == "मराठी मजकूर"
        assert result.metadata["page_number"] == 1
        assert result.score == 0.85

    def test_search_result_repr(self):
        """Test SearchResult string representation."""
        doc = Document(page_content="Short text", metadata={})
        result = SearchResult(document=doc, score=0.5)
        repr_str = repr(result)
        assert "0.5000" in repr_str


class TestChromaServiceInit:
    """Tests for ChromaService initialization (no embedding model required)."""

    def test_not_initialized_by_default(self):
        """Test that the store is not created on init."""
        mock_embedding = MagicMock()
        service = ChromaService(embedding_service=mock_embedding)
        assert service.document_count == 0

    def test_ensure_store_raises_before_create(self):
        """Test that operations before create() raise RuntimeError."""
        mock_embedding = MagicMock()
        service = ChromaService(embedding_service=mock_embedding)
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_vectorstore()

    def test_add_documents_before_create_raises(self):
        """Test that add_documents before create() raises RuntimeError."""
        mock_embedding = MagicMock()
        service = ChromaService(embedding_service=mock_embedding)
        with pytest.raises(RuntimeError, match="not initialized"):
            service.add_documents([])

    def test_search_before_create_raises(self):
        """Test that search before create() raises RuntimeError."""
        mock_embedding = MagicMock()
        service = ChromaService(embedding_service=mock_embedding)
        with pytest.raises(RuntimeError, match="not initialized"):
            service.search("test query")


@pytest.mark.slow
class TestChromaServiceWithStore:
    """Integration tests for ChromaService with a real vector store.

    These tests require an embedding model and are marked 'slow'.
    """

    @pytest.fixture
    def chroma_service(self, tmp_path):
        """Create a ChromaService with temporary storage."""
        from app.embeddings.embedding_service import EmbeddingService

        settings = Settings(
            chroma_persist_dir=tmp_path / "chroma_test",
            collection_name="test_collection",
        )

        embedding_service = EmbeddingService(settings=settings)
        embedding_service.initialize()

        service = ChromaService(
            embedding_service=embedding_service,
            settings=settings,
        )
        service.create()
        return service

    def test_create_returns_store(self, chroma_service):
        """Test that create() returns a Chroma instance."""
        store = chroma_service.get_vectorstore()
        assert store is not None

    def test_add_and_search(self, chroma_service):
        """Test adding documents and searching."""
        docs = [
            Document(
                page_content="मराठी भाषा ही सुंदर आहे.",
                metadata={"page_number": 1, "chapter": "intro"},
            ),
            Document(
                page_content="गणित विषय कठीण आहे.",
                metadata={"page_number": 2, "chapter": "math"},
            ),
        ]
        ids = chroma_service.add_documents(docs)
        assert len(ids) == 2

        results = chroma_service.search("मराठी भाषा", k=1)
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)

    def test_reset_clears_store(self, chroma_service):
        """Test that reset clears all documents."""
        docs = [
            Document(page_content="test content", metadata={"page_number": 1}),
        ]
        chroma_service.add_documents(docs)
        assert chroma_service.document_count >= 1

        chroma_service.reset()
        assert chroma_service.document_count == 0
