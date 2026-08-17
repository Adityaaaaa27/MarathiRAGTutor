"""Unit tests for TransliterationService.

Tests Roman script detection, Devanagari validation, zero-latency Devanagari bypass,
code-switching handling, and robust fallback behavior.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.preprocessing.transliteration_service import TransliterationService


class TestTransliterationServiceDetection:
    """Test character script detection helpers."""

    def test_contains_roman_or_english_true(self):
        """Should detect Latin/Roman letters."""
        assert TransliterationService.contains_roman_or_english("Matheran baddal") is True
        assert TransliterationService.contains_roman_or_english("What is the lesson?") is True
        assert TransliterationService.contains_roman_or_english("mla ya pathachi summary pahije") is True
        assert TransliterationService.contains_roman_or_english("chapter 3 madhye kay ahe?") is True
        assert TransliterationService.contains_roman_or_english("आजोबांचे letter") is True

    def test_contains_roman_or_english_false(self):
        """Should return False for pure Devanagari, numbers, and punctuation."""
        assert TransliterationService.contains_roman_or_english("माथेरानबद्दल काय माहिती दिली आहे?") is False
        assert TransliterationService.contains_roman_or_english("१ ते २० पर्यंतचे सर्व पाठ सांगा.") is False
        assert TransliterationService.contains_roman_or_english("श्यामचे बंधुप्रेम") is False
        assert TransliterationService.contains_roman_or_english("   ") is False

    def test_contains_devanagari(self):
        """Should detect presence of Devanagari unicode characters."""
        assert TransliterationService.contains_devanagari("माथेरान") is True
        assert TransliterationService.contains_devanagari("आजोबांचे letter") is True
        assert TransliterationService.contains_devanagari("Matheran") is False
        assert TransliterationService.contains_devanagari("12345?!") is False


class TestTransliterationServiceBypass:
    """Test zero-latency bypass for Devanagari queries."""

    def test_pure_devanagari_bypasses_llm(self):
        """Pure Devanagari text must not invoke LLM."""
        service = TransliterationService()
        service._llm = MagicMock()

        marathi_query = "माथेरान या पाठात काय सांगितले आहे?"
        result = service.transliterate_to_marathi(marathi_query)

        assert result == marathi_query
        service._llm.invoke.assert_not_called()

    def test_empty_or_whitespace_query(self):
        """Empty or whitespace queries return unchanged."""
        service = TransliterationService()
        service._llm = MagicMock()

        assert service.transliterate_to_marathi("") == ""
        assert service.transliterate_to_marathi("   ") == "   "
        service._llm.invoke.assert_not_called()


class TestTransliterationServiceConversion:
    """Test LLM invocation and clean output formatting."""

    def test_transliterates_romanized_marathi(self):
        """Should call LLM and return stripped Devanagari text."""
        service = TransliterationService()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ' "माथेरानबद्दल काय माहिती दिली आहे?" '
        mock_llm.invoke.return_value = mock_response

        service._llm = mock_llm
        service._initialized = True

        result = service.transliterate_to_marathi("Matheran baddal kay mahiti dili ahe?")
        assert result == "माथेरानबद्दल काय माहिती दिली आहे?"
        mock_llm.invoke.assert_called_once()

    def test_handles_accidental_markdown_or_quotes(self):
        """Should strip markdown formatting and quotes from LLM response."""
        service = TransliterationService()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "**पाठ ३ मध्ये काय आहे?**"
        mock_llm.invoke.return_value = mock_response

        service._llm = mock_llm
        service._initialized = True

        result = service.transliterate_to_marathi("chapter 3 madhye kay ahe?")
        assert result == "पाठ ३ मध्ये काय आहे?"

    def test_fallback_on_non_devanagari_output(self):
        """Should fallback gracefully if LLM returns output without Devanagari."""
        service = TransliterationService()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Sorry, I cannot answer."
        mock_llm.invoke.return_value = mock_response

        service._llm = mock_llm
        service._initialized = True

        query = "Matheran baddal kay mahiti dili ahe?"
        result = service.transliterate_to_marathi(query)
        assert result == query

    def test_fallback_on_exception(self):
        """Should return original query if an exception occurs during LLM call."""
        service = TransliterationService()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API connection timed out")

        service._llm = mock_llm
        service._initialized = True

        query = "What is the moral of the story?"
        result = service.transliterate_to_marathi(query)
        assert result == query
