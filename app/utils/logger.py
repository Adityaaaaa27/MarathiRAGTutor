"""Centralized Logging Configuration.

Provides a factory function for creating module-specific loggers
with consistent formatting, file output, and Rich console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Module-level flag to ensure global setup runs only once
_logging_configured: bool = False
_log_file_path: Optional[Path] = None


def _setup_global_logging(log_dir: Path, log_level: str = "INFO") -> None:
    """Configure root logger with file and Rich console handlers.

    This function is idempotent — it only configures handlers on the
    first invocation. Subsequent calls are no-ops.

    Args:
        log_dir: Directory where log files will be stored.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    global _logging_configured, _log_file_path

    if _logging_configured:
        return

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    _log_file_path = log_dir / "app.log"

    # Parse level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Prevent duplicate handlers on re-import
    root_logger.handlers.clear()

    # --- File Handler ---
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(
        filename=str(_log_file_path),
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # --- Rich Console Handler ---
    console = Console(stderr=True, width=120)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        level=numeric_level,
    )
    root_logger.addHandler(rich_handler)

    # Suppress noisy third-party loggers
    for noisy_logger in ("httpx", "httpcore", "chromadb", "sentence_transformers", "urllib3"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, initializing global logging if needed.

    This is the ONLY entry point for obtaining loggers throughout the
    application. It lazily initializes global logging configuration
    on first call.

    Args:
        name: Logger name (typically ``__name__`` of the calling module).

    Returns:
        A configured ``logging.Logger`` instance.

    Example::

        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting PDF ingestion...")
    """
    if not _logging_configured:
        # Late import to avoid circular dependency at module load time
        from app.config.settings import get_settings

        settings = get_settings()
        _setup_global_logging(
            log_dir=settings.log_dir,
            log_level=settings.log_level,
        )

    return logging.getLogger(name)
