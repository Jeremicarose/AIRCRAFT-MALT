export interface ConsoleRoute {
  key: string;
  href: string;
  label: string;
  detail: string;
  group: 'Registry' | 'MLAT reference' | 'System';
}

export const consoleRoutes: ConsoleRoute[] = [
  { key: 'registry', href: '/app/registry', label: 'Receiver directory', detail: 'Canonical identity, ownership, and lifecycle', group: 'Registry' },
  { key: 'overview', href: '/app/overview', label: 'MLAT overview', detail: 'Reference consumer posture', group: 'MLAT reference' },
  { key: 'localization', href: '/app/localization', label: 'Live Map', detail: 'Aircraft and receiver operations', group: 'MLAT reference' },
  { key: 'aircraft', href: '/app/aircraft', label: 'Aircraft', detail: 'Localization and receiver contribution', group: 'MLAT reference' },
  { key: 'receivers', href: '/app/receivers', label: 'MLAT receivers', detail: 'Registry identities in the current receiver pool', group: 'MLAT reference' },
  { key: 'pipeline', href: '/app/pipeline', label: 'Pipeline', detail: 'Discovery, ingest, and localization', group: 'MLAT reference' },
  { key: 'metrics', href: '/app/metrics', label: 'Metrics', detail: 'System observability', group: 'MLAT reference' },
  { key: 'environment', href: '/app/environment', label: 'Diagnostics', detail: 'Deployment, connectivity, and readiness', group: 'System' },
  { key: 'settings', href: '/app/settings', label: 'Settings', detail: 'Console preferences', group: 'System' },
];
