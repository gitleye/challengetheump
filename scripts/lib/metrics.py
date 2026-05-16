"""
Metric calculations: WPA, rolling windows, correlations, success rates.

All functions here are pure and tested independently.
Heavy pandas operations live in compute_metrics.py; this module
contains the math that needs unit tests.
"""

from __future__ import annotations

import math
from typing import Optional


# ---- Success rate --------------------------------------------------------

SMALL_SAMPLE_THRESHOLD = 10  # warn if fewer challenges than this


def compute_success_rate(
    successful: int,
    total: int,
) -> tuple[Optional[float], Optional[str]]:
    """
    Returns (rate, warning_message).
    rate is None if total == 0.
    warning_message is non-None if total < SMALL_SAMPLE_THRESHOLD.
    """
    if total == 0:
        return None, None
    rate = successful / total
    warning = None
    if total < SMALL_SAMPLE_THRESHOLD:
        warning = (
            f"Small sample: {total} challenges "
            f"(threshold: {SMALL_SAMPLE_THRESHOLD}). "
            f"Success rate may not be reliable."
        )
    return rate, warning


# ---- WPA -----------------------------------------------------------------

def sum_challenge_wpa(
    wpa_values: list[float],
) -> tuple[Optional[float], Optional[str]]:
    """
    Sum WPA values from successful challenges.

    Returns (total_wpa, warning_message).
    wpa_values should only contain overturned challenges.
    """
    if not wpa_values:
        return None, None
    total = sum(wpa_values)
    warning = None
    if len(wpa_values) < 5:
        warning = (
            f"WPA based on only {len(wpa_values)} successful challenges. "
            f"Highly volatile — interpret with caution."
        )
    return round(total, 4), warning


def compute_rolling_wpa(
    dated_wpa: list[tuple[str, float]],  # (date_str, wpa)
    window_days: int = 30,
    reference_date: Optional[str] = None,
) -> Optional[float]:
    """
    Sum WPA values within the last `window_days` of `reference_date`.

    dated_wpa: list of (ISO date string, wpa float)
    reference_date: ISO date string; defaults to max date in data
    """
    if not dated_wpa:
        return None

    from datetime import date, timedelta

    parsed = [(date.fromisoformat(d), w) for d, w in dated_wpa]
    if reference_date:
        ref = date.fromisoformat(reference_date)
    else:
        ref = max(d for d, _ in parsed)

    cutoff = ref - timedelta(days=window_days)
    window_vals = [w for d, w in parsed if d > cutoff]
    if not window_vals:
        return None
    return round(sum(window_vals), 4)


# ---- Pythagorean win expectancy -----------------------------------------

def pythagorean_win_pct(
    runs_scored: float,
    runs_allowed: float,
    exponent: float = 1.83,
) -> Optional[float]:
    """
    Standard Pythagorean win expectancy.
    Returns None if runs_allowed == 0 or inputs are invalid.
    """
    if runs_allowed <= 0 or runs_scored < 0:
        return None
    rs_exp = runs_scored ** exponent
    ra_exp = runs_allowed ** exponent
    denom = rs_exp + ra_exp
    if denom == 0:
        return None
    return round(rs_exp / denom, 4)


# ---- Rate stats ----------------------------------------------------------

def compute_k_rate(
    strikeouts: int,
    plate_appearances: int,
) -> Optional[float]:
    if plate_appearances == 0:
        return None
    return round(strikeouts / plate_appearances, 4)


def compute_bb_rate(
    walks: int,
    plate_appearances: int,
) -> Optional[float]:
    if plate_appearances == 0:
        return None
    return round(walks / plate_appearances, 4)


# ---- Confidence interval -------------------------------------------------

def wilson_confidence_interval(
    successes: int,
    total: int,
    z: float = 1.96,  # 95% CI
) -> tuple[float, float]:
    """
    Wilson score confidence interval for a proportion.
    Returns (lower, upper) bounds.
    """
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    center = (p + z**2 / (2 * total)) / (1 + z**2 / total)
    spread = (z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2))) / (1 + z**2 / total)
    return (round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4))


# ---- Correlation ---------------------------------------------------------

def pearson_r(xs: list[float], ys: list[float]) -> Optional[float]:
    """
    Pearson correlation coefficient between two lists.
    Returns None if calculation is impossible (< 2 points, zero variance).
    """
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    std_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    std_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if std_x == 0 or std_y == 0:
        return None
    return round(cov / (std_x * std_y), 4)


# ---- Net overturns -------------------------------------------------------

def compute_net_overturns(overturns_for: int, overturns_against: int) -> int:
    """Overturns in a team's favor minus overturns against them."""
    return overturns_for - overturns_against
