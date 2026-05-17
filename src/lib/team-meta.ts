/**
 * MLB team metadata: abbreviation → numeric ID + primary color.
 * Used for team logo URLs and color-coded UI elements.
 */

export interface TeamMeta {
  id: number;
  color: string;        // primary brand color (dark mode friendly)
  colorLight: string;   // primary brand color for light mode
  name: string;
}

export const TEAM_META: Record<string, TeamMeta> = {
  AZ:  { id: 109, color: '#E8365A', colorLight: '#A71930', name: 'Arizona Diamondbacks' },
  ATL: { id: 144, color: '#F04E6E', colorLight: '#CE1141', name: 'Atlanta Braves' },
  BAL: { id: 110, color: '#FF6B2B', colorLight: '#DF4601', name: 'Baltimore Orioles' },
  BOS: { id: 111, color: '#E04850', colorLight: '#BD3039', name: 'Boston Red Sox' },
  CHC: { id: 112, color: '#4A7DD4', colorLight: '#0E3386', name: 'Chicago Cubs' },
  CWS: { id: 145, color: '#8A8A8A', colorLight: '#27251F', name: 'Chicago White Sox' },
  CIN: { id: 113, color: '#EF4444', colorLight: '#C6011F', name: 'Cincinnati Reds' },
  CLE: { id: 114, color: '#3B8DD4', colorLight: '#00385D', name: 'Cleveland Guardians' },
  COL: { id: 115, color: '#7B7BBF', colorLight: '#333366', name: 'Colorado Rockies' },
  DET: { id: 116, color: '#4A80BF', colorLight: '#0C2340', name: 'Detroit Tigers' },
  HOU: { id: 117, color: '#3B7DD9', colorLight: '#002D62', name: 'Houston Astros' },
  KC:  { id: 118, color: '#4A8DE0', colorLight: '#004687', name: 'Kansas City Royals' },
  LAA: { id: 108, color: '#E84050', colorLight: '#BA0021', name: 'Los Angeles Angels' },
  LAD: { id: 119, color: '#4A9AE0', colorLight: '#005A9C', name: 'Los Angeles Dodgers' },
  MIA: { id: 146, color: '#40C8F0', colorLight: '#00A3E0', name: 'Miami Marlins' },
  MIL: { id: 158, color: '#FFC52F', colorLight: '#C9A200', name: 'Milwaukee Brewers' },
  MIN: { id: 142, color: '#4A80C8', colorLight: '#002B5C', name: 'Minnesota Twins' },
  NYM: { id: 121, color: '#4A80E0', colorLight: '#002D72', name: 'New York Mets' },
  NYY: { id: 147, color: '#4A7AD4', colorLight: '#003087', name: 'New York Yankees' },
  ATH: { id: 133, color: '#2D8B5E', colorLight: '#003831', name: 'Athletics' },
  PHI: { id: 143, color: '#F04050', colorLight: '#E81828', name: 'Philadelphia Phillies' },
  PIT: { id: 134, color: '#FDB827', colorLight: '#D49B00', name: 'Pittsburgh Pirates' },
  SD:  { id: 135, color: '#A08060', colorLight: '#2F241D', name: 'San Diego Padres' },
  SF:  { id: 137, color: '#FF7A40', colorLight: '#FD5A1E', name: 'San Francisco Giants' },
  SEA: { id: 136, color: '#4A80C0', colorLight: '#0C2C56', name: 'Seattle Mariners' },
  STL: { id: 138, color: '#E84060', colorLight: '#C41E3A', name: 'St. Louis Cardinals' },
  TB:  { id: 139, color: '#4A80D0', colorLight: '#092C5C', name: 'Tampa Bay Rays' },
  TEX: { id: 140, color: '#4A7ACA', colorLight: '#003278', name: 'Texas Rangers' },
  TOR: { id: 141, color: '#4A90D4', colorLight: '#134A8E', name: 'Toronto Blue Jays' },
  WSH: { id: 120, color: '#E03030', colorLight: '#AB0003', name: 'Washington Nationals' },
};

/** Get team logo URL from MLB Static CDN */
export function teamLogoUrl(teamId: string): string {
  const meta = TEAM_META[teamId];
  if (!meta) return '';
  return `https://www.mlbstatic.com/team-logos/${meta.id}.svg`;
}

/** Get player headshot URL from MLB CDN (same pattern used on player detail pages) */
export function playerHeadshotUrl(playerId: number): string {
  return `https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/${playerId}/headshot/67/current`;
}

/** Get team color for current theme context */
export function teamColor(teamId: string, isLight = false): string {
  const meta = TEAM_META[teamId];
  if (!meta) return '#888888';
  return isLight ? meta.colorLight : meta.color;
}
