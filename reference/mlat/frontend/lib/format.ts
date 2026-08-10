import type { Position, StatusTone } from '@/lib/types';

export function number(value: unknown, digits = 0, fallback = 'n/a'): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return digits > 0 ? numeric.toFixed(digits) : Math.round(numeric).toLocaleString();
}

export function percent(value: unknown, digits = 0, fallback = 'n/a'): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return `${(numeric * 100).toFixed(digits)}%`;
}

export function relativeTime(timestamp: unknown): string {
  const numeric = Number(timestamp);
  if (!Number.isFinite(numeric)) return 'n/a';
  const seconds = Math.max(0, Math.round(Date.now() / 1000 - numeric));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function ageSeconds(timestamp: unknown): number | null {
  const numeric = Number(timestamp);
  return Number.isFinite(numeric) ? Math.max(0, Date.now() / 1000 - numeric) : null;
}

export function titleCase(value: unknown): string {
  return String(value || 'unknown').replaceAll(/[_-]+/g, ' ').replace(/\b\w/g, (match) => match.toUpperCase());
}

export function toneFromScore(score: unknown): StatusTone {
  const numeric = Number(score);
  if (!Number.isFinite(numeric)) return 'neutral';
  if (numeric >= 0.8) return 'healthy';
  if (numeric >= 0.55) return 'attention';
  return 'failure';
}

export function toneFromFreshness(value: unknown, warnAt = 30, riskAt = 120): StatusTone {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 'neutral';
  if (numeric <= warnAt) return 'healthy';
  if (numeric <= riskAt) return 'attention';
  return 'failure';
}

export function formatDateTime(epochSeconds: unknown): string {
  const numeric = Number(epochSeconds);
  return Number.isFinite(numeric) ? `${new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(numeric * 1000))} UTC` : 'Awaiting timestamp';
}

export function formatCoordinate(lat: unknown, lon: unknown): string {
  const latitude = Number(lat);
  const longitude = Number(lon);
  return Number.isFinite(latitude) && Number.isFinite(longitude) ? `${latitude.toFixed(3)}°, ${longitude.toFixed(3)}°` : 'No coordinates';
}

export function formatAltitude(meters: unknown): string {
  const numeric = Number(meters);
  return Number.isFinite(numeric) ? `${Math.round(numeric).toLocaleString()} m` : 'Unknown altitude';
}

export function formatDistanceMeters(meters: unknown): string {
  const numeric = Number(meters);
  if (!Number.isFinite(numeric)) return 'n/a';
  return numeric >= 1000 ? `${(numeric / 1000).toFixed(1)} km` : `${Math.round(numeric)} m`;
}

export function positionCoordinates(position?: Position | null): [number, number] | null {
  const latitude = Number(position?.position?.latitude ?? position?.latitude);
  const longitude = Number(position?.position?.longitude ?? position?.longitude);
  return Number.isFinite(latitude) && Number.isFinite(longitude) ? [longitude, latitude] : null;
}

export function latestPositions(rows: Position[]): Position[] {
  const latest = new Map<string, Position>();
  [...rows].sort((a, b) => Number(b.timestamp || 0) - Number(a.timestamp || 0)).forEach((row) => {
    if (!latest.has(row.aircraft_id)) latest.set(row.aircraft_id, row);
  });
  return [...latest.values()];
}

export function truncateMiddle(value: unknown, start = 8, end = 6): string {
  const text = String(value || 'Not available');
  return text.length > start + end + 3 ? `${text.slice(0, start)}…${text.slice(-end)}` : text;
}
