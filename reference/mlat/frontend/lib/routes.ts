export interface ConsoleRoute {
  key: string;
  href: string;
  label: string;
  detail: string;
  group: 'Registry' | 'MLAT reference' | 'System';
}

export const consoleRoutes: ConsoleRoute[] = [
  { key: 'registry', href: '/app/registry', label: 'Receiver directory', detail: 'Canonical identity, ownership, and lifecycle', group: 'Registry' },
  { key: 'guide', href: '/app/guide', label: 'Explorer missions', detail: 'Learn the investigation workflow and earn browser-local badges', group: 'Registry' },
  { key: 'overview', href: '/app/overview', label: 'MLAT overview', detail: 'Reference consumer posture', group: 'MLAT reference' },
  { key: 'localization', href: '/app/localization', label: 'Airspace map', detail: 'Aircraft and receiver geometry from the current source', group: 'MLAT reference' },
  { key: 'aircraft', href: '/app/aircraft', label: 'Aircraft', detail: 'Localization and receiver contribution', group: 'MLAT reference' },
  { key: 'receivers', href: '/app/receivers', label: 'MLAT receivers', detail: 'Registry identities in the current receiver pool', group: 'MLAT reference' },
  { key: 'pipeline', href: '/app/pipeline', label: 'Pipeline', detail: 'Discovery, ingest, and localization', group: 'MLAT reference' },
  { key: 'metrics', href: '/app/metrics', label: 'Metrics', detail: 'System observability', group: 'MLAT reference' },
  { key: 'benchmark', href: '/app/benchmark', label: 'Accuracy benchmark', detail: 'Historical solver accuracy and limits', group: 'MLAT reference' },
  { key: 'replay', href: '/app/replay', label: 'Historical replay', detail: 'Recorded events, processing stages, and source limitations', group: 'MLAT reference' },
  { key: 'environment', href: '/app/environment', label: 'Diagnostics', detail: 'Deployment, connectivity, and readiness', group: 'System' },
  { key: 'settings', href: '/app/settings', label: 'Settings', detail: 'Console preferences', group: 'System' },
];
