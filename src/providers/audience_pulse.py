import json
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_float, parse_int

logger = logging.getLogger(__name__)


class AudiencePulseProvider(Provider):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[MovieRecord]:
        try:
            with open(self.file_path, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"AudiencePulseProvider: file not found: {self.file_path}"
            )

        if not isinstance(data, list):
            logger.warning("AudiencePulseProvider: expected JSON array, got %s", type(data).__name__)
            return []

        return [r for r in (self._parse_entry(e) for e in data) if r is not None]

    def _parse_entry(self, entry: dict) -> Optional[MovieRecord]:
        if not isinstance(entry, dict):
            logger.warning("AudiencePulseProvider: skipping non-dict entry: %r", entry)
            return None

        title = entry.get('title')
        if not title or not str(title).strip():
            logger.warning("AudiencePulseProvider: skipping entry with empty title: %r", entry)
            return None
        title = str(title).strip()

        year = parse_int(entry.get('year'), 'year', 'AudiencePulseProvider')
        if year is None:
            logger.warning("AudiencePulseProvider: skipping entry with invalid year: %r", entry)
            return None

        return MovieRecord(
            title=title,
            year=year,
            audience_avg_score=parse_float(
                entry.get('audience_average_score'), 'audience_average_score', 'AudiencePulseProvider'
            ),
            total_audience_ratings=parse_int(
                entry.get('total_audience_ratings'), 'total_audience_ratings', 'AudiencePulseProvider'
            ),
            domestic_box_office_audience=parse_int(
                entry.get('domestic_box_office_gross'), 'domestic_box_office_gross', 'AudiencePulseProvider'
            ),
        )
