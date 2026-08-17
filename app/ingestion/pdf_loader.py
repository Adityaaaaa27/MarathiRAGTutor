"""PDF Document Loader.

Extracts text content from Marathi PDF textbooks using PyMuPDF (fitz).
Returns structured page-wise content with metadata, handling corrupted
and empty pages gracefully.
"""

from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF
from pydantic import BaseModel, Field

from app.config.constants import SUPPORTED_EXTENSIONS
from app.config.settings import Settings, get_settings
from app.utils.helpers import timer, validate_extension, validate_file_exists
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PageContent(BaseModel):
    """Represents the extracted content from a single PDF page.

    Attributes:
        page_number: 1-indexed page number in the PDF.
        text: Raw extracted text content.
        char_count: Number of characters on the page.
        is_empty: True if the page yielded no meaningful text.
        error: Error message if extraction failed for this page.
    """

    page_number: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(default="", description="Raw extracted text content")
    char_count: int = Field(default=0, ge=0, description="Character count")
    is_empty: bool = Field(default=False, description="Whether page had no text")
    error: Optional[str] = Field(default=None, description="Extraction error if any")


class ExtractionResult(BaseModel):
    """Aggregated result of a full PDF extraction.

    Attributes:
        source: Path to the source PDF file.
        total_pages: Total number of pages in the document.
        extracted_pages: Number of pages with successfully extracted text.
        empty_pages: Number of pages with no meaningful content.
        failed_pages: Number of pages that failed during extraction.
        pages: List of all page contents.
    """

    source: str = Field(..., description="Source PDF file path")
    total_pages: int = Field(default=0, ge=0)
    extracted_pages: int = Field(default=0, ge=0)
    empty_pages: int = Field(default=0, ge=0)
    failed_pages: int = Field(default=0, ge=0)
    pages: list[PageContent] = Field(default_factory=list)


class PDFLoader:
    """Robust PDF text extractor for Marathi Devanagari textbooks.

    Uses PyMuPDF for high-fidelity Unicode text extraction.
    Handles corrupted pages, empty pages, and encoding issues gracefully.

    Args:
        settings: Application settings instance. Injected for testability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    @timer
    def load(self, pdf_path: Optional[Path] = None) -> ExtractionResult:
        """Extract text from all pages of a PDF file.

        Args:
            pdf_path: Path to the PDF. Defaults to ``settings.pdf_path``.

        Returns:
            ``ExtractionResult`` containing page-wise content and statistics.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If the file is not a supported format.
            RuntimeError: If the PDF cannot be opened at all.
        """
        path = pdf_path or self._settings.pdf_path
        path = validate_file_exists(path)
        validate_extension(path, SUPPORTED_EXTENSIONS)

        logger.info("Loading PDF: [bold]%s[/bold]", path.name, extra={"markup": True})

        result = ExtractionResult(source=str(path))

        try:
            doc = pymupdf.open(str(path))
        except Exception as exc:
            logger.error("Failed to open PDF '%s': %s", path.name, exc)
            raise RuntimeError(f"Cannot open PDF file: {path}") from exc

        result.total_pages = len(doc)
        logger.info("PDF contains [cyan]%d[/cyan] pages", result.total_pages, extra={"markup": True})

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page_content = self._extract_page(doc, page_idx, page_num)
            result.pages.append(page_content)

            if page_content.error:
                result.failed_pages += 1
            elif page_content.is_empty:
                result.empty_pages += 1
            else:
                result.extracted_pages += 1

        doc.close()

        logger.info(
            "Extraction complete: [green]%d extracted[/green], "
            "[yellow]%d empty[/yellow], [red]%d failed[/red] (of %d total)",
            result.extracted_pages,
            result.empty_pages,
            result.failed_pages,
            result.total_pages,
            extra={"markup": True},
        )

        return result

    def _extract_page(
        self, doc: pymupdf.Document, page_idx: int, page_num: int
    ) -> PageContent:
        """Extract text from a single PDF page.

        Args:
            doc: Open PyMuPDF document.
            page_idx: 0-indexed page index.
            page_num: 1-indexed page number.

        Returns:
            ``PageContent`` with extracted text or error details.
        """
        try:
            page = doc.load_page(page_idx)
            text = page.get_text("text")  # Plain text with Unicode

            # Strip and check for meaningful content
            text = text.strip()

            if not text or len(text) < 5:
                logger.debug("Page %d: empty or near-empty content", page_num)
                return PageContent(
                    page_number=page_num,
                    text="",
                    char_count=0,
                    is_empty=True,
                )

            logger.debug("Page %d: extracted %d characters", page_num, len(text))
            return PageContent(
                page_number=page_num,
                text=text,
                char_count=len(text),
                is_empty=False,
            )

        except Exception as exc:
            logger.warning("Page %d: extraction failed — %s", page_num, exc)
            return PageContent(
                page_number=page_num,
                text="",
                char_count=0,
                is_empty=True,
                error=str(exc),
            )
