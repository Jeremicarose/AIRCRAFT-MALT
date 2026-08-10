import type { HealthData, ModeData, ReceiversResponse, ShellSnapshot } from '@/lib/types';

const FALLBACK_API_BASE = 'http://127.0.0.1:5057';

export function getApiBase(): string {
  if (typeof window === 'undefined') {
    const internal = process.env.MLAT_API_INTERNAL_URL?.trim();
    if (internal) return internal.replace(/\/$/, '');
  }
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return explicit ? explicit.replace(/\/$/, '') : FALLBACK_API_BASE;
}

export function apiUrl(path: string): string {
  return `${getApiBase()}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), { ...init, cache: 'no-store' });
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${path}`);
  return response.json() as Promise<T>;
}

export async function fetchJsonSafe<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  try {
    return await fetchJson<T>(path, init);
  } catch {
    return fallback;
  }
}

export async function fetchShellSnapshot(): Promise<ShellSnapshot> {
  const [modeData, healthData, aircraftData, receiverData] = await Promise.all([
    fetchJsonSafe<ModeData | null>('/api/system/mode', null),
    fetchJsonSafe<HealthData | null>('/api/health', null),
    fetchJsonSafe<{ aircraft?: string[]; count?: number } | null>('/api/aircraft?seconds=300', null),
    fetchJsonSafe<ReceiversResponse | null>('/api/receivers', null),
  ]);
  return { modeData, healthData, aircraftData, receiverData };
}
