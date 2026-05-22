"""
MLB Stats API client.

Endpoints: https://statsapi.mlb.com/api/v1/
Documentation: https://github.com/toddrob99/MLB-StatsAPI (unofficial)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

from . import cache

logger = logging.getLogger(__name__)

BASE = "https://statsapi.mlb.com/api/v1"
_LAST_REQUEST: float = 0.0
_MIN_INTERVAL = 0.5


def _throttle() -> None:
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST = time.time()


def _get(path: str, params: Optional[dict] = None, ttl: int = 3600) -> Any:
    url = f"{BASE}{path}"
    _throttle()
    data, from_cache = cache.get(url, params=params, ttl=ttl)
    logger.debug(f"StatsAPI {path} (cached={from_cache})")
    return data


# ---- Standings -----------------------------------------------------------

LEAGUE_IDS = {"AL": 103, "NL": 104}

_DIVISION_NAMES: dict[int, str] = {
    200: "AL West",
    201: "AL East",
    202: "AL Central",
    203: "NL West",
    204: "NL East",
    205: "NL Central",
}

_LEAGUE_BY_DIVISION: dict[int, str] = {
    200: "AL", 201: "AL", 202: "AL",
    203: "NL", 204: "NL", 205: "NL",
}


def fetch_standings(season: int) -> list[dict]:
    """
    Returns a list of team standing dicts with wins, losses, win_pct, etc.

    Each dict has:
        team_id (str), team_name (str), wins (int), losses (int),
        win_pct (float), division (str), league (str)
    """
    data = _get(
        "/standings",
        params={
            "leagueId": "103,104",
            "season": season,
            "standingsTypes": "regularSeason",
            "hydrate": "team",
        },
        ttl=1800,  # refresh standings every 30 min
    )

    records: list[dict] = []
    for division_record in data.get("records", []):
        div_id = division_record.get("division", {}).get("id")
        division_name = _DIVISION_NAMES.get(div_id, "Unknown")
        league_name = _LEAGUE_BY_DIVISION.get(div_id, "")

        if not league_name:
            league_raw = division_record.get("league", {}).get("abbreviation", "")
            league_id = division_record.get("league", {}).get("id")
            if league_id == 103 or league_raw == "AL":
                league_name = "AL"
            elif league_id == 104 or league_raw == "NL":
                league_name = "NL"
            else:
                league_name = "AL"

        for team_record in division_record.get("teamRecords", []):
            team = team_record.get("team", {})
            team_abbrev = team.get("abbreviation", "???")
            wins = int(team_record.get("wins", 0))
            losses = int(team_record.get("losses", 0))
            total = wins + losses
            win_pct = wins / total if total > 0 else 0.0

            records.append(
                {
                    "team_id": team_abbrev,
                    "team_name": team.get("name", "Unknown"),
                    "team_city": team.get("locationName", ""),
                    "division": division_name,
                    "league": league_name,
                    "wins": wins,
                    "losses": losses,
                    "win_pct": win_pct,
                }
            )

    logger.info(f"Standings: {len(records)} teams for season {season}")
    return records


# ---- Schedule / game results ---------------------------------------------

def fetch_game_log(season: int, team_id_mlb: int) -> list[dict]:
    """
    Returns a list of game result dicts for the given team.
    team_id_mlb is the MLB numeric team ID (not abbreviation).
    """
    data = _get(
        f"/teams/{team_id_mlb}/game_log",
        params={"season": season, "gameType": "R"},
        ttl=1800,
    )
    return data.get("dates", [])


def fetch_team_id_map(season: int) -> dict[str, int]:
    """
    Returns mapping of team abbreviation → MLB numeric team ID.
    """
    data = _get("/teams", params={"season": season, "sportId": 1}, ttl=86400)
    result: dict[str, int] = {}
    for team in data.get("teams", []):
        abbrev = team.get("abbreviation")
        mlb_id = team.get("id")
        if abbrev and mlb_id:
            result[abbrev] = mlb_id
    return result


# ---- League-level stats --------------------------------------------------

def fetch_league_hitting_stats(season: int) -> Optional[dict]:
    """
    League-wide hitting stats for the given season: BB%, K%, etc.
    Returns None on failure.
    """
    try:
        data = _get(
            "/stats",
            params={
                "stats": "season",
                "group": "hitting",
                "season": season,
                "sportId": 1,
                "gameType": "R",
            },
            ttl=3600,
        )
        splits = data.get("stats", [{}])[0].get("splits", [])
        if splits:
            return splits[0].get("stat", {})
    except Exception as exc:
        logger.warning(f"League hitting stats failed: {exc}")
    return None


def fetch_prior_season_hitting_stats(season: int) -> Optional[dict]:
    return fetch_league_hitting_stats(season - 1)
