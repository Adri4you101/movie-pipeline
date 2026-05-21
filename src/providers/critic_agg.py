"""Provider for CriticAgg — weekly CSV of critic scores."""

import csv
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_float, parse_int, sanitize_string

logger = logging.getLogger(__name__)


class CriticAggProvider(Provider):
    """Reads critic score data from a CriticAgg CSV file.

    Expected columns:
        movie_title, release_year, critic_score_percentage,
        top_critic_score, total_critic_reviews_counted

    Rows are skipped if ``movie_title`` is empty/whitespace or ``release_year``
    cannot be parsed as an integer. All other numeric fields degrade gracefully
    to None on bad input rather than dropping the row.

    Args:
        file_path: Path to the provider1.csv file.
    """

    _REQUIRED_COLUMNS = frozenset({'movie_title', 'release_year'})
    _OPTIONAL_COLUMNS = frozenset({
        'critic_score_percentage', 'top_critic_score', 'total_critic_reviews_counted'
    })

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[MovieRecord]:
        """Parse the CSV and return one MovieRecord per valid row.

        Returns:
            List of MovieRecord objects with critic-score fields populated.

        Raises:
            FileNotFoundError: If ``file_path`` does not exist.
            ValueError: If any required column is absent from the CSV header.
        """
        try:
            with open(self.file_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    self._validate_columns(set(reader.fieldnames))
                return [r for r in (self._parse_row(row) for row in reader)
                        if r is not None]
        except FileNotFoundError:
            raise FileNotFoundError(
                f"CriticAggProvider: file not found: {self.file_path}"
            )

    def _validate_columns(self, headers: set) -> None:
        """Raise ValueError if required columns are missing; warn for optional ones."""
        missing_required = self._REQUIRED_COLUMNS - headers
        if missing_required:
            raise ValueError(
                f"CriticAggProvider: missing required columns: {missing_required}"
            )
        missing_optional = self._OPTIONAL_COLUMNS - headers
        if missing_optional:
            logger.warning(
                "CriticAggProvider: missing optional columns (fields will be None): %s",
                missing_optional,
            )

    def _parse_row(self, row: dict) -> Optional[MovieRecord]:
        """Convert a single CSV row dict into a MovieRecord, or None if invalid."""
        title = sanitize_string(row.get('movie_title', '').strip())
        if not title:
            logger.warning("CriticAggProvider: skipping row with empty title: %s", row)
            return None

        year = parse_int(row.get('release_year'), 'release_year', 'CriticAggProvider')
        if year is None:
            logger.warning("CriticAggProvider: skipping row with invalid year: %s", row)
            return None

        return MovieRecord(
            title=title,
            year=year,
            critic_score_pct=parse_float(
                row.get('critic_score_percentage'), 'critic_score_percentage', 'CriticAggProvider'
            ),
            top_critic_score=parse_float(
                row.get('top_critic_score'), 'top_critic_score', 'CriticAggProvider'
            ),
            total_critic_reviews=parse_int(
                row.get('total_critic_reviews_counted'), 'total_critic_reviews_counted', 'CriticAggProvider'
            ),
        )
