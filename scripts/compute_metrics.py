"""
Read raw fetched data and compute all derived metrics.

Uses real Baseball Savant ABS leaderboard data with these key fields:
  n_challenges           → total challenges
  n_overturns            → successful (overturned) challenges
  rate_overturns         → success rate (0–1)
  net_net_runs           → net run value vs. expected (our WPA-proxy headline metric)
  n_chal_runs_gained     → runs gained via own challenges
  n_chal_runs_lost       → runs surrendered via opponent challenges
  n_strikeouts           → strikeouts erased via challenges
  n_walks                → walks gained via challenges
  team_abbr / player_name / fielder_2 → identity fields
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from lib.metrics import (
    compute_net_overturns,
    compute_rolling_wpa,
    compute_success_rate,
    pearson_r,
    pythagorean_win_pct,
    sum_challenge_wpa,
    wilson_confidence_interval,
)
from lib.savant import safe_float, safe_int, safe_rate, team_id_from_record
from lib.schemas import (
    DataQuality,
    DailyData,
    DailySnapshot,
    LeagueSummary,
    PlayerChallengeStats,
    PlayerRecord,
    PlayerRole,
    PlayersData,
    SampleSizeWarning,
    TeamChallengeStats,
    TeamDailySnapshot,
    TeamRecord,
    TeamsData,
)

logger = logging.getLogger(__name__)


@dataclass
class ComputedMetrics:
    teams: TeamsData
    players: PlayersData
    daily: DailyData
    league: LeagueSummary
    now_iso: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def compute(fetch) -> ComputedMetrics:  # type: ignore[no-untyped-def]
    from fetch_data import FetchResult
    assert isinstance(fetch, FetchResult)

    now = (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )

    teams_data = _compute_teams(fetch, now)
    players_data = _compute_players(fetch, now)
    daily_data = _compute_daily(fetch, teams_data, now)
    league = _compute_league(fetch, teams_data, now)

    return ComputedMetrics(
        teams=teams_data,
        players=players_data,
        daily=daily_data,
        league=league,
        now_iso=now,
    )


# ---- Teams ---------------------------------------------------------------

def _compute_teams(fetch, now: str) -> TeamsData:  # type: ignore[no-untyped-def]
    standings_by_id: dict[str, dict] = {s["team_id"]: s for s in fetch.standings}

    # Index Savant batting/catching data by team_abbr
    batting_by_team: dict[str, dict] = {}
    catching_by_team: dict[str, dict] = {}

    if fetch.abs_batting_team:
        for rec in fetch.abs_batting_team:
            tid = team_id_from_record(rec)
            batting_by_team[tid] = rec

    if fetch.abs_catching_team:
        for rec in fetch.abs_catching_team:
            tid = team_id_from_record(rec)
            catching_by_team[tid] = rec

    team_records: list[TeamRecord] = []
    for team_id, standing in standings_by_id.items():
        bat = batting_by_team.get(team_id, {})
        cat = catching_by_team.get(team_id, {})

        ch_stats, warnings, quality = _team_challenge_stats_from_savant(team_id, bat, cat)

        record = TeamRecord(
            team_id=team_id,
            team_name=standing["team_name"],
            team_city=standing.get("team_city", ""),
            division=standing["division"],
            league=standing["league"],
            wins=standing["wins"],
            losses=standing["losses"],
            win_pct=round(standing["win_pct"], 4),
            win_pct_expected=None,  # needs RS/RA data — future enhancement
            challenges=ch_stats,
            rolling_30d=None,  # no daily breakdown from Savant leaderboard
            sample_warnings=warnings,
            data_quality=quality,
        )
        team_records.append(record)

    # Sort by challenge WPA (net_net_runs) descending
    team_records.sort(
        key=lambda t: (t.challenges.challenge_wpa or float("-inf")),
        reverse=True,
    )

    return TeamsData(teams=team_records, last_updated=now, season=fetch.season)


def _team_challenge_stats_from_savant(
    team_id: str,
    bat: dict,  # batting-team record
    cat: dict,  # catching-team record
) -> tuple[TeamChallengeStats, list[SampleSizeWarning], DataQuality]:
    # Offense stats (batting team = team at bat challenging calls)
    offense_challenges = safe_int(bat.get("n_challenges"))
    offense_overturns = safe_int(bat.get("n_overturns"))
    offense_runs_gained = safe_float(bat.get("n_chal_runs_gained")) or 0.0
    offense_net_runs = safe_float(bat.get("net_net_runs"))
    offense_k = safe_int(bat.get("n_strikeouts"))
    offense_bb = safe_int(bat.get("n_walks"))

    # Defense stats (catching team = fielding team challenging calls)
    defense_challenges = safe_int(cat.get("n_challenges"))
    defense_overturns = safe_int(cat.get("n_overturns"))
    defense_runs_gained = safe_float(cat.get("n_chal_runs_gained")) or 0.0
    defense_net_runs = safe_float(cat.get("net_net_runs"))

    total_challenges = offense_challenges + defense_challenges
    total_overturns = offense_overturns + defense_overturns

    success_rate, rate_warning = compute_success_rate(total_overturns, total_challenges)

    # Also compute opponent overturns for net_overturns
    opponent_overturns = safe_int(bat.get("n_overturns_against", 0)) + safe_int(cat.get("n_overturns_against", 0))
    net_overturns = compute_net_overturns(total_overturns, opponent_overturns)

    # Headline metric: net run value above expected (from Savant)
    # bat net_net_runs = runs from batting challenges vs expected
    # cat net_net_runs = runs from catching challenges vs expected
    challenge_wpa: Optional[float] = None
    if offense_net_runs is not None or defense_net_runs is not None:
        challenge_wpa = round(
            (offense_net_runs or 0.0) + (defense_net_runs or 0.0),
            4,
        )

    warnings: list[SampleSizeWarning] = []
    if rate_warning:
        warnings.append(SampleSizeWarning(
            field="success_rate", n=total_challenges,
            threshold=10, message=rate_warning,
        ))
    if total_challenges > 0 and total_challenges < 5:
        warnings.append(SampleSizeWarning(
            field="challenge_wpa", n=total_challenges,
            threshold=5,
            message=f"Net run value based on only {total_challenges} challenges — highly volatile.",
        ))

    ch_stats = TeamChallengeStats(
        total_challenges=total_challenges,
        offense_challenges=offense_challenges,
        defense_challenges=defense_challenges,
        successful_challenges=total_overturns,
        success_rate=success_rate,
        net_overturns=net_overturns,
        challenge_wpa=challenge_wpa,
        strikeouts_overturned=offense_k + safe_int(defense_k := cat.get("n_strikeouts", 0)),
        walks_gained=offense_bb + safe_int(cat.get("n_walks", 0)),
    )

    quality = DataQuality.OK if total_challenges > 0 else DataQuality.MISSING
    return ch_stats, warnings, quality


# ---- Players -------------------------------------------------------------

def _compute_players(fetch, now: str) -> PlayersData:  # type: ignore[no-untyped-def]
    records: list[PlayerRecord] = []

    # Catchers from dedicated endpoint
    if fetch.abs_catchers:
        for rec in sorted(fetch.abs_catchers, key=lambda r: safe_int(r.get("n_challenges")), reverse=True)[:50]:
            pr = _player_record_from_savant(rec, PlayerRole.CATCHER)
            if pr:
                records.append(pr)

    # Batters — use dedicated batter endpoint, fall back to all-players
    batter_source = fetch.abs_batters or fetch.abs_players
    if batter_source:
        for rec in sorted(batter_source, key=lambda r: safe_int(r.get("n_challenges")), reverse=True)[:50]:
            pr = _player_record_from_savant(rec, PlayerRole.BATTER)
            if pr:
                records.append(pr)

    return PlayersData(players=records, last_updated=now, season=fetch.season)


def _player_record_from_savant(
    rec: dict,
    role: PlayerRole,
) -> Optional[PlayerRecord]:
    total = safe_int(rec.get("n_challenges"))
    if total == 0:
        return None

    overturns = safe_int(rec.get("n_overturns"))
    success_rate, rate_warning = compute_success_rate(overturns, total)

    team_id = team_id_from_record(rec)
    name = str(rec.get("player_name", f"Player {rec.get('id', '?')}"))

    warnings: list[SampleSizeWarning] = []
    if rate_warning:
        warnings.append(SampleSizeWarning(
            field="success_rate", n=total, threshold=10, message=rate_warning,
        ))

    strikeouts_avoided: Optional[int] = None
    walks_gained: Optional[int] = None
    overturns_generated: Optional[int] = None

    if role == PlayerRole.BATTER:
        strikeouts_avoided = safe_int(rec.get("n_strikeouts"))
        walks_gained = safe_int(rec.get("n_walks"))
    else:
        overturns_generated = overturns

    player_id_raw = rec.get("fielder_2") or rec.get("id") or rec.get("bat_team_id") or 0
    try:
        player_id = int(player_id_raw)
    except (TypeError, ValueError):
        player_id = abs(hash(str(player_id_raw))) % 1_000_000

    ch_stats = PlayerChallengeStats(
        role=role,
        total_challenges=total,
        successful_challenges=overturns,
        success_rate=success_rate,
        strikeouts_avoided=strikeouts_avoided,
        walks_gained=walks_gained,
        overturns_generated=overturns_generated,
    )

    return PlayerRecord(
        player_id=player_id,
        name=name,
        team_id=team_id,
        position=role.value.capitalize(),
        challenges=ch_stats,
        sample_warnings=warnings,
        data_quality=DataQuality.OK,
    )


# ---- Daily time series ---------------------------------------------------

def _compute_daily(fetch, teams_data: TeamsData, now: str) -> DailyData:  # type: ignore[no-untyped-def]
    # The Baseball Savant leaderboard doesn't provide daily breakdowns —
    # that requires the full Statcast pitch-by-pitch data.
    # We produce a single "as of today" snapshot for now.
    # Daily time series will be enriched in future pipeline runs.

    total_challenges = sum(t.challenges.total_challenges for t in teams_data.teams)
    total_overturns = sum(t.challenges.successful_challenges for t in teams_data.teams)
    rate, _ = compute_success_rate(total_overturns, total_challenges)

    snapshot = DailySnapshot(
        date=now[:10],
        league_success_rate=rate,
        league_total_challenges=total_challenges,
        league_total_overturns=total_overturns,
    )

    team_snapshots = [
        TeamDailySnapshot(
            date=now[:10],
            team_id=t.team_id,
            rolling_30d_challenge_wpa=t.challenges.challenge_wpa,
            rolling_30d_success_rate=t.challenges.success_rate,
        )
        for t in teams_data.teams
        if t.challenges.total_challenges > 0
    ]

    return DailyData(
        snapshots=[snapshot],
        team_snapshots=team_snapshots,
        last_updated=now,
        season=fetch.season,
    )


# ---- League summary ------------------------------------------------------

def _compute_league(fetch, teams_data: TeamsData, now: str) -> LeagueSummary:  # type: ignore[no-untyped-def]
    challenge_sum = sum(t.challenges.total_challenges for t in teams_data.teams)
    overturn_sum = sum(t.challenges.successful_challenges for t in teams_data.teams)
    if challenge_sum % 2 != 0 or overturn_sum % 2 != 0:
        logger.warning("Odd total (%d challenges, %d overturns) — possible data anomaly", challenge_sum, overturn_sum)
    total_challenges = challenge_sum // 2  # deduplicate bat+catch
    total_overturns = overturn_sum // 2
    overall_rate, _ = compute_success_rate(total_overturns, total_challenges)

    def _rate(stats: Optional[dict], k_field: str, bb_field: str, pa_field: str):
        if not stats:
            return None, None
        pa = int(stats.get(pa_field, 0) or 0)
        if pa == 0:
            return None, None
        k = int(stats.get(k_field, 0) or 0)
        bb = int(stats.get(bb_field, 0) or 0)
        return round(k / pa, 4), round(bb / pa, 4)

    k_rate, bb_rate = _rate(fetch.league_hitting, "strikeOuts", "baseOnBalls", "plateAppearances")
    k_rate_prior, bb_rate_prior = _rate(
        fetch.prior_league_hitting, "strikeOuts", "baseOnBalls", "plateAppearances"
    )

    quality = DataQuality.OK if total_challenges > 0 else DataQuality.MISSING
    if fetch.stale_sources:
        quality = DataQuality.PARTIAL

    return LeagueSummary(
        total_challenges=total_challenges,
        total_overturns=total_overturns,
        overall_success_rate=overall_rate,
        walk_rate=bb_rate,
        walk_rate_prior_season=bb_rate_prior,
        k_rate=k_rate,
        k_rate_prior_season=k_rate_prior,
        last_updated=now,
        season=fetch.season,
        data_quality=quality,
    )
