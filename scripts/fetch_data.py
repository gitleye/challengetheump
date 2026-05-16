"""
Fetch raw data from all sources and write to the local cache.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from lib import savant, statsapi

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent / ".cache" / "raw"


@dataclass
class FetchResult:
    season: int
    standings: list[dict] = field(default_factory=list)
    # Savant ABS leaderboard data
    abs_batting_team: Optional[list[dict]] = None   # 30 team batting-side records
    abs_catching_team: Optional[list[dict]] = None  # 30 team fielding-side records
    abs_players: Optional[list[dict]] = None        # ~353 player records (all batters)
    abs_batters: Optional[list[dict]] = None         # batter-specific endpoint
    abs_catchers: Optional[list[dict]] = None       # ~82 catcher records
    # League stats
    league_hitting: Optional[dict] = None
    prior_league_hitting: Optional[dict] = None
    stale_sources: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def fetch_all(season: int) -> FetchResult:
    result = FetchResult(season=season)

    # ---- Standings -------------------------------------------------------
    logger.info("Fetching team standings from MLB Stats API")
    try:
        result.standings = statsapi.fetch_standings(season)
    except Exception as exc:
        msg = f"Standings fetch failed: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        result.stale_sources.append("standings")

    # ---- Baseball Savant ABS leaderboards --------------------------------
    logger.info("Fetching ABS leaderboard from Baseball Savant")
    try:
        all_data = savant.fetch_all_abs_data(season)
        result.abs_batting_team = all_data.get("batting_team")
        result.abs_catching_team = all_data.get("catching_team")
        result.abs_players = all_data.get("players")
        result.abs_batters = all_data.get("batters")
        result.abs_catchers = all_data.get("catchers")

        for key, val in all_data.items():
            if val is None:
                logger.warning(f"Savant {key} returned no data")
                result.stale_sources.append(f"savant_{key}")
            else:
                logger.info(f"Savant {key}: {len(val)} records")
    except Exception as exc:
        msg = f"Baseball Savant ABS fetch failed: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        result.stale_sources.append("savant_all")

    # ---- League-level hitting stats --------------------------------------
    logger.info("Fetching league hitting stats")
    try:
        result.league_hitting = statsapi.fetch_league_hitting_stats(season)
        result.prior_league_hitting = statsapi.fetch_prior_season_hitting_stats(season)
    except Exception as exc:
        logger.warning(f"League hitting stats failed: {exc}")
        result.stale_sources.append("league_hitting")

    _persist(result)

    logger.info(
        f"Fetch complete. Standings: {len(result.standings)} teams. "
        f"ABS batting-team: {len(result.abs_batting_team or [])}. "
        f"ABS players: {len(result.abs_players or [])}. "
        f"Stale: {result.stale_sources}"
    )
    return result


def _persist(result: FetchResult) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if result.standings:
        (RAW_DIR / "standings.json").write_text(json.dumps(result.standings, indent=2))

    for attr, filename in [
        ("abs_batting_team", "abs_batting_team.json"),
        ("abs_catching_team", "abs_catching_team.json"),
        ("abs_players", "abs_players.json"),
        ("abs_batters", "abs_batters.json"),
        ("abs_catchers", "abs_catchers.json"),
    ]:
        val = getattr(result, attr)
        if val is not None:
            (RAW_DIR / filename).write_text(json.dumps(val, indent=2))

    if result.league_hitting:
        (RAW_DIR / "league_hitting.json").write_text(json.dumps(result.league_hitting, indent=2))

    if result.prior_league_hitting:
        (RAW_DIR / "prior_league_hitting.json").write_text(json.dumps(result.prior_league_hitting, indent=2))


def load_cached(season: int) -> FetchResult:
    """Load previously persisted raw data without HTTP requests."""
    result = FetchResult(season=season)

    def _load_json(name: str) -> Optional[list | dict]:
        path = RAW_DIR / name
        if path.exists():
            return json.loads(path.read_text())
        return None

    result.standings = _load_json("standings.json") or []
    result.abs_batting_team = _load_json("abs_batting_team.json")
    result.abs_catching_team = _load_json("abs_catching_team.json")
    result.abs_players = _load_json("abs_players.json")
    result.abs_batters = _load_json("abs_batters.json")
    result.abs_catchers = _load_json("abs_catchers.json")
    result.league_hitting = _load_json("league_hitting.json")
    result.prior_league_hitting = _load_json("prior_league_hitting.json")

    return result
