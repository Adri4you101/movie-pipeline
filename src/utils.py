"""Shared parsing and sanitization helpers used by all providers."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Characters that trigger formula execution in spreadsheet applications (Excel, Google Sheets).
_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def sanitize_string(value: str) -> str:
    """Neutralise CSV/spreadsheet formula injection by prepending a single quote.

    If a string starts with a character that spreadsheet applications interpret as
    a formula prefix (=, +, -, @, tab, carriage return), a leading apostrophe is
    prepended. Excel and Google Sheets treat the apostrophe as a signal to render
    the cell as plain text rather than evaluating it as a formula.

    Args:
        value: The raw string read from a provider file.

    Returns:
        The original string, or the string prefixed with "'" if it started with
        a formula character.
    """
    if value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def normalize_title(title: str) -> str:
    """Return a lowercased, stripped version of a movie title for use as a merge key.

    Args:
        title: The raw title string from any provider.

    Returns:
        The title in lowercase with leading/trailing whitespace removed.
    """
    return title.strip().lower()


def parse_float(value, field_name: str, source: str) -> Optional[float]:
    """Convert a raw provider value to float, returning None on failure.

    Accepts strings, numbers, or any type that can be converted via str().
    Leading and trailing whitespace is stripped before conversion.

    Args:
        value: The raw value to parse. None is returned immediately if this is None.
        field_name: Name of the field being parsed, used in the warning log.
        source: Name of the provider or context, used in the warning log.

    Returns:
        The parsed float, or None if the value is None or cannot be converted.
    """
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        logger.warning("%s: cannot parse float for '%s': %r", source, field_name, value)
        return None


def parse_int(value, field_name: str, source: str) -> Optional[int]:
    """Convert a raw provider value to int, returning None on failure.

    Conversion goes through float first so that strings like "2010.0" are handled
    correctly (int("2010.0") raises ValueError, but int(float("2010.0")) does not).

    Args:
        value: The raw value to parse. None is returned immediately if this is None.
        field_name: Name of the field being parsed, used in the warning log.
        source: Name of the provider or context, used in the warning log.

    Returns:
        The parsed int (truncated, not rounded), or None if the value is None or
        cannot be converted.
    """
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        logger.warning("%s: cannot parse int for '%s': %r", source, field_name, value)
        return None
