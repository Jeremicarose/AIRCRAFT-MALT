export interface ConsoleRoute {
  key: string;
  href: string;
  label: string;
  detail: string;
  group: 'Operate' | 'Explore' | 'Investigate' | 'System';
}

export const consoleRoutes: ConsoleRoute[] = [
  { key: 'overview', href: '/app/overview', label: 'Overview', detail: 'System posture', group: 'Operate' },
  { key: 'localization', href: '/app/localization', label: 'Live map', detail: 'Airspace operations', group: 'Operate' },
  { key: 'aircraft', href: '/app/aircraft', label: 'Aircraft', detail: 'Tracks and confidence', group: 'Explore' },
  { key: 'receivers', href: '/app/receivers', label: 'Receivers', detail: 'Infrastructure inventory', group: 'Explore' },
  { key: 'pipeline', href: '/app/pipeline', label: 'Pipeline', detail: 'Evidence debugger', group: 'Investigate' },
  { key: 'metrics', href: '/app/metrics', label: 'Metrics', detail: 'System observability', group: 'Investigate' },
  { key: 'environment', href: '/app/environment', label: 'Environment', detail: 'Deployment configuration', group: 'System' },
  { key: 'settings', href: '/app/settings', label: 'Settings', detail: 'Console preferences', group: 'System' },
];
