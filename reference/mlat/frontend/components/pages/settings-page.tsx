'use client';

import { Bell, Database, Gauge, Layers3, Link2, RefreshCw, ScanLine, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ActivityRail, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { PreferenceRow } from '@/components/ui/preference-row';
import { Switch } from '@/components/ui/switch';
import { useOperatorStore } from '@/lib/operator-store';
import type { StatusTone } from '@/lib/types';

const preferencesKey = 'mlat-console-preferences';
const historyKey = 'mlat-console-preference-history';

type PreferenceHistory = {
  id: string;
  timestamp: number;
  title: string;
  detail: string;
};

export function SettingsPage() {
  const showReceiverLinks = useOperatorStore((state) => state.showReceiverLinks);
  const showUncertainty = useOperatorStore((state) => state.showUncertainty);
  const toggleReceiverLinks = useOperatorStore((state) => state.toggleReceiverLinks);
  const toggleUncertainty = useOperatorStore((state) => state.toggleUncertainty);
  const rightDockOpen = useOperatorStore((state) => state.rightDockOpen);
  const setRightDockOpen = useOperatorStore((state) => state.setRightDockOpen);
  const density = useOperatorStore((state) => state.density);
  const setDensity = useOperatorStore((state) => state.setDensity);
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [desktopAlerts, setDesktopAlerts] = useState(false);
  const [history, setHistory] = useState<PreferenceHistory[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<'unsupported' | NotificationPermission>('unsupported');
  const [reducedMotion, setReducedMotion] = useState(false);

  const recordChange = (title: string, detail: string) => {
    const entry: PreferenceHistory = { id: `${Date.now()}-${title}`, timestamp: Date.now() / 1000, title, detail };
    setHistory((current) => [entry, ...current].slice(0, 8));
  };

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(preferencesKey);
      if (stored) {
        const preferences = JSON.parse(stored) as { refreshInterval?: number; desktopAlerts?: boolean };
        if (preferences.refreshInterval) setRefreshInterval(preferences.refreshInterval);
        setDesktopAlerts(Boolean(preferences.desktopAlerts));
      }
      const storedHistory = window.localStorage.getItem(historyKey);
      if (storedHistory) setHistory((JSON.parse(storedHistory) as PreferenceHistory[]).slice(0, 8));
    } catch { /* Invalid local state falls back to the console defaults. */ }
    setNotificationPermission('Notification' in window ? Notification.permission : 'unsupported');
    setReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(preferencesKey, JSON.stringify({ refreshInterval, desktopAlerts, compactRows: density === 'compact' }));
    window.localStorage.setItem(historyKey, JSON.stringify(history));
    document.documentElement.dataset.compactRows = density === 'compact' ? 'true' : 'false';
    window.dispatchEvent(new Event('mlat-preferences-change'));
  }, [density, desktopAlerts, history, hydrated, refreshInterval]);

  const updateDesktopAlerts = async (checked: boolean) => {
    if (!checked) {
      setDesktopAlerts(false);
      recordChange('Desktop alerts disabled', 'Global failure notifications will remain in the console.');
      return;
    }
    if (!('Notification' in window)) {
      recordChange('Desktop alerts unavailable', 'This browser does not expose notification permission.');
      return;
    }
    const permission = Notification.permission === 'granted' ? 'granted' : await Notification.requestPermission();
    setNotificationPermission(permission);
    setDesktopAlerts(permission === 'granted');
    recordChange(permission === 'granted' ? 'Desktop alerts enabled' : 'Desktop alerts blocked', permission === 'granted' ? 'Global failure notifications may appear on this device.' : 'Browser notification permission was not granted.');
  };

  const capabilityTimeline = useMemo(() => {
    const permissionTone: StatusTone = notificationPermission === 'granted' ? 'healthy' : notificationPermission === 'denied' || notificationPermission === 'unsupported' ? 'failure' : 'attention';
    return [
      { title: 'Local persistence', detail: 'Console preferences and change history are stored on this device.', tone: 'healthy' as StatusTone },
      { title: 'Notification permission', detail: notificationPermission === 'granted' ? 'Desktop delivery is available.' : notificationPermission === 'default' ? 'Permission has not been requested.' : notificationPermission === 'denied' ? 'Desktop delivery is blocked by the browser.' : 'Desktop delivery is not supported.', tone: permissionTone },
      { title: 'Reduced motion', detail: reducedMotion ? 'Reduced motion is active for this browser.' : 'Standard 180 ms state transitions are active.', tone: reducedMotion ? 'selection' as StatusTone : 'neutral' as StatusTone },
    ];
  }, [notificationPermission, reducedMotion]);

  const changeTimeline = history.map((entry) => ({
    title: entry.title,
    detail: entry.detail,
    tone: 'selection' as StatusTone,
    meta: new Date(entry.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }));

  const activityRail = [
    { title: 'Refresh interval', detail: `Fallback polling is set to ${refreshInterval} seconds on this device.`, meta: `${refreshInterval}s`, tone: 'selection' as StatusTone },
    { title: 'Desktop alerts', detail: desktopAlerts ? 'Desktop alerts are enabled for failure states.' : 'Desktop alerts are disabled for this browser.', meta: desktopAlerts ? 'Enabled' : 'Disabled', tone: desktopAlerts ? 'healthy' as StatusTone : 'attention' as StatusTone },
    { title: 'Row density', detail: density === 'compact' ? 'Compact inventory rows are active.' : 'Comfortable inventory rows are active.', meta: density, tone: density === 'compact' ? 'selection' as StatusTone : 'neutral' as StatusTone },
  ];

  useEffect(() => {
    useOperatorStore.getState().setInvestigationContext({ focus: 'settings', timeRange: 'preferences' });
    useOperatorStore.getState().setDock({
      entityType: 'settings',
      title: 'Operator preferences',
      subtitle: 'Pinned from the settings workspace.',
      statusLabel: desktopAlerts ? 'Alerts enabled' : 'Local only',
      statusTone: desktopAlerts ? 'healthy' : 'attention',
      facts: [
        { label: 'Refresh interval', value: `${refreshInterval}s` },
        { label: 'Density', value: density },
        { label: 'Receiver links', value: showReceiverLinks ? 'Visible' : 'Hidden', tone: showReceiverLinks ? 'selection' : 'neutral' },
        { label: 'Uncertainty', value: showUncertainty ? 'Visible' : 'Hidden', tone: showUncertainty ? 'selection' : 'neutral' },
      ],
      timeline: capabilityTimeline,
      evidence: changeTimeline.slice(0, 4).map((entry) => ({ title: entry.title, detail: entry.detail, state: entry.meta, tone: entry.tone })) || [{ title: 'No changes', detail: 'Preference changes will appear here once local settings are updated.', state: 'Idle', tone: 'neutral' as StatusTone }],
      actions: [
        { label: 'Open live map', href: '/app/localization', tone: 'secondary' },
        { label: 'Open overview', href: '/app/overview', tone: 'primary' },
      ],
    });
    return () => useOperatorStore.getState().setDock(null);
  }, [capabilityTimeline, changeTimeline, density, desktopAlerts, refreshInterval, showReceiverLinks, showUncertainty]);

  return (
    <div className="space-y-4 max-w-6xl">
      <WorkspaceHeader eyebrow="System" title="Operator preferences workspace" description="Settings now groups shell, map, refresh, and notification behavior into a denser operator-preferences surface with local previews and change history." rail={<SignalMarquee items={[{ label: 'Refresh', value: `${refreshInterval}s`, tone: 'selection' }, { label: 'Alerts', value: desktopAlerts ? 'Enabled' : 'Disabled', tone: desktopAlerts ? 'healthy' : 'attention' }, { label: 'Density', value: density, tone: density === 'compact' ? 'selection' : 'neutral' }, { label: 'Permission', value: notificationPermission, tone: notificationPermission === 'granted' ? 'healthy' : notificationPermission === 'default' ? 'attention' : 'failure' }]} />} />
      <WorkspaceSplit
        secondaryWidth="360px"
        primary={<div className="min-w-0 space-y-4"><WorkspacePanel title="Live updates" detail="Console refresh and attention behavior" tone="selection"><PreferenceRow icon={RefreshCw} title="Refresh interval" detail="Polling interval used when a live stream is unavailable." control={<div className="flex items-center gap-3"><input id="refresh-interval" type="range" min="5" max="60" step="5" value={refreshInterval} onChange={(event) => setRefreshInterval(Number(event.target.value))} onPointerUp={() => recordChange('Refresh interval updated', `Fallback polling set to ${refreshInterval} seconds.`)} onKeyUp={(event) => { if (event.key.startsWith('Arrow')) recordChange('Refresh interval updated', `Fallback polling set to ${refreshInterval} seconds.`); }} aria-label="Refresh interval in seconds" className="w-24 accent-signal-blue" /><output htmlFor="refresh-interval" className="w-8 text-right text-xs font-semibold text-ink-secondary tabular-nums">{refreshInterval}s</output></div>} /><PreferenceRow icon={Bell} title="Desktop alerts" detail="Notify when global system health enters a failure state." control={<Switch checked={desktopAlerts} onCheckedChange={(checked) => void updateDesktopAlerts(checked)} label="Enable desktop alerts" disabled={notificationPermission === 'unsupported'} />} /></WorkspacePanel><WorkspacePanel title="Shell layout" detail="Shared console framing and dense workspace defaults" tone="trust"><PreferenceRow icon={Layers3} title="Persistent evidence dock" detail="Keep the shell-level right-side drill-down dock open across routes." control={<Switch checked={rightDockOpen} onCheckedChange={(checked) => { setRightDockOpen(checked); recordChange(checked ? 'Evidence dock opened' : 'Evidence dock hidden', checked ? 'The shell keeps the shared drill-down dock visible.' : 'The shell hides the shared drill-down dock until reopened.'); }} label="Show evidence dock" />} /><PreferenceRow icon={Gauge} title="Compact table rows" detail="Reduce row height for high-density laptop and ultra-wide views." control={<Switch checked={density === 'compact'} onCheckedChange={(checked) => { setDensity(checked ? 'compact' : 'comfortable'); recordChange(checked ? 'Compact rows enabled' : 'Comfortable rows enabled', checked ? 'Inventory rows use the high-density setting.' : 'Inventory rows use the standard setting.'); }} label="Use compact table rows" />} /></WorkspacePanel><WorkspacePanel title="Map defaults" detail="Layers shown when opening the live map" tone="selection"><PreferenceRow icon={Link2} title="Receiver geometry" detail="Draw links from the selected aircraft to contributing receivers." control={<Switch checked={showReceiverLinks} onCheckedChange={() => { toggleReceiverLinks(); recordChange(showReceiverLinks ? 'Receiver geometry hidden' : 'Receiver geometry shown', 'The live map layer default changed on this device.'); }} label="Show receiver geometry" />} /><PreferenceRow icon={ScanLine} title="Uncertainty ring" detail="Show the latest uncertainty area for the selected solve." control={<Switch checked={showUncertainty} onCheckedChange={() => { toggleUncertainty(); recordChange(showUncertainty ? 'Uncertainty ring hidden' : 'Uncertainty ring shown', 'The live map layer default changed on this device.'); }} label="Show uncertainty ring" />} /></WorkspacePanel></div>}
        secondary={<aside className="space-y-4 self-start xl:sticky xl:top-20"><WorkspacePanel title="Current local console posture" detail="Browser capabilities and local preference state" tone={desktopAlerts ? 'healthy' : 'attention'}><ActivityRail items={activityRail} /><div className="border-t border-line"><Timeline items={capabilityTimeline} /></div></WorkspacePanel><WorkspacePanel title="Recent local changes" detail={`${history.length} retained on this device`} tone="selection">{changeTimeline.length ? <Timeline items={changeTimeline} /> : <div className="flex min-h-36 items-center gap-3 px-4 py-6"><Database className="size-4 shrink-0 text-ink-quiet" /><p className="text-xs leading-5 text-ink-quiet">Preference changes made on this device will appear here.</p></div>}</WorkspacePanel><div className="flex items-start gap-3 rounded-lg border border-trust-cyan/20 bg-trust-cyan/[0.055] p-4"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-trust-cyan" /><div><p className="text-xs font-semibold text-ink">Local scope</p><p className="mt-1 text-xs leading-5 text-ink-quiet">These settings affect this browser only. Deployment configuration remains under Environment.</p></div></div></aside>}
      />
    </div>
  );
}
