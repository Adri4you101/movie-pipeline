"""Merges records from multiple providers into a single UnifiedDataset."""

from src.models import MovieRecord, UnifiedDataset
from src.utils import normalize_title

_MERGEABLE_FIELDS = [
    'critic_score_pct', 'top_critic_score', 'total_critic_reviews',
    'audience_avg_score', 'total_audience_ratings', 'domestic_box_office_audience',
    'domestic_box_office', 'international_box_office', 'production_budget', 'marketing_spend',
]


def merge(provider_results: list[list[MovieRecord]]) -> UnifiedDataset:
    """Combine records from all providers into one MovieRecord per film.

    Records are grouped by ``(normalized_title, year)``. For each unique film, a
    fresh MovieRecord is created and fields are applied from each provider in
    order using a last-non-None-wins strategy: a field is only overwritten when
    the incoming value is not None.

    Films that appear in only one provider are included in the output with their
    available fields populated and the rest as None.

    Args:
        provider_results: A list of per-provider record lists, in the order the
            providers were run. Each inner list is the return value of a single
            ``Provider.parse()`` call.

    Returns:
        A UnifiedDataset containing one MovieRecord per distinct (title, year)
        pair, sorted alphabetically by normalised title and then by year.
    """
    grouped: dict[tuple[str, int], MovieRecord] = {}

    for records in provider_results:
        for record in records:
            key = (normalize_title(record.title), record.year)
            if key not in grouped:
                grouped[key] = MovieRecord(title=record.title, year=record.year)
            _apply_fields(grouped[key], record)

    movies = [grouped[k] for k in sorted(grouped.keys())]
    return UnifiedDataset(movies=movies)


def _apply_fields(target: MovieRecord, source: MovieRecord) -> None:
    """Copy non-None fields from ``source`` onto ``target``.

    Only fields listed in ``_MERGEABLE_FIELDS`` are considered; ``title`` and
    ``year`` (the merge key) are never overwritten.
    """
    for field in _MERGEABLE_FIELDS:
        value = getattr(source, field)
        if value is not None:
            setattr(target, field, value)
