"""Mistral Vision OCR PDF Loader.

Replaces the legacy PyMuPDF text extractor for PDFs using non-Unicode fonts
(e.g. BalBharati01/02, Shree-Dev, APS, Akruti).

Each page is rendered as a high-resolution image and sent to Mistral pixtral-12b
for OCR. Results are cached in a JSON sidecar file so re-ingestion is fast.
"""

from __future__ import annotations

import base64
import io
import json
import time
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
    """Represents the extracted content from a single PDF page."""

    page_number: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(default="", description="Raw extracted text content")
    char_count: int = Field(default=0, ge=0, description="Character count")
    is_empty: bool = Field(default=False, description="Whether page had no text")
    error: Optional[str] = Field(default=None, description="Extraction error if any")


class ExtractionResult(BaseModel):
    """Aggregated result of a full PDF extraction."""

    source: str = Field(..., description="Source PDF file path")
    total_pages: int = Field(default=0, ge=0)
    extracted_pages: int = Field(default=0, ge=0)
    empty_pages: int = Field(default=0, ge=0)
    failed_pages: int = Field(default=0, ge=0)
    pages: list[PageContent] = Field(default_factory=list)


class PDFLoader:
    """Mistral pixtral Vision OCR PDF loader for legacy BalBharati-encoded Marathi PDFs.

    Renders each PDF page as a 300-DPI PNG and sends to Mistral pixtral-12b for
    accurate Marathi Devanagari OCR. Caches results to avoid re-processing.

    Args:
        settings: Application settings instance.
        standard: Grade/standard number (6, 7, 8, 9, 10).
        dpi: Render resolution (default 300 for clean OCR).
        use_cache: If True, save/load OCR results from a JSON sidecar file.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        standard: int = 6,
        dpi: int = 300,
        use_cache: bool = True,
    ) -> None:
        self._settings = settings or get_settings()
        self._standard = standard
        self._dpi = dpi
        self._use_cache = use_cache
        self._mistral_client = None

    @property
    def ocr_prompt(self) -> str:
        """Prompt instructing the model to extract Marathi text faithfully."""
        return (
            f"This is a page from a Maharashtra state Board Marathi textbook for Standard {self._standard}. "
            "Please extract ALL text from this image accurately in proper Marathi Devanagari Unicode. "
            "Preserve the original structure: headings, stanzas, paragraphs, numbered lists, author names, and footnotes. "
            "Do NOT translate. Do NOT summarize. Do NOT add explanations. Output ONLY the extracted Marathi text verbatim. "
            "If the page is completely blank, an image with no text, or a decorative cover, output exactly: [BLANK PAGE]"
        )

    def _get_mistral_client(self):
        """Lazily initialize Mistral client."""
        if self._mistral_client is not None:
            return self._mistral_client
        try:
            from mistralai import Mistral  # type: ignore
            import os
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("MISTRAL_API_KEY not set in .env")
            self._mistral_client = Mistral(api_key=api_key)
            logger.info("✅ Mistral Vision OCR client initialized (pixtral-12b)")
        except ImportError:
            raise RuntimeError("mistralai package not installed. Run: pip install mistralai")
        return self._mistral_client

    def _load_cache(self, cache_path: Path) -> dict[str, str]:
        """Load OCR cache from JSON file."""
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                logger.info("📦 Loaded OCR cache (%s): %d pages cached", cache_path.name, len(data))
                return data
            except Exception:
                logger.warning("Cache file corrupted, starting fresh")
        return {}

    def _save_cache(self, cache_path: Path, cache: dict[str, str]) -> None:
        """Save OCR cache to JSON file."""
        cache_path.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _render_page_as_png(self, page: pymupdf.Page) -> bytes:
        """Render a PDF page to a PNG bytes object at self._dpi."""
        mat = pymupdf.Matrix(self._dpi / 72, self._dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
        return pix.tobytes("png")

    def _ocr_page_with_mistral(self, png_bytes: bytes, page_num: int) -> str:
        """Send a page image to Mistral pixtral-12b for OCR."""
        client = self._get_mistral_client()
        b64 = base64.b64encode(png_bytes).decode()

        for attempt in range(5):
            try:
                response = client.chat.complete(
                    model="pixtral-12b-2409",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"},
                            },
                            {"type": "text", "text": self.ocr_prompt},
                        ],
                    }],
                )
                text = response.choices[0].message.content.strip()
                if text == "[BLANK PAGE]":
                    return ""
                return text
            except Exception as exc:
                if attempt < 4:
                    exc_str = str(exc)
                    if "429" in exc_str or "rate" in exc_str.lower():
                        wait = 5 * (2 ** attempt)
                    else:
                        wait = 2 ** attempt
                    logger.warning(
                        "Page %d OCR attempt %d failed: %s — retrying in %ds...",
                        page_num, attempt + 1, exc, wait,
                    )
                    time.sleep(wait)
                else:
                    raise

    @timer
    def load(
        self,
        pdf_path: Optional[Path] = None,
        cache_path: Optional[Path] = None,
    ) -> ExtractionResult:
        """Extract text from all pages of a PDF using Mistral Vision OCR in parallel.

        Args:
            pdf_path: Path to the PDF. Defaults to settings.pdf_path.
            cache_path: Optional path to the cache JSON file.

        Returns:
            ExtractionResult containing page-wise content and statistics.
        """
        import concurrent.futures
        import threading

        path = pdf_path or self._settings.pdf_path
        path = validate_file_exists(path)
        validate_extension(path, SUPPORTED_EXTENSIONS)

        logger.info("Loading PDF (Mistral Vision OCR): [bold]%s[/bold]", path.name, extra={"markup": True})

        # Cache file lives alongside the PDF by default
        effective_cache_path = cache_path or (path.parent / f"{path.stem}_ocr_cache.json")
        cache: dict[str, str] = {}
        if self._use_cache:
            cache = self._load_cache(effective_cache_path)

        result = ExtractionResult(source=str(path))

        try:
            doc = pymupdf.open(str(path))
        except Exception as exc:
            raise RuntimeError(f"Cannot open PDF file: {path}") from exc

        result.total_pages = len(doc)
        logger.info("PDF contains [cyan]%d[/cyan] pages", result.total_pages, extra={"markup": True})

        # Build list of pages needing OCR
        pages_to_ocr = []
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            if not self._use_cache or str(page_num) not in cache:
                try:
                    page = doc.load_page(page_idx)
                    png_bytes = self._render_page_as_png(page)
                    pages_to_ocr.append((page_num, png_bytes))
                except Exception as exc:
                    logger.warning("Failed to render page %d: %s", page_num, exc)

        # Run OCR in parallel for pages not in cache
        if pages_to_ocr:
            logger.info(
                "Std %d: Processing [bold cyan]%d pages[/bold cyan] in parallel via Mistral Vision OCR...",
                self._standard, len(pages_to_ocr), extra={"markup": True}
            )
            cache_lock = threading.Lock()
            
            def process_page(item):
                p_num, png_data = item
                try:
                    logger.info("Std %d | Starting Page %d/%d OCR...", self._standard, p_num, result.total_pages)
                    txt = self._ocr_page_with_mistral(png_data, p_num)
                    with cache_lock:
                        cache[str(p_num)] = txt
                        if self._use_cache:
                            self._save_cache(effective_cache_path, cache)
                    logger.info("Std %d | Finished Page %d/%d OCR ✅", self._standard, p_num, result.total_pages)
                except Exception as exc:
                    logger.warning("Std %d | Page %d OCR Failed ❌: %s", self._standard, p_num, exc)

            max_workers = 5  # Process up to 5 pages concurrently to respect rate limits
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Use list to consume the generator and block until all are complete
                list(executor.map(process_page, pages_to_ocr))

        # Re-assemble the results sequentially
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            cache_key = str(page_num)
            text = cache.get(cache_key, "")

            if not text or len(text.strip()) < 5:
                result.empty_pages += 1
                result.pages.append(PageContent(
                    page_number=page_num, text="", char_count=0, is_empty=True
                ))
            else:
                result.extracted_pages += 1
                result.pages.append(PageContent(
                    page_number=page_num,
                    text=text.strip(),
                    char_count=len(text),
                    is_empty=False,
                ))

        doc.close()

        logger.info(
            "OCR complete (Std %d): [green]%d extracted[/green], "
            "[yellow]%d empty[/yellow], [red]%d failed[/red] (of %d total)",
            self._standard,
            result.extracted_pages,
            result.empty_pages,
            result.failed_pages,
            result.total_pages,
            extra={"markup": True},
        )

        return result
