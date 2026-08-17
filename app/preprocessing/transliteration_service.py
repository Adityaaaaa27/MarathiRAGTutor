"""Transliteration and Query Normalization Service.

Converts Romanized Marathi (Marathlish), English, and mixed Hindi/English/Marathi
queries into clean, standard Devanagari Marathi suitable for Maharashtra State Board
educational textbook RAG retrieval.
"""

import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI

from app.config.settings import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

TRANSLITERATION_SYSTEM_PROMPT = """तुम्ही महाराष्ट्र राज्य पाठ्यपुस्तक मंडळाच्या मराठी विषयासाठी भाषा रूपांतर तज्ञ आहात.
तुमचे एकमेव काम: खालील इनपुट मराठी देवनागरी लिपीत रूपांतरित करणे.

नियम:
1. इनपुट रोमन लिपीतील मराठी असेल (Marathlish) तर देवनागरीत रूपांतरित करा.
2. इनपुट हिंदी असेल तर मराठीत भाषांतर करा.
3. इनपुट इंग्रजी असेल तर मराठी देवनागरीत भाषांतर करा.
4. इनपुट हिंदी + मराठी + इंग्रजी मिश्रित असेल तर संपूर्ण वाक्य स्वच्छ मराठी देवनागरीत द्या.
5. chapter/lesson/patha यांचे रूपांतर "पाठ" असे करा.
6. फक्त देवनागरी मराठी आउटपुट द्या — कोणतेही स्पष्टीकरण नाही, कोणतेही इंग्रजी नाही, कोणतेही कोटेशन मार्क नाही, कोणतेही मार्कडाउन नाही.
7. प्रश्नाची रचना जशी आहे तशी ठेवा.
8. इयत्ता ६ ते १० च्या शालेय विद्यार्थ्यांना समजेल अशी सोपी पाठ्यपुस्तक मराठी वापरा.

उदाहरणे:
Input: "Matheran baddal kay mahiti dili ahe?"
Output: माथेरानबद्दल काय माहिती दिली आहे?
Input: "ya kaviteche nav kay ahe?"
Output: या कवितेचे नाव काय आहे?
Input: "What is the moral of the story?"
Output: या गोष्टीतून काय बोध मिळतो?
Input: "ajobanche patra"
Output: आजोबांचे पत्र
Input: "chapter 3 madhye kay ahe?"
Output: पाठ ३ मध्ये काय आहे?
Input: "mla ya pathachi summary pahije"
Output: मला या पाठाचा सारांश हवा आहे.
Input: "iska matlab kya hai?"
Output: याचा अर्थ काय आहे?
Input: "lesson 5 cha answer sang"
Output: पाठ ५ चे उत्तर सांगा.
Input: "grandfathers letter mhanje konata path?"
Output: आजोबांचे पत्र म्हणजे कोणता पाठ?
Input: "ya kavitet kavi kay sangto?"
Output: या कवितेत कवी काय सांगतो?
"""


class TransliterationService:
    """Service to transliterate Romanized Marathi and translate English queries to Marathi.

    Converts user input into clean Marathi Devanagari script for improved
    ChromaDB vector embedding alignment and chapter/TOC keyword matching.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._llm = None
        self._initialized = False

    @staticmethod
    def contains_roman_or_english(text: str) -> bool:
        """Check if the text contains any Latin/Roman alphabetic characters."""
        return bool(re.search(r"[a-zA-Z]", text))

    @staticmethod
    def contains_devanagari(text: str) -> bool:
        """Check if the text contains Devanagari script characters."""
        return bool(re.search(r"[\u0900-\u097F]", text))

    def initialize(self) -> None:
        """Initialize the lightweight fast LLM for transliteration."""
        try:
            # Check if Gemini or Mistral is configured
            if self._settings.llm_provider.lower() == "gemini" and self._settings.gemini_api_key:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._llm = ChatGoogleGenerativeAI(
                    model=self._settings.gemini_model_name,
                    google_api_key=self._settings.gemini_api_key,
                    temperature=0.0,
                    max_output_tokens=500,
                )
                logger.info("✅ TransliterationService initialized with Gemini")
            elif self._settings.mistral_api_key:
                self._llm = ChatMistralAI(
                    model="mistral-small-latest",
                    mistral_api_key=self._settings.mistral_api_key,
                    temperature=0.0,
                    max_tokens=500,
                )
                logger.info("✅ TransliterationService initialized with Mistral (small)")
            else:
                logger.warning("No API key available for TransliterationService.")

            self._initialized = True
        except Exception as exc:
            logger.error("Failed to initialize TransliterationService: %s", exc)
            self._initialized = False

    def transliterate_to_marathi(self, query: str) -> str:
        """Transliterate or translate the query into Devanagari Marathi.

        If the input is already pure Devanagari text, returns the query immediately
        with zero latency. If the input contains Roman/Latin letters, converts it.

        Args:
            query: User's input text (Marathlish, English, Hindi, or Marathi).

        Returns:
            Normalized Marathi query in Devanagari script.
        """
        if not query or not query.strip():
            return query

        stripped_query = query.strip()

        # 1. Zero-latency bypass if query is already Devanagari only
        if not self.contains_roman_or_english(stripped_query):
            return stripped_query

        # 2. If service is not initialized, attempt quick initialization
        if not self._initialized or self._llm is None:
            self.initialize()
            if self._llm is None:
                logger.warning("TransliterationService not ready; returning original query.")
                return stripped_query

        logger.info(
            "Transliterating Roman/English query: '%s'",
            stripped_query[:80],
        )

        # 3. Invoke LLM for transliteration / normalization
        try:
            messages = [
                SystemMessage(content=TRANSLITERATION_SYSTEM_PROMPT),
                HumanMessage(content=f'Input: "{stripped_query}"\nOutput:'),
            ]
            response = self._llm.invoke(messages)
            result = str(response.content).strip()

            # Clean any accidental quotes, backticks, or markdown artifacts
            result = re.sub(r"^[\"\'`*#]+|[\"\'`*#]+$", "", result).strip()
            result = re.sub(r"^Output:\s*", "", result, flags=re.IGNORECASE).strip()

            if self.contains_devanagari(result):
                logger.info(
                    "Transliterated: '%s' ➔ '%s'",
                    stripped_query[:50],
                    result[:50],
                )
                return result
            else:
                logger.warning(
                    "Transliteration did not yield Devanagari characters: '%s'",
                    result,
                )
                return self._simple_fallback(stripped_query)

        except Exception as exc:
            logger.error("Transliteration error for query '%s': %s", stripped_query, exc)
            return self._simple_fallback(stripped_query)

    def _simple_fallback(self, query: str) -> str:
        """Fallback when transliteration is unavailable or produces invalid output."""
        return query
