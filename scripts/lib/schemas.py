"""
Pydantic schemas — source of truth for all data shapes.
These must stay in sync with src/lib/types.ts.
Run write_json.py to regenerate the TypeScript types.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class DataQuality(str, Enum):
    OK = "ok"
    STALE = "stale"
    PARTIAL = "partial"
    MISSING = "missing"


class SampleSizeWarning(BaseModel):
    field: str
    n: int
    threshold: int
    message: str


class Metadata(BaseModel):
    last_updated: str = Field(..., description="ISO 8601 datetime")
    season: int
    data_quality: DataQuality
    stale_sources: list[str] = Field(default_factory=list)
    pipeline_version: str
    games_through: Optional[str] = None  # ISO date


# ---- Teams ---------------------------------------------------------------

class TeamChallengeStats(BaseModel):
    total_challenges: int = 0
    offense_challenges: int = 0
    defense_challenges: int = 0
    successful_challenges: int = 0
    success_rate: Optional[float] = None  # 0–1
    usage_rate: Optional[float] = None
    net_overturns: int = 0
    challenge_wpa: Optional[float] = None
    strikeouts_overturned: int = 0
    walks_gained: int = 0


class TeamRecord(BaseModel):
    team_id: str
    team_name: str
    team_city: str
    division: str
    league: Literal["AL", "NL"]
    wins: int
    losses: int
    win_pct: float
    win_pct_expected: Optional[float] = None
    challenges: TeamChallengeStats
    rolling_30d: Optional[TeamChallengeStats] = None
    sample_warnings: list[SampleSizeWarning] = Field(default_factory=list)
    data_quality: DataQuality = DataQuality.OK


class TeamsData(BaseModel):
    teams: list[TeamRecord]
    last_updated: str
    season: int


# ---- Players -------------------------------------------------------------

class PlayerRole(str, Enum):
    BATTER = "batter"
    CATCHER = "catcher"
    PITCHER = "pitcher"


class PlayerChallengeStats(BaseModel):
    role: PlayerRole
    total_challenges: int = 0
    successful_challenges: int = 0
    success_rate: Optional[float] = None
    strikeouts_avoided: Optional[int] = None  # batters only
    walks_gained: Optional[int] = None         # batters only
    overturns_generated: Optional[int] = None  # catchers/pitchers


class PlayerRecord(BaseModel):
    player_id: int  # MLB player ID
    name: str
    team_id: str
    position: str
    challenges: PlayerChallengeStats
    sample_warnings: list[SampleSizeWarning] = Field(default_factory=list)
    data_quality: DataQuality = DataQuality.OK


class PlayersData(BaseModel):
    players: list[PlayerRecord]
    last_updated: str
    season: int


# ---- Daily time series ---------------------------------------------------

class DailySnapshot(BaseModel):
    date: str  # ISO date
    league_success_rate: Optional[float] = None
    league_total_challenges: int = 0
    league_total_overturns: int = 0


class TeamDailySnapshot(BaseModel):
    date: str
    team_id: str
    rolling_30d_challenge_wpa: Optional[float] = None
    rolling_30d_success_rate: Optional[float] = None


class DailyData(BaseModel):
    snapshots: list[DailySnapshot]
    team_snapshots: list[TeamDailySnapshot]
    last_updated: str
    season: int


# ---- League summary ------------------------------------------------------

class LeagueSummary(BaseModel):
    total_challenges: int = 0
    total_overturns: int = 0
    overall_success_rate: Optional[float] = None
    walk_rate: Optional[float] = None
    walk_rate_prior_season: Optional[float] = None
    k_rate: Optional[float] = None
    k_rate_prior_season: Optional[float] = None
    avg_game_time_min: Optional[float] = None
    avg_game_time_prior_season_min: Optional[float] = None
    pitches_outside_zone_called_strikes_pct: Optional[float] = None
    last_updated: str
    season: int
    data_quality: DataQuality = DataQuality.OK


# ---- Metrics glossary ----------------------------------------------------

class MetricDefinition(BaseModel):
    key: str
    label: str
    definition: str
    formula: Optional[str] = None
    caveats: list[str] = Field(default_factory=list)
    unit: Optional[str] = None


class MetricsGlossary(BaseModel):
    metrics: list[MetricDefinition]
    generated: str  # ISO datetime
