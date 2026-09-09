import type { HealthData, ModeData, ReceiversResponse, ShellSnapshot } from '@/lib/types';

const FALLBACK_API_BASE = 'http://127.0.0.1:5057';
export const PUBLIC_POSITIONS_PATH = '/api/positions/recent?seconds=300&limit=100';

function normalizeApiBase(value: string): string {
  const trimmed = value.trim().replace(/\/$/, '');
  return /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export function getApiBase(): string {
  if (typeof window === 'undefined') {
    const internal = process.env.MLAT_API_INTERNAL_URL?.trim();
    if (internal) return normalizeApiBase(internal);
  }
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (explicit) return normalizeApiBase(explicit);
  return typeof window === 'undefined' ? FALLBACK_API_BASE : '';
}

export function apiUrl(path: string): string {
  return `${getApiBase()}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), { ...init, cache: 'no-store' });
  if (!response.ok) {
    let message = `The service returned HTTP ${response.status}.`;
    try {
      const payload = await response.json() as { error?: unknown };
      if (typeof payload.error === 'string' && payload.error.trim()) message = payload.error;
    } catch { /* The status and path still provide a useful failure. */ }
    throw new ApiRequestError(message, response.status, path);
  }
  return response.json() as Promise<T>;
}

export async function fetchJsonState<T>(path: string, fallback: T): Promise<{ data: T; error: string | null }> {
  try {
    return { data: await fetchJson<T>(path), error: null };
  } catch (error) {
    return {
      data: fallback,
      error: error instanceof Error ? error.message : 'The service request failed.',
    };
  }
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
