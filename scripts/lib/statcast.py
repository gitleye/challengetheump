"""
pybaseball wrapper for Statcast pitch-by-pitch data.

pybaseball wraps Baseball Savant's CSV endpoint. We use it for:
  - Full Statcast game-by-game data (includes delta_home_win_exp for WPA)
  - ABS challenge pitch identification via description / events columns
"""

from __future__ import annotations

import datetime
import io
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from . import cache

logger = logging.getLogger(__name__)

# Columns we actually need — reduces memory and parse time
COLS_NEEDED = [
    "game_date",
    "game_pk",
    "inning",
    "inning_topbot",
    "at_bat_number",
    "pitch_number",
    "batter",
    "pitcher",
    "fielder_2",  # catcher
    "home_team",
    "away_team",
    "description",
    "events",
    "type",
    "zone",
    "plate_x",
    "plate_z",
    "sz_top",
    "sz_bot",
    "delta_home_win_exp",
    "delta_run_exp",
    "estimated_woba_using_speedangle",
    "stand",  # batter handedness
    "p_throws",  # pitcher handedness
    # ABS-specific columns (may not exist pre-2026; we handle missing gracefully)
    "abs_challenge_description",
    "abs_challenge_outcome",
    "abs_challenge_team",
]

# ABS-related keywords in the description column
ABS_KEYWORDS = {"abs_challenge", "abs_ball", "abs_called_strike", "challenge"}


def _is_season_active(season: int) -> bool:
    today = datetime.date.today()
    return datetime.date(season, 3, 20) <= today <= datetime.date(season, 11, 1)


def fetch_statcast_range(
    start: datetime.date,
    end: datetime.date,
    team: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    Fetch Statcast data for a date range using pybaseball.
    Falls back to direct CSV fetch if pybaseball fails.
    Returns None on complete failure.
    """
    try:
        import pybaseball  # noqa: PLC0415

        pybaseball.cache.enable()
        logger.info(f"pybaseball: fetching {start} → {end}" + (f" team={team}" if team else ""))
        df = pybaseball.statcast(
            start_dt=start.strftime("%Y-%m-%d"),
            end_dt=end.strftime("%Y-%m-%d"),
            team=team,
            parallel=False,
        )
        if df is None or len(df) == 0:
            logger.warning(f"pybaseball returned empty for {start} → {end}")
            return None
        # Keep only columns that exist in this DataFrame
        keep = [c for c in COLS_NEEDED if c in df.columns]
        return df[keep].copy()
    except Exception as exc:
        logger.warning(f"pybaseball fetch failed ({exc}), trying direct CSV")
        return None


def fetch_abs_pitches_for_season(season: int) -> Optional[pd.DataFrame]:
    """
    Pull all pitches that are ABS-challenge-related for the season.

    Strategy:
    1. Try pybaseball for the full season to date
    2. Filter for ABS challenge descriptions
    3. Return deduplicated DataFrame

    The Statcast `description` column in 2026 contains values like:
    - "abs_called_strike" — called strike via ABS (not challenged)
    - "abs_ball" — ball via ABS
    - "abs_challenge_called_strike" — originally called strike, challenged
    - "abs_challenge_ball" — originally called ball, challenged
    - "abs_challenge_overturn" — challenge succeeded
    - "abs_challenge_upheld" — challenge failed

    In practice the exact values depend on Baseball Savant's schema.
    We capture anything containing "abs" or "challenge" as a candidate.
    """
    if not _is_season_active(season):
        logger.info(f"Season {season} not active — skipping ABS pitch fetch")
        return None

    today = datetime.date.today()
    start = datetime.date(season, 3, 20)

    df = fetch_statcast_range(start, today)
    if df is None:
        return None

    # Filter for ABS-related pitches
    if "description" in df.columns:
        mask = df["description"].str.contains("abs|challenge", case=False, na=False)
        df_abs = df[mask].copy()
        logger.info(f"ABS pitches found: {len(df_abs)} / {len(df)} total pitches")
        if len(df_abs) == 0:
            # Description column exists but no ABS pitches — either early season
            # or the column naming is different. Return all for downstream analysis.
            logger.warning("No ABS descriptions found — returning full Statcast for inspection")
            return df
        return df_abs

    if "abs_challenge_outcome" in df.columns:
        df_abs = df[df["abs_challenge_outcome"].notna()].copy()
        logger.info(f"ABS challenges (via abs_challenge_outcome): {len(df_abs)}")
        return df_abs

    logger.warning("No ABS-specific columns found in Statcast data")
    return df


def classify_abs_outcome(row: pd.Series) -> Optional[str]:
    """
    Classify a Statcast row as an ABS challenge outcome.

    Returns one of: 'overturn', 'upheld', 'no_challenge', None
    """
    desc = str(row.get("description", "")).lower()
    outcome = str(row.get("abs_challenge_outcome", "")).lower()

    if "overturn" in desc or "overturn" in outcome:
        return "overturn"
    if "upheld" in desc or "upheld" in outcome:
        return "upheld"
    if "challenge" in desc:
        # Challenge initiated but outcome unclear from description alone
        return "unknown"
    return None


def identify_challenger(row: pd.Series) -> Optional[str]:
    """
    Determine which team initiated the ABS challenge.
    Returns 'offense' or 'defense', or None if unknown.

    In Statcast, the batter's team is 'offense'. A ball call challenged by
    the batter (seeking a called strike reversal) is 'offense'. A strike call
    challenged by the catcher/pitcher is 'defense'.
    """
    desc = str(row.get("description", "")).lower()
    abs_team = str(row.get("abs_challenge_team", "")).lower()

    if "offense" in abs_team or "batter" in abs_team:
        return "offense"
    if "defense" in abs_team or "catcher" in abs_team or "pitcher" in abs_team:
        return "defense"

    # Infer from description: if original call was "ball" and it was challenged,
    # the batter (offense) is more likely; if "strike", defense is more likely.
    if "abs_challenge" in desc:
        if "ball" in desc:
            return "offense"
        if "strike" in desc:
            return "defense"
    return None
