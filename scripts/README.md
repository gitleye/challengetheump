# ABS Dashboard — Data Pipeline

Python pipeline that fetches MLB ABS Challenge System data, computes derived metrics, and writes
static JSON files to `../src/data/`. Runs daily in GitHub Actions.

## Prerequisites

- Python 3.12+
- `pip install -r requirements.txt` (or use a virtual environment)

## Quick start

```bash
cd scripts
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

This will:
1. Fetch raw data from Baseball Savant, MLB Stats API, and pybaseball
2. Cache raw responses in `.cache/` (gitignored)
3. Compute all metrics
4. Validate against Pydantic schemas
5. Write JSON to `../src/data/`
6. Regenerate TypeScript types in `../src/lib/types.ts`

## Running tests

```bash
pytest tests/ -v
pytest tests/ --cov=lib --cov-report=term-missing
```

## Scripts

| File | Purpose |
|------|---------|
| `run.py` | Entry point — orchestrates the full pipeline |
| `fetch_data.py` | Pulls raw data from all sources, caches locally |
| `compute_metrics.py` | Reads cache, computes all derived stats |
| `write_json.py` | Validates and writes final JSON to `../src/data/` |
| `lib/savant.py` | Baseball Savant HTTP client |
| `lib/statsapi.py` | MLB Stats API client |
| `lib/statcast.py` | pybaseball wrapper |
| `lib/metrics.py` | WPA calculations, rolling windows, correlations |
| `lib/schemas.py` | Pydantic models (source of truth for data shapes) |

## Cache

Raw API responses are cached in `scripts/.cache/` with file mtime used to determine staleness.
The cache directory is gitignored. Delete it to force a full refetch.

```bash
rm -rf scripts/.cache/
```

## Off-season behavior

Outside the MLB regular season (roughly April–October), the pipeline skips live data fetches
and outputs `metadata.json` with `data_quality: "missing"` and a clear message. The Astro site
handles this gracefully without breaking the build.

## Debugging

The pipeline uses structured JSON logging. Set `PIPELINE_LOG_LEVEL=DEBUG` for verbose output:

```bash
PIPELINE_LOG_LEVEL=DEBUG python run.py
```

Logs are written to stdout and captured by GitHub Actions.

## GitHub Actions

Two workflows use this pipeline:

- **`daily-data-refresh.yml`** — Runs at 11:00 UTC daily, commits changed JSON to `main`
- **`data-pr-check.yml`** — Runs on PRs to validate the pipeline doesn't break

See `.github/workflows/` for details.
