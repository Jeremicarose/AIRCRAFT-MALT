import type { HealthData, ModeData, ReceiversResponse, ShellSnapshot } from '@/lib/types';

const FALLBACK_API_BASE = 'http://127.0.0.1:5057';
export const API_REQUEST_TIMEOUT_MS = 12_000;
export const PUBLIC_POSITIONS_PATH = '/api/positions/recent?seconds=300&limit=100';

export const apiQueryKeys = {
  aircraft: ['aircraft'] as const,
  health: ['health'] as const,
  mode: ['mode'] as const,
  pipeline: ['pipeline'] as const,
  positions: ['positions'] as const,
  receivers: ['receivers'] as const,
};

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

export function presentApiError(error: unknown, fallbackDetail: string): { detail: string; technicalDetail?: string } {
  if (!(error instanceof ApiRequestError)) {
    return {
      detail: fallbackDetail,
      technicalDetail: error instanceof Error ? error.message : undefined,
    };
  }

  let detail = fallbackDetail;
  if (error.status === 0) detail = 'The service could not be reached. Check the connection, then try again.';
  else if (error.status === 404) detail = 'The requested data is not available from this deployment. You can continue using the other workspaces.';
  else if (error.status === 429) detail = 'The service is receiving too many requests. Wait a moment, then try again.';
  else if (error.status === 504) detail = 'The service did not respond in time. Existing data may be stale; try again when the connection recovers.';
  else if (error.status >= 500) detail = 'The service is temporarily unavailable. Existing data may be stale; try again in a moment.';

  return {
    detail,
    technicalDetail: `${error.message} (HTTP ${error.status || 'network'}, ${error.path})`,
  };
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
  const timeoutSignal = AbortSignal.timeout(API_REQUEST_TIMEOUT_MS);
  const signal = init?.signal ? AbortSignal.any([init.signal, timeoutSignal]) : timeoutSignal;
  let response: Response;
  try {
    response = await fetch(apiUrl(path), { ...init, cache: 'no-store', signal });
  } catch (error) {
    const timedOut = timeoutSignal.aborted && !init?.signal?.aborted;
    throw new ApiRequestError(
      timedOut ? `The service did not respond within ${API_REQUEST_TIMEOUT_MS / 1000} seconds.` : 'The service request could not be completed.',
      timedOut ? 504 : 0,
      path,
    );
  }
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
