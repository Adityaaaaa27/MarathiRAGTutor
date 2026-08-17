"""Constants used across the Marathi RAG Tutor application.

Contains centralized string definitions, metadata schema keys,
refusal responses, Devanagari character ranges, and default values.
"""

from typing import Final

# Application Metadata
APP_NAME: Final[str] = "Marathi RAG Tutor"
APP_VERSION: Final[str] = "1.0.0"
APP_DESCRIPTION: Final[str] = (
    "A textbook-grounded educational RAG system for Maharashtra State Board Marathi (Std. 6 & 7)."
)

# Standard Grounding Refusal (Mandatory compliance)
NOT_AVAILABLE_MESSAGE: Final[str] = "This information is not available in the selected textbook."
NOT_AVAILABLE_MESSAGE_MARATHI: Final[str] = "ही माहिती निवडलेल्या पाठ्यपुस्तकात उपलब्ध नाही."

# Metadata Keys
META_PAGE_NUMBER: Final[str] = "page_number"
META_CHAPTER: Final[str] = "chapter"
META_CHUNK_ID: Final[str] = "chunk_id"
META_SOURCE: Final[str] = "source"
META_TEXTBOOK_ID: Final[str] = "textbook_id"
META_STANDARD: Final[str] = "standard"
META_SUBJECT: Final[str] = "subject"
META_TOTAL_PAGES: Final[str] = "total_pages"

# Default Textbook Metadata (designed for future multi-book expansion)
DEFAULT_TEXTBOOK_ID: Final[str] = "mh_state_board_marathi_std_6"
DEFAULT_STANDARD: Final[int] = 6
DEFAULT_SUBJECT: Final[str] = "Marathi"
DEFAULT_LANGUAGE: Final[str] = "mr"

# Devanagari & Marathi Unicode Character Sets
DEVANAGARI_DANDA: Final[str] = "\u0964"         # । (Purna Viram)
DEVANAGARI_DOUBLE_DANDA: Final[str] = "\u0965"  # ॥ (Deergha Viram)
DEVANAGARI_OM: Final[str] = "\u0950"            # ॐ

# Regex Patterns for Chapter Detection in Marathi Textbooks
MARATHI_CHAPTER_PATTERNS: Final[list[str]] = [
    r"(?:पाठ|धडा)\s*([०-९\d]+)\s*[:.\-–]?\s*([^\n]+)",
    r"(?:कविता)\s*([०-९\d]+)\s*[:.\-–]?\s*([^\n]+)",
    r"(?:स्थूलवाचन)\s*[:.\-–]?\s*([^\n]+)",
    r"^([०-९\d]+)\.\s*([^\n]+)",
]

# Supported Standards (6th to 10th)
AVAILABLE_STANDARDS: Final[dict[int, dict[str, str]]] = {
    6: {
        "name": "इयत्ता ६ वी",
        "title": "बालभारती (इयत्ता सहावी)",
        "pdf_filename": "6th.pdf",
        "cache_filename": "6th_ocr_cache.json",
        "textbook_id": "mh_state_board_marathi_std_6",
    },
    7: {
        "name": "इयत्ता ७ वी",
        "title": "बालभारती (इयत्ता सातवी)",
        "pdf_filename": "7th.pdf",
        "cache_filename": "7th_ocr_cache.json",
        "textbook_id": "mh_state_board_marathi_std_7",
    },
    8: {
        "name": "इयत्ता ८ वी",
        "title": "बालभारती (इयत्ता आठवी)",
        "pdf_filename": "8th.pdf",
        "cache_filename": "8th_ocr_cache.json",
        "textbook_id": "mh_state_board_marathi_std_8",
    },
}

# Supported File Formats
SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".pdf",)

# ChromaDB Collection Defaults (Unified Multi-Standard Store)
DEFAULT_COLLECTION_NAME: Final[str] = "marathi_textbooks_all"

# Model Defaults
PRIMARY_EMBEDDING_MODEL: Final[str] = "BAAI/bge-m3"
FALLBACK_EMBEDDING_MODEL: Final[str] = "intfloat/multilingual-e5-large"
DEFAULT_MISTRAL_MODEL: Final[str] = "mistral-large-latest"
