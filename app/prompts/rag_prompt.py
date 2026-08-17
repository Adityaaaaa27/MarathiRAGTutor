"""RAG Prompt Engineering Module.

Defines the centralized prompt template that strictly instructs the LLM
to answer only from retrieved textbook context, cite page numbers,
explain in simple Marathi, and refuse to fabricate or guess.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config.constants import NOT_AVAILABLE_MESSAGE, NOT_AVAILABLE_MESSAGE_MARATHI
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """तुम्ही एक अनुभवी मराठी शिक्षक आहात. तुमचे काम विद्यार्थ्यांना महाराष्ट्र राज्य मंडळाच्या मराठी पाठ्यपुस्तकातून शिकवणे आहे.

## तुमचे नियम:

१. **फक्त पाठ्यपुस्तकातील माहिती वापरा**: तुम्हाला खालील "संदर्भ" (context) मध्ये दिलेली माहिती वापरूनच उत्तर द्या. कोणतीही बाहेरची माहिती वापरू नका.

२. **माहिती उपलब्ध नसल्यास**: जर दिलेल्या संदर्भात उत्तर सापडत नसेल, तर फक्त स्पष्टपणे सांगा:
   "{not_available_marathi}"
   कधीही अंदाज लावू नका किंवा खोटी माहिती देऊ नका.

३. **सोप्या मराठीत समजावून सांगा**: विद्यार्थ्यांना समजेल अशा सोप्या, स्पष्ट आणि शुद्ध मराठी भाषेत थेट उत्तर द्या.

४. **अतिरिक्त संदर्भ किंवा पृष्ठ क्रमांक लिहू नका**: उत्तरात कोणताही पृष्ठ क्रमांक (page number) किंवा संदर्भ (reference) असा उल्लेख करू नका. फक्त थेट आणि समर्पक उत्तर द्या.

---

## संदर्भ (Retrieved Context):

{context}

---

वरील संदर्भ वापरून विद्यार्थ्याच्या प्रश्नाचे थेट आणि स्पष्ट उत्तर द्या.""".format(
    not_available_marathi=NOT_AVAILABLE_MESSAGE_MARATHI,
    context="{context}",
)

HUMAN_TEMPLATE = """विद्यार्थ्याचा प्रश्न: {question}"""


class PromptService:
    """Provides the centralized RAG prompt template.

    This is the single source of truth for the LLM's behavioral
    instructions. The prompt enforces:
    - Textbook-only grounding
    - Mandatory page citations
    - Simple Marathi explanations
    - Explicit refusal when context is insufficient
    - No outside knowledge or fabrication
    """

    def __init__(self) -> None:
        self._prompt: ChatPromptTemplate = self._build_prompt()
        logger.info("✅ RAG prompt template initialized")

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the ChatPromptTemplate from system and human templates.

        Returns:
            Configured ``ChatPromptTemplate`` with ``context`` and
            ``question`` input variables.
        """
        return ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_TEMPLATE),
        ])

    def get_prompt(self) -> ChatPromptTemplate:
        """Return the RAG prompt template.

        Returns:
            The configured ``ChatPromptTemplate``.
        """
        return self._prompt

    def format_context(self, documents: list) -> str:
        """Format retrieved documents into a context string.

        Each document's content is prefixed with its page number
        for the LLM to reference in citations.

        Args:
            documents: List of LangChain ``Document`` objects.

        Returns:
            Formatted context string with page annotations.
        """
        if not documents:
            return "संदर्भ उपलब्ध नाही (No context available)."

        context_parts: list[str] = []
        for i, doc in enumerate(documents, 1):
            page_num = doc.metadata.get("page_number", "?")
            chapter = doc.metadata.get("chapter", "unknown")
            context_parts.append(
                f"[संदर्भ {i} | पृष्ठ: {page_num} | अध्याय: {chapter}]\n"
                f"{doc.page_content}"
            )

        return "\n\n---\n\n".join(context_parts)
