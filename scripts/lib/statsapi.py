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
            "hydrate": "team(division,league)",
        },
        ttl=1800,  # refresh standings every 30 min
    )

    records: list[dict] = []
    for division_record in data.get("records", []):
        division_name = (
            division_record.get("division", {}).get("nameShort")
            or division_record.get("division", {}).get("name", "Unknown")
        )
        league_raw = division_record.get("league", {}).get("abbreviation", "")
        # Normalize to AL/NL — the API sometimes returns full names or league IDs
        if "american" in league_raw.lower() or league_raw == "AL" or "103" in str(division_record.get("league", {}).get("id", "")):
            league_name = "AL"
        elif "national" in league_raw.lower() or league_raw == "NL" or "104" in str(division_record.get("league", {}).get("id", "")):
            league_name = "NL"
        else:
            # Infer from division name as last resort
            div = division_name.upper()
            league_name = "AL" if "AMERICAN" in div else ("NL" if "NATIONAL" in div else "AL")

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
