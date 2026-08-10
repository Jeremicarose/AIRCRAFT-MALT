'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { Activity, ChevronLeft, ChevronRight, Database, Gauge, History, Map, Menu, PanelLeftClose, PanelRightClose, PanelRightOpen, Plane, RadioTower, Search, Settings, Sparkles, Star, SlidersHorizontal, Workflow } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { CommandPalette } from '@/components/ui/command-palette';
import { Button } from '@/components/ui/button';
import { StatusChip } from '@/components/ui/status-chip';
import { NotificationCenter } from '@/components/ui/notification-center';
import { Tooltip } from '@/components/ui/tooltip';
import { consoleRoutes, type ConsoleRoute } from '@/lib/routes';
import { toneFromFreshness } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { InvestigationDockState, ShellSnapshot, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';
import { InvestigationActions, InvestigationEvidenceList, InvestigationFacts, InvestigationTimeline } from '@/components/operations-ui';

const routeIcons: Record<string, LucideIcon> = {
  overview: Gauge,
  localization: Map,
  aircraft: Plane,
  receivers: RadioTower,
  pipeline: Workflow,
  metrics: Activity,
  environment: Database,
  settings: Settings,
};

const groups: ConsoleRoute['group'][] = ['Operate', 'Explore', 'Investigate', 'System'];

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
  return consoleRoutes.find((route) => route.key === pageKey)?.label ?? 'Console';
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
                <Link
                  href={route.href}
                  onClick={onNavigate}
                  aria-current={active ? 'page' : undefined}
                  className={cn('group flex h-9 items-center gap-3 rounded-md px-2.5 text-[13px] font-medium text-ink-secondary transition-colors duration-standard hover:bg-graphite-hover hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue', active && 'bg-graphite-hover text-ink')}
                >
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

function ContextChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-graphite-raised/55 px-2.5 py-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-ink-quiet">{label}</p>
      <p className="mt-1 text-xs font-semibold text-ink-secondary">{value}</p>
    </div>
  );
}

function ShellRailCard({ icon: Icon, label, value, detail, accent = 'text-ink-quiet' }: { icon: LucideIcon; label: string; value: string; detail: string; accent?: string }) {
  return (
    <div className="min-w-[220px] rounded-xl border border-line bg-[linear-gradient(180deg,rgba(18,22,27,0.98),rgba(10,13,17,0.96))] px-3.5 py-3 shadow-[0_18px_30px_-28px_rgba(0,0,0,0.8)]">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-line bg-graphite-raised/80">
          <Icon className={`size-4 ${accent}`} />
        </span>
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-quiet">{label}</p>
          <p className="mt-1 truncate text-sm font-semibold text-ink">{value}</p>
          <p className="mt-1 text-[11px] leading-5 text-ink-quiet">{detail}</p>
        </div>
      </div>
    </div>
  );
}

function DockPlaceholder({ pageKey }: { pageKey: string }) {
  return (
    <div className="flex h-full flex-col justify-between p-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-quiet">Investigation dock</p>
        <h2 className="mt-2 text-sm font-semibold text-ink">{routeLabelFromKey(pageKey)} workspace</h2>
        <p className="mt-2 text-xs leading-5 text-ink-quiet">Select an aircraft, receiver, or evidence surface to pin shared context here. This dock persists across routes so operators can keep the same investigation in view.</p>
      </div>
      <div className="rounded-lg border border-dashed border-line bg-graphite-raised/35 p-3">
        <p className="text-[11px] font-semibold text-ink-secondary">Pinned context</p>
        <p className="mt-1 text-xs leading-5 text-ink-quiet">The shell will retain selected aircraft, receiver, filters, and timeline focus between pages.</p>
      </div>
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
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-quiet">Pinned investigation</p>
            <h2 className="mt-1 truncate text-sm font-semibold text-ink">{dock.title}</h2>
            {dock.subtitle ? <p className="mt-1 text-xs leading-5 text-ink-quiet">{dock.subtitle}</p> : null}
          </div>
          {dock.statusLabel ? <StatusChip label={dock.statusLabel} tone={dock.statusTone} className="shrink-0" /> : null}
        </div>
      </div>
      {dock.actions?.length ? <div className="border-b border-line"><InvestigationActions actions={dock.actions} /></div> : null}
      {dock.facts?.length ? <div className="border-b border-line"><InvestigationFacts items={dock.facts} /></div> : null}
      {dock.timeline?.length ? <div className="border-b border-line"><div className="px-4 pt-4"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-quiet">Timeline</p></div><InvestigationTimeline items={dock.timeline} /></div> : null}
      {dock.evidence?.length ? <div><div className="px-4 pt-4"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-quiet">Evidence</p></div><InvestigationEvidenceList items={dock.evidence} /></div> : null}
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
  const investigation = useOperatorStore((state) => state.investigation);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const dock = useOperatorStore((state) => state.dock);
  const density = useOperatorStore((state) => state.density);
  const routeHistory = useOperatorStore((state) => state.routeHistory);
  const starredRoutes = useOperatorStore((state) => state.starredRoutes);
  const recentInvestigations = useOperatorStore((state) => state.recentInvestigations);
  const pushRouteHistory = useOperatorStore((state) => state.pushRouteHistory);
  const pushRecentInvestigation = useOperatorStore((state) => state.pushRecentInvestigation);
  const toggleStarredRoute = useOperatorStore((state) => state.toggleStarredRoute);
  const reduceMotion = useReducedMotion();
  const summary = getSystemSummary(snapshot);
  const signalAge = snapshot.healthData?.freshness?.last_signal_age_s;
  const signalTone = toneFromFreshness(signalAge, 15, 60);
  const pinnedRoute = consoleRoutes.find((route) => route.key === pageKey);
  const breadcrumbRoutes = [
    { label: 'Console', href: '/app/overview' },
    ...(pinnedRoute ? [{ label: pinnedRoute.group, href: pinnedRoute.href }, { label: pinnedRoute.label, href: pinnedRoute.href }] : [{ label: title, href: '#' }]),
  ];
  const favoriteRoutes = starredRoutes.map((routeKey) => consoleRoutes.find((route) => route.key === routeKey)).filter((route): route is ConsoleRoute => Boolean(route));
  const routeHistoryPreview = routeHistory.slice(0, 3);
  const recentInvestigationPreview = recentInvestigations.slice(0, 3);

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
    setInvestigationContext({ routeKey: pageKey });
    const route = consoleRoutes.find((item) => item.key === pageKey);
    if (route) pushRouteHistory({ key: route.key, label: route.label, href: route.href });
  }, [pageKey, pushRouteHistory, setInvestigationContext]);

  useEffect(() => {
    document.documentElement.dataset.compactRows = density === 'compact' ? 'true' : 'false';
  }, [density]);

  useEffect(() => {
    if (!dock?.title) return;
    const activeRoute = dock.actions?.find((action) => action.href?.startsWith('/app/'))?.href;
    pushRecentInvestigation({
      id: `${dock.entityType}:${dock.title}`,
      title: dock.title,
      entityType: dock.entityType,
      routeKey: pageKey,
      href: activeRoute,
      focus: investigation.focus ?? dock.title,
      statusLabel: dock.statusLabel,
      statusTone: dock.statusTone,
    });
  }, [dock, investigation.focus, pageKey, pushRecentInvestigation]);

  useEffect(() => {
    if (summary.tone !== 'failure' || !('Notification' in window) || Notification.permission !== 'granted') return;
    try {
      const preferences = JSON.parse(window.localStorage.getItem('mlat-console-preferences') ?? '{}') as { desktopAlerts?: boolean };
      const noticeKey = `mlat-notice-${summary.label}`;
      if (preferences.desktopAlerts && !window.sessionStorage.getItem(noticeKey)) {
        new Notification('MLAT Airspace Console', { body: `${summary.label}. Open the pipeline to inspect the current blocker.` });
        window.sessionStorage.setItem(noticeKey, 'shown');
      }
    } catch { /* Browser notifications are an optional local preference. */ }
  }, [summary.label, summary.tone]);

  return (
    <div className="min-h-screen bg-graphite-deep text-ink" data-page={pageKey}>
      <aside className={cn('fixed inset-y-0 left-0 z-sticky hidden border-r border-line bg-[#0b0e12] transition-[width] duration-standard ease-operational lg:flex lg:flex-col', collapsed ? 'w-[68px]' : 'w-[232px]')}>
        <div className={cn('flex h-16 items-center border-b border-line', collapsed ? 'justify-center px-2' : 'justify-between px-3')}>
          <Link href="/app/overview" className="flex min-w-0 items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">
            <span className="relative flex size-8 shrink-0 items-center justify-center rounded-md bg-signal-blue text-[11px] font-bold text-graphite-deep"><span className="absolute inset-[5px] rounded-full border border-graphite-deep/45" />A</span>
            {!collapsed ? <span className="min-w-0"><strong className="block truncate text-[13px] font-semibold text-ink">Airspace Console</strong><small className="block truncate text-[10px] font-medium text-ink-quiet">MLAT OPERATIONS</small></span> : null}
          </Link>
          {!collapsed ? <Tooltip label="Collapse sidebar" side="bottom"><Button variant="ghost" size="icon-sm" aria-label="Collapse sidebar" onClick={() => setCollapsed(true)}><PanelLeftClose className="size-4" /></Button></Tooltip> : null}
        </div>
        <Navigation collapsed={collapsed} />
        <div className="border-t border-line p-2">
          <div className={cn('flex items-center gap-2 rounded-md px-2 py-2', collapsed && 'justify-center px-0')}>
            <span className={cn('size-2 shrink-0 rounded-full', summary.tone === 'healthy' ? 'bg-healthy' : summary.tone === 'replay' ? 'bg-replay' : summary.tone === 'attention' ? 'bg-attention' : 'bg-failure')} />
            {!collapsed ? <div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-ink-secondary">{summary.environment}</p><p className="truncate text-[10px] text-ink-quiet">{summary.label}</p></div> : null}
            {collapsed ? <Tooltip label="Expand sidebar"><Button variant="ghost" size="icon-sm" aria-label="Expand sidebar" onClick={() => setCollapsed(false)}><ChevronRight className="size-4" /></Button></Tooltip> : null}
          </div>
        </div>
      </aside>

      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-modal-backdrop bg-black/60 lg:hidden" />
          <Dialog.Content asChild aria-describedby={undefined}>
            <motion.aside className="fixed inset-y-0 left-0 z-modal flex w-[260px] flex-col border-r border-line bg-[#0b0e12] outline-none lg:hidden" initial={reduceMotion ? false : { x: -260 }} animate={{ x: 0 }} transition={{ duration: reduceMotion ? 0 : 0.18, ease: [0.22, 1, 0.36, 1] }}>
              <Dialog.Title className="sr-only">Console navigation</Dialog.Title>
              <div className="flex h-16 items-center justify-between border-b border-line px-3"><span className="text-sm font-semibold">Airspace Console</span><Dialog.Close asChild><Button variant="ghost" size="icon-sm" aria-label="Close navigation"><ChevronLeft className="size-4" /></Button></Dialog.Close></div>
              <Navigation collapsed={false} onNavigate={() => setMobileOpen(false)} />
            </motion.aside>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <div className={cn('transition-[padding-left,padding-right] duration-standard ease-operational', collapsed ? 'lg:pl-[68px]' : 'lg:pl-[232px]', rightDockOpen ? '2xl:pr-[360px]' : '2xl:pr-0')}>
        <header className="sticky top-0 z-sticky border-b border-line bg-graphite-deep/95 px-4 backdrop-blur-md sm:px-6">
          <div className="flex min-h-16 items-center justify-between gap-4 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu className="size-4" /></Button>
              <div className="min-w-0">
                <div className="mb-1 hidden items-center gap-1.5 text-[11px] text-ink-quiet md:flex">
                  {breadcrumbRoutes.map((item, index) => (
                    <div key={`${item.label}-${index}`} className="flex items-center gap-1.5">
                      {index ? <ChevronRight className="size-3 text-ink-quiet/70" /> : null}
                      <Link href={item.href} className="rounded-sm hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">{item.label}</Link>
                    </div>
                  ))}
                </div>
                <h1 className="truncate text-lg font-semibold leading-tight tracking-normal text-ink sm:text-xl">{title}</h1>
                <p className="mt-0.5 hidden truncate text-xs text-ink-quiet sm:block">{description}</p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button onClick={() => setCommandOpen(true)} className="hidden h-8 min-w-[190px] items-center gap-2 rounded-md border border-line bg-graphite px-2.5 text-xs text-ink-quiet transition-colors duration-standard hover:border-[#3a4350] hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue md:flex"><Search className="size-3.5" /><span className="flex-1 text-left">Search mission control</span><kbd className="rounded border border-line bg-graphite-raised px-1.5 py-0.5 font-sans text-[10px]">⌘/Ctrl K</kbd></button>
              <Tooltip label={favoriteRoutes.some((route) => route.key === pageKey) ? 'Remove workspace from favorites' : 'Add workspace to favorites'} side="bottom"><Button variant="ghost" size="icon-sm" aria-label={favoriteRoutes.some((route) => route.key === pageKey) ? 'Remove workspace from favorites' : 'Add workspace to favorites'} onClick={() => toggleStarredRoute(pageKey)}><Star className={cn('size-4', favoriteRoutes.some((route) => route.key === pageKey) ? 'fill-amber-300 text-amber-300' : '')} /></Button></Tooltip>
              <Tooltip label={rightDockOpen ? 'Hide investigation dock' : 'Show investigation dock'} side="bottom"><Button variant="ghost" size="icon-sm" aria-label={rightDockOpen ? 'Hide investigation dock' : 'Show investigation dock'} onClick={() => setRightDockOpen(!rightDockOpen)}>{rightDockOpen ? <PanelRightClose className="size-4" /> : <PanelRightOpen className="size-4" />}</Button></Tooltip>
              <StatusChip label={summary.label} tone={summary.tone} />
              <NotificationCenter snapshot={snapshot} />
              <Tooltip label="Search console" side="bottom"><Button variant="ghost" size="icon-sm" className="md:hidden" aria-label="Search console" onClick={() => setCommandOpen(true)}><Search className="size-4" /></Button></Tooltip>
              <span className="sr-only">Signal freshness: {signalTone}</span>
            </div>
          </div>
          <div className="grid gap-3 border-t border-line/70 py-3 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
            <div className="grid gap-2 xl:grid-cols-[repeat(3,minmax(0,1fr))]">
              <ContextChip label="Environment" value={summary.environment} />
              <ContextChip label="Signal age" value={signalAge == null ? 'Unavailable' : `${Math.round(signalAge)}s`} />
              <ContextChip label="Route" value={investigation.routeKey ? routeLabelFromKey(investigation.routeKey) : routeLabelFromKey(pageKey)} />
              <ContextChip label="Aircraft focus" value={selectedAircraftId ?? 'None pinned'} />
              <ContextChip label="Receiver focus" value={selectedReceiverId ?? 'None pinned'} />
              <ContextChip label="Time window" value={investigation.timeRange ?? '10m'} />
            </div>
            <div className="flex min-w-0 items-center gap-2 overflow-x-auto pb-1 xl:justify-end xl:pb-0">
              <ShellRailCard icon={Star} label="Favorites" value={favoriteRoutes[0]?.label ?? 'No favorites'} detail={favoriteRoutes.length ? `${favoriteRoutes.length} workspaces pinned for quick return.` : 'Pin a workspace to keep it in your mission bar.'} accent="text-amber-300" />
              <ShellRailCard icon={History} label="Last route" value={routeHistoryPreview[0]?.label ?? 'No history'} detail={routeHistoryPreview[1] ? `Previous stop: ${routeHistoryPreview[1].label}.` : 'Recent navigation appears here as you move between workspaces.'} accent="text-signal-blue" />
              <ShellRailCard icon={Sparkles} label="Recent investigation" value={recentInvestigationPreview[0]?.title ?? 'Nothing pinned'} detail={recentInvestigationPreview[0]?.statusLabel ?? 'Pinned evidence follows you across the console.'} accent="text-trust-cyan" />
            </div>
          </div>
        </header>
        <motion.main key={pageKey} className="min-w-0 p-4 sm:p-6" initial={reduceMotion ? false : { opacity: 0.96, y: 2 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : 0.16, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.main>
        <div className="border-t border-line bg-[#090c10]/92 px-4 py-3 backdrop-blur sm:px-6">
          <div className="flex gap-3 overflow-x-auto pb-1">
            <ShellRailCard icon={History} label="Route history" value={routeHistoryPreview[0]?.label ?? 'No recent routes'} detail={routeHistoryPreview.map((route) => route.label).slice(1).join(' • ') || 'Use this rail to keep navigation continuity.'} accent="text-signal-blue" />
            <ShellRailCard icon={Plane} label="Pinned aircraft" value={selectedAircraftId ?? 'No aircraft pinned'} detail={selectedAircraftId ? 'Shared investigation context remains attached across pages.' : 'Select an aircraft to keep its trajectory in context.'} accent="text-selection" />
            <ShellRailCard icon={RadioTower} label="Pinned receiver" value={selectedReceiverId ?? 'No receiver pinned'} detail={selectedReceiverId ? 'Receiver trust and health stay visible while you navigate.' : 'Select a receiver to preserve fleet context.'} accent="text-trust-cyan" />
            <ShellRailCard icon={Sparkles} label="Investigation rail" value={recentInvestigationPreview[0]?.title ?? 'Awaiting drill-down'} detail={recentInvestigationPreview.length > 1 ? `Next: ${recentInvestigationPreview[1]?.title}` : 'Pinned evidence and timeline moments accumulate here.'} accent="text-healthy" />
          </div>
        </div>
      </div>

      {rightDockOpen ? (
        <aside className="fixed inset-y-0 right-0 z-[35] hidden w-[360px] border-l border-line bg-[#0c1015]/98 backdrop-blur-md 2xl:flex 2xl:flex-col">
          <div className="flex h-16 items-center justify-between border-b border-line px-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-quiet">Drill-down</p>
              <p className="mt-1 text-sm font-semibold text-ink">Operator evidence dock</p>
            </div>
            <Tooltip label="Hide investigation dock" side="left"><Button variant="ghost" size="icon-sm" aria-label="Hide investigation dock" onClick={() => setRightDockOpen(false)}><PanelRightClose className="size-4" /></Button></Tooltip>
          </div>
          <InvestigationDock dock={dock} pageKey={pageKey} />
        </aside>
      ) : null}
      <CommandPalette snapshot={snapshot} />
    </div>
  );
}
