"""Tests for Text Cleaner Module."""

import pytest

from app.preprocessing.cleaner import TextCleaner


class TestTextCleaner:
    """Tests for the TextCleaner class."""

    def setup_method(self):
        """Create a cleaner instance for each test."""
        self.cleaner = TextCleaner()

    def test_empty_string_returns_empty(self):
        """Test that empty input returns empty output."""
        assert self.cleaner.clean("") == ""
        assert self.cleaner.clean("   ") == ""
        assert self.cleaner.clean(None.__str__() if False else "") == ""

    def test_unicode_nfc_normalization(self):
        """Test that text is normalized to NFC form."""
        import unicodedata

        # Create a decomposed string
        decomposed = unicodedata.normalize("NFD", "मराठी")
        result = self.cleaner.clean(decomposed)
        # Result should be NFC-normalized
        assert unicodedata.is_normalized("NFC", result)

    def test_marathi_punctuation_preserved(self):
        """Test that Marathi Danda and Double Danda are preserved."""
        text = "हे एक वाक्य आहे। दुसरे वाक्य॥"
        result = self.cleaner.clean(text)
        assert "।" in result or "." in result  # Danda preserved or converted
        assert "॥" in result  # Double Danda preserved

    def test_page_number_removal(self):
        """Test that standalone page numbers are removed."""
        text = "काही मजकूर\n42\nआणखी मजकूर"
        result = self.cleaner.clean(text)
        assert "42" not in result.split("\n")

    def test_devanagari_page_number_removal(self):
        """Test that Devanagari page numbers are removed."""
        text = "काही मजकूर\n४२\nआणखी मजकूर"
        result = self.cleaner.clean(text)
        # Standalone Devanagari number line should be removed
        lines = [l.strip() for l in result.split("\n") if l.strip()]
        assert "४२" not in lines

    def test_whitespace_normalization(self):
        """Test that excessive whitespace is collapsed."""
        text = "मराठी    भाषा     शिकणे"
        result = self.cleaner.clean(text)
        assert "    " not in result  # No quadruple spaces

    def test_multiple_newlines_collapsed(self):
        """Test that 3+ newlines collapse to double newlines."""
        text = "पहिला परिच्छेद\n\n\n\n\nदुसरा परिच्छेद"
        result = self.cleaner.clean(text)
        assert "\n\n\n" not in result

    def test_clean_pages_removes_empty(self):
        """Test that clean_pages removes pages that become empty after cleaning."""
        pages = [
            {"page_number": 1, "text": "मराठी मजकूर"},
            {"page_number": 2, "text": "   "},  # Will become empty
            {"page_number": 3, "text": "आणखी मजकूर"},
        ]
        result = self.cleaner.clean_pages(pages)
        assert len(result) == 2
        assert result[0]["page_number"] == 1
        assert result[1]["page_number"] == 3

    def test_clean_preserves_meaningful_content(self):
        """Test that meaningful Marathi content is preserved."""
        text = "महाराष्ट्र राज्य मंडळाचे मराठी पाठ्यपुस्तक सहावी इयत्तेसाठी तयार केले आहे."
        result = self.cleaner.clean(text)
        assert "पाठ्यपुस्तक" in result
        assert "सहावी" in result
