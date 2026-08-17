"""Tests for PDF Loader Module."""

import tempfile
from pathlib import Path

import pytest

from app.ingestion.pdf_loader import ExtractionResult, PDFLoader, PageContent


class TestPageContent:
    """Tests for the PageContent Pydantic model."""

    def test_valid_page_content(self):
        """Test creating a valid PageContent instance."""
        page = PageContent(page_number=1, text="मराठी मजकूर", char_count=12)
        assert page.page_number == 1
        assert page.text == "मराठी मजकूर"
        assert page.char_count == 12
        assert page.is_empty is False
        assert page.error is None

    def test_empty_page_content(self):
        """Test creating an empty page."""
        page = PageContent(page_number=5, text="", char_count=0, is_empty=True)
        assert page.is_empty is True

    def test_error_page_content(self):
        """Test creating a page with an error."""
        page = PageContent(
            page_number=3, text="", char_count=0, is_empty=True, error="Corrupted"
        )
        assert page.error == "Corrupted"

    def test_page_number_must_be_positive(self):
        """Test that page_number must be >= 1."""
        with pytest.raises(Exception):
            PageContent(page_number=0, text="test")


class TestExtractionResult:
    """Tests for the ExtractionResult model."""

    def test_default_extraction_result(self):
        """Test default values of ExtractionResult."""
        result = ExtractionResult(source="test.pdf")
        assert result.total_pages == 0
        assert result.extracted_pages == 0
        assert result.empty_pages == 0
        assert result.failed_pages == 0
        assert result.pages == []

    def test_extraction_result_with_pages(self):
        """Test ExtractionResult with page data."""
        pages = [
            PageContent(page_number=1, text="Content", char_count=7),
            PageContent(page_number=2, text="", char_count=0, is_empty=True),
        ]
        result = ExtractionResult(
            source="test.pdf",
            total_pages=2,
            extracted_pages=1,
            empty_pages=1,
            pages=pages,
        )
        assert len(result.pages) == 2
        assert result.extracted_pages == 1


class TestPDFLoader:
    """Tests for the PDFLoader class."""

    def test_missing_file_raises_error(self):
        """Test that loading a non-existent file raises FileNotFoundError."""
        loader = PDFLoader()
        with pytest.raises(FileNotFoundError):
            loader.load(Path("/nonexistent/file.pdf"))

    def test_unsupported_extension_raises_error(self, tmp_path):
        """Test that a non-PDF file raises ValueError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        loader = PDFLoader()
        with pytest.raises(ValueError, match="Unsupported file extension"):
            loader.load(txt_file)

    def test_load_valid_pdf(self, tmp_path):
        """Test loading a valid (minimal) PDF file."""
        # Create a minimal PDF using PyMuPDF
        import pymupdf

        pdf_path = tmp_path / "test.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "मराठी पाठ्यपुस्तक", fontname="helv", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        loader = PDFLoader()
        result = loader.load(pdf_path)

        assert result.total_pages == 1
        assert result.source == str(pdf_path)
        assert len(result.pages) == 1
