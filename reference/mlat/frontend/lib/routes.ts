export interface ConsoleRoute {
  key: string;
  href: string;
  label: string;
  detail: string;
  group: 'Operations' | 'System';
}

export const consoleRoutes: ConsoleRoute[] = [
  { key: 'overview', href: '/app/overview', label: 'Overview', detail: 'System flow and current posture', group: 'Operations' },
  { key: 'localization', href: '/app/localization', label: 'Live Map', detail: 'Aircraft and receiver operations', group: 'Operations' },
  { key: 'aircraft', href: '/app/aircraft', label: 'Aircraft', detail: 'Localization and receiver contribution', group: 'Operations' },
  { key: 'receivers', href: '/app/receivers', label: 'Receivers', detail: 'Registry identity, eligibility, and operational role', group: 'Operations' },
  { key: 'pipeline', href: '/app/pipeline', label: 'Pipeline', detail: 'Discovery, ingest, and localization', group: 'Operations' },
  { key: 'metrics', href: '/app/metrics', label: 'Metrics', detail: 'System observability', group: 'Operations' },
  { key: 'environment', href: '/app/environment', label: 'Environment', detail: 'Deployment and connectivity', group: 'System' },
  { key: 'settings', href: '/app/settings', label: 'Settings', detail: 'Console preferences', group: 'System' },
];
