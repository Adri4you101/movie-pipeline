"""Data models for the movie score pipeline.

This module defines the two core structures used throughout the pipeline:

- MovieRecord: holds all fields for a single film, gathered from one or more
  providers. Fields from providers that do not carry data for a given film are
  left as None.
- UnifiedDataset: the final output of the pipeline; wraps a list of MovieRecord
  objects and exposes a keyed lookup interface.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from src.utils import normalize_title


@dataclass
class MovieRecord:
    """All known data for a single film, merged across providers.

    ``title`` and ``year`` are the merge key and are always present.
    Every other field is optional: if a provider does not supply a value for a
    given film, the field remains None.

    Attributes:
        title: Original-casing title as read from the first provider that
            supplied it.
        year: Four-digit release year.
        critic_score_pct: Critic approval percentage (0–100) from CriticAgg.
        top_critic_score: Weighted top-critic score (0–10) from CriticAgg.
        total_critic_reviews: Number of critic reviews counted by CriticAgg.
        audience_avg_score: Average audience score (0–10) from AudiencePulse.
        total_audience_ratings: Number of audience ratings from AudiencePulse.
        domestic_box_office_audience: Domestic gross as reported by AudiencePulse.
        domestic_box_office: Domestic gross as reported by BoxOfficeMetrics.
        international_box_office: International gross from BoxOfficeMetrics.
        production_budget: Production budget in USD from BoxOfficeMetrics.
        marketing_spend: Marketing spend in USD from BoxOfficeMetrics.
        worldwide_box_office: Computed property; sum of domestic and international
            gross when both are available, otherwise None.
    """

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
        """Sum of domestic and international box office, or None if either is missing."""
        if self.domestic_box_office is not None and self.international_box_office is not None:
            return self.domestic_box_office + self.international_box_office
        return None


@dataclass
class UnifiedDataset:
    """The final output of the pipeline: a collection of merged MovieRecords.

    In addition to the ordered list exposed by ``all()``, an internal index
    keyed by ``(normalized_title, year)`` is built at construction time so that
    ``get()`` lookups are O(1).

    Attributes:
        movies: List of MovieRecord objects sorted alphabetically by title, then
            by year.
    """

    movies: list[MovieRecord]

    def __post_init__(self):
        self._index: dict[tuple[str, int], MovieRecord] = {}
        for m in self.movies:
            key = (normalize_title(m.title), m.year)
            if key not in self._index:
                self._index[key] = m

    def get(self, title: str, year: Optional[int] = None) -> Optional[MovieRecord]:
        """Look up a film by title and optional year.

        Title matching is case-insensitive and whitespace-insensitive.
        If ``year`` is omitted and multiple films share the same normalized title,
        the one with the lowest year is returned.

        Args:
            title: Film title to look up (any casing, any surrounding whitespace).
            year: Release year. If provided, the lookup is exact on (title, year).

        Returns:
            The matching MovieRecord, or None if no match is found.
        """
        normalized = normalize_title(title)
        if year is not None:
            return self._index.get((normalized, year))
        matches = [m for (t, _), m in self._index.items() if t == normalized]
        return min(matches, key=lambda m: m.year) if matches else None

    def all(self) -> list[MovieRecord]:
        """Return all movies in the dataset as a list.

        Returns:
            A new list containing all MovieRecord objects in their sorted order.
        """
        return list(self.movies)
