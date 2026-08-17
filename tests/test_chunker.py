"""Tests for Text Chunker Module."""

import pytest

from app.preprocessing.chunker import TextChunker


class TestTextChunker:
    """Tests for the TextChunker class."""

    def setup_method(self):
        """Create a chunker instance for each test."""
        self.chunker = TextChunker()

    def test_single_page_chunking(self):
        """Test chunking a single page of content."""
        pages = [
            {
                "page_number": 1,
                "text": "मराठी भाषा ही एक इंडो-आर्य भाषा आहे. " * 50,
            }
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        assert len(chunks) > 0

    def test_chunk_metadata_present(self):
        """Test that each chunk contains required metadata keys."""
        pages = [
            {
                "page_number": 5,
                "text": "काही मजकूर येथे आहे. " * 30,
            }
        ]
        chunks = self.chunker.chunk_pages(pages, "textbook.pdf")

        required_keys = [
            "page_number", "chapter", "chunk_id",
            "source", "textbook_id", "standard", "subject",
        ]
        for chunk in chunks:
            for key in required_keys:
                assert key in chunk.metadata, f"Missing metadata key: {key}"

    def test_page_number_in_metadata(self):
        """Test that page_number is correctly assigned."""
        pages = [
            {"page_number": 10, "text": "मजकूर " * 100},
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        for chunk in chunks:
            assert chunk.metadata["page_number"] == 10

    def test_source_in_metadata(self):
        """Test that source filename is set correctly."""
        pages = [
            {"page_number": 1, "text": "मजकूर " * 100},
        ]
        chunks = self.chunker.chunk_pages(pages, "my_textbook.pdf")
        for chunk in chunks:
            assert chunk.metadata["source"] == "my_textbook.pdf"

    def test_multiple_pages_chunking(self):
        """Test chunking across multiple pages."""
        pages = [
            {"page_number": i, "text": f"पृष्ठ {i} मजकूर. " * 40}
            for i in range(1, 4)
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        assert len(chunks) > 3  # Should produce multiple chunks

    def test_empty_pages_produce_no_chunks(self):
        """Test that empty pages don't produce chunks."""
        pages = [
            {"page_number": 1, "text": ""},
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        assert len(chunks) == 0

    def test_chapter_detection(self):
        """Test that Marathi chapter headings are detected."""
        pages = [
            {
                "page_number": 1,
                "text": "पाठ ३ : आजोबांचे पत्र\nहा पाठ खूप छान आहे. " * 30,
            }
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        # At least one chunk should have a detected chapter
        chapters = [c.metadata["chapter"] for c in chunks]
        assert any(ch != "unknown" for ch in chapters)

    def test_chunk_id_uniqueness(self):
        """Test that every chunk has a unique chunk_id."""
        pages = [
            {"page_number": i, "text": "मजकूर " * 100}
            for i in range(1, 5)
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        chunk_ids = [c.metadata["chunk_id"] for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_textbook_id_and_standard_present(self):
        """Test future-ready metadata fields are populated."""
        pages = [
            {"page_number": 1, "text": "मजकूर " * 100},
        ]
        chunks = self.chunker.chunk_pages(pages, "test.pdf")
        for chunk in chunks:
            assert chunk.metadata["textbook_id"] == "mh_state_board_marathi_std_6"
            assert chunk.metadata["standard"] == 6
            assert chunk.metadata["subject"] == "Marathi"
