'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Clock3, Crosshair, Filter, Link2, Plane, Radio, RefreshCw, Target, Wifi, WifiOff } from 'lucide-react';
import { io } from 'socket.io-client';
import { useEffect, useMemo, useState } from 'react';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { ActivityRail, ConfidenceGauge, FactGrid, Inspector, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { Button, buttonVariants } from '@/components/ui/button';
import { StatusChip } from '@/components/ui/status-chip';
import { Tooltip } from '@/components/ui/tooltip';
import { RelativeTime } from '@/components/ui/relative-time';
import { SearchField } from '@/components/ui/search-field';
import { fetchJson, getApiBase } from '@/lib/api';
import { formatAltitude, formatCoordinate, formatDistanceMeters, latestPositions, number, percent, toneFromScore } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { HealthData, ModeData, PositionsResponse, ReceiversResponse, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

interface LiveMapPageProps {
  initialModeData: ModeData | null;
  initialHealthData: HealthData | null;
  initialPositionsData: PositionsResponse;
  initialReceiversData: ReceiversResponse;
}

export default function LiveMapPage({ initialModeData, initialHealthData, initialPositionsData, initialReceiversData }: LiveMapPageProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [fitRequest, setFitRequest] = useState(0);
  const [streamConnected, setStreamConnected] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [timeMode, setTimeMode] = useState<'live' | 'replay'>('live');
  const selectedAircraftId = useOperatorStore((state) => state.selectedAircraftId);
  const selectedReceiverId = useOperatorStore((state) => state.selectedReceiverId);
  const setSelectedAircraftId = useOperatorStore((state) => state.setSelectedAircraftId);
  const setSelectedReceiverId = useOperatorStore((state) => state.setSelectedReceiverId);
  const showReceiverLinks = useOperatorStore((state) => state.showReceiverLinks);
  const showUncertainty = useOperatorStore((state) => state.showUncertainty);
  const toggleReceiverLinks = useOperatorStore((state) => state.toggleReceiverLinks);
  const toggleUncertainty = useOperatorStore((state) => state.toggleUncertainty);
  const setDock = useOperatorStore((state) => state.setDock);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);

  const positionsQuery = useQuery({ queryKey: ['positions', 'live-map'], queryFn: () => fetchJson<PositionsResponse>('/api/positions/recent?seconds=600&limit=250'), initialData: initialPositionsData, refetchInterval: refreshInterval * 1_000 });
  const receiversQuery = useQuery({ queryKey: ['receivers'], queryFn: () => fetchJson<ReceiversResponse>('/api/receivers'), initialData: initialReceiversData, refetchInterval: 20_000 });
  const modeQuery = useQuery({ queryKey: ['mode'], queryFn: () => fetchJson<ModeData>('/api/system/mode'), initialData: initialModeData ?? undefined, refetchInterval: 20_000 });
  const healthQuery = useQuery({ queryKey: ['health'], queryFn: () => fetchJson<HealthData>('/api/health'), initialData: initialHealthData ?? undefined, refetchInterval: refreshInterval * 1_000 });

  const aircraft = useMemo(() => latestPositions(positionsQuery.data?.positions ?? []), [positionsQuery.data]);
  const receivers = receiversQuery.data?.receivers ?? [];
  const selectedAircraft = aircraft.find((item) => item.aircraft_id === selectedAircraftId) ?? aircraft[0] ?? null;
  const selectedReceiver = receivers.find((item) => item.receiver_id === selectedReceiverId) ?? null;
  const contributingReceivers = selectedAircraft ? receivers.filter((receiver) => selectedAircraft.correlation?.receiver_ids?.includes(receiver.receiver_id)) : [];
  const searchResults = search.trim() ? aircraft.filter((item) => item.aircraft_id.toLowerCase().includes(search.trim().toLowerCase())).slice(0, 8) : [];
  const isReplay = Boolean(modeQuery.data?.demo_mode || modeQuery.data?.simulation_mode || modeQuery.data?.synthetic_feed_mode);

  useEffect(() => {
    if (!selectedAircraftId && aircraft[0]) setSelectedAircraftId(aircraft[0].aircraft_id);
  }, [aircraft, selectedAircraftId, setSelectedAircraftId]);

  useEffect(() => {
    const loadPreference = () => {
      try {
        const stored = JSON.parse(window.localStorage.getItem('mlat-console-preferences') ?? '{}') as { refreshInterval?: number };
        if (Number.isFinite(stored.refreshInterval)) setRefreshInterval(Math.max(5, Math.min(60, Number(stored.refreshInterval))));
      } catch { /* Ignore invalid local preferences. */ }
    };
    loadPreference();
    window.addEventListener('mlat-preferences-change', loadPreference);
    return () => window.removeEventListener('mlat-preferences-change', loadPreference);
  }, []);

  useEffect(() => {
    if (!modeQuery.data?.websocket_available) return;
    const socket = io(getApiBase(), { path: '/socket.io/', transports: ['websocket', 'polling'] });
    socket.on('connect', () => setStreamConnected(true));
    socket.on('disconnect', () => setStreamConnected(false));
    socket.on('position_update', () => queryClient.invalidateQueries({ queryKey: ['positions'] }));
    return () => { socket.disconnect(); };
  }, [modeQuery.data?.websocket_available, queryClient]);

  useEffect(() => {
    setInvestigationContext({ focus: selectedAircraft?.aircraft_id ?? selectedReceiver?.receiver_id ?? 'live-map', timeRange: timeMode === 'live' ? '10m' : 'replay' });
    setDock({
      entityType: 'aircraft',
      title: selectedAircraft?.aircraft_id ?? 'Live map focus',
      subtitle: selectedAircraft ? 'Pinned directly from the spatial debugger.' : 'Use the map or search to select an active aircraft.',
      statusLabel: selectedAircraft ? percent(selectedAircraft.quality?.score, 0) : isReplay ? 'Replay' : streamConnected ? 'Streaming' : 'Polling',
      statusTone: selectedAircraft ? toneFromScore(selectedAircraft.quality?.score) : isReplay ? 'replay' : streamConnected ? 'healthy' : 'attention',
      facts: selectedAircraft ? [
        { label: 'Position', value: formatCoordinate(selectedAircraft.position?.latitude ?? selectedAircraft.latitude, selectedAircraft.position?.longitude ?? selectedAircraft.longitude) },
        { label: 'Altitude', value: formatAltitude(selectedAircraft.position?.altitude ?? selectedAircraft.altitude) },
        { label: 'Uncertainty', value: formatDistanceMeters(selectedAircraft.quality?.uncertainty_m ?? selectedAircraft.uncertainty) },
        { label: 'Receivers', value: number(selectedAircraft.correlation?.receiver_count ?? selectedAircraft.num_receivers) },
      ] : [
        { label: 'Aircraft', value: number(aircraft.length) },
        { label: 'Receivers', value: number(receivers.length) },
        { label: 'Transport', value: streamConnected ? 'Websocket' : 'Polling', tone: streamConnected ? 'healthy' : 'attention' },
        { label: 'Window', value: timeMode === 'live' ? 'Live stream' : 'Replay context', tone: timeMode === 'live' ? 'selection' : 'replay' },
      ],
      timeline: [
        { title: 'Spatial source', detail: isReplay ? 'Replay or synthetic source is active.' : 'Live receiver network is active.', tone: isReplay ? 'replay' : 'healthy' },
        { title: 'Transport', detail: streamConnected ? 'Websocket updates are connected.' : `Fallback polling every ${refreshInterval}s.`, tone: streamConnected ? 'healthy' : 'attention' },
        { title: 'Selected receiver geometry', detail: contributingReceivers.length ? `${contributingReceivers.length} receivers currently contribute to the selected solve.` : 'No contributing receiver metadata is attached to the current focus.', tone: contributingReceivers.length ? 'selection' : 'attention' },
      ],
      evidence: [
        { title: 'Spatial debugger', detail: 'Layer toggles, fit controls, and direct entity selection stay connected to the shared shell dock.', state: 'Active', tone: 'selection' },
      ],
      actions: [
        { label: 'Open aircraft workspace', href: selectedAircraft ? `/app/aircraft?aircraft=${encodeURIComponent(selectedAircraft.aircraft_id)}` : '/app/aircraft', tone: 'primary' },
        { label: 'Open receivers', href: '/app/receivers', tone: 'secondary' },
      ],
    });
    return () => setDock(null);
  }, [aircraft.length, contributingReceivers.length, isReplay, receivers.length, refreshInterval, selectedAircraft, selectedReceiver?.receiver_id, setDock, setInvestigationContext, streamConnected, timeMode]);

  const refresh = () => Promise.all([positionsQuery.refetch(), receiversQuery.refetch(), healthQuery.refetch()]);

  const activityRail = [
    { title: 'Position stream', detail: streamConnected ? 'Websocket pushes live position updates into the map.' : `Fallback polling every ${refreshInterval}s keeps the air picture current.`, meta: streamConnected ? 'Live' : 'Polling', tone: streamConnected ? 'healthy' : 'attention' as StatusTone },
    { title: 'Receiver graph', detail: showReceiverLinks ? 'Receiver geometry links are visible for the selected solve.' : 'Receiver geometry links are hidden in the current view.', meta: showReceiverLinks ? 'On' : 'Off', tone: showReceiverLinks ? 'selection' : 'neutral' as StatusTone },
    { title: 'Uncertainty layer', detail: showUncertainty ? 'Solve uncertainty is rendered directly on the map.' : 'Uncertainty ring is hidden to prioritize track clutter.', meta: showUncertainty ? 'On' : 'Off', tone: showUncertainty ? 'selection' : 'neutral' as StatusTone },
  ];

  const receiverTimeline = contributingReceivers.slice(0, 5).map((receiver) => ({
    title: receiver.receiver_id,
    detail: `${receiver.status || 'Status unavailable'} · ${receiver.latitude && receiver.longitude ? formatCoordinate(receiver.latitude, receiver.longitude) : 'No coordinates'}`,
    tone: receiver.receiver_id === selectedReceiverId ? 'selection' as StatusTone : 'healthy' as StatusTone,
    meta: receiver.last_seen ? `${Math.max(0, Math.round(Date.now() / 1000 - receiver.last_seen))}s` : 'n/a',
  }));

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        eyebrow="Operate"
        title="Spatial debugger"
        description="The live map is now the center of the console. Operators can search, pin entities, toggle geometric context, and move directly into receiver or aircraft investigations while keeping the same shared dock."
        status={<StatusChip label={isReplay ? 'Replay' : streamConnected ? 'Streaming' : modeQuery.data?.runtime_status === 'active' ? 'Live refresh' : 'Offline'} tone={isReplay ? 'replay' : streamConnected || modeQuery.data?.runtime_status === 'active' ? 'healthy' : 'failure'} />}
        actions={<div className="flex flex-wrap items-center gap-2"><button type="button" onClick={() => setTimeMode(timeMode === 'live' ? 'replay' : 'live')} className={buttonVariants({ variant: 'secondary', size: 'sm' })}><Clock3 className="size-3.5" />{timeMode === 'live' ? 'Switch to replay context' : 'Return to live context'}</button><button type="button" onClick={() => void refresh()} className={buttonVariants({ variant: 'primary', size: 'sm' })}><RefreshCw className={cn('size-3.5', positionsQuery.isFetching && 'animate-spin')} />Refresh</button></div>}
        rail={<SignalMarquee items={[{ label: 'Aircraft', value: number(aircraft.length), tone: aircraft.length ? 'healthy' : 'attention' }, { label: 'Receivers', value: number(receivers.length), tone: receivers.length ? 'trust' : 'attention' }, { label: 'Transport', value: streamConnected ? 'Websocket' : 'Polling', tone: streamConnected ? 'healthy' : 'attention' }, { label: 'Context', value: timeMode === 'live' ? 'Live window' : 'Replay window', tone: timeMode === 'live' ? 'selection' : 'replay' }]} />}
      />

      <WorkspaceSplit
        secondaryWidth="420px"
        primary={<WorkspacePanel title="Live spatial canvas" detail="Search, fit, replay context, and layer toggles stay anchored to the map." tone="trust"><div className="relative min-h-[620px] overflow-hidden bg-[#090c10]"><div className="absolute left-3 right-14 top-3 z-dropdown flex flex-wrap items-center gap-2"><div className="relative min-w-[220px] flex-1 sm:max-w-[360px]"><SearchField value={search} onValueChange={setSearch} placeholder="Search aircraft" label="Search aircraft" elevated />{searchResults.length ? <div className="absolute left-0 right-0 top-11 overflow-hidden rounded-md border border-line bg-[#11151a] shadow-overlay">{searchResults.map((item) => <button key={item.aircraft_id} type="button" onClick={() => { setSelectedAircraftId(item.aircraft_id); setSearch(''); setFitRequest((value) => value + 1); }} className="flex w-full items-center gap-3 border-b border-line px-3 py-2.5 text-left text-xs text-ink-secondary last:border-0 hover:bg-graphite-hover hover:text-ink"><Plane className="size-3.5 text-signal-blue" /><span className="font-semibold">{item.aircraft_id}</span><span className="ml-auto text-ink-quiet">{percent(item.quality?.score, 0)}</span></button>)}</div> : null}</div><DropdownMenu.Root><DropdownMenu.Trigger asChild><Button size="icon" className="bg-graphite/95 shadow-map backdrop-blur-sm" aria-label="Map filters"><Filter className="size-4" /></Button></DropdownMenu.Trigger><DropdownMenu.Portal><DropdownMenu.Content align="start" sideOffset={6} className="z-dropdown min-w-52 rounded-md border border-line bg-[#11151a] p-1 shadow-overlay"><DropdownMenu.Label className="px-2 py-1.5 text-[11px] font-semibold text-ink-quiet">Map layers</DropdownMenu.Label><DropdownMenu.CheckboxItem checked={showReceiverLinks} onCheckedChange={toggleReceiverLinks} className="flex cursor-default items-center gap-2 rounded px-2 py-2 text-xs text-ink-secondary outline-none data-[highlighted]:bg-graphite-hover data-[highlighted]:text-ink"><span className={cn('size-3 rounded-sm border border-line', showReceiverLinks && 'border-signal-blue bg-signal-blue')} /><Link2 className="size-3.5" />Receiver links</DropdownMenu.CheckboxItem><DropdownMenu.CheckboxItem checked={showUncertainty} onCheckedChange={toggleUncertainty} className="flex cursor-default items-center gap-2 rounded px-2 py-2 text-xs text-ink-secondary outline-none data-[highlighted]:bg-graphite-hover data-[highlighted]:text-ink"><span className={cn('size-3 rounded-sm border border-line', showUncertainty && 'border-signal-blue bg-signal-blue')} /><Target className="size-3.5" />Uncertainty</DropdownMenu.CheckboxItem></DropdownMenu.Content></DropdownMenu.Portal></DropdownMenu.Root><Tooltip label="Fit selection" side="bottom"><Button size="icon" className="bg-graphite/95 shadow-map backdrop-blur-sm" onClick={() => setFitRequest((value) => value + 1)} aria-label="Fit selected aircraft"><Crosshair className="size-4" /></Button></Tooltip></div><LazyAirspaceMap aircraft={aircraft} receivers={receivers} selectedAircraftId={selectedAircraft?.aircraft_id} selectedReceiverId={selectedReceiver?.receiver_id} onSelectAircraft={setSelectedAircraftId} onSelectReceiver={setSelectedReceiverId} showReceiverLinks={showReceiverLinks} showUncertainty={showUncertainty} fitRequest={fitRequest} className="map-live" /><div className="absolute bottom-3 left-3 z-dropdown flex items-center gap-3 rounded-md border border-line bg-graphite/92 px-3 py-2 text-[11px] text-ink-secondary shadow-map backdrop-blur-sm"><span className="flex items-center gap-1.5"><Plane className="size-3 text-signal-blue" />{aircraft.length} aircraft</span><span className="h-3 w-px bg-line" /><span className="flex items-center gap-1.5"><Radio className="size-3 text-series-teal" />{receivers.length} receivers</span><span className="hidden h-3 w-px bg-line sm:block" /><span className="hidden sm:inline">Signal {healthQuery.data?.freshness?.last_signal_age_s == null ? 'unavailable' : `${Math.round(healthQuery.data.freshness.last_signal_age_s)}s`}</span></div></div></WorkspacePanel>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Map behavior" detail="Current transport, layer state, and operator context." tone={streamConnected ? 'healthy' : 'attention'}><ActivityRail items={activityRail} /></WorkspacePanel><WorkspacePanel title="Receiver contribution timeline" detail="The selected solve can pivot directly into infrastructure context." tone={receiverTimeline.length ? 'selection' : 'attention'}>{receiverTimeline.length ? <Timeline items={receiverTimeline} /> : <div className="grid min-h-40 place-items-center px-6 text-center text-xs text-ink-quiet">Select an aircraft with receiver contribution metadata to populate this timeline.</div>}</WorkspacePanel></div>}
      />

      <Inspector title={selectedAircraft?.aircraft_id ?? 'No aircraft selected'} subtitle={selectedAircraft ? <span>Updated <RelativeTime timestamp={selectedAircraft.timestamp} /></span> : 'Select an aircraft on the map'} status={selectedAircraft ? <StatusChip label={percent(selectedAircraft.quality?.score, 0)} tone={toneFromScore(selectedAircraft.quality?.score)} /> : <StatusChip label="Waiting" />} className="xl:hidden">
        {selectedAircraft ? <>
          <div className="border-b border-line p-4"><ConfidenceGauge value={Number(selectedAircraft.quality?.score ?? 0)} /></div>
          <FactGrid items={[
            { label: 'Position', value: formatCoordinate(selectedAircraft.position?.latitude ?? selectedAircraft.latitude, selectedAircraft.position?.longitude ?? selectedAircraft.longitude) },
            { label: 'Altitude', value: formatAltitude(selectedAircraft.position?.altitude ?? selectedAircraft.altitude) },
            { label: 'Uncertainty', value: formatDistanceMeters(selectedAircraft.quality?.uncertainty_m ?? selectedAircraft.uncertainty) },
            { label: 'Receivers', value: number(selectedAircraft.correlation?.receiver_count ?? selectedAircraft.num_receivers) },
          ]} />
          <div className="border-b border-line p-4"><div className="mb-3 flex items-center justify-between"><p className="text-xs font-semibold text-ink">Contributing receivers</p><span className="text-[11px] text-ink-quiet">{contributingReceivers.length}</span></div><div className="space-y-1">{contributingReceivers.length ? contributingReceivers.map((receiver) => <button key={receiver.receiver_id} type="button" onClick={() => { setSelectedReceiverId(receiver.receiver_id); setFitRequest((value) => value + 1); }} className={cn('flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-xs text-ink-secondary outline-none transition-colors duration-standard hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-signal-blue', receiver.receiver_id === selectedReceiverId && 'bg-graphite-hover text-ink')}><span className="size-1.5 rounded-full bg-series-teal" /><span className="truncate">{receiver.receiver_id}</span><span className="ml-auto text-[10px] text-ink-quiet"><RelativeTime timestamp={receiver.last_seen} /></span></button>) : <p className="text-xs leading-5 text-ink-quiet">No receiver contribution metadata is available.</p>}</div></div>
          <div className="p-4"><div className="flex items-center gap-2 text-xs text-ink-secondary">{streamConnected ? <Wifi className="size-3.5 text-healthy" /> : <WifiOff className="size-3.5 text-ink-quiet" />}<span>{streamConnected ? 'Position stream connected' : 'Using interval refresh'}</span></div></div>
        </> : <div className="p-6 text-center text-xs text-ink-quiet">Aircraft will appear when solved positions enter the current window.</div>}
      </Inspector>
    </div>
  );
}
