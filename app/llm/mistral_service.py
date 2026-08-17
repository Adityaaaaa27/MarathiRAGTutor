"""Mistral LLM Service Module.

Provides a centralized wrapper around ChatMistralAI. No other module
in the application should directly instantiate LangChain LLM classes —
all access goes through MistralService.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_mistralai import ChatMistralAI

from app.config.settings import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MistralService:
    """Centralized Mistral AI LLM provider.

    Wraps ``ChatMistralAI`` from ``langchain_mistralai`` and manages
    API key loading, model selection, and temperature configuration.

    All LLM interactions in the application go through this service.

    Args:
        settings: Application settings. Injected for testability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._llm: Optional[ChatMistralAI] = None

    def initialize(self) -> None:
        """Initialize the Mistral LLM client.

        Validates the API key and creates the ChatMistralAI instance.

        Raises:
            ValueError: If the Mistral API key is missing or invalid.
            RuntimeError: If the LLM client fails to initialize.
        """
        if not self._settings.validate_api_key():
            raise ValueError(
                "Mistral API key is missing or invalid. "
                "Set MISTRAL_API_KEY in your .env file. "
                "Get a key from: https://console.mistral.ai/"
            )

        logger.info(
            "Initializing Mistral LLM: model=[bold]%s[/bold], temp=%.2f",
            self._settings.mistral_model_name,
            self._settings.mistral_temperature,
            extra={"markup": True},
        )

        try:
            self._llm = ChatMistralAI(
                model=self._settings.mistral_model_name,
                mistral_api_key=self._settings.mistral_api_key,
                temperature=self._settings.mistral_temperature,
                max_tokens=self._settings.mistral_max_tokens,
                timeout=self._settings.mistral_timeout_seconds,
            )
            logger.info("✅ Mistral LLM initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize Mistral LLM: %s", exc)
            raise RuntimeError(
                f"Mistral LLM initialization failed: {exc}"
            ) from exc

    def get_llm(self) -> BaseChatModel:
        """Return the initialized ChatMistralAI instance.

        Returns:
            The active ``BaseChatModel`` instance.

        Raises:
            RuntimeError: If the service has not been initialized.
        """
        if self._llm is None:
            raise RuntimeError(
                "MistralService not initialized. Call initialize() first."
            )
        return self._llm

    def invoke(self, prompt: str) -> str:
        """Send a prompt to the Mistral API and return the response.

        This is a convenience method for simple single-turn invocations.
        For RAG chains, prefer using ``get_llm()`` within LCEL pipelines.

        Args:
            prompt: The prompt text to send.

        Returns:
            The model's response as a string.

        Raises:
            RuntimeError: If the service has not been initialized.
            Exception: If the API call fails (network, timeout, etc.).
        """
        llm = self.get_llm()

        logger.debug("Invoking Mistral with prompt length: %d chars", len(prompt))

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            result = str(response.content)
            logger.debug("Mistral response length: %d chars", len(result))
            return result
        except Exception as exc:
            logger.error("Mistral API call failed: %s", exc)
            raise

    @property
    def is_initialized(self) -> bool:
        """Check if the LLM client is loaded and ready."""
        return self._llm is not None

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self._settings.mistral_model_name
