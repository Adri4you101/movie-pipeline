"""Provider for AudiencePulse — bi-weekly JSON of audience ratings and box office."""

import json
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_float, parse_int, sanitize_string

logger = logging.getLogger(__name__)


class AudiencePulseProvider(Provider):
    """Reads audience rating and box office data from an AudiencePulse JSON file.

    The file must be a JSON array where each element is an object with the keys:
        title, year, audience_average_score, total_audience_ratings,
        domestic_box_office_gross

    Note: ``year`` is supplied as a string in this source ("2010") and is cast to
    int during parsing. ``domestic_box_office_gross`` is stored in the
    ``domestic_box_office_audience`` field to distinguish it from the same figure
    reported by BoxOfficeMetrics.

    Schema validation is performed against the first entry in the array. Required
    keys missing from that entry raise ValueError immediately; missing optional
    keys emit a warning.

    Entries are skipped if ``title`` is empty/whitespace or ``year`` cannot be
    parsed. All other numeric fields degrade gracefully to None on bad input.

    Args:
        file_path: Path to the provider2.json file.
    """

    _REQUIRED_COLUMNS = frozenset({'title', 'year'})
    _OPTIONAL_COLUMNS = frozenset({
        'audience_average_score', 'total_audience_ratings', 'domestic_box_office_gross'
    })

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[MovieRecord]:
        """Parse the JSON file and return one MovieRecord per valid entry.

        Returns:
            List of MovieRecord objects with audience-score fields populated.

        Raises:
            FileNotFoundError: If ``file_path`` does not exist.
            ValueError: If any required key is absent from the first entry.
        """
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

        first = next((e for e in data if isinstance(e, dict)), None)
        if first is not None:
            self._validate_columns(set(first.keys()))

        return [r for r in (self._parse_entry(e) for e in data) if r is not None]

    def _validate_columns(self, keys: set) -> None:
        """Warn if required or optional keys are absent from the first entry.

        JSON has no header row — each entry is self-describing, so missing keys
        in one entry may be bad data rather than a schema change. Warnings are
        emitted either way; per-entry checks handle skipping invalid records.
        """
        missing_required = self._REQUIRED_COLUMNS - keys
        if missing_required:
            logger.warning(
                "AudiencePulseProvider: first entry missing expected keys %s — "
                "possible schema change",
                missing_required,
            )
        missing_optional = self._OPTIONAL_COLUMNS - keys
        if missing_optional:
            logger.warning(
                "AudiencePulseProvider: missing optional keys (fields will be None): %s",
                missing_optional,
            )

    def _parse_entry(self, entry: dict) -> Optional[MovieRecord]:
        """Convert a single JSON object into a MovieRecord, or None if invalid."""
        if not isinstance(entry, dict):
            logger.warning("AudiencePulseProvider: skipping non-dict entry: %r", entry)
            return None

        title = entry.get('title')
        if not title or not str(title).strip():
            logger.warning("AudiencePulseProvider: skipping entry with empty title: %r", entry)
            return None
        title = sanitize_string(str(title).strip())

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
