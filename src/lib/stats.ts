/**
 * Client-side helper functions for stat display and formatting.
 * All heavy computation happens in the Python pipeline — these are presentation helpers only.
 */

/** Format a decimal win percentage as ".500" style string. */
export function formatWinPct(pct: number | null): string {
  if (pct === null) return '—';
  return pct.toFixed(3).replace(/^0/, '');
}

/** Format a success rate as "63.4%" string. */
export function formatRate(rate: number | null, decimals = 1): string {
  if (rate === null) return '—';
  return `${(rate * 100).toFixed(decimals)}%`;
}

/** Format a WPA value as "+0.32" or "−0.14" with sign. */
export function formatWpa(wpa: number | null): string {
  if (wpa === null) return '—';
  const sign = wpa >= 0 ? '+' : '';
  return `${sign}${wpa.toFixed(2)}`;
}

/** Format a game time in minutes as "2h 58m". */
export function formatGameTime(minutes: number | null): string {
  if (minutes === null) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

/** Return a CSS color class name based on a delta (positive = green, negative = red). */
export function deltaColorClass(delta: number | null): string {
  if (delta === null) return 'text-text-tertiary';
  if (delta > 0) return 'text-success';
  if (delta < 0) return 'text-danger';
  return 'text-text-tertiary';
}

/** Clamp a number between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Compute rank within an array by a numeric accessor (1-indexed, higher = better by default). */
export function rankBy<T>(
  items: T[],
  accessor: (item: T) => number | null,
  ascending = false
): Map<T, number> {
  const sorted = [...items]
    .filter((item) => accessor(item) !== null)
    .sort((a, b) => {
      const av = accessor(a) ?? 0;
      const bv = accessor(b) ?? 0;
      return ascending ? av - bv : bv - av;
    });

  const rankMap = new Map<T, number>();
  sorted.forEach((item, index) => rankMap.set(item, index + 1));
  return rankMap;
}

/** Format a date string (ISO) as "May 16, 2026". */
export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

/** Compute Pearson correlation coefficient between two arrays. */
export function pearsonR(xs: number[], ys: number[]): number | null {
  const n = Math.min(xs.length, ys.length);
  if (n < 3) return null;
  const mx = xs.reduce((a, b) => a + b, 0) / n;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0, dx2 = 0, dy2 = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx;
    const dy = ys[i] - my;
    num += dx * dy;
    dx2 += dx * dx;
    dy2 += dy * dy;
  }
  const denom = Math.sqrt(dx2 * dy2);
  return denom === 0 ? null : num / denom;
}

/** Format a short date string (ISO) as "May 16". */
export function formatDateShort(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

/** Return true if a date is within the current MLB season window (roughly April–October). */
export function isInSeason(date: Date = new Date()): boolean {
  const month = date.getMonth() + 1; // 1-indexed
  return month >= 3 && month <= 10;
}
