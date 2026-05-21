import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Characters that trigger formula execution in spreadsheet applications (Excel, Google Sheets).
_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def sanitize_string(value: str) -> str:
    """Neutralise CSV/spreadsheet formula injection by prepending a single quote."""
    if value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def normalize_title(title: str) -> str:
    return title.strip().lower()


def parse_float(value, field_name: str, source: str) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        logger.warning("%s: cannot parse float for '%s': %r", source, field_name, value)
        return None


def parse_int(value, field_name: str, source: str) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        logger.warning("%s: cannot parse int for '%s': %r", source, field_name, value)
        return None
