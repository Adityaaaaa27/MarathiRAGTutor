"""Tests for Mistral LLM Service Module."""

import pytest
from unittest.mock import MagicMock, patch

from app.config.settings import Settings
from app.llm.mistral_service import MistralService


class TestMistralServiceInit:
    """Tests for MistralService initialization and validation."""

    def test_not_initialized_by_default(self):
        """Test that service starts uninitialized."""
        service = MistralService()
        assert service.is_initialized is False

    def test_get_llm_before_init_raises(self):
        """Test that accessing LLM before init raises RuntimeError."""
        service = MistralService()
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_llm()

    def test_invoke_before_init_raises(self):
        """Test that invoke before init raises RuntimeError."""
        service = MistralService()
        with pytest.raises(RuntimeError, match="not initialized"):
            service.invoke("test prompt")

    def test_missing_api_key_raises_value_error(self):
        """Test that missing API key raises ValueError on initialize."""
        settings = Settings(mistral_api_key="")
        service = MistralService(settings=settings)
        with pytest.raises(ValueError, match="missing or invalid"):
            service.initialize()

    def test_placeholder_api_key_raises_value_error(self):
        """Test that placeholder API key raises ValueError."""
        settings = Settings(mistral_api_key="your_mistral_api_key_here")
        service = MistralService(settings=settings)
        with pytest.raises(ValueError, match="missing or invalid"):
            service.initialize()

    def test_model_name_from_settings(self):
        """Test that model name comes from settings."""
        settings = Settings(mistral_model_name="mistral-small-latest")
        service = MistralService(settings=settings)
        assert service.model_name == "mistral-small-latest"

    @patch("app.llm.mistral_service.ChatMistralAI")
    def test_initialize_with_valid_key(self, mock_chat):
        """Test successful initialization with a valid API key."""
        mock_chat.return_value = MagicMock()
        settings = Settings(mistral_api_key="valid-test-key-12345")
        service = MistralService(settings=settings)
        service.initialize()

        assert service.is_initialized is True
        mock_chat.assert_called_once()

    @patch("app.llm.mistral_service.ChatMistralAI")
    def test_get_llm_after_init(self, mock_chat):
        """Test that get_llm returns the LLM after initialization."""
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        settings = Settings(mistral_api_key="valid-test-key-12345")
        service = MistralService(settings=settings)
        service.initialize()

        llm = service.get_llm()
        assert llm is mock_llm
