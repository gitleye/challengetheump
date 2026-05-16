"""
Baseball Savant ABS Challenge data client.

The ABS Challenge leaderboard lives at:
  baseballsavant.mlb.com/leaderboard/abs-challenges

The page renders JSON data inline as a JavaScript const. We scrape and parse it.
No auth required; data is public.

Key field mapping (Baseball Savant → our schema):
  n_challenges           → total_challenges
  n_overturns            → successful_challenges
  n_fails                → failed_challenges
  rate_overturns         → success_rate (0–1)
  n_chal_runs_gained     → runs gained via overturns (FOR the challenger)
  n_chal_runs_lost       → runs given up via failed challenges
  net_net_runs           → net run value vs. expected (our headline metric)
  n_strikeouts           → strikeouts affected
  n_walks                → walks affected
  team_abbr              → team_id (abbreviation)
  player_name            → name
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Optional

import requests

from . import cache

logger = logging.getLogger(__name__)

BASE = "https://baseballsavant.mlb.com"
_LAST_REQUEST: float = 0.0
_MIN_INTERVAL = 1.0


def _throttle() -> None:
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST = time.time()


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 ABS-Dashboard/0.1 (research; github.com/leyeoyelami/abs-dashboard)",
        "Accept": "text/html,application/xhtml+xml",
    })
    return s


def _scrape_leaderboard_page(url: str, session: requests.Session) -> Optional[list[dict]]:
    """
    Fetch a Baseball Savant ABS leaderboard page and extract the embedded JSON.

    The page embeds data as:
        const vizChallenges = [{...}, ...];
    or a similar const assignment containing 'n_challenges'.
    """
    _throttle()
    html_text, from_cache = cache.get_csv(url, session=session, ttl=3600 * 4)
    if not html_text:
        return None

    # Find the embedded JS const containing challenge data
    # Pattern: const <name> = [{ ... }];
    matches = re.findall(r'const\s+\w+\s*=\s*(\[.*?\]);', html_text, re.DOTALL)
    for m in matches:
        if 'n_challenges' in m and len(m) > 500:
            try:
                data = json.loads(m)
                if isinstance(data, list) and len(data) > 0:
                    logger.debug(
                        f"Scraped {len(data)} records from {url} (cached={from_cache})"
                    )
                    return data
            except json.JSONDecodeError:
                continue

    logger.warning(f"Could not extract challenge data from {url}")
    return None


def fetch_team_batting_challenges(season: int) -> Optional[list[dict]]:
    """
    Fetch team-level batting (offense) challenge stats.
    Returns 30 team records.
    """
    session = _session()
    url = f"{BASE}/leaderboard/abs-challenges?challengeType=batting-team&level=mlb&gameType=regular&year={season}"
    return _scrape_leaderboard_page(url, session)


def fetch_team_catching_challenges(season: int) -> Optional[list[dict]]:
    """
    Fetch team-level catching (defense) challenge stats.
    Returns 30 team records.
    """
    session = _session()
    url = f"{BASE}/leaderboard/abs-challenges?challengeType=catching-team&level=mlb&gameType=regular&year={season}"
    return _scrape_leaderboard_page(url, session)


def fetch_player_challenges(season: int) -> Optional[list[dict]]:
    """
    Fetch player-level challenge stats (all roles combined).
    Returns ~353 player records.
    """
    session = _session()
    url = f"{BASE}/leaderboard/abs-challenges?level=mlb&gameType=regular&year={season}"
    return _scrape_leaderboard_page(url, session)


def fetch_catcher_challenges(season: int) -> Optional[list[dict]]:
    """
    Fetch catcher-specific challenge stats.
    Returns ~82 catcher records.
    """
    session = _session()
    url = f"{BASE}/leaderboard/abs-challenges?challengeType=catcher&level=mlb&gameType=regular&year={season}"
    return _scrape_leaderboard_page(url, session)


def fetch_batter_challenges(season: int) -> Optional[list[dict]]:
    """
    Fetch batter-specific challenge stats.
    """
    session = _session()
    url = f"{BASE}/leaderboard/abs-challenges?challengeType=batter&level=mlb&gameType=regular&year={season}"
    return _scrape_leaderboard_page(url, session)


# ---- Field extraction helpers -------------------------------------------

def safe_rate(val: Any) -> Optional[float]:
    """Convert a rate value (0–1 or 0–100) to a 0–1 proportion."""
    if val is None:
        return None
    try:
        f = float(val)
        # Savant returns rates as fractions (0.625), not percentages
        return round(f, 4)
    except (TypeError, ValueError):
        return None


def safe_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 4) if f == f else None  # NaN check
    except (TypeError, ValueError):
        return None


def team_id_from_record(record: dict) -> str:
    """
    Extract normalized team abbreviation from a Savant record.
    Tries team_abbr, parent_org_code, then player_team.
    """
    for key in ("team_abbr", "parent_org_code", "player_team"):
        val = record.get(key, "")
        if val and str(val).strip():
            return str(val).strip().upper()
    return "UNK"


def fetch_all_abs_data(season: int) -> dict[str, Optional[list[dict]]]:
    """
    Fetch all ABS leaderboard data in one call. Returns dict of lists.

    Note: the default all-players endpoint returns only batters (player_at_bat == id).
    There is no pitcher-specific challenge endpoint — catchers initiate defensive challenges.
    """
    logger.info(f"Fetching Baseball Savant ABS data for season {season}")
    return {
        "batting_team": fetch_team_batting_challenges(season),
        "catching_team": fetch_team_catching_challenges(season),
        "players": fetch_player_challenges(season),
        "batters": fetch_batter_challenges(season),
        "catchers": fetch_catcher_challenges(season),
    }


# ---- Static team mapping ------------------------------------------------

def fetch_team_ids(season: int) -> dict[str, str]:
    """Returns a mapping of abbreviation → full team name."""
    return {
        "ARI": "Arizona Diamondbacks",
        "ATL": "Atlanta Braves",
        "BAL": "Baltimore Orioles",
        "BOS": "Boston Red Sox",
        "CHC": "Chicago Cubs",
        "CWS": "Chicago White Sox",
        "CIN": "Cincinnati Reds",
        "CLE": "Cleveland Guardians",
        "COL": "Colorado Rockies",
        "DET": "Detroit Tigers",
        "HOU": "Houston Astros",
        "KC": "Kansas City Royals",
        "LAA": "Los Angeles Angels",
        "LAD": "Los Angeles Dodgers",
        "MIA": "Miami Marlins",
        "MIL": "Milwaukee Brewers",
        "MIN": "Minnesota Twins",
        "NYM": "New York Mets",
        "NYY": "New York Yankees",
        "OAK": "Athletics",
        "PHI": "Philadelphia Phillies",
        "PIT": "Pittsburgh Pirates",
        "SD": "San Diego Padres",
        "SF": "San Francisco Giants",
        "SEA": "Seattle Mariners",
        "STL": "St. Louis Cardinals",
        "TB": "Tampa Bay Rays",
        "TEX": "Texas Rangers",
        "TOR": "Toronto Blue Jays",
        "WSH": "Washington Nationals",
    }
