"""Tests for Retriever Service Module."""

import pytest
from unittest.mock import MagicMock, patch

from app.config.settings import Settings
from app.retrieval.retriever import RetrieverService


class TestRetrieverService:
    """Tests for the RetrieverService class."""

    def test_get_retriever_default_top_k(self):
        """Test retriever creation with default top-k."""
        mock_chroma = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.get_vectorstore.return_value = mock_vectorstore
        mock_vectorstore.as_retriever.return_value = MagicMock()

        settings = Settings(retriever_top_k=5)
        service = RetrieverService(chroma_service=mock_chroma, settings=settings)

        retriever = service.get_retriever()
        assert retriever is not None
        mock_vectorstore.as_retriever.assert_called_once()

        call_kwargs = mock_vectorstore.as_retriever.call_args
        assert call_kwargs.kwargs["search_kwargs"]["k"] == 5

    def test_get_retriever_custom_top_k(self):
        """Test retriever creation with custom top-k."""
        mock_chroma = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.get_vectorstore.return_value = mock_vectorstore
        mock_vectorstore.as_retriever.return_value = MagicMock()

        service = RetrieverService(chroma_service=mock_chroma)
        retriever = service.get_retriever(top_k=10)

        call_kwargs = mock_vectorstore.as_retriever.call_args
        assert call_kwargs.kwargs["search_kwargs"]["k"] == 10

    def test_get_retriever_with_filters(self):
        """Test retriever creation with metadata filters."""
        mock_chroma = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.get_vectorstore.return_value = mock_vectorstore
        mock_vectorstore.as_retriever.return_value = MagicMock()

        service = RetrieverService(chroma_service=mock_chroma)
        filters = {"textbook_id": "mh_state_board_marathi_std_6"}
        retriever = service.get_retriever(filters=filters)

        call_kwargs = mock_vectorstore.as_retriever.call_args
        assert call_kwargs.kwargs["search_kwargs"]["filter"] == filters

    def test_get_retriever_with_score_threshold(self):
        """Test retriever uses score threshold when configured."""
        mock_chroma = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.get_vectorstore.return_value = mock_vectorstore
        mock_vectorstore.as_retriever.return_value = MagicMock()

        settings = Settings(retriever_score_threshold=0.7)
        service = RetrieverService(chroma_service=mock_chroma, settings=settings)
        retriever = service.get_retriever()

        call_kwargs = mock_vectorstore.as_retriever.call_args
        assert call_kwargs.kwargs["search_type"] == "similarity_score_threshold"
        assert call_kwargs.kwargs["search_kwargs"]["score_threshold"] == 0.7
