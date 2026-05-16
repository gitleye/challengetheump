#!/usr/bin/env python3
"""
Entry point for the ABS Dashboard data pipeline.

Usage:
    python scripts/run.py                   # full run
    python scripts/run.py --dry-run         # fetch + compute, don't write JSON
    python scripts/run.py --skip-fetch      # use cached data, recompute only
    python scripts/run.py --season 2026     # explicit season (default: current)
    python scripts/run.py --types-only      # regenerate TypeScript types only
"""

from __future__ import annotations

import argparse
import datetime
import logging
import os
import sys
from pathlib import Path

# Ensure scripts/ is on sys.path when called from repo root
sys.path.insert(0, str(Path(__file__).parent))

log_level = os.environ.get("PIPELINE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
)
logger = logging.getLogger("run")

PIPELINE_VERSION = "0.1.0"


def _current_season() -> int:
    today = datetime.date.today()
    # MLB season runs roughly March–October; use current year if in season, else prior year
    return today.year if today.month >= 3 else today.year - 1


def _is_offseason(season: int) -> bool:
    today = datetime.date.today()
    season_start = datetime.date(season, 3, 20)
    season_end = datetime.date(season, 11, 1)
    return not (season_start <= today <= season_end)


def main() -> int:
    parser = argparse.ArgumentParser(description="ABS Dashboard data pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Compute but don't write JSON")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached data only")
    parser.add_argument("--season", type=int, default=_current_season(), help="MLB season year")
    parser.add_argument("--types-only", action="store_true", help="Regenerate TS types and exit")
    args = parser.parse_args()

    logger.info(f"ABS Dashboard pipeline v{PIPELINE_VERSION} starting — season {args.season}")

    # ---- Off-season check ------------------------------------------------
    if _is_offseason(args.season) and not args.skip_fetch:
        logger.warning(
            f"Season {args.season} is not currently active (today: {datetime.date.today()}). "
            f"Skipping live data fetches. Pass --skip-fetch to use cached data."
        )
        _write_offseason_metadata(args.season)
        return 0

    # ---- TypeScript types only -------------------------------------------
    if args.types_only:
        from write_json import regenerate_typescript_types
        import datetime as dt

        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        regenerate_typescript_types(now)
        return 0

    # ---- Fetch -----------------------------------------------------------
    from fetch_data import FetchResult, fetch_all, load_cached

    if args.skip_fetch:
        logger.info("--skip-fetch: loading from cache")
        fetch_result = load_cached(args.season)
    else:
        fetch_result = fetch_all(args.season)

    if fetch_result.errors:
        logger.warning(f"Fetch completed with {len(fetch_result.errors)} errors:")
        for err in fetch_result.errors:
            logger.warning(f"  {err}")

    # ---- Compute ---------------------------------------------------------
    logger.info("Computing metrics")
    from compute_metrics import compute

    metrics = compute(fetch_result)
    # Attach stale sources for metadata
    metrics._stale_sources = fetch_result.stale_sources  # type: ignore[attr-defined]

    _log_summary(metrics)

    # ---- Write -----------------------------------------------------------
    from write_json import regenerate_typescript_types, write_all

    success = write_all(metrics, dry_run=args.dry_run)
    if not success:
        logger.error("Pipeline failed at write step")
        return 1

    if not args.dry_run:
        regenerate_typescript_types(metrics.now_iso)

    logger.info(
        f"Pipeline complete. "
        f"Teams: {len(metrics.teams.teams)}, "
        f"Players: {len(metrics.players.players)}, "
        f"Daily snapshots: {len(metrics.daily.snapshots)}"
    )
    return 0


def _write_offseason_metadata(season: int) -> None:
    """Write a minimal metadata.json indicating we're in the off-season."""
    import datetime as dt
    import json
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "src" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    meta = {
        "last_updated": now,
        "season": season,
        "data_quality": "missing",
        "stale_sources": ["all — off-season"],
        "pipeline_version": PIPELINE_VERSION,
        "games_through": None,
        "_note": f"Season {season} is not active. Data will populate once games begin.",
    }
    path = data_dir / "metadata.json"
    path.write_text(json.dumps(meta, indent=2))
    logger.info(f"Wrote off-season metadata to {path}")


def _log_summary(metrics) -> None:  # type: ignore[no-untyped-def]
    teams_with_data = [t for t in metrics.teams.teams if t.challenges.total_challenges > 0]
    logger.info(
        f"Summary — "
        f"{len(metrics.teams.teams)} teams total, "
        f"{len(teams_with_data)} with challenge data, "
        f"{len(metrics.players.players)} players, "
        f"{len(metrics.daily.snapshots)} daily snapshots"
    )
    if teams_with_data:
        top = max(teams_with_data, key=lambda t: t.challenges.challenge_wpa or float("-inf"))
        logger.info(
            f"Top team by WPA: {top.team_name} "
            f"(WPA={top.challenges.challenge_wpa}, "
            f"success={top.challenges.success_rate:.1%} if top.challenges.success_rate else 'N/A')"
        )


if __name__ == "__main__":
    sys.exit(main())
