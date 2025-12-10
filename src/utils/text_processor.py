import re
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Removes extra whitespace, newlines, and non-printable characters.
    Useful for cleaning user queries before embedding.
    """
    if not text:
        return ""

    # Replace multiple spaces/newlines with a single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate_text(text: str, max_chars: int = 1000) -> str:
    """
    Truncates text safely (e.g., for logging or context limits).
    """
    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


def format_currency(amount: float, currency: str = "AZN") -> str:
    """
    Standardizes price formatting for Course cards.
    """
    if amount is None:
        return "Pulsuz" if currency == "AZN" else "Free"
    return f"{amount:.2f} {currency}"
