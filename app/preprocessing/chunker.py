"""Text Chunking Module.

Splits cleaned textbook content into semantically meaningful chunks
using LangChain's RecursiveCharacterTextSplitter. Each chunk is
enriched with metadata for traceability and multi-standard expansion.
"""

import re
import uuid
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.constants import (
    DEFAULT_STANDARD,
    DEFAULT_SUBJECT,
    DEFAULT_TEXTBOOK_ID,
    MARATHI_CHAPTER_PATTERNS,
    META_CHAPTER,
    META_CHUNK_ID,
    META_PAGE_NUMBER,
    META_SOURCE,
    META_STANDARD,
    META_SUBJECT,
    META_TEXTBOOK_ID,
)
from app.config.settings import Settings, get_settings
from app.utils.helpers import marathi_to_arabic_numeral
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Splits cleaned text into metadata-enriched chunks.

    Uses ``RecursiveCharacterTextSplitter`` with Marathi-aware separators
    to preserve semantic coherence at paragraph and sentence boundaries.

    Each chunk includes metadata:
    - ``page_number``: Source page in the PDF.
    - ``chapter``: Detected chapter name (best-effort).
    - ``chunk_id``: Unique identifier for the chunk.
    - ``source``: Source filename.
    - ``textbook_id``: Identifier for multi-textbook support.
    - ``standard``: School standard/grade.
    - ``subject``: Subject name.

    Args:
        settings: Application settings. Injected for testability.
    """

    # Separators ordered from strongest to weakest boundary
    MARATHI_SEPARATORS: list[str] = [
        "\n\n",     # Paragraph break (strongest)
        "\n",       # Line break
        "।",        # Devanagari Danda (sentence end)
        "॥",        # Devanagari Double Danda
        ".",         # Full stop
        " ",         # Word boundary (weakest)
        "",          # Character-level fallback
    ]

    # ── Page to Chapter Mapping: Standard 6 (100 pages) ────────────────────────
    PAGE_CHAPTER_MAP_6: dict[int, str] = {
        1: "मुखपृष्ठ व प्रस्तावना",
        2: "मुखपृष्ठ व प्रस्तावना",
        3: "पाठ्यपुस्तक माहिती",
        4: "समिती व लेखक",
        5: "भारताचे संविधान",
        6: "प्रतिज्ञा व राष्ट्रगीत",
        7: "प्रस्तावना",
        8: "भाषाविषयक अध्ययन निष्पत्ती",
        9: "शिक्षक व पालकांसाठी सूचना",
        10: "अनुक्रमणिका",
        11: "१. या भारतात बंधुभाव (प्रार्थना) - राष्ट्रसंत श्री तुकडोजी महाराज",
        12: "२. चिमणीचं घरटं - अलका उमरणीकर",
        13: "२. चिमणीचं घरटं - अलका उमरणीकर",
        14: "२. चिमणीचं घरटं - अलका उमरणीकर",
        15: "२. चिमणीचं घरटं - अलका उमरणीकर",
        16: "२. चिमणीचं घरटं - अलका उमरणीकर",
        17: "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य",
        18: "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य",
        19: "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य",
        20: "चित्रवाचन",
        21: "चित्रवाचन",
        22: "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे",
        23: "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे",
        24: "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे",
        25: "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे",
        26: "५. आईचे पत्र",
        27: "५. आईचे पत्र",
        28: "५. आईचे पत्र",
        29: "५. आईचे पत्र",
        30: "५. आईचे पत्र",
        31: "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव",
        32: "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव",
        33: "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव",
        34: "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव",
        35: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        36: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        37: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        38: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        39: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        40: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        41: "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर",
        42: "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर",
        43: "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर",
        44: "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर",
        45: "९. निसर्गरम्य माथेरान - सुशील दुधाणे",
        46: "९. निसर्गरम्य माथेरान - सुशील दुधाणे",
        47: "९. निसर्गरम्य माथेरान - सुशील दुधाणे",
        48: "अनुभव लेखन",
        49: "अनुभव लेखन",
        50: "अनुभव लेखन",
        51: "१०. मी मोठा की लहान? - सुनंदा उमर्जी",
        52: "१०. मी मोठा की लहान? - सुनंदा उमर्जी",
        53: "१०. मी मोठा की लहान? - सुनंदा उमर्जी",
        54: "१०. मी मोठा की लहान? - सुनंदा उमर्जी",
        55: "१०. मी मोठा की लहान? - सुनंदा उमर्जी",
        56: "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत",
        57: "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत",
        58: "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत",
        59: "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत",
        60: "१२. जाहिरात",
        61: "१२. जाहिरात",
        62: "१२. जाहिरात",
        63: "१२. जाहिरात",
        64: "१२. जाहिरात",
        65: "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट",
        66: "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट",
        67: "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट",
        68: "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट",
        69: "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट",
        70: "१४. सुगी (कविता) - संतोष आळंजरकर",
        71: "१४. सुगी (कविता) - संतोष आळंजरकर",
        72: "१४. सुगी (कविता) - संतोष आळंजरकर",
        73: "१४. सुगी (कविता) - संतोष आळंजरकर",
        74: "१५. थोरांची ओळख - डॉ. ए. पी. जे. अब्दुल कलाम",
        75: "१५. थोरांची ओळख - लालबहादूर शास्त्री",
        76: "१६. मायबोली (कविता) - सुरेश भट",
        77: "१६. मायबोली (कविता) - सुरेश भट",
        78: "१६. मायबोली (कविता) - सुरेश भट",
        79: "१६. मायबोली (कविता) - सुरेश भट",
        80: "१६. मायबोली (कविता) - सुरेश भट",
        81: "१७. आपली संस्कृती, आपल्या परंपरा",
        82: "१७. आपली संस्कृती, आपल्या परंपरा",
        83: "१७. आपली संस्कृती, आपल्या परंपरा",
        84: "१७. आपली संस्कृती, आपल्या परंपरा",
        85: "१७. आपली संस्कृती, आपल्या परंपरा",
        86: "१७. आपली संस्कृती, आपल्या परंपरा",
        87: "१८. नव्या तू (कविता) - राजेंद्र आरेकर",
        88: "१८. नव्या तू (कविता) - राजेंद्र आरेकर",
        89: "१८. नव्या तू (कविता) - राजेंद्र आरेकर",
        90: "१८. नव्या तू (कविता) - राजेंद्र आरेकर",
        91: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        92: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        93: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        94: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        95: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        96: "१९. विभूतींची भंबेरी - प्र. के. अत्रे",
        97: "माझा अनुभव (अनुभव लेखन)",
        98: "२०. विचारधन",
        99: "२०. विचारधन",
        100: "२०. विचारधन",
    }

    # ── Page to Chapter Mapping: Standard 7 (66 pages) ────────────────────────
    PAGE_CHAPTER_MAP_7: dict[int, str] = {
        1: "मुखपृष्ठ व संविधान",
        2: "संविधान व प्रतिज्ञा",
        3: "ओळखा पाहू",
        4: "शासन निर्णय माहिती",
        5: "प्रथमावृत्ती",
        6: "भारताचे संविधान",
        7: "राष्ट्रगीत व प्रतिज्ञा",
        8: "प्रस्तावना",
        9: "भाषाविषयक अध्ययन निष्पत्ती",
        10: "शब्दकोशाचा वापर",
        11: "अनुक्रमणिका",
        12: "१. प्रार्थना - जगदीश खेबुडकर",
        13: "२. श्यामचे बंधुप्रेम - सानेगुरुजी",
        14: "२. श्यामचे बंधुप्रेम - सानेगुरुजी",
        15: "२. श्यामचे बंधुप्रेम - सानेगुरुजी",
        16: "२. श्यामचे बंधुप्रेम - सानेगुरुजी",
        17: "२. श्यामचे बंधुप्रेम - सानेगुरुजी (व्याकरण)",
        18: "३. माझ्या अंगणात (कविता) - ज्ञानेश्वर कोळी",
        19: "३. माझ्या अंगणात (कविता) - ज्ञानेश्वर कोळी",
        20: "३. माझ्या अंगणात (कविता) - ज्ञानेश्वर कोळी",
        21: "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम",
        22: "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम",
        23: "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम",
        24: "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम",
        25: "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम",
        26: "५. दादास पत्र",
        27: "५. दादास पत्र",
        28: "५. दादास पत्र (आम्ही सूचनाफलक वाचतो)",
        29: "६. टप् टप् पडती (कविता) - मंगेश पाडगावकर",
        30: "६. टप् टप् पडती (कविता) - मंगेश पाडगावकर",
        31: "६. टप् टप् पडती (कविता) - मंगेश पाडगावकर",
        32: "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार",
        33: "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार",
        34: "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार",
        35: "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार",
        36: "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार",
        37: "आपली समस्या आपले उपाय-१",
        38: "आम्ही जाहिरात वाचतो",
        39: "८. शब्दांचे घर (कविता) - कल्याण इनामदार",
        40: "८. शब्दांचे घर (कविता) - कल्याण इनामदार",
        41: "८. शब्दांचे घर (कविता) - कल्याण इनामदार",
        42: "९. वाचनाचे वेड - आशा पाटील",
        43: "९. वाचनाचे वेड - आशा पाटील",
        44: "९. वाचनाचे वेड - आशा पाटील",
        45: "९. वाचनाचे वेड - आशा पाटील",
        46: "आम्ही बातमी वाचतो",
        47: "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे",
        48: "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे",
        49: "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे",
        50: "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे",
        51: "११. लेख (कविता) - अस्मिता जोगदंडे-चांदणे",
        52: "११. लेख (कविता) - अस्मिता जोगदंडे-चांदणे",
        53: "११. लेख (कविता) - अस्मिता जोगदंडे-चांदणे",
        54: "आपली समस्या आपले उपाय-२",
        55: "१२. रोजनिशी",
        56: "१२. रोजनिशी",
        57: "१२. रोजनिशी",
        58: "१३. अदलाबदल - पन्नालाल पटेल",
        59: "१३. अदलाबदल - पन्नालाल पटेल",
        60: "१३. अदलाबदल - पन्नालाल पटेल",
        61: "१३. अदलाबदल - पन्नालाल पटेल",
        62: "१३. अदलाबदल - पन्नालाल पटेल",
        63: "१४. संतवाणी - संत जनाबाई, संत तुकाराम",
        64: "आम्ही कथा लिहितो",
        65: "पुस्तकांची माहिती",
        66: "पुस्तकांची माहिती व शेवटचे पृष्ठ",
    }

    # ── Page to Chapter Mapping: Standard 8 (58 pages) ────────────────────────
    PAGE_CHAPTER_MAP_8: dict[int, str] = {
        1: "मुखपृष्ठ व संविधान",
        2: "भारताचे संविधान",
        3: "मैत्री तंत्रज्ञानाशी",
        4: "शासन निर्णय माहिती",
        5: "प्रथमावृत्ती",
        6: "भारतीय संविधान",
        7: "राष्ट्रगीत व प्रतिज्ञा",
        8: "प्रस्तावना",
        9: "भाषाविषयक अध्ययन निष्पत्ती",
        10: "अध्ययन–अध्यापनाची प्रक्रिया",
        11: "अनुक्रमणिका",
        12: "१. भारत अमुचा देश (गीत) - शरद कांबळे",
        13: "२. चिव चिव चिमण्या - विजय तेंडुलकर",
        14: "२. चिव चिव चिमण्या - विजय तेंडुलकर",
        15: "२. चिव चिव चिमण्या - विजय तेंडुलकर",
        16: "पत्रलेखन",
        17: "पत्रलेखन",
        18: "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य",
        19: "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य",
        20: "४. सावलीतून जा आणि सावलीतून ये - सु. ह. जोशी",
        21: "४. सावलीतून जा आणि सावलीतून ये - सु. ह. जोशी",
        22: "४. सावलीतून जा आणि सावलीतून ये - सु. ह. जोशी",
        23: "लिहिते होऊया",
        24: "बातमी लेखन",
        25: "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग",
        26: "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग",
        27: "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग",
        28: "वाक्य म्हणजे काय",
        29: "६. कोळ्याची पोर (कविता) - सुरेखा गावडे",
        30: "६. कोळ्याची पोर (कविता) - सुरेखा गावडे",
        31: "खालील उतारा वाचा",
        32: "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे",
        33: "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे",
        34: "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे",
        35: "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे",
        36: "व्याकरण (केवलवाक्य)",
        37: "जाहिरात वाचन",
        38: "८. पाखरांचे मागणे (कविता) - प्रेमचंद अहिराव",
        39: "८. पाखरांचे मागणे (कविता) - प्रेमचंद अहिराव",
        40: "चर्चा करूया",
        41: "९. भूमिगत - मुमताज रहिमतपुरे",
        42: "९. भूमिगत - मुमताज रहिमतपुरे",
        43: "९. भूमिगत - मुमताज रहिमतपुरे",
        44: "सूचनाफलक तयार करणे",
        45: "सूचनाफलक तयार करणे",
        46: "१०. जीवन सुंदर करू! (कविता) - शं. ल. नाईक",
        47: "१०. जीवन सुंदर करू! (कविता) - शं. ल. नाईक",
        48: "१०. जीवन सुंदर करू! (कविता) - शं. ल. नाईक",
        49: "उतारा वाचन",
        50: "११. प्राणी आणि आपण - ललितगौरी डांगे",
        51: "११. प्राणी आणि आपण - ललितगौरी डांगे",
        52: "११. प्राणी आणि आपण - ललितगौरी डांगे",
        53: "१२. संतवाणी - संत एकनाथ, संत श्रीनिवासा",
        54: "१२. संतवाणी - संत एकनाथ, संत श्रीनिवासा",
        55: "संदर्भ ग्रंथ व पुस्तके",
        56: "सूचना फलक तयार करा",
        57: "साहित्य विक्री माहिती",
        58: "शेवटचे पृष्ठ",
    }

    _STD_CHAPTER_MAPS: dict[int, dict[int, str]] = {
        6: PAGE_CHAPTER_MAP_6,
        7: PAGE_CHAPTER_MAP_7,
        8: PAGE_CHAPTER_MAP_8,
    }

    PAGE_CHAPTER_MAP = PAGE_CHAPTER_MAP_6

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            separators=self.MARATHI_SEPARATORS,
            length_function=len,
            is_separator_regex=False,
            strip_whitespace=True,
        )

        # Compile chapter detection patterns
        self._chapter_patterns = [
            re.compile(p, re.UNICODE) for p in MARATHI_CHAPTER_PATTERNS
        ]

        # Track detected chapters for sequential assignment
        self._current_chapter: str = "unknown"

    def chunk_pages(
        self,
        pages: list[dict[str, str | int]],
        source_filename: str = "textbook.pdf",
        standard: int = 6,
        textbook_id: Optional[str] = None,
    ) -> list[Document]:
        """Split multiple pages into chunks with metadata.

        Args:
            pages: List of dicts with ``page_number`` and ``text`` keys.
            source_filename: Name of the source PDF file.
            standard: Grade/standard number (6, 7, etc.).
            textbook_id: Unique textbook identifier string.

        Returns:
            List of LangChain ``Document`` objects with enriched metadata.
        """
        all_chunks: list[Document] = []
        chunk_counter = 0
        effective_textbook_id = textbook_id or f"mh_state_board_marathi_std_{standard}"

        chapter_map = TextChunker._STD_CHAPTER_MAPS.get(standard, {})
        self._current_chapter = chapter_map.get(1, "प्रस्तावना")

        for page in pages:
            page_number = int(page["page_number"])
            text = str(page["text"])

            if page_number in chapter_map:
                self._current_chapter = chapter_map[page_number]
            else:
                detected_chapter = self._detect_chapter(text)
                if detected_chapter:
                    self._current_chapter = detected_chapter

            text_chunks = self._splitter.split_text(text)

            for chunk_text in text_chunks:
                chunk_counter += 1
                chunk_id = f"{effective_textbook_id}_p{page_number}_c{chunk_counter}"

                enriched_text = f"[इयत्ता {standard} वी | {self._current_chapter} | पृष्ठ: {page_number}]\n{chunk_text}"

                doc = Document(
                    page_content=enriched_text,
                    metadata={
                        META_PAGE_NUMBER: page_number,
                        META_CHAPTER: self._current_chapter,
                        META_CHUNK_ID: chunk_id,
                        META_SOURCE: source_filename,
                        META_TEXTBOOK_ID: effective_textbook_id,
                        META_STANDARD: int(standard),
                        META_SUBJECT: DEFAULT_SUBJECT,
                    },
                )
                all_chunks.append(doc)

        logger.info(
            "Chunking complete (Std %d): [cyan]%d chunks[/cyan] from [cyan]%d pages[/cyan]",
            standard,
            len(all_chunks),
            len(pages),
            extra={"markup": True},
        )

        return all_chunks

    def _detect_chapter(self, text: str) -> Optional[str]:
        """Detect chapter/lesson title from page content."""
        search_text = text[:500]

        for pattern in self._chapter_patterns:
            match = pattern.search(search_text)
            if match:
                groups = match.groups()
                chapter_parts = [marathi_to_arabic_numeral(g.strip()) for g in groups if g]
                chapter_name = " - ".join(chapter_parts)
                return chapter_name.strip()

        return None
