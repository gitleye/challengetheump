/**
 * Shared TypeScript types for the ABS Dashboard.
 * These must stay in sync with the Pydantic schemas in scripts/lib/schemas.py.
 * Do not edit manually — regenerate from the Python pipeline (see scripts/README.md).
 *
 * Generated: placeholder (run scripts/run.py to regenerate)
 */

// ---- Data quality -------------------------------------------------------

export type DataQuality = 'ok' | 'stale' | 'partial' | 'missing';

export interface SampleSizeWarning {
  field: string;
  n: number;
  threshold: number;
  message: string;
}

// ---- Metadata -----------------------------------------------------------

export interface Metadata {
  last_updated: string; // ISO 8601
  season: number;
  data_quality: DataQuality;
  stale_sources: string[];
  pipeline_version: string;
  games_through: string | null; // ISO date of most recent game included
}

// ---- Teams --------------------------------------------------------------

export interface TeamChallengeStats {
  total_challenges: number;
  offense_challenges: number;
  defense_challenges: number;
  successful_challenges: number;
  success_rate: number | null; // 0–1; null if no challenges
  usage_rate: number | null; // challenges per opportunity; null if unknown
  net_overturns: number; // overturns_for - overturns_against
  challenge_wpa: number | null; // Win Probability Added from successful challenges
  strikeouts_gained: number;
  walks_erased: number;
}

export interface TeamRecord {
  team_id: string; // e.g. "NYY"
  team_name: string;
  team_city: string;
  division: string;
  league: 'AL' | 'NL';
  wins: number;
  losses: number;
  win_pct: number; // 0–1
  win_pct_expected: number | null; // Pythagorean or projection baseline
  challenges: TeamChallengeStats;
  rolling_30d: TeamChallengeStats | null;
  sample_warnings: SampleSizeWarning[];
  data_quality: DataQuality;
}

export interface TeamsData {
  teams: TeamRecord[];
  last_updated: string;
  season: number;
}

// ---- Players ------------------------------------------------------------

export type PlayerRole = 'batter' | 'catcher' | 'pitcher';

export interface PlayerChallengeStats {
  role: PlayerRole;
  total_challenges: number;
  successful_challenges: number;
  success_rate: number | null;
  strikeouts_avoided: number | null; // batters only
  walks_gained: number | null; // batters only
  overturns_generated: number | null; // catchers/pitchers
}

export interface PlayerRecord {
  player_id: number; // MLB player ID
  name: string;
  team_id: string;
  position: string;
  challenges: PlayerChallengeStats;
  sample_warnings: SampleSizeWarning[];
  data_quality: DataQuality;
}

export interface PlayersData {
  players: PlayerRecord[];
  last_updated: string;
  season: number;
}

// ---- Daily time series --------------------------------------------------

export interface DailySnapshot {
  date: string; // ISO date
  league_success_rate: number | null;
  league_total_challenges: number;
  league_total_overturns: number;
}

export interface TeamDailySnapshot {
  date: string;
  team_id: string;
  rolling_30d_challenge_wpa: number | null;
  rolling_30d_success_rate: number | null;
}

export interface DailyData {
  snapshots: DailySnapshot[];
  team_snapshots: TeamDailySnapshot[];
  last_updated: string;
  season: number;
}

// ---- League summary -----------------------------------------------------

export interface LeagueSummary {
  total_challenges: number;
  total_overturns: number;
  overall_success_rate: number | null;
  walk_rate: number | null;
  walk_rate_prior_season: number | null;
  k_rate: number | null;
  k_rate_prior_season: number | null;
  avg_game_time_min: number | null;
  avg_game_time_prior_season_min: number | null;
  pitches_outside_zone_called_strikes_pct: number | null;
  last_updated: string;
  season: number;
  data_quality: DataQuality;
}

// ---- Metrics glossary ---------------------------------------------------

export interface MetricDefinition {
  key: string;
  label: string;
  definition: string;
  formula: string | null;
  caveats: string[];
  unit: string | null;
}

export interface MetricsGlossary {
  metrics: MetricDefinition[];
  generated: string;
}
