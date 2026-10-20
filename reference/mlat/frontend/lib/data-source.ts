import type { ModeData, StatusTone } from './types.ts';

export type DataSourceKind = 'live' | 'replay' | 'simulation' | 'cached' | 'unknown';

export interface DataSourceState {
  kind: DataSourceKind;
  label: string;
  detail: string;
  tone: StatusTone;
  mapTitle: string;
}

const SOURCE_STATES: Record<DataSourceKind, DataSourceState> = {
  live: {
    kind: 'live',
    label: 'LIVE',
    detail: 'Current receiver observations reported by the MLAT runtime.',
    tone: 'healthy',
    mapTitle: 'Live airspace map',
  },
  replay: {
    kind: 'replay',
    label: 'HISTORICAL REPLAY',
    detail: 'Historical observations with their original time context. Replay progress is not current receiver activity.',
    tone: 'replay',
    mapTitle: 'Replay airspace map',
  },
  simulation: {
    kind: 'simulation',
    label: 'SYNTHETIC',
    detail: 'Synthetic demonstration observations. They are not live receiver evidence.',
    tone: 'replay',
    mapTitle: 'Simulation airspace map',
  },
  cached: {
    kind: 'cached',
    label: 'CACHED',
    detail: 'Last-known data is shown because the current source could not be refreshed.',
    tone: 'attention',
    mapTitle: 'Cached airspace map',
  },
  unknown: {
    kind: 'unknown',
    label: 'UNKNOWN',
    detail: 'The runtime has not provided enough information to identify this data source.',
    tone: 'attention',
    mapTitle: 'Airspace map',
  },
};

export function dataSourceState(mode: ModeData | null | undefined, options: { cached?: boolean } = {}): DataSourceState {
  if (options.cached && mode) {
    const source = dataSourceState(mode);
    return { ...SOURCE_STATES.cached, label: `${source.label} (CACHED)`, detail: `${source.detail} The last refresh failed; these records may be stale.` };
  }
  if (!mode) return SOURCE_STATES.unknown;

  if (mode.data_provenance === 'UNKNOWN') return SOURCE_STATES.unknown;
  if (mode.data_provenance === 'SYNTHETIC') return SOURCE_STATES.simulation;
  if (mode.data_provenance === 'HISTORICAL_REPLAY') return SOURCE_STATES.replay;
  if (mode.data_provenance === 'LIVE') return SOURCE_STATES.live;

  const modeName = String(mode.mode ?? '').trim().toLowerCase();
  if (mode.demo_mode || modeName === 'demo') return SOURCE_STATES.simulation;
  if (modeName === 'historical_replay') return SOURCE_STATES.replay;
  if (mode.simulation_mode || modeName === 'simulation' || mode.synthetic_feed_mode) return SOURCE_STATES.simulation;
  if (modeName === 'live' && mode.runtime_status === 'active') return SOURCE_STATES.live;
  return SOURCE_STATES.unknown;
}
