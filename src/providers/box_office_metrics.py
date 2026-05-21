"""Provider for BoxOfficeMetrics — monthly CSVs of box office figures and financials."""

import csv
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_int, normalize_title, sanitize_string

logger = logging.getLogger(__name__)


class BoxOfficeMetricsProvider(Provider):
    """Reads box office and financial data from three separate BoxOfficeMetrics CSVs.

    This provider merges the three files internally before returning records, so
    the rest of the pipeline sees a single list of MovieRecord objects with all
    available fields populated.

    File schemas:
        domestic/international CSV:
            film_name, year_of_release, box_office_gross_usd
        financials CSV:
            film_name, year_of_release, production_budget_usd, marketing_spend_usd

    A film may appear in any combination of the three files. If it is absent from
    one file its corresponding fields are left as None.

    Args:
        domestic_path: Path to provider3_domestic.csv.
        international_path: Path to provider3_international.csv.
        financials_path: Path to provider3_financials.csv.
    """

    def __init__(self, domestic_path: str, international_path: str, financials_path: str):
        self.domestic_path = domestic_path
        self.international_path = international_path
        self.financials_path = financials_path

    def parse(self) -> list[MovieRecord]:
        """Read and merge the three CSV files, returning one MovieRecord per film.

        Returns:
            List of MovieRecord objects with box-office and financial fields
            populated where available.

        Raises:
            FileNotFoundError: If any of the three CSV files does not exist.
        """
        domestic = self._read_box_office(self.domestic_path, 'domestic')
        international = self._read_box_office(self.international_path, 'international')
        financials = self._read_financials(self.financials_path)

        all_keys = set(domestic) | set(international) | set(financials)
        records = []
        for key in sorted(all_keys):
            orig_title = self._pick_title(key, domestic, international, financials)
            if orig_title is None:
                continue
            _, year = key
            records.append(MovieRecord(
                title=orig_title,
                year=year,
                domestic_box_office=domestic.get(key, {}).get('gross'),
                international_box_office=international.get(key, {}).get('gross'),
                production_budget=financials.get(key, {}).get('budget'),
                marketing_spend=financials.get(key, {}).get('marketing'),
            ))
        return records

    def _read_box_office(self, path: str, label: str) -> dict:
        """Read a domestic or international box office CSV into a keyed dict.

        Args:
            path: Path to the CSV file.
            label: Human-readable label ("domestic" or "international") used in
                log messages.

        Returns:
            Dict mapping ``(normalized_title, year)`` to a row dict with keys
            ``key``, ``title``, and ``gross``.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
        """
        result = {}
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    entry = self._parse_box_office_row(row, label)
                    if entry:
                        result[entry['key']] = entry
        except FileNotFoundError:
            raise FileNotFoundError(
                f"BoxOfficeMetricsProvider: file not found: {path}"
            )
        return result

    def _parse_box_office_row(self, row: dict, label: str) -> Optional[dict]:
        """Parse one row from a box office CSV, returning None if the row is invalid."""
        title = sanitize_string(row.get('film_name', '').strip())
        if not title:
            return None
        year = parse_int(row.get('year_of_release'), 'year_of_release', f'BoxOfficeMetrics/{label}')
        if year is None:
            return None
        return {
            'key': (normalize_title(title), year),
            'title': title,
            'gross': parse_int(row.get('box_office_gross_usd'), 'box_office_gross_usd', f'BoxOfficeMetrics/{label}'),
        }

    def _read_financials(self, path: str) -> dict:
        """Read the financials CSV into a keyed dict.

        Args:
            path: Path to the financials CSV file.

        Returns:
            Dict mapping ``(normalized_title, year)`` to a row dict with keys
            ``key``, ``title``, ``budget``, and ``marketing``.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
        """
        result = {}
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    entry = self._parse_financials_row(row)
                    if entry:
                        result[entry['key']] = entry
        except FileNotFoundError:
            raise FileNotFoundError(
                f"BoxOfficeMetricsProvider: file not found: {path}"
            )
        return result

    def _parse_financials_row(self, row: dict) -> Optional[dict]:
        """Parse one row from the financials CSV, returning None if the row is invalid."""
        title = sanitize_string(row.get('film_name', '').strip())
        if not title:
            return None
        year = parse_int(row.get('year_of_release'), 'year_of_release', 'BoxOfficeMetrics/financials')
        if year is None:
            return None
        return {
            'key': (normalize_title(title), year),
            'title': title,
            'budget': parse_int(row.get('production_budget_usd'), 'production_budget_usd', 'BoxOfficeMetrics/financials'),
            'marketing': parse_int(row.get('marketing_spend_usd'), 'marketing_spend_usd', 'BoxOfficeMetrics/financials'),
        }

    def _pick_title(self, key, *sources) -> Optional[str]:
        """Return the original-casing title for a key from the first source that has it."""
        for source in sources:
            if key in source:
                return source[key]['title']
        return None
