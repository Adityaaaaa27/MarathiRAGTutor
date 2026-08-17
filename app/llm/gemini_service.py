"""Google Gemini LLM Service Module.

Provides a centralized wrapper around ChatGoogleGenerativeAI from
langchain-google-genai. Matches the BaseLLM service interface for plug-and-play
swapping between Mistral and Gemini.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiService:
    """Centralized Google Gemini LLM provider.

    Wraps ``ChatGoogleGenerativeAI`` and manages API key loading,
    model selection (e.g. gemini-1.5-flash, gemini-2.0-flash), and temperature.

    Args:
        settings: Application settings. Injected for testability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._llm: Optional[ChatGoogleGenerativeAI] = None

    def initialize(self) -> None:
        """Initialize the Gemini LLM client."""
        api_key = self._settings.gemini_api_key
        if not api_key or api_key.strip() == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key is missing or invalid. "
                "Set GEMINI_API_KEY in your .env file. "
                "Get a free key from: https://aistudio.google.com/app/apikey"
            )

        model_name = self._settings.gemini_model_name
        logger.info(
            "Initializing Gemini LLM: model=[bold]%s[/bold], temp=%.2f",
            model_name,
            self._settings.gemini_temperature,
            extra={"markup": True},
        )

        try:
            self._llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=self._settings.gemini_temperature,
                max_output_tokens=self._settings.gemini_max_tokens,
            )
            logger.info("✅ Google Gemini LLM initialized successfully (%s)", model_name)
        except Exception as exc:
            logger.error("Failed to initialize Gemini LLM: %s", exc)
            raise RuntimeError(f"Gemini LLM initialization failed: {exc}") from exc

    def get_llm(self) -> BaseChatModel:
        """Return the initialized ChatGoogleGenerativeAI instance."""
        if self._llm is None:
            raise RuntimeError("GeminiService not initialized. Call initialize() first.")
        return self._llm

    def invoke(self, prompt: str) -> str:
        """Send a prompt to the Gemini API and return the response."""
        llm = self.get_llm()
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            return str(response.content)
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise

    @property
    def is_initialized(self) -> bool:
        """Check if the LLM client is loaded and ready."""
        return self._llm is not None

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self._settings.gemini_model_name
