from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from src.utils import normalize_title


@dataclass
class MovieRecord:
    title: str
    year: int

    # Provider 1 — CriticAgg
    critic_score_pct: Optional[float] = None
    top_critic_score: Optional[float] = None
    total_critic_reviews: Optional[int] = None

    # Provider 2 — AudiencePulse
    audience_avg_score: Optional[float] = None
    total_audience_ratings: Optional[int] = None
    domestic_box_office_audience: Optional[int] = None

    # Provider 3 — BoxOfficeMetrics
    domestic_box_office: Optional[int] = None
    international_box_office: Optional[int] = None
    production_budget: Optional[int] = None
    marketing_spend: Optional[int] = None

    @property
    def worldwide_box_office(self) -> Optional[int]:
        if self.domestic_box_office is not None and self.international_box_office is not None:
            return self.domestic_box_office + self.international_box_office
        return None


@dataclass
class UnifiedDataset:
    movies: list[MovieRecord]

    def __post_init__(self):
        self._index: dict[tuple[str, int], MovieRecord] = {}
        for m in self.movies:
            key = (normalize_title(m.title), m.year)
            if key not in self._index:
                self._index[key] = m

    def get(self, title: str, year: Optional[int] = None) -> Optional[MovieRecord]:
        normalized = normalize_title(title)
        if year is not None:
            return self._index.get((normalized, year))
        matches = [m for (t, _), m in self._index.items() if t == normalized]
        return min(matches, key=lambda m: m.year) if matches else None

    def all(self) -> list[MovieRecord]:
        return list(self.movies)
