from src.models import MovieRecord, UnifiedDataset
from src.utils import normalize_title

_MERGEABLE_FIELDS = [
    'critic_score_pct', 'top_critic_score', 'total_critic_reviews',
    'audience_avg_score', 'total_audience_ratings', 'domestic_box_office_audience',
    'domestic_box_office', 'international_box_office', 'production_budget', 'marketing_spend',
]


def merge(provider_results: list[list[MovieRecord]]) -> UnifiedDataset:
    grouped: dict[tuple[str, int], MovieRecord] = {}

    for records in provider_results:
        for record in records:
            key = (normalize_title(record.title), record.year)
            if key not in grouped:
                grouped[key] = MovieRecord(title=record.title, year=record.year)
            _apply_fields(grouped[key], record)

    movies = sorted(grouped.values(), key=lambda m: (normalize_title(m.title), m.year))
    return UnifiedDataset(movies=movies)


def _apply_fields(target: MovieRecord, source: MovieRecord) -> None:
    for field in _MERGEABLE_FIELDS:
        value = getattr(source, field)
        if value is not None:
            setattr(target, field, value)
