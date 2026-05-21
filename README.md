# Movie Score Data Pipeline

A Python ETL pipeline that ingests, cleans, and combines movie data from three independent providers into a single unified dataset — ready for querying by a data science team.

## Overview

Each provider delivers data in a different format and schema. This pipeline normalises and merges them by `(title, year)`, tolerates missing or malformed values, and produces one `MovieRecord` per film with all available fields populated.

```
Provider 1 — CriticAgg       (CSV)   critic scores
Provider 2 — AudiencePulse   (JSON)  audience ratings + box office
Provider 3 — BoxOfficeMetrics (3 CSVs) domestic/international box office + financials
                          ↓
                    merge by (title, year)
                          ↓
                    UnifiedDataset
```

## Requirements

- Python 3.10 or higher
- No external dependencies — standard library only

## Running the pipeline

```bash
python3 main.py
```

Expected output:

```
============================================================
  Movie Score Pipeline — 3 films loaded
============================================================

  Inception (2010)
    Critic score:      87.0%  (top critic: 8.1,  reviews: 450)
    Audience score:    9.1    (ratings: 1,500,000)
    Domestic BO:       $292,576,195
    Worldwide BO:      $828,276,195
    Budget:            $160,000,000  |  Marketing: $100,000,000

  ...
```

## Querying the dataset

The pipeline returns a `UnifiedDataset` that can be queried directly in Python:

```python
from src.pipeline import Pipeline
from src.providers.critic_agg import CriticAggProvider
from src.providers.audience_pulse import AudiencePulseProvider
from src.providers.box_office_metrics import BoxOfficeMetricsProvider

dataset = Pipeline([
    CriticAggProvider("data/provider1.csv"),
    AudiencePulseProvider("data/provider2.json"),
    BoxOfficeMetricsProvider(
        "data/provider3_domestic.csv",
        "data/provider3_international.csv",
        "data/provider3_financials.csv",
    ),
]).run()

# Look up a specific film
movie = dataset.get("Inception", 2010)
print(movie.critic_score_pct)       # 87.0
print(movie.audience_avg_score)     # 9.1
print(movie.worldwide_box_office)   # 828276195

# Look up without year — returns the earliest match
movie = dataset.get("Inception")

# Iterate all films
for movie in dataset.all():
    print(movie.title, movie.year, movie.production_budget)
```

Title lookups are case-insensitive and whitespace-insensitive. Fields not supplied by any provider are `None`.

## Running the tests

```bash
python3 -m unittest discover tests/ -v
```

All tests use the standard library (`unittest`) with temporary in-memory or temp-file fixtures — no setup required.

## Project structure

```
movie-pipeline/
├── main.py                          # Entry point
├── data/
│   ├── provider1.csv                # CriticAgg sample data
│   ├── provider2.json               # AudiencePulse sample data
│   ├── provider3_domestic.csv       # BoxOfficeMetrics — domestic gross
│   ├── provider3_international.csv  # BoxOfficeMetrics — international gross
│   └── provider3_financials.csv     # BoxOfficeMetrics — budget & marketing
├── src/
│   ├── models.py                    # MovieRecord, UnifiedDataset
│   ├── merger.py                    # Merges provider results by (title, year)
│   ├── pipeline.py                  # Orchestrates providers + merger
│   ├── utils.py                     # Shared parsing helpers (parse_int, parse_float, normalize_title)
│   └── providers/
│       ├── base.py                  # Abstract Provider base class
│       ├── critic_agg.py            # Provider 1 — CSV reader
│       ├── audience_pulse.py        # Provider 2 — JSON reader
│       └── box_office_metrics.py    # Provider 3 — 3-file CSV reader
└── tests/
    ├── test_models.py
    ├── test_merger.py
    ├── test_pipeline.py
    ├── test_utils.py
    └── test_providers/
```

## Data providers

| Provider | File(s) | Fields |
|---|---|---|
| CriticAgg | `provider1.csv` | critic score %, top critic score, review count |
| AudiencePulse | `provider2.json` | audience avg score, total ratings, domestic gross |
| BoxOfficeMetrics | `provider3_domestic.csv`, `provider3_international.csv`, `provider3_financials.csv` | domestic gross, international gross, production budget, marketing spend |

## Design decisions

**Merge strategy — last non-None wins.** Each provider's records are applied in order. A field is only overwritten if the incoming value is non-null. This means a film can appear in only one provider and still be included in the output with its available fields populated and the rest as `None`.

**Title normalisation.** Titles are lowercased and stripped before keying, so `"The Dark Knight"`, `"the dark knight"`, and `" The Dark Knight "` all resolve to the same record.

**Defensive parsing.** Every numeric field goes through `parse_int` / `parse_float`. Bad values produce `None` and a warning log entry — the row is kept, not dropped (unless the title or year itself is invalid, in which case the row is skipped entirely).

**Computed field.** `MovieRecord.worldwide_box_office` is a `@property` — it returns `domestic + international` only when both are present, otherwise `None`. No storage, no sync issues.

## Handling schema changes

Each provider declares its expected schema as frozenset class constants:

```python
class CriticAggProvider(Provider):
    _REQUIRED_COLUMNS = frozenset({'movie_title', 'release_year'})
    _OPTIONAL_COLUMNS = frozenset({'critic_score_percentage', 'top_critic_score', ...})
```

These are validated at parse time before any row is processed:

| Situation | Behaviour |
|---|---|
| Required column renamed or removed | `ValueError` with the missing column name — fails fast, no silent data loss |
| Optional column renamed or removed | `WARNING` log entry — pipeline continues, affected fields become `None` |
| New column added | Silently ignored |
| Column type changed | Absorbed by `parse_int` / `parse_float` — bad values become `None` with a warning |

**CSV vs JSON.** CSV providers raise `ValueError` on a missing required column because the header row is an explicit schema declaration — if `movie_title` is gone, every row will silently produce no title and the dataset will be empty. JSON providers only warn: JSON has no header row, so a missing key in one entry is more likely bad data than a schema change, and per-entry checks already handle skipping it.

**Adapting to a schema change** is a one-line fix in the provider:

```python
# provider renamed movie_title → film_title
title = sanitize_string(row.get('film_title', '').strip())
```

Update `_REQUIRED_COLUMNS` to match and the validation stays accurate.

## Adding a new provider

1. Create `src/providers/my_provider.py`:

```python
from src.providers.base import Provider
from src.models import MovieRecord

class MyProvider(Provider):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[MovieRecord]:
        # read your file, return list[MovieRecord]
        ...
```

2. Add any new fields to `MovieRecord` in `src/models.py` — keep them `Optional` with a `None` default.

3. Register it in `main.py`:

```python
from src.providers.my_provider import MyProvider

providers = [
    CriticAggProvider("data/provider1.csv"),
    AudiencePulseProvider("data/provider2.json"),
    BoxOfficeMetricsProvider(...),
    MyProvider("data/provider4.csv"),   # ← add here
]
```

No other changes needed — the merger and pipeline are provider-agnostic.
