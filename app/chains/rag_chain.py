"""RAG Chain Module.

Builds the complete LCEL (LangChain Expression Language) pipeline:
Question → Retriever → Context → Prompt → Mistral → Parser.
Returns structured results with answer, retrieved chunks, metadata,
and similarity scores.
"""

import re
from typing import Any, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field

from app.llm.mistral_service import MistralService
from app.prompts.rag_prompt import PromptService
from app.retrieval.retriever import RetrieverService
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)


class RetrievedChunk(BaseModel):
    """Represents a single retrieved chunk in the query result.

    Attributes:
        content: The chunk text content.
        page_number: Source page in the textbook.
        chapter: Detected chapter name.
        chunk_id: Unique chunk identifier.
        score: Similarity score from vector search.
    """

    content: str = Field(..., description="Chunk text content")
    page_number: int = Field(default=0, description="Source page number")
    chapter: str = Field(default="unknown", description="Chapter name")
    chunk_id: str = Field(default="", description="Chunk identifier")
    score: float = Field(default=0.0, description="Similarity score")


class QueryResult(BaseModel):
    """Structured result from the RAG chain.

    Attributes:
        question: The original user question.
        answer: The generated answer from the LLM.
        retrieved_chunks: List of chunks used for context.
        page_numbers: Unique page numbers referenced.
        source: Textbook source identifier.
    """

    question: str = Field(..., description="Original user question")
    answer: str = Field(default="", description="Generated answer")
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list, description="Retrieved chunks with metadata"
    )
    page_numbers: list[int] = Field(
        default_factory=list, description="Referenced page numbers"
    )
    source: str = Field(default="", description="Textbook source identifier")


CHAPTER_KEYWORDS: dict[str, list[str]] = {
    # ─── Standard 6 ─────────────────────────────────────────────────────────────
    "१. या भारतात बंधुभाव (प्रार्थना) - राष्ट्रसंत श्री तुकडोजी महाराज": ["बंधुभाव", "तुकडोजी महाराज"],
    "२. चिमणीचं घरटं - अलका उमरणीकर": ["चिमणीचं घरटं", "चिमणी", "अलका उमरणीकर", "ईशा"],
    "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य": ["पाणीच पाणी", "शंकर वैद्य"],
    "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे": ["महाराष्ट्रकन्या", "पद्मा गोळे"],
    "५. आईचे पत्र": ["आईचे पत्र"],
    "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव": ["अमुचा बाग", "यशवंत देव"],
    "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर": ["तीन पुड्यांचा डबा", "आजोबांचा डबा", "अदिती देवधर", "स्टीलचा डबा"],
    "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर": ["नव्या युगाची गाणी", "वंदना विटणकर"],
    "९. निसर्गरम्य माथेरान - सुशील दुधाणे": ["माथेरान", "सुशील दुधाणे"],
    "१०. मी मोठा की लहान? - सुनंदा उमर्जी": ["मी मोठा की लहान", "सुनंदा उमर्जी"],
    "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत": ["गवतफुला", "इंदिरा संत"],
    "१२. जाहिरात": ["जाहिरात"],
    "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट": ["कूटप्रश्न", "रामानुजन", "दिवाकर बापट"],
    "१४. सुगी (कविता) - संतोष आळंजरकर": ["सुगी", "संतोष आळंजरकर"],
    "१५. थोरांची ओळख - डॉ. ए. पी. जे. अब्दुल कलाम": ["अब्दुल कलाम", "कलाम", "लालबहादूर शास्त्री", "शास्त्री"],
    "१६. मायबोली (कविता) - सुरेश भट": ["मायबोली", "सुरेश भट"],
    "१७. आपली संस्कृती, आपल्या परंपरा": ["आपली संस्कृती", "आपल्या परंपरा"],
    "१८. नव्या तू (कविता) - राजेंद्र आरेकर": ["नव्या तू", "राजेंद्र आरेकर"],
    "१९. विभूतींची भंबेरी - प्र. के. अत्रे": ["विभूतींची भंबेरी", "अत्रे", "प्र. के. अत्रे"],
    "२०. विचारधन": ["विचारधन"],

    # ─── Standard 7 ─────────────────────────────────────────────────────────────
    "१. प्रार्थना - जगदीश खेबुडकर": ["खेबुडकर", "प्रार्थना जगदीश"],
    "२. श्यामचे बंधुप्रेम - सानेगुरुजी": ["श्यामचे बंधुप्रेम", "श्यामाचे बंधुप्रेम", "सानेगुरुजी", "श्याम"],
    "३. माझ्या अंगणात (कविता) - ज्ञानेश्वर कोळी": ["माझ्या अंगणात", "ज्ञानेश्वर कोळी"],
    "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम": ["गोपाळाचे शौर्य", "लक्ष्मीकमल गेडाम", "लक्ष्मीकांत गेडाम", "गोपाळ"],
    "५. दादास पत्र": ["दादास पत्र", "दादाला पत्र"],
    "६. टप् टप् पडती (कविता) - मंगेश पाडगावकर": ["टप् टप् पडती", "मंगेश पाडगावकर"],
    "७. आजारी पडण्याचा प्रयोग - डॉ. मा. मिरासदार": ["आजारी पडण्याचा प्रयोग", "मिरासदार"],
    "८. शब्दांचे घर (कविता) - कल्याण इनामदार": ["शब्दांचे घर", "कल्याण इनामदार"],
    "९. वाचनाचे वेड - आशा पाटील": ["वाचनाचे वेड", "आशा पाटील", "अशा पाटील"],
    "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे": ["पंडिता रामाबाई", "रामाबाई", "अनुपमा उजगरे"],
    "११. लेख (कविता) - अस्मिता जोगदंडे-चांदणे": ["लेख कविता", "अस्मिता जोगदंडे"],
    "१२. रोजनिशी": ["रोजनिशी"],
    "१३. अदलाबदल - पन्नालाल पटेल": ["अदलाबदल", "पन्नालाल पटेल"],
    "१४. संतवाणी - संत जनाबाई, संत तुकाराम": ["संत जनाबाई", "संतवाणी सातवी"],

    # ─── Standard 8 ─────────────────────────────────────────────────────────────
    "१. भारत अमुचा देश (गीत) - शरद कांबळे": ["भारत अमुचा देश", "शरद कांबळे"],
    "२. चिव चिव चिमण्या - विजय तेंडुलकर": ["चिव चिव चिमण्या", "विजय तेंडुलकर", "तेंडुलकर"],
    "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य": ["पाणीच पाणी", "शंकर वैद्य"],
    "४. सावलीतून जा आणि सावलीतून ये - सु. ह. जोशी": ["सावलीतून जा", "सावलीतून ये", "जोशी सावली"],
    "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग": ["स्टीफन हॉकिंग", "हॉकिंग", "किशोर पवार"],
    "६. कोळ्याची पोर (कविता) - सुरेखा गावडे": ["कोळ्याची पोर", "सुरेखा गावडे"],
    "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे": ["ध्येयपूर्तीचा ध्यास", "लक्ष्मण लोंढे"],
    "८. पाखरांचे मागणे (कविता) - प्रेमचंद अहिराव": ["पाखरांचे मागणे", "प्रेमचंद अहिराव"],
    "९. भूमिगत - मुमताज रहिमतपुरे": ["भूमिगत", "मुमताज रहिमतपुरे"],
    "१०. जीवन सुंदर करू! (कविता) - शं. ल. नाईक": ["जीवन सुंदर करू", "नाईक जीवन"],
    "११. प्राणी आणि आपण - ललितगौरी डांगे": ["प्राणी आणि आपण", "ललितगौरी डांगे"],
    "१२. संतवाणी - संत एकनाथ, संत श्रीनिवासा": ["संत एकनाथ", "संत श्रीनिवासा", "श्रीनिलोबाराय"],

    # ─── Standard 9 ─────────────────────────────────────────────────────────────
    "१. सर्वात्मका शिवसुंदरा (प्रार्थना) - कुसुमाग्रज": ["सर्वात्मका शिवसुंदरा", "कुसुमाग्रज प्रार्थना"],
    "२. संतवाणी - भेटीलागी जीवा (संत तुकाराम), संतकृपा झाली (संत बहिणाबाई)": ["भेटीलागी जीवा", "संतकृपा झाली", "बहिणाबाई"],
    "३. 'बेटा, मी एकटो आहे!' - वि.पु. काळे": ["बेटा मी एकटो आहे", "एकटो आहे", "वि.पु. काळे", "विपु काळे"],
    "४. जि. आय. पी. रेल्वे - प्रबोधनकार ठाकरे": ["जि. आय. पी. रेल्वे", "जीआयपी रेल्वे", "प्रबोधनकार ठाकरे"],
    "५. रंग माझा वेगळा (कविता) - इंदिरा संत": ["रंग माझा वेगळा", "इंदिरा संत"],
    "६. त्याचे जगणे - मुक्ता": ["त्याचे जगणे", "मुक्ता जगणे"],
    "७. मनाचे श्लोक (कविता) - समर्थ रामदास": ["मनाचे श्लोक", "समर्थ रामदास"],
    "८. कुसुमाग्रज - महाकवी वि. वा. शिरवाडकर": ["कुसुमाग्रज शिरवाडकर", "विष्णू वामन शिरवाडकर"],
    "९. आभाळातल्या पाऊलवाटा - जयंत विद्वांस": ["आभाळातल्या पाऊलवाटा", "जयंत विद्वांस"],
    "१०. वीणा (कविता) - ना. धो. महानोर": ["वीणा कविता", "महानोर"],
    "११. 'वसुधैव कुटुंबकम्' - रमेश वरखेडे": ["वसुधैव कुटुंबकम्", "रमेश वरखेडे"],
    "१२. वाट पाहताना (कविता) - बा. सी. मर्ढेकर": ["वाट पाहताना", "मर्ढेकर"],
    "१३. दिव्याची ज्योत - सुधा मूर्ती": ["दिव्याची ज्योत", "सुधा मूर्ती"],
    "१४. ते जीवनदायी झाड - विनायक रानडे": ["ते जीवनदायी झाड", "जीवनदायी झाड", "विनायक रानडे"],
    "१५. माझे शिक्षक व संस्कार - रा. ना. चव्हाण": ["माझे शिक्षक व संस्कार", "चव्हाण शिक्षक"],
}


TOC_KEYWORDS: list[str] = [
    "अनुक्रमणिका", "विषयसूची", "विषय सूची", "सर्व पाठ", "सर्व कविता", "सर्व धडे",
    "धड्यांची यादी", "पाठांची यादी", "कवितांची यादी", "सर्व विषय", "कोणकोणते धडे",
    "कोणकोणते पाठ", "कोणत्या कविता", "१ ते २०", "१ ते 20", "1 ते 20", "1 to 20",
    "पुस्तकातील सर्व", "पाठ्यपुस्तकातील सर्व", "धडे आणि कविता", "पाठ आणि कविता",
    "table of contents", "chapters list", "all lessons", "all chapters", "all poems",
    "प्रकरणांची यादी", "सर्व धड्यांची", "सर्व पाठांची", "सर्व धडे", "सर्व कविता",
]


class RAGChain:
    """Production-grade RAG pipeline implementing LCEL with strict grounding."""

    def __init__(
        self,
        retriever_service: RetrieverService,
        prompt_service: PromptService,
        mistral_service: MistralService,
        chroma_service: ChromaService,
    ) -> None:
        self._retriever_service = retriever_service
        self._prompt_service = prompt_service
        self._mistral_service = mistral_service
        self._chroma_service = chroma_service

    def _is_toc_query(self, query: str) -> bool:
        """Check if query is asking for Table of Contents, list of chapters/lessons/poems."""
        cleaned = re.sub(r"[‘'“”\"’]", "", query).strip().lower()
        return any(kw in cleaned for kw in TOC_KEYWORDS)

    def _detect_chapter(self, query: str) -> Optional[str]:
        """Detect if the query specifically targets a known chapter."""
        if self._is_toc_query(query):
            return None
        cleaned_q = re.sub(r"[‘'“”\"’]", "", query)
        for chapter, keywords in CHAPTER_KEYWORDS.items():
            for kw in keywords:
                if kw in cleaned_q:
                    return chapter
        return None

    def invoke(
        self,
        question: str,
        standard: Optional[int | str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> QueryResult:
        """Execute the full RAG pipeline for a question.

        Args:
            question: User question in Marathi or English.
            standard: Grade/standard (6, 7, 8, 9, 10 or 'all'/None).
            filters: Optional metadata filters for retrieval.

        Returns:
            ``QueryResult`` with answer, chunks, metadata, and scores.
        """
        logger.info(
            "RAG chain invoked: [bold]%s[/bold] (Standard: %s)",
            question[:100],
            str(standard or "all"),
            extra={"markup": True},
        )

        cleaned_q = re.sub(r"[‘'“”\"’]", "", question)
        search_results = []

        # Parse standard filter
        std_filter = {}
        if standard is not None and str(standard).strip().lower() not in ("all", "0", ""):
            try:
                std_filter["standard"] = int(standard)
            except ValueError:
                pass

        # Case A: TOC / Overview query -> retrieve Table of Contents chunks
        if self._is_toc_query(cleaned_q):
            logger.info("Detected Table of Contents / Overview query")
            general_filter = dict(filters or {})
            if std_filter:
                general_filter.update(std_filter)

            toc_results = self._chroma_service.search(
                query="अनुक्रमणिका सर्व पाठ आणि कवितांची यादी सूची भाग १ भाग २",
                filter_dict=general_filter if general_filter else None,
            )
            p10_results = self._chroma_service.search(
                query="अनुक्रमणिका",
                filter_dict=general_filter if general_filter else None,
            )
            general_results = self._chroma_service.search(
                query=cleaned_q,
                filter_dict=general_filter if general_filter else None,
            )

            # Combine and deduplicate by chunk_id
            seen_ids = set()
            for r in (toc_results + p10_results + general_results):
                cid = r.document.metadata.get("chunk_id", r.document.page_content[:50])
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    search_results.append(r)

        # Case B: Specific Chapter query with hybrid standard fallback
        else:
            detected_chapter = self._detect_chapter(cleaned_q)
            chapter_results = []
            if detected_chapter:
                logger.info("Detected specific chapter filter: %s", detected_chapter)
                chapter_filter = dict(filters or {})
                if std_filter:
                    chapter_filter.update(std_filter)
                chapter_filter["chapter"] = detected_chapter
                chapter_results = self._chroma_service.search(
                    query=cleaned_q,
                    filter_dict=chapter_filter,
                )

            # Broad standard search (safety net against chapter boundary edge-cases)
            general_std_filter = dict(filters or {})
            if std_filter:
                general_std_filter.update(std_filter)

            general_results = self._chroma_service.search(
                query=cleaned_q,
                filter_dict=general_std_filter if general_std_filter else None,
            )

            # Combine: prioritize chapter-matched chunks first, then append semantic search chunks without duplicates
            seen_ids = set()
            for r in chapter_results:
                cid = r.document.metadata.get("chunk_id", r.document.page_content[:50])
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    search_results.append(r)

            for r in general_results:
                cid = r.document.metadata.get("chunk_id", r.document.page_content[:50])
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    search_results.append(r)

        # Step 2: Build retrieved chunks with metadata and scores
        retrieved_chunks: list[RetrievedChunk] = []
        documents: list[Document] = []

        for result in search_results:
            doc = result.document
            documents.append(doc)

            chunk = RetrievedChunk(
                content=doc.page_content,
                page_number=doc.metadata.get("page_number", 0),
                chapter=doc.metadata.get("chapter", "unknown"),
                chunk_id=doc.metadata.get("chunk_id", ""),
                score=result.score,
            )
            retrieved_chunks.append(chunk)

        # Step 3: Format context from documents
        context_str = self._prompt_service.format_context(documents)

        # Step 4: Build and invoke the LCEL chain
        prompt = self._prompt_service.get_prompt()
        llm = self._mistral_service.get_llm()
        parser = StrOutputParser()

        chain = prompt | llm | parser

        logger.debug("Invoking LLM with %d context chunks", len(documents))
        answer = chain.invoke({
            "context": context_str,
            "question": question,
        })

        # Step 5: Collect unique page numbers
        page_numbers = sorted(set(
            chunk.page_number for chunk in retrieved_chunks if chunk.page_number > 0
        ))

        # Build source identifier based on standard
        source_std = std_filter.get("standard", "all")
        source_id = (
            f"mh_state_board_marathi_std_{source_std}"
            if source_std != "all"
            else "mh_state_board_marathi_all"
        )

        result = QueryResult(
            question=question,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            page_numbers=page_numbers,
            source=source_id,
        )

        logger.info(
            "RAG chain complete: %d chunks, pages=%s",
            len(retrieved_chunks),
            page_numbers,
        )

        return result
