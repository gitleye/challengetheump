"""
Unit tests for lib/metrics.py — all the math that underpins the dashboard.

These are fast, pure-function tests. No network calls, no file I/O.
"""

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.metrics import (
    SMALL_SAMPLE_THRESHOLD,
    compute_net_overturns,
    compute_rolling_wpa,
    compute_success_rate,
    pearson_r,
    pythagorean_win_pct,
    sum_challenge_wpa,
    wilson_confidence_interval,
)


# ---- compute_success_rate -----------------------------------------------

class TestSuccessRate:
    def test_zero_total_returns_none(self):
        rate, warning = compute_success_rate(0, 0)
        assert rate is None
        assert warning is None

    def test_perfect_rate(self):
        rate, warning = compute_success_rate(5, 5)
        assert rate == 1.0

    def test_zero_rate(self):
        rate, _ = compute_success_rate(0, 10)
        assert rate == 0.0

    def test_partial_rate(self):
        rate, _ = compute_success_rate(3, 4)
        assert abs(rate - 0.75) < 1e-9

    def test_small_sample_warning_triggered(self):
        _, warning = compute_success_rate(1, SMALL_SAMPLE_THRESHOLD - 1)
        assert warning is not None
        assert "sample" in warning.lower()

    def test_no_warning_above_threshold(self):
        _, warning = compute_success_rate(5, SMALL_SAMPLE_THRESHOLD)
        assert warning is None

    def test_rate_is_proportion(self):
        rate, _ = compute_success_rate(7, 14)
        assert 0.0 <= rate <= 1.0


# ---- sum_challenge_wpa --------------------------------------------------

class TestSumChallengeWpa:
    def test_empty_list_returns_none(self):
        total, warning = sum_challenge_wpa([])
        assert total is None
        assert warning is None

    def test_sums_correctly(self):
        total, _ = sum_challenge_wpa([0.1, 0.2, 0.15, 0.05, 0.1])
        assert abs(total - 0.6) < 1e-4

    def test_rounds_to_four_decimal_places(self):
        total, _ = sum_challenge_wpa([0.12345678])
        assert total == 0.1235

    def test_small_sample_warning(self):
        _, warning = sum_challenge_wpa([0.1, 0.2])  # < 5 items
        assert warning is not None

    def test_no_warning_at_five_plus(self):
        _, warning = sum_challenge_wpa([0.1, 0.2, 0.1, 0.05, 0.15])
        assert warning is None

    def test_negative_wpa_values(self):
        # Defensive challenge that backfired — negative WPA should sum
        total, _ = sum_challenge_wpa([-0.05, 0.2, 0.1])
        assert abs(total - 0.25) < 1e-4


# ---- compute_rolling_wpa ------------------------------------------------

class TestRollingWpa:
    def test_empty_returns_none(self):
        assert compute_rolling_wpa([]) is None

    def test_all_in_window(self):
        data = [("2026-04-01", 0.1), ("2026-04-15", 0.2), ("2026-04-29", 0.15)]
        result = compute_rolling_wpa(data, window_days=30, reference_date="2026-04-30")
        assert abs(result - 0.45) < 1e-4

    def test_excludes_outside_window(self):
        data = [
            ("2026-03-01", 0.5),  # outside 30-day window from Apr 30
            ("2026-04-15", 0.2),
            ("2026-04-29", 0.15),
        ]
        result = compute_rolling_wpa(data, window_days=30, reference_date="2026-04-30")
        assert abs(result - 0.35) < 1e-4

    def test_all_outside_window_returns_none(self):
        data = [("2026-01-01", 0.5), ("2026-02-01", 0.3)]
        result = compute_rolling_wpa(data, window_days=30, reference_date="2026-04-30")
        assert result is None

    def test_uses_max_date_as_default_reference(self):
        data = [("2026-04-01", 0.1), ("2026-04-15", 0.2)]
        # Max date is Apr 15; 30-day window from Apr 15 includes Apr 1
        result = compute_rolling_wpa(data, window_days=30)
        assert abs(result - 0.3) < 1e-4


# ---- pythagorean_win_pct ------------------------------------------------

class TestPythagorean:
    def test_equal_rs_ra_gives_500(self):
        result = pythagorean_win_pct(100, 100)
        assert abs(result - 0.5) < 1e-4

    def test_more_rs_than_ra(self):
        result = pythagorean_win_pct(200, 100)
        assert result > 0.5

    def test_more_ra_than_rs(self):
        result = pythagorean_win_pct(100, 200)
        assert result < 0.5

    def test_zero_ra_returns_none(self):
        assert pythagorean_win_pct(100, 0) is None

    def test_zero_rs(self):
        result = pythagorean_win_pct(0, 100)
        assert result == 0.0

    def test_result_in_range(self):
        result = pythagorean_win_pct(500, 450)
        assert 0.0 <= result <= 1.0

    def test_rounds_to_four_places(self):
        result = pythagorean_win_pct(150, 130)
        assert result == round(result, 4)


# ---- wilson_confidence_interval -----------------------------------------

class TestWilson:
    def test_zero_total_returns_full_range(self):
        lo, hi = wilson_confidence_interval(0, 0)
        assert lo == 0.0
        assert hi == 1.0

    def test_bounds_within_zero_one(self):
        lo, hi = wilson_confidence_interval(3, 5)
        assert 0.0 <= lo < hi <= 1.0

    def test_perfect_rate_upper_bound_less_than_one(self):
        # Wilson CI for 5/5 should be below 1.0
        lo, hi = wilson_confidence_interval(5, 5)
        assert hi <= 1.0
        assert lo > 0.5  # should be high

    def test_zero_rate_lower_bound_above_zero(self):
        lo, hi = wilson_confidence_interval(0, 10)
        assert lo == 0.0
        assert hi > 0.0

    def test_symmetric_around_half(self):
        lo1, hi1 = wilson_confidence_interval(5, 10)  # 50%
        # Roughly symmetric
        assert abs((lo1 + hi1) / 2 - 0.5) < 0.1


# ---- pearson_r ----------------------------------------------------------

class TestPearsonR:
    def test_perfect_positive_correlation(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]
        assert abs(pearson_r(xs, ys) - 1.0) < 1e-9

    def test_perfect_negative_correlation(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [10.0, 8.0, 6.0, 4.0, 2.0]
        assert abs(pearson_r(xs, ys) - (-1.0)) < 1e-9

    def test_no_correlation(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [2.0, 2.0, 2.0, 2.0]  # constant y → zero variance
        assert pearson_r(xs, ys) is None

    def test_too_few_points(self):
        assert pearson_r([1.0], [1.0]) is None
        assert pearson_r([], []) is None

    def test_mismatched_lengths(self):
        assert pearson_r([1.0, 2.0], [1.0]) is None

    def test_result_in_range(self):
        xs = [0.2, 0.4, 0.3, 0.6, 0.5]
        ys = [0.45, 0.50, 0.48, 0.55, 0.52]
        r = pearson_r(xs, ys)
        assert r is not None
        assert -1.0 <= r <= 1.0


# ---- compute_net_overturns ----------------------------------------------

class TestNetOverturns:
    def test_positive(self):
        assert compute_net_overturns(10, 6) == 4

    def test_negative(self):
        assert compute_net_overturns(3, 8) == -5

    def test_zero(self):
        assert compute_net_overturns(5, 5) == 0
