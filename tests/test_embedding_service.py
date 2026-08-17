"""Tests for Embedding Service Module.

Note: These tests require model downloads on first run.
Tests marked with @pytest.mark.slow can be skipped with:
    pytest -m "not slow"
"""

import pytest

from app.config.settings import Settings
from app.embeddings.embedding_service import EmbeddingService


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization (no model download)."""

    def test_not_initialized_by_default(self):
        """Test that service starts uninitialized."""
        service = EmbeddingService()
        assert service.is_initialized is False

    def test_get_embeddings_before_init_raises(self):
        """Test that accessing embeddings before init raises RuntimeError."""
        service = EmbeddingService()
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_embeddings()

    def test_embed_query_before_init_raises(self):
        """Test that embed_query before init raises RuntimeError."""
        service = EmbeddingService()
        with pytest.raises(RuntimeError, match="not initialized"):
            service.embed_query("test")

    def test_embed_documents_before_init_raises(self):
        """Test that embed_documents before init raises RuntimeError."""
        service = EmbeddingService()
        with pytest.raises(RuntimeError, match="not initialized"):
            service.embed_documents(["test"])

    def test_model_name_defaults_to_primary(self):
        """Test default model name matches configured model in settings."""
        service = EmbeddingService()
        assert service.model_name == service._settings.embedding_model_name


@pytest.mark.slow
class TestEmbeddingServiceWithModel:
    """Tests that require downloading an embedding model.

    These are marked 'slow' because model download can take minutes.
    Run with: pytest -m slow
    """

    @pytest.fixture(autouse=True)
    def setup_service(self):
        """Initialize the embedding service once for all tests in this class."""
        self.service = EmbeddingService()
        self.service.initialize()

    def test_is_initialized_after_init(self):
        """Test that service reports as initialized."""
        assert self.service.is_initialized is True

    def test_embed_query_returns_vector(self):
        """Test that embed_query returns a list of floats."""
        vector = self.service.embed_query("मराठी भाषा")
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)

    def test_embed_documents_returns_vectors(self):
        """Test that embed_documents returns a list of vectors."""
        texts = ["मराठी", "भाषा"]
        vectors = self.service.embed_documents(texts)
        assert len(vectors) == 2
        assert len(vectors[0]) == len(vectors[1])

    def test_get_embeddings_returns_instance(self):
        """Test that get_embeddings returns a HuggingFaceEmbeddings instance."""
        embeddings = self.service.get_embeddings()
        assert embeddings is not None
