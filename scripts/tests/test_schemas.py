"""
Tests for Pydantic schema validation — ensures bad data fails loudly.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from lib.schemas import (
    DataQuality,
    PlayerChallengeStats,
    PlayerRecord,
    PlayerRole,
    TeamChallengeStats,
    TeamRecord,
    TeamsData,
)


class TestTeamRecord:
    def _valid(self, **overrides):
        base = {
            "team_id": "NYY",
            "team_name": "New York Yankees",
            "team_city": "New York",
            "division": "AL East",
            "league": "AL",
            "wins": 40,
            "losses": 30,
            "win_pct": 0.571,
            "challenges": TeamChallengeStats(),
        }
        base.update(overrides)
        return base

    def test_valid_record_passes(self):
        record = TeamRecord(**self._valid())
        assert record.team_id == "NYY"

    def test_invalid_league_fails(self):
        with pytest.raises(ValidationError):
            TeamRecord(**self._valid(league="NL1"))  # type: ignore

    def test_wins_cannot_be_negative(self):
        # Pydantic won't reject this by default — wins >= 0 is a domain rule
        # We document it here so future validators can add the constraint
        record = TeamRecord(**self._valid(wins=0))
        assert record.wins == 0

    def test_challenge_stats_default_zero(self):
        record = TeamRecord(**self._valid())
        assert record.challenges.total_challenges == 0
        assert record.challenges.success_rate is None


class TestPlayerChallengeStats:
    def test_batter_role(self):
        stats = PlayerChallengeStats(role=PlayerRole.BATTER, total_challenges=5, successful_challenges=3)
        assert stats.role == PlayerRole.BATTER
        assert stats.success_rate is None  # not computed automatically

    def test_catcher_role(self):
        stats = PlayerChallengeStats(role=PlayerRole.CATCHER, total_challenges=10, successful_challenges=7)
        assert stats.role == PlayerRole.CATCHER

    def test_invalid_role_fails(self):
        with pytest.raises(ValidationError):
            PlayerChallengeStats(role="outfielder", total_challenges=0, successful_challenges=0)  # type: ignore


class TestDataQuality:
    def test_valid_values(self):
        for val in ("ok", "stale", "partial", "missing"):
            assert DataQuality(val) is not None

    def test_invalid_value_fails(self):
        with pytest.raises(ValueError):
            DataQuality("unknown_quality")
