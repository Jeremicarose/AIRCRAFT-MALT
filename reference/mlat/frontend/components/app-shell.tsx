'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { Activity, ChevronLeft, ChevronRight, Database, Gauge, Map, Menu, PanelLeftClose, PanelRightClose, PanelRightOpen, Plane, RadioTower, Search, Settings, SlidersHorizontal, Workflow, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { InvestigationActions, InvestigationEvidenceList, InvestigationFacts, InvestigationTimeline } from '@/components/operations-ui';
import { FirstRunNotice } from '@/components/first-run-notice';
import { WalletControl } from '@/components/wallet-control';
import { Button } from '@/components/ui/button';
import { CommandPalette } from '@/components/ui/command-palette';
import { NotificationCenter } from '@/components/ui/notification-center';
import { StatusChip } from '@/components/ui/status-chip';
import { Tooltip } from '@/components/ui/tooltip';
import { toneFromFreshness, truncateMiddle } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import { consoleRoutes, type ConsoleRoute } from '@/lib/routes';
import type { InvestigationDockState, ShellSnapshot, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

const routeIcons: Record<string, LucideIcon> = {
  overview: Gauge,
  localization: Map,
  aircraft: Plane,
  receivers: RadioTower,
  pipeline: Workflow,
  registry: Database,
  metrics: Activity,
  environment: Database,
  settings: Settings,
};

const groups: ConsoleRoute['group'][] = ['Registry', 'MLAT reference', 'System'];

function getSystemSummary(snapshot: ShellSnapshot): { label: string; tone: StatusTone; environment: string } {
  const mode = snapshot.modeData;
  if (!mode) return { label: 'Unavailable', tone: 'failure', environment: 'Unknown' };
  const isReplay = Boolean(mode.demo_mode || mode.simulation_mode || mode.synthetic_feed_mode);
  const isActive = mode.runtime_status === 'active';
  if (isReplay) return { label: 'Replay', tone: 'replay', environment: 'Replay' };
  if (isActive) return { label: 'Healthy', tone: 'healthy', environment: mode.strict_production_mode ? 'Production' : 'Live' };
  if (mode.runtime_status === 'stale') return { label: 'Degraded', tone: 'attention', environment: 'Live' };
  return { label: 'Offline', tone: 'failure', environment: mode.strict_production_mode ? 'Production' : 'Configured' };
}

function routeLabelFromKey(pageKey: string) {
  return consoleRoutes.find((route) => route.key === pageKey)?.label
    ?? (pageKey === 'registry' ? 'Receiver directory' : 'Console');
}

function Navigation({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-2 py-3">
      {groups.map((group) => (
        <div key={group}>
          {!collapsed ? <p className="mb-1.5 px-2 text-[11px] font-semibold text-ink-quiet">{group}</p> : null}
          <nav aria-label={group} className="space-y-0.5">
            {consoleRoutes.filter((route) => route.group === group).map((route) => {
              const active = pathname === route.href || (route.key === 'metrics' && pathname === '/app/analytics');
              const Icon = routeIcons[route.key] ?? SlidersHorizontal;
              const link = (
                <Link href={route.href} onClick={onNavigate} aria-current={active ? 'page' : undefined} className={cn('group flex h-10 items-center gap-3 rounded-md px-2.5 text-[13px] font-medium text-ink-secondary transition-colors duration-standard hover:bg-graphite-hover hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue', active && 'bg-graphite-hover text-ink')}>
                  <Icon className={cn('size-4 shrink-0 text-ink-quiet transition-colors group-hover:text-ink-secondary', active && 'text-signal-blue')} strokeWidth={2} />
                  {!collapsed ? <span className="truncate">{route.label}</span> : null}
                </Link>
              );
              return collapsed ? <Tooltip key={route.key} label={route.label}>{link}</Tooltip> : <div key={route.key}>{link}</div>;
            })}
          </nav>
        </div>
      ))}
    </div>
  );
}

function DockPlaceholder({ pageKey }: { pageKey: string }) {
  return (
    <div className="p-5">
      <h2 className="text-sm font-semibold text-ink">No investigation selected</h2>
      <p className="mt-2 text-xs leading-5 text-ink-quiet">Select a receiver, aircraft, or pipeline stage in {routeLabelFromKey(pageKey)}. Its details and evidence will remain available here while you move through the console.</p>
    </div>
  );
}

function InvestigationDock({ dock, pageKey }: { dock: InvestigationDockState | null; pageKey: string }) {
  if (!dock) return <DockPlaceholder pageKey={pageKey} />;
  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-line px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] font-medium text-ink-quiet">Selected investigation</p>
            <h2 className="mt-1 break-words text-sm font-semibold text-ink">{dock.title}</h2>
            {dock.subtitle ? <p className="mt-1 text-xs leading-5 text-ink-quiet">{dock.subtitle}</p> : null}
          </div>
          {dock.statusLabel ? <StatusChip label={dock.statusLabel} tone={dock.statusTone} className="shrink-0" /> : null}
        </div>
      </div>
      {dock.actions?.length ? <div className="border-b border-line"><InvestigationActions actions={dock.actions} /></div> : null}
      {dock.facts?.length ? <div className="border-b border-line"><InvestigationFacts items={dock.facts} /></div> : null}
      {dock.timeline?.length ? <div className="border-b border-line"><div className="px-4 pt-4"><p className="text-xs font-semibold text-ink">Lifecycle and state</p></div><InvestigationTimeline items={dock.timeline} /></div> : null}
      {dock.evidence?.length ? <div><div className="px-4 pt-4"><p className="text-xs font-semibold text-ink">Evidence</p></div><InvestigationEvidenceList items={dock.evidence} /></div> : null}
    </div>
  );
}

function ContextBar({ snapshot, selectedAircraftId, selectedReceiverId, pageKey }: { snapshot: ShellSnapshot; selectedAircraftId: string | null; selectedReceiverId: string | null; pageKey: string }) {
  const registryPage = pageKey === 'registry';
  const summary = registryPage ? { label: 'Registry V2', tone: 'trust' as const } : getSystemSummary(snapshot);
  const signalAge = snapshot.healthData?.freshness?.last_signal_age_s;
  return (
    <div className="flex min-h-10 items-center gap-3 overflow-x-auto border-t border-line px-4 py-2 text-[11px] text-ink-quiet sm:px-6">
      <span className="shrink-0 font-semibold text-trust-cyan">CKB Pudge testnet</span>
      <span className="h-3 w-px shrink-0 bg-line" aria-hidden="true" />
      <StatusChip label={summary.label} tone={summary.tone} />
      <span className="shrink-0">{routeLabelFromKey(pageKey)}</span>
      <span className="h-3 w-px shrink-0 bg-line" aria-hidden="true" />
      {selectedReceiverId ? <Link href={`/app/receivers?receiver=${encodeURIComponent(selectedReceiverId)}`} className="shrink-0 rounded-sm text-ink-secondary hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">Receiver {truncateMiddle(selectedReceiverId, 8, 5)}</Link> : <span className="shrink-0">No receiver selected</span>}
      {selectedAircraftId ? <Link href={`/app/aircraft?aircraft=${encodeURIComponent(selectedAircraftId)}`} className="shrink-0 rounded-sm text-ink-secondary hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">Aircraft {selectedAircraftId}</Link> : null}
      <span className="ml-auto hidden shrink-0 sm:inline">{registryPage ? 'Public indexer directory' : `Signal ${signalAge == null ? 'unavailable' : `${Math.round(signalAge)}s ago`}`}</span>
    </div>
  );
}

export function AppShell({ pageKey, title, description, snapshot, children }: { pageKey: string; title: string; description: string; snapshot: ShellSnapshot; children: ReactNode }) {
  const collapsed = useOperatorStore((state) => state.sidebarCollapsed);
  const setCollapsed = useOperatorStore((state) => state.setSidebarCollapsed);
  const mobileOpen = useOperatorStore((state) => state.mobileNavigationOpen);
  const setMobileOpen = useOperatorStore((state) => state.setMobileNavigationOpen);
  const setCommandOpen = useOperatorStore((state) => state.setCommandOpen);
  const rightDockOpen = useOperatorStore((state) => state.rightDockOpen);
  const setRightDockOpen = useOperatorStore((state) => state.setRightDockOpen);
  const selectedAircraftId = useOperatorStore((state) => state.selectedAircraftId);
  const selectedReceiverId = useOperatorStore((state) => state.selectedReceiverId);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const dock = useOperatorStore((state) => state.dock);
  const density = useOperatorStore((state) => state.density);
  const pushRouteHistory = useOperatorStore((state) => state.pushRouteHistory);
  const pushRecentInvestigation = useOperatorStore((state) => state.pushRecentInvestigation);
  const storeHydrated = useOperatorStore((state) => state.hasHydrated);
  const reduceMotion = useReducedMotion();
  const [wideDock, setWideDock] = useState(false);
  const summary = pageKey === 'registry'
    ? { label: 'Registry V2', tone: 'trust' as const, environment: 'Pudge' }
    : getSystemSummary(snapshot);
  const signalAge = snapshot.healthData?.freshness?.last_signal_age_s;
  const signalTone = toneFromFreshness(signalAge, 15, 60);
  const pinnedRoute = consoleRoutes.find((route) => route.key === pageKey);
  const breadcrumbRoutes = [{ label: 'Receiver Registry', href: '/app/registry' }, ...(pinnedRoute ? [{ label: pinnedRoute.group, href: pinnedRoute.href }, { label: pinnedRoute.label, href: pinnedRoute.href }] : [{ label: title, href: '#' }])];

  useEffect(() => {
    const media = window.matchMedia('(min-width: 1536px)');
    const update = () => setWideDock(media.matches);
    update();
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target instanceof HTMLElement ? event.target : null;
      const insideControl = target?.closest('input, textarea, select, button, a, [contenteditable="true"]');
      if (event.key === '[' && !event.metaKey && !event.ctrlKey && !insideControl) setCollapsed(!collapsed);
      if (event.key === ']' && !event.metaKey && !event.ctrlKey && !insideControl) setRightDockOpen(!rightDockOpen);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [collapsed, rightDockOpen, setCollapsed, setRightDockOpen]);

  useEffect(() => {
    if (!storeHydrated) return;
    setInvestigationContext({ routeKey: pageKey });
    const route = consoleRoutes.find((item) => item.key === pageKey);
    if (route) pushRouteHistory({ key: route.key, label: route.label, href: route.href });
  }, [pageKey, pushRouteHistory, setInvestigationContext, storeHydrated]);

  useEffect(() => {
    document.documentElement.dataset.compactRows = density === 'compact' ? 'true' : 'false';
  }, [density]);

  useEffect(() => {
    if (!storeHydrated || !dock?.title) return;
    const activeRoute = dock.actions?.find((action) => action.href?.startsWith('/app/'))?.href;
    pushRecentInvestigation({ id: `${dock.entityType}:${dock.title}`, title: dock.title, entityType: dock.entityType, routeKey: pageKey, href: activeRoute, focus: dock.title, statusLabel: dock.statusLabel, statusTone: dock.statusTone });
  }, [dock, pageKey, pushRecentInvestigation, storeHydrated]);

  useEffect(() => {
    if (summary.tone !== 'failure' || !('Notification' in window) || Notification.permission !== 'granted') return;
    try {
      const preferences = JSON.parse(window.localStorage.getItem('mlat-console-preferences') ?? '{}') as { desktopAlerts?: boolean };
      const noticeKey = `mlat-notice-${summary.label}`;
      if (preferences.desktopAlerts && !window.sessionStorage.getItem(noticeKey)) {
        new Notification('Receiver Registry', { body: `${summary.label}. Open the pipeline to inspect the current blocker.` });
        window.sessionStorage.setItem(noticeKey, 'shown');
      }
    } catch { /* Browser notifications are an optional local preference. */ }
  }, [summary.label, summary.tone]);

  return (
    <div className="min-h-screen bg-graphite-deep text-ink" data-page={pageKey}>
      <a href="#main-content" className="sr-only z-modal rounded-md bg-signal-blue px-3 py-2 font-semibold text-graphite-deep focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to main content</a>
      <aside className={cn('fixed inset-y-0 left-0 z-sticky hidden border-r border-line bg-[#0b0e12] transition-[width] duration-standard ease-operational lg:flex lg:flex-col', collapsed ? 'w-[68px]' : 'w-[232px]')}>
        <div className={cn('flex h-16 items-center border-b border-line', collapsed ? 'justify-center px-2' : 'justify-between px-3')}>
          <Link href="/app/registry" className="flex min-w-0 items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">
            <span className="relative flex size-8 shrink-0 items-center justify-center rounded-md bg-signal-blue text-[11px] font-bold text-graphite-deep"><span className="absolute inset-[5px] rounded-full border border-graphite-deep/45" />R</span>
            {!collapsed ? <span className="min-w-0"><strong className="block truncate text-[13px] font-semibold text-ink">Receiver Registry</strong><small className="block truncate text-[10px] font-medium text-ink-quiet">CKB TESTNET</small></span> : null}
          </Link>
          {!collapsed ? <Tooltip label="Collapse sidebar" side="bottom"><Button variant="ghost" size="icon-sm" aria-label="Collapse sidebar" onClick={() => setCollapsed(true)}><PanelLeftClose className="size-4" /></Button></Tooltip> : null}
        </div>
        <Navigation collapsed={collapsed} />
        <div className="border-t border-line p-2">
          <div className={cn('flex items-center gap-2 rounded-md px-2 py-2', collapsed && 'justify-center px-0')}>
            <span className={cn('size-2 shrink-0 rounded-full', summary.tone === 'healthy' ? 'bg-healthy' : summary.tone === 'trust' ? 'bg-trust-cyan' : summary.tone === 'replay' ? 'bg-replay' : summary.tone === 'attention' ? 'bg-attention' : 'bg-failure')} />
            {!collapsed ? <div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-ink-secondary">CKB testnet</p><p className="truncate text-[10px] text-ink-quiet">{summary.environment} · {summary.label}</p></div> : null}
            {collapsed ? <Tooltip label="Expand sidebar"><Button variant="ghost" size="icon-sm" aria-label="Expand sidebar" onClick={() => setCollapsed(false)}><ChevronRight className="size-4" /></Button></Tooltip> : null}
          </div>
        </div>
      </aside>

      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-modal-backdrop bg-black/65 lg:hidden" />
          <Dialog.Content asChild aria-describedby={undefined}>
            <motion.aside className="fixed inset-y-0 left-0 z-modal flex w-[280px] max-w-[86vw] flex-col border-r border-line bg-[#0b0e12] outline-none lg:hidden" initial={reduceMotion ? false : { x: -280 }} animate={{ x: 0 }} transition={{ duration: reduceMotion ? 0 : 0.18, ease: [0.22, 1, 0.36, 1] }}>
              <Dialog.Title className="sr-only">Console navigation</Dialog.Title>
              <div className="flex h-16 items-center justify-between border-b border-line px-3"><span className="text-sm font-semibold">Receiver Registry</span><Dialog.Close asChild><Button variant="ghost" size="icon-sm" aria-label="Close navigation"><ChevronLeft className="size-4" /></Button></Dialog.Close></div>
              <Navigation collapsed={false} onNavigate={() => setMobileOpen(false)} />
              <div className="border-t border-line p-3"><WalletControl /></div>
            </motion.aside>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <div className={cn('transition-[padding-left,padding-right] duration-standard ease-operational', collapsed ? 'lg:pl-[68px]' : 'lg:pl-[232px]', rightDockOpen && wideDock ? '2xl:pr-[360px]' : '2xl:pr-0')}>
        <header className="sticky top-0 z-sticky border-b border-line bg-graphite-deep/95 backdrop-blur-md">
          <div className="flex min-h-16 items-center justify-between gap-3 px-3 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu className="size-4" /></Button>
              <div className="min-w-0">
                <div className="mb-1 hidden items-center gap-1.5 text-[11px] text-ink-quiet md:flex">
                  {breadcrumbRoutes.map((item, index) => <div key={`${item.label}-${index}`} className="flex items-center gap-1.5">{index ? <ChevronRight className="size-3 text-ink-quiet/70" /> : null}<Link href={item.href} className="rounded-sm hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">{item.label}</Link></div>)}
                </div>
                <h1 className="truncate text-base font-semibold leading-tight text-ink sm:text-xl">{title}</h1>
                <p className="mt-0.5 hidden truncate text-xs text-ink-quiet sm:block">{description}</p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-1 sm:gap-2">
              <button onClick={() => setCommandOpen(true)} className="hidden h-9 min-w-[180px] items-center gap-2 rounded-md border border-line bg-graphite px-2.5 text-xs text-ink-quiet transition-colors duration-standard hover:border-[#3a4350] hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue xl:flex"><Search className="size-3.5" /><span className="flex-1 text-left">Search console</span><kbd className="rounded border border-line bg-graphite-raised px-1.5 py-0.5 font-sans text-[10px]">Ctrl K</kbd></button>
              <div className="hidden md:block"><WalletControl /></div>
              <Tooltip label={rightDockOpen ? 'Hide investigation inspector' : 'Show investigation inspector'} side="bottom"><Button variant="ghost" size="icon-sm" aria-label={rightDockOpen ? 'Hide investigation inspector' : 'Show investigation inspector'} onClick={() => setRightDockOpen(!rightDockOpen)}>{rightDockOpen ? <PanelRightClose className="size-4" /> : <PanelRightOpen className="size-4" />}</Button></Tooltip>
              <NotificationCenter snapshot={snapshot} />
              <Tooltip label="Search console" side="bottom"><Button variant="ghost" size="icon-sm" className="xl:hidden" aria-label="Search console" onClick={() => setCommandOpen(true)}><Search className="size-4" /></Button></Tooltip>
              <span className="sr-only">Signal freshness: {signalTone}</span>
            </div>
          </div>
          <ContextBar snapshot={snapshot} selectedAircraftId={selectedAircraftId} selectedReceiverId={selectedReceiverId} pageKey={pageKey} />
        </header>
        <main id="main-content" className="min-w-0 p-3 sm:p-6">{pageKey === 'registry' ? <FirstRunNotice /> : null}{children}</main>
      </div>

      <Dialog.Root open={rightDockOpen && !wideDock} onOpenChange={setRightDockOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-modal-backdrop bg-black/60" />
          <Dialog.Content className="fixed inset-y-0 right-0 z-modal flex w-[380px] max-w-[94vw] flex-col border-l border-line bg-[#0c1015] outline-none" aria-describedby={undefined}>
            <div className="flex h-16 items-center justify-between border-b border-line px-4"><Dialog.Title className="text-sm font-semibold text-ink">Investigation inspector</Dialog.Title><Dialog.Close asChild><Button variant="ghost" size="icon-sm" aria-label="Close investigation inspector"><X className="size-4" /></Button></Dialog.Close></div>
            <InvestigationDock dock={dock} pageKey={pageKey} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {rightDockOpen && wideDock ? <aside className="fixed inset-y-0 right-0 z-sticky hidden w-[360px] flex-col border-l border-line bg-[#0c1015] 2xl:flex"><div className="flex h-16 items-center justify-between border-b border-line px-4"><p className="text-sm font-semibold text-ink">Investigation inspector</p><Tooltip label="Hide investigation inspector" side="left"><Button variant="ghost" size="icon-sm" aria-label="Hide investigation inspector" onClick={() => setRightDockOpen(false)}><PanelRightClose className="size-4" /></Button></Tooltip></div><InvestigationDock dock={dock} pageKey={pageKey} /></aside> : null}
      <CommandPalette snapshot={snapshot} />
    </div>
  );
}
