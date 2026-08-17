"""Utility Helper Functions.

Provides common utility functions used across multiple modules:
timing decorators, file validation, Unicode normalization, and
Marathi numeral conversion.
"""

import functools
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.utils.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def timer(func: F) -> F:
    """Decorator that logs the execution time of a function.

    Args:
        func: The function to time.

    Returns:
        Wrapped function that logs elapsed time at INFO level.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(
            "[bold cyan]⏱ %s[/bold cyan] completed in [green]%.2fs[/green]",
            func.__qualname__,
            elapsed,
            extra={"markup": True},
        )
        return result

    return wrapper  # type: ignore[return-value]


def validate_file_exists(file_path: Path | str) -> Path:
    """Validate that a file exists and is a regular file.

    Args:
        file_path: Path to validate (Path or str).

    Returns:
        Resolved absolute path.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If path is not a regular file.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    resolved = path_obj.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Path is not a regular file: {resolved}")
    return resolved


def validate_extension(file_path: Path | str, allowed: tuple[str, ...]) -> None:
    """Validate that a file has an allowed extension.

    Args:
        file_path: Path to check (Path or str).
        allowed: Tuple of allowed extensions (e.g., ``('.pdf',)``).

    Raises:
        ValueError: If file extension is not in the allowed set.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    if path_obj.suffix.lower() not in allowed:
        raise ValueError(
            f"Unsupported file extension '{path_obj.suffix}'. Allowed: {allowed}"
        )


def normalize_unicode(text: str) -> str:
    """Normalize Unicode text to NFC form.

    NFC (Canonical Decomposition followed by Canonical Composition)
    is the recommended normalization for Devanagari text, ensuring
    composed characters are used consistently.

    Args:
        text: Raw input string.

    Returns:
        NFC-normalized string.
    """
    return unicodedata.normalize("NFC", text)


def marathi_to_arabic_numeral(marathi_num: str) -> str:
    """Convert Devanagari numerals (०-९) to Arabic numerals (0-9).

    Args:
        marathi_num: String possibly containing Devanagari digits.

    Returns:
        String with Devanagari digits replaced by Arabic digits.

    Example::

        >>> marathi_to_arabic_numeral("पाठ ३")
        'पाठ 3'
    """
    devanagari_digits = "०१२३४५६७८९"
    translation_table = str.maketrans(devanagari_digits, "0123456789")
    return marathi_num.translate(translation_table)


def safe_resolve_path(base: Path, relative: str) -> Path:
    """Safely resolve a relative path against a base directory.

    Args:
        base: Base directory path.
        relative: Relative path string.

    Returns:
        Resolved absolute path.
    """
    return (base / relative).resolve()


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to a maximum length, appending ellipsis if needed.

    Args:
        text: Input text.
        max_length: Maximum character length.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "…"


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds into a human-readable string.

    Args:
        seconds: Elapsed time in seconds.

    Returns:
        Formatted string (e.g., '1.23s', '2m 15.4s').
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining = seconds % 60
    return f"{minutes}m {remaining:.1f}s"
