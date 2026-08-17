"""Ingestion Service Orchestrator.

Coordinates the full ingestion pipeline:
PDF Load → Clean → Chunk → Embed → Store → Persist.
Returns structured statistics about the ingestion run.
"""

import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.config.settings import Settings, get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.pdf_loader import PDFLoader
from app.preprocessing.chunker import TextChunker
from app.preprocessing.cleaner import TextCleaner
from app.utils.helpers import format_elapsed
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)


class IngestionResult(BaseModel):
    """Statistics from a complete ingestion run.

    Attributes:
        source_file: Path to the ingested PDF.
        total_pages: Total pages in the PDF.
        extracted_pages: Pages with successfully extracted text.
        empty_pages: Pages with no content.
        failed_pages: Pages that failed extraction.
        total_chunks: Number of chunks created.
        documents_stored: Number of documents stored in vector DB.
        embedding_model: Name of the embedding model used.
        pdf_load_time: Time to load and extract PDF.
        cleaning_time: Time to clean text.
        chunking_time: Time to chunk text.
        embedding_store_time: Time to embed and store in ChromaDB.
        total_time: Total pipeline time.
    """

    source_file: str = Field(default="")
    total_pages: int = Field(default=0, ge=0)
    extracted_pages: int = Field(default=0, ge=0)
    empty_pages: int = Field(default=0, ge=0)
    failed_pages: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=0, ge=0)
    documents_stored: int = Field(default=0, ge=0)
    embedding_model: str = Field(default="")
    pdf_load_time: str = Field(default="")
    cleaning_time: str = Field(default="")
    chunking_time: str = Field(default="")
    embedding_store_time: str = Field(default="")
    total_time: str = Field(default="")


class IngestService:
    """Orchestrates the full textbook ingestion pipeline.

    Pipeline:
        1. Load PDF (PDFLoader)
        2. Clean text (TextCleaner)
        3. Chunk text (TextChunker)
        4. Initialize embeddings (EmbeddingService)
        5. Store in vector DB (ChromaService)
        6. Persist data

    All dependencies are injected for testability.

    Args:
        pdf_loader: PDF extraction service.
        text_cleaner: Text cleaning service.
        text_chunker: Text chunking service.
        embedding_service: Embedding model service.
        chroma_service: Vector store service.
        settings: Application settings.
    """

    def __init__(
        self,
        pdf_loader: PDFLoader,
        text_cleaner: TextCleaner,
        text_chunker: TextChunker,
        embedding_service: EmbeddingService,
        chroma_service: ChromaService,
        settings: Optional[Settings] = None,
    ) -> None:
        self._pdf_loader = pdf_loader
        self._text_cleaner = text_cleaner
        self._text_chunker = text_chunker
        self._embedding_service = embedding_service
        self._chroma_service = chroma_service
        self._settings = settings or get_settings()

    def run(self, pdf_path: Optional[Path] = None) -> IngestionResult:
        """Execute the full ingestion pipeline.

        Args:
            pdf_path: Path to the PDF. Defaults to settings value.

        Returns:
            ``IngestionResult`` with statistics from each pipeline stage.

        Raises:
            FileNotFoundError: If the PDF does not exist.
            RuntimeError: If any pipeline stage fails critically.
        """
        total_start = time.perf_counter()
        result = IngestionResult()

        # --- Stage 1: PDF Extraction ---
        logger.info("=" * 60)
        logger.info("Stage 1/5: PDF Extraction")
        logger.info("=" * 60)

        stage_start = time.perf_counter()
        extraction = self._pdf_loader.load(pdf_path)
        result.pdf_load_time = format_elapsed(time.perf_counter() - stage_start)

        result.source_file = extraction.source
        result.total_pages = extraction.total_pages
        result.extracted_pages = extraction.extracted_pages
        result.empty_pages = extraction.empty_pages
        result.failed_pages = extraction.failed_pages

        if result.extracted_pages == 0:
            raise RuntimeError(
                f"No text could be extracted from {extraction.source}. "
                "The PDF may be image-based (scanned) and requires OCR."
            )

        # Build page list for cleaning
        pages = [
            {"page_number": p.page_number, "text": p.text}
            for p in extraction.pages
            if not p.is_empty and not p.error
        ]

        # --- Stage 2: Text Cleaning ---
        logger.info("=" * 60)
        logger.info("Stage 2/5: Text Cleaning")
        logger.info("=" * 60)

        stage_start = time.perf_counter()
        cleaned_pages = self._text_cleaner.clean_pages(pages)
        result.cleaning_time = format_elapsed(time.perf_counter() - stage_start)

        if not cleaned_pages:
            raise RuntimeError("All pages were empty after cleaning.")

        # --- Stage 3: Text Chunking ---
        logger.info("=" * 60)
        logger.info("Stage 3/5: Text Chunking")
        logger.info("=" * 60)

        stage_start = time.perf_counter()
        source_filename = Path(extraction.source).name
        chunks = self._text_chunker.chunk_pages(cleaned_pages, source_filename)

        # Inject synthetic TOC/metadata chunks to ensure the system can
        # always answer "what topics are in the textbook?" even when the
        # PDF's front pages have font encoding issues.
        toc_chunks = self._build_synthetic_toc_chunks(source_filename)
        chunks.extend(toc_chunks)
        logger.info("Added %d synthetic TOC/metadata chunks", len(toc_chunks))

        result.chunking_time = format_elapsed(time.perf_counter() - stage_start)
        result.total_chunks = len(chunks)

        if not chunks:
            raise RuntimeError("No chunks were created from the cleaned text.")

        # --- Stage 4: Embedding Initialization ---
        logger.info("=" * 60)
        logger.info("Stage 4/5: Embedding Model Initialization")
        logger.info("=" * 60)

        if not self._embedding_service.is_initialized:
            self._embedding_service.initialize()
        result.embedding_model = self._embedding_service.model_name

        # --- Stage 5: Vector Store ---
        logger.info("=" * 60)
        logger.info("Stage 5/5: Vector Store Ingestion")
        logger.info("=" * 60)

        stage_start = time.perf_counter()
        self._chroma_service.reset_collection()
        self._chroma_service.create()
        ids = self._chroma_service.add_documents(chunks)
        self._chroma_service.persist()
        result.embedding_store_time = format_elapsed(time.perf_counter() - stage_start)
        result.documents_stored = len(ids)

        # --- Complete ---
        result.total_time = format_elapsed(time.perf_counter() - total_start)

        logger.info("=" * 60)
        logger.info("✅ Ingestion pipeline complete!")
        logger.info("=" * 60)

        return result

    @staticmethod
    def _build_synthetic_toc_chunks(source_filename: str) -> list:
        """Build synthetic Table of Contents chunks for the textbook.

        The Std 6 Marathi textbook PDF uses embedded fonts on its front
        pages (including the TOC / अनुक्रमणिका) that PyMuPDF cannot
        properly decode, producing garbled text. These synthetic chunks
        ensure the system can answer questions about the textbook's
        structure, topics, and chapters accurately.

        Args:
            source_filename: Name of the source PDF file.

        Returns:
            List of LangChain ``Document`` objects with TOC content.
        """
        from langchain_core.documents import Document
        from app.config.constants import (
            DEFAULT_TEXTBOOK_ID, DEFAULT_STANDARD, DEFAULT_SUBJECT,
            META_PAGE_NUMBER, META_CHAPTER, META_CHUNK_ID, META_SOURCE,
            META_TEXTBOOK_ID, META_STANDARD, META_SUBJECT,
        )

        toc_part1 = (
            "अनुक्रमणिका - इयत्ता सहावी मराठी पाठ्यपुस्तक (शिकू मराठी आनंदाने)\n\n"
            "भाग - १\n"
            "अ. क्र. पाठ/कविता - लेखक/कवी - पृष्ठ क्र.\n"
            "१. या भारतात बंधुभाव (प्रार्थना) - राष्ट्रसंत श्री तुकडोजी महाराज - पृष्ठ १\n"
            "२. चिमणीचं घरटं - अलका उमरणीकर - पृष्ठ २\n"
            "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य - पृष्ठ ७\n"
            "चित्रवाचन - पृष्ठ १०\n"
            "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे - पृष्ठ १२\n"
            "५. आईचे पत्र - पृष्ठ १६\n\n"
            "भाग - २\n"
            "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव - पृष्ठ २१\n"
            "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर - पृष्ठ २५\n"
            "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर - पृष्ठ ३२\n"
            "९. निसर्गरम्य माथेरान - सुशील दुधाणे - पृष्ठ ३५\n"
            "अनुभव लेखन - पृष्ठ ३८\n"
        )

        toc_part2 = (
            "अनुक्रमणिका (भाग ३ व ४) - इयत्ता सहावी मराठी पाठ्यपुस्तक\n\n"
            "भाग - ३\n"
            "बातमी आकलन - पृष्ठ ४०\n"
            "१०. मी मोठा की लहान? - सुनंदा उमर्जी - पृष्ठ ४२\n"
            "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत - पृष्ठ ४६\n"
            "१२. जाहिरात - पृष्ठ ५०\n"
            "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट - पृष्ठ ५५\n"
            "१४. सुगी (कविता) - संतोष आळंजरकर - पृष्ठ ६०\n\n"
            "भाग - ४\n"
            "१५. थोरांची ओळख:\n"
            "    (अ) डॉ. ए. पी. जे. अब्दुल कलाम - पृष्ठ ६४\n"
            "    (आ) लालबहादूर शास्त्री - जयसिंगराव राठोड - पृष्ठ ६५\n"
            "१६. मायबोली (कविता) - सुरेश भट - पृष्ठ ६६\n"
            "१७. आपली संस्कृती, आपल्या परंपरा - पृष्ठ ७१\n"
            "१८. नव्या तू (कविता) - राजेंद्र आरेकर - पृष्ठ ७७\n"
            "१९. विभूतींची भंबेरी - प्र. के. अत्रे - पृष्ठ ८१\n"
            "माझा अनुभव (अनुभव लेखन) - पृष्ठ ८७\n"
            "२०. विचारधन - पृष्ठ ८८\n"
        )

        toc_summary = (
            "या पाठ्यपुस्तकात (इयत्ता सहावी मराठी - शिकू मराठी आनंदाने) एकूण २० पाठ आणि कविता आहेत. "
            "यामध्ये प्रार्थना, कविता, कथा, पत्र, प्रवासवर्णन (निसर्गरम्य माथेरान), संवाद, जाहिरात, "
            "थोरांची ओळख आणि विचारधन यांचा समावेश आहे. "
            "पाठ्यपुस्तक चार भागांमध्ये (भाग १ ते ४) विभागलेले आहे. "
            "हे पाठ्यपुस्तक महाराष्ट्र राज्य पाठ्यपुस्तक निर्मिती व अभ्यासक्रम संशोधन मंडळ, पुणे यांनी प्रकाशित केले आहे."
        )

        base_meta = {
            META_SOURCE: source_filename,
            META_TEXTBOOK_ID: DEFAULT_TEXTBOOK_ID,
            META_STANDARD: DEFAULT_STANDARD,
            META_SUBJECT: DEFAULT_SUBJECT,
        }

        chunks = [
            Document(
                page_content=toc_part1,
                metadata={
                    **base_meta,
                    META_PAGE_NUMBER: 10,
                    META_CHAPTER: "अनुक्रमणिका (भाग १ व २)",
                    META_CHUNK_ID: f"{DEFAULT_TEXTBOOK_ID}_toc_part1",
                },
            ),
            Document(
                page_content=toc_part2,
                metadata={
                    **base_meta,
                    META_PAGE_NUMBER: 10,
                    META_CHAPTER: "अनुक्रमणिका (भाग ३ व ४)",
                    META_CHUNK_ID: f"{DEFAULT_TEXTBOOK_ID}_toc_part2",
                },
            ),
            Document(
                page_content=toc_summary,
                metadata={
                    **base_meta,
                    META_PAGE_NUMBER: 10,
                    META_CHAPTER: "अनुक्रमणिका - सारांश",
                    META_CHUNK_ID: f"{DEFAULT_TEXTBOOK_ID}_toc_summary",
                },
            ),
        ]

        return chunks

