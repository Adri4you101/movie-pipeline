import logging
from typing import Optional

logger = logging.getLogger(__name__)


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
