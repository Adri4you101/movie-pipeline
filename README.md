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
