import csv
import logging
from typing import Optional
from src.models import MovieRecord
from src.providers.base import Provider
from src.utils import parse_int, normalize_title

logger = logging.getLogger(__name__)


class BoxOfficeMetricsProvider(Provider):
    def __init__(self, domestic_path: str, international_path: str, financials_path: str):
        self.domestic_path = domestic_path
        self.international_path = international_path
        self.financials_path = financials_path

    def parse(self) -> list[MovieRecord]:
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
        title = row.get('film_name', '').strip()
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
        title = row.get('film_name', '').strip()
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
        for source in sources:
            if key in source:
                return source[key]['title']
        return None
