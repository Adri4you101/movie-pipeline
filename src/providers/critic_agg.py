import csv
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_float, parse_int

logger = logging.getLogger(__name__)


class CriticAggProvider(Provider):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[MovieRecord]:
        try:
            with open(self.file_path, newline='', encoding='utf-8-sig') as f:
                return [r for r in (self._parse_row(row)
                                    for row in csv.DictReader(f))
                        if r is not None]
        except FileNotFoundError:
            raise FileNotFoundError(
                f"CriticAggProvider: file not found: {self.file_path}"
            )

    def _parse_row(self, row: dict) -> Optional[MovieRecord]:
        title = row.get('movie_title', '').strip()
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
