"""
Tests for Statcast ABS outcome classification logic.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.statcast import classify_abs_outcome, identify_challenger


class TestClassifyAbsOutcome:
    def _row(self, description="", abs_challenge_outcome=""):
        return pd.Series({"description": description, "abs_challenge_outcome": abs_challenge_outcome})

    def test_overturn_from_description(self):
        row = self._row(description="abs_challenge_overturn")
        assert classify_abs_outcome(row) == "overturn"

    def test_overturn_from_outcome_column(self):
        row = self._row(abs_challenge_outcome="overturn")
        assert classify_abs_outcome(row) == "overturn"

    def test_upheld_from_description(self):
        row = self._row(description="abs_challenge_upheld")
        assert classify_abs_outcome(row) == "upheld"

    def test_upheld_from_outcome_column(self):
        row = self._row(abs_challenge_outcome="upheld")
        assert classify_abs_outcome(row) == "upheld"

    def test_unknown_challenge(self):
        row = self._row(description="abs_challenge_called_strike")
        assert classify_abs_outcome(row) == "unknown"

    def test_non_challenge_returns_none(self):
        row = self._row(description="called_strike")
        assert classify_abs_outcome(row) is None

    def test_empty_returns_none(self):
        row = self._row()
        assert classify_abs_outcome(row) is None


class TestIdentifyChallenger:
    def _row(self, description="", abs_challenge_team=""):
        return pd.Series({"description": description, "abs_challenge_team": abs_challenge_team})

    def test_offense_from_team_column(self):
        row = self._row(abs_challenge_team="offense")
        assert identify_challenger(row) == "offense"

    def test_defense_from_team_column(self):
        row = self._row(abs_challenge_team="defense")
        assert identify_challenger(row) == "defense"

    def test_batter_keyword_maps_to_offense(self):
        row = self._row(abs_challenge_team="batter")
        assert identify_challenger(row) == "offense"

    def test_catcher_keyword_maps_to_defense(self):
        row = self._row(abs_challenge_team="catcher")
        assert identify_challenger(row) == "defense"

    def test_infer_offense_from_ball_challenge(self):
        row = self._row(description="abs_challenge_ball")
        assert identify_challenger(row) == "offense"

    def test_infer_defense_from_strike_challenge(self):
        row = self._row(description="abs_challenge_called_strike")
        assert identify_challenger(row) == "defense"

    def test_unknown_returns_none(self):
        row = self._row(description="abs_challenge")
        assert identify_challenger(row) is None
