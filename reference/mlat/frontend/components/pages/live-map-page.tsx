'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useQuery } from '@tanstack/react-query';
import { Crosshair, Filter, Link2, MapPin, Plane, Radio, RefreshCw, Target, Wifi, WifiOff } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { ReceiverInspector } from '@/components/receiver-inspector';
import { ActivityRail, ConfidenceGauge, FactGrid, Inspector, SignalMarquee, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { Button, buttonVariants } from '@/components/ui/button';
import { DataNotice } from '@/components/ui/data-notice';
import { RelativeTime } from '@/components/ui/relative-time';
import { SearchField } from '@/components/ui/search-field';
import { StatusChip } from '@/components/ui/status-chip';
import { Tooltip } from '@/components/ui/tooltip';
import { apiQueryKeys, fetchJson, presentApiError, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import { formatAltitude, formatCoordinate, formatDistanceMeters, latestPositions, number, percent, toneFromScore } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import { receiverDockState, reconcileReceivers } from '@/lib/receiver-state';
import type { HealthData, ModeData, Position, PositionsResponse, ReceiversResponse, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

interface LiveMapPageProps {
  initialModeData: ModeData | null;
  initialHealthData: HealthData | null;
  initialPositionsData: PositionsResponse;
  initialPositionsError: string | null;
  initialReceiversData: ReceiversResponse;
  initialReceiversError: string | null;
  initialSelectedAircraftId?: string | null;
  initialSelectedReceiverId?: string | null;
}

type FocusType = 'aircraft' | 'receiver';

export default function LiveMapPage({ initialModeData, initialHealthData, initialPositionsData, initialPositionsError, initialReceiversData, initialReceiversError, initialSelectedAircraftId, initialSelectedReceiverId }: LiveMapPageProps) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [fitRequest, setFitRequest] = useState(0);
  const streamConnected = false;
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [focusType, setFocusType] = useState<FocusType>(initialSelectedReceiverId ? 'receiver' : 'aircraft');
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
  const storeHydrated = useOperatorStore((state) => state.hasHydrated);

  const positionsQuery = useQuery({ queryKey: apiQueryKeys.positions, queryFn: () => fetchJson<PositionsResponse>(PUBLIC_POSITIONS_PATH), initialData: initialPositionsData, initialDataUpdatedAt: initialPositionsError ? 0 : undefined, refetchInterval: refreshInterval * 1_000 });
  const receiversQuery = useQuery({ queryKey: apiQueryKeys.receivers, queryFn: () => fetchJson<ReceiversResponse>('/api/receivers'), initialData: initialReceiversData, initialDataUpdatedAt: initialReceiversError ? 0 : undefined });
  const modeQuery = useQuery({ queryKey: apiQueryKeys.mode, queryFn: () => fetchJson<ModeData>('/api/system/mode'), initialData: initialModeData ?? undefined });
  const healthQuery = useQuery({ queryKey: apiQueryKeys.health, queryFn: () => fetchJson<HealthData>('/api/health'), initialData: initialHealthData ?? undefined });

  const aircraft = useMemo(() => latestPositions(positionsQuery.data?.positions ?? []), [positionsQuery.data]);
  const receivers = receiversQuery.data?.receivers ?? [];
  const receiverModels = useMemo(() => reconcileReceivers({ runtimeReceivers: receivers, positions: positionsQuery.data?.positions ?? [], runtimeInventoryAvailable: Boolean(receiversQuery.data) && !receiversQuery.error }), [positionsQuery.data?.positions, receivers, receiversQuery.data, receiversQuery.error]);
  const selectedAircraft = aircraft.find((item) => item.aircraft_id === (initialSelectedAircraftId ?? selectedAircraftId)) ?? aircraft.find((item) => item.aircraft_id === selectedAircraftId) ?? aircraft[0] ?? null;
  const selectedReceiverModel = receiverModels.find((item) => item.key === (initialSelectedReceiverId ?? selectedReceiverId)) ?? receiverModels.find((item) => item.key === selectedReceiverId) ?? null;
  const contributingReceivers = selectedAircraft
    ? receiverModels.filter((receiver) => receiver.relatedAircraftIds.includes(selectedAircraft.aircraft_id))
    : [];
  const isReplay = Boolean(modeQuery.data?.demo_mode || modeQuery.data?.simulation_mode || modeQuery.data?.synthetic_feed_mode);

  const selectAircraft = useCallback((aircraftId: string) => {
    setFocusType('aircraft');
    setSelectedAircraftId(aircraftId);
    setFitRequest((value) => value + 1);
    router.replace(`/app/localization?aircraft=${encodeURIComponent(aircraftId)}`, { scroll: false });
  }, [router, setSelectedAircraftId]);

  const selectReceiver = useCallback((receiverId: string) => {
    setFocusType('receiver');
    setSelectedReceiverId(receiverId);
    setFitRequest((value) => value + 1);
    router.replace(`/app/localization?receiver=${encodeURIComponent(receiverId)}`, { scroll: false });
  }, [router, setSelectedReceiverId]);

  useEffect(() => {
    if (!storeHydrated) return;
    if (initialSelectedReceiverId) {
      setSelectedReceiverId(initialSelectedReceiverId);
      setFocusType('receiver');
      return;
    }
    if (initialSelectedAircraftId) {
      setSelectedAircraftId(initialSelectedAircraftId);
      setFocusType('aircraft');
      return;
    }
    if (!selectedAircraftId && aircraft[0]) setSelectedAircraftId(aircraft[0].aircraft_id);
  }, [aircraft, initialSelectedAircraftId, initialSelectedReceiverId, selectedAircraftId, setSelectedAircraftId, setSelectedReceiverId, storeHydrated]);

  useEffect(() => {
    const loadPreference = () => {
      try {
        const stored = JSON.parse(window.localStorage.getItem('mlat-console-preferences') ?? '{}') as { refreshInterval?: number };
        if (Number.isFinite(stored.refreshInterval)) setRefreshInterval(Math.max(5, Math.min(60, Number(stored.refreshInterval))));
      } catch { /* Invalid local preferences use the ten-second default. */ }
    };
    loadPreference();
    window.addEventListener('mlat-preferences-change', loadPreference);
    return () => window.removeEventListener('mlat-preferences-change', loadPreference);
  }, []);

  useEffect(() => {
    if (!storeHydrated) return;
    const receiverModelFocus = focusType === 'receiver' ? selectedReceiverModel : null;
    const aircraftFocus = focusType === 'aircraft' ? selectedAircraft : null;
    setInvestigationContext({ focus: receiverModelFocus?.key ?? aircraftFocus?.aircraft_id ?? 'live-map', timeRange: isReplay ? 'replay' : '5m' });
    if (receiverModelFocus) {
      setDock(receiverDockState(receiverModelFocus, { includeRegistryAction: true }));
      return () => setDock(null);
    }
    setDock({
      entityType: 'aircraft',
      title: aircraftFocus?.aircraft_id ?? 'Network map',
      subtitle: aircraftFocus ? 'Selected directly from the spatial workspace.' : 'Select an aircraft or receiver on the map.',
      statusLabel: aircraftFocus ? percent(aircraftFocus.quality?.score, 0) : isReplay ? 'Replay' : streamConnected ? 'Streaming' : 'Polling',
      statusTone: aircraftFocus ? toneFromScore(aircraftFocus.quality?.score) : isReplay ? 'replay' : streamConnected ? 'healthy' : 'attention',
      facts: aircraftFocus ? [{ label: 'Position', value: formatCoordinate(aircraftFocus.position?.latitude ?? aircraftFocus.latitude, aircraftFocus.position?.longitude ?? aircraftFocus.longitude) }, { label: 'Altitude', value: formatAltitude(aircraftFocus.position?.altitude ?? aircraftFocus.altitude) }, { label: 'Uncertainty', value: formatDistanceMeters(aircraftFocus.quality?.uncertainty_m ?? aircraftFocus.uncertainty) }, { label: 'Receivers', value: number(aircraftFocus.correlation?.receiver_count ?? aircraftFocus.num_receivers) }] : [{ label: 'Aircraft', value: number(aircraft.length) }, { label: 'Receivers', value: number(receivers.length) }, { label: 'Transport', value: streamConnected ? 'Websocket' : 'Polling' }, { label: 'Source', value: isReplay ? 'Replay' : 'Live' }],
      timeline: [{ title: 'Data source', detail: isReplay ? 'Synthetic replay is active. Results are not live CKB evidence.' : 'Live receiver input is active.', tone: isReplay ? 'replay' : 'healthy' }, { title: 'Transport', detail: streamConnected ? 'Websocket updates are connected.' : `Polling every ${refreshInterval} seconds.`, tone: streamConnected ? 'healthy' : 'attention' }],
      actions: [{ label: 'Open aircraft details', href: aircraftFocus ? `/app/aircraft?aircraft=${encodeURIComponent(aircraftFocus.aircraft_id)}` : '/app/aircraft', tone: 'primary' }, { label: 'Open receivers', href: '/app/receivers', tone: 'secondary' }],
    });
    return () => setDock(null);
  }, [aircraft.length, focusType, isReplay, receivers.length, refreshInterval, selectedAircraft, selectedReceiverModel, setDock, setInvestigationContext, storeHydrated, streamConnected]);

  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return [];
    return [
      ...aircraft.filter((item) => item.aircraft_id.toLowerCase().includes(query)).slice(0, 5).map((item) => ({ id: item.aircraft_id, label: item.aircraft_id, type: 'aircraft' as const, detail: percent(item.quality?.score, 0) })),
      ...receiverModels.filter((item) => `${item.label} ${item.identity ?? ''}`.toLowerCase().includes(query)).slice(0, 5).map((item) => ({ id: item.key, label: item.label, type: 'receiver' as const, detail: item.identity ? 'Registry identity' : 'Operational receiver' })),
    ];
  }, [aircraft, receiverModels, search]);

  const refresh = () => Promise.all([positionsQuery.refetch(), receiversQuery.refetch(), modeQuery.refetch(), healthQuery.refetch()]);
  const focusReceiverModel = focusType === 'receiver' ? selectedReceiverModel : null;
  const focusAircraft = focusType === 'aircraft' ? selectedAircraft : null;
  const positionFailure = positionsQuery.error ?? (initialPositionsError && !positionsQuery.isFetchedAfterMount ? new Error(initialPositionsError) : null);
  const positionError = positionFailure ? presentApiError(positionFailure, 'The latest aircraft positions could not be refreshed. Last-known positions remain visible and may be stale.') : null;
  const receiverFailure = receiversQuery.error ?? (initialReceiversError && !receiversQuery.isFetchedAfterMount ? new Error(initialReceiversError) : null);
  const receiverError = receiverFailure ? presentApiError(receiverFailure, 'Receiver status could not be refreshed. Aircraft positions remain available, but receiver availability is unknown.') : null;
  const healthError = healthQuery.error ? presentApiError(healthQuery.error, 'System freshness could not be checked. The map remains usable, but its live status cannot be confirmed.') : null;
  const hasPositionData = Boolean(positionsQuery.data?.positions.length);
  const connectionLabel = isReplay
    ? 'Replay data'
    : positionError
      ? hasPositionData ? 'Stale data' : 'Offline'
      : modeQuery.data?.runtime_status === 'active' && !healthError
        ? 'Live polling'
        : 'Status unavailable';
  const connectionTone: StatusTone = isReplay ? 'replay' : positionError ? hasPositionData ? 'attention' : 'failure' : connectionLabel === 'Live polling' ? 'healthy' : 'attention';
  const refreshPending = positionsQuery.isFetching || receiversQuery.isFetching || modeQuery.isFetching || healthQuery.isFetching;
  const activityRail = [
    { title: 'Position updates', detail: positionError ? 'The last refresh failed. Last-known positions may be stale.' : `Polling every ${refreshInterval} seconds.`, meta: positionError ? connectionLabel : 'Polling', tone: positionError ? connectionTone : 'healthy' as StatusTone },
    { title: 'Receiver geometry', detail: showReceiverLinks ? 'Links are visible for the selected aircraft.' : 'Links are hidden.', meta: showReceiverLinks ? 'On' : 'Off', tone: showReceiverLinks ? 'selection' : 'neutral' as StatusTone },
    { title: 'Data provenance', detail: isReplay ? 'Synthetic replay, not live registry evidence.' : 'Live runtime input.', meta: isReplay ? 'Replay' : 'Live', tone: isReplay ? 'replay' : 'healthy' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      {positionError ? <DataNotice title="The air picture could not be refreshed" detail={positionError.detail} technicalDetail={positionError.technicalDetail} onRetry={() => void positionsQuery.refetch()} /> : null}
      {receiverError ? <DataNotice title="Receiver status is unavailable" detail={receiverError.detail} technicalDetail={receiverError.technicalDetail} tone="attention" onRetry={() => void receiversQuery.refetch()} /> : null}
      {healthError ? <DataNotice title="Live freshness could not be confirmed" detail={healthError.detail} technicalDetail={healthError.technicalDetail} tone="attention" onRetry={() => void healthQuery.refetch()} /> : null}
      <WorkspaceHeader title="Network map" description={isReplay ? 'Explore the replay receiver network and solved aircraft. Replay data demonstrates the MLAT workflow but is not live CKB evidence.' : 'Select an aircraft or receiver to keep its location, status, and evidence in the shared inspector.'} status={<StatusChip label={connectionLabel} tone={connectionTone} />} actions={<button type="button" onClick={() => void refresh()} disabled={refreshPending} className={buttonVariants({ variant: 'primary', size: 'sm' })}><RefreshCw className={cn('size-3.5', refreshPending && 'animate-spin')} />{refreshPending ? 'Refreshing' : 'Refresh map'}</button>} rail={<SignalMarquee items={[{ label: 'Aircraft', value: number(aircraft.length), tone: aircraft.length ? 'healthy' : 'attention' }, { label: 'Receivers', value: receiverError ? 'Unknown' : number(receivers.length), tone: receiverError ? 'attention' : receivers.length ? 'selection' : 'attention' }, { label: 'Connection', value: connectionLabel, tone: connectionTone }, { label: 'Network', value: 'CKB testnet', tone: 'trust' }]} />}/>

      <WorkspaceSplit
        secondaryWidth="380px"
        primary={<WorkspacePanel title="Airspace" detail="Search or select a marker. The selected entity opens in the inspector." tone="trust"><div className="relative overflow-hidden bg-[#090c10]"><div className="absolute left-3 right-14 top-3 z-dropdown flex items-start gap-2"><div className="relative min-w-0 flex-1 sm:max-w-[380px]"><SearchField value={search} onValueChange={setSearch} placeholder="Search aircraft or receivers" label="Search the map" elevated />{search.trim() ? <div className="absolute left-0 right-0 top-11 overflow-hidden rounded-md border border-line bg-[#11151a] shadow-overlay">{searchResults.length ? searchResults.map((item) => <button key={`${item.type}-${item.id}`} type="button" onClick={() => { item.type === 'aircraft' ? selectAircraft(item.id) : selectReceiver(item.id); setSearch(''); }} className="flex min-h-11 w-full items-center gap-3 border-b border-line px-3 py-2.5 text-left text-xs text-ink-secondary last:border-0 hover:bg-graphite-hover hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">{item.type === 'aircraft' ? <Plane className="size-3.5 text-signal-blue" /> : <MapPin className="size-3.5 text-series-teal" />}<span className="min-w-0 flex-1 truncate font-semibold">{item.label}</span><span className="text-ink-quiet">{item.detail}</span></button>) : <div className="px-3 py-4 text-xs text-ink-quiet">No map entities match this search.</div>}</div> : null}</div><DropdownMenu.Root><DropdownMenu.Trigger asChild><Button size="icon" className="bg-graphite/95 shadow-map" aria-label="Map filters"><Filter className="size-4" /></Button></DropdownMenu.Trigger><DropdownMenu.Portal><DropdownMenu.Content align="end" sideOffset={6} className="z-dropdown min-w-52 rounded-md border border-line bg-[#11151a] p-1 shadow-overlay"><DropdownMenu.Label className="px-2 py-1.5 text-xs font-semibold text-ink-quiet">Map layers</DropdownMenu.Label><DropdownMenu.CheckboxItem checked={showReceiverLinks} onCheckedChange={toggleReceiverLinks} className="flex min-h-10 cursor-default items-center gap-2 rounded px-2 py-2 text-xs text-ink-secondary outline-none data-[highlighted]:bg-graphite-hover data-[highlighted]:text-ink"><span className={cn('size-3 rounded-sm border border-line', showReceiverLinks && 'border-signal-blue bg-signal-blue')} /><Link2 className="size-3.5" />Receiver links</DropdownMenu.CheckboxItem><DropdownMenu.CheckboxItem checked={showUncertainty} onCheckedChange={toggleUncertainty} className="flex min-h-10 cursor-default items-center gap-2 rounded px-2 py-2 text-xs text-ink-secondary outline-none data-[highlighted]:bg-graphite-hover data-[highlighted]:text-ink"><span className={cn('size-3 rounded-sm border border-line', showUncertainty && 'border-signal-blue bg-signal-blue')} /><Target className="size-3.5" />Uncertainty</DropdownMenu.CheckboxItem></DropdownMenu.Content></DropdownMenu.Portal></DropdownMenu.Root><Tooltip label="Fit selected entity" side="bottom"><Button size="icon" className="bg-graphite/95 shadow-map" onClick={() => setFitRequest((value) => value + 1)} aria-label="Fit selected map entity"><Crosshair className="size-4" /></Button></Tooltip></div><LazyAirspaceMap aircraft={aircraft} receivers={receivers} selectedAircraftId={selectedAircraft?.aircraft_id} selectedReceiverId={selectedReceiverModel?.key} onSelectAircraft={selectAircraft} onSelectReceiver={selectReceiver} showReceiverLinks={showReceiverLinks} showUncertainty={showUncertainty} fitRequest={fitRequest} className="map-live" /><div className="absolute bottom-3 left-3 z-dropdown flex items-center gap-3 rounded-md bg-graphite/95 px-3 py-2 text-[11px] text-ink-secondary shadow-map"><span className="flex items-center gap-1.5"><Plane className="size-3 text-signal-blue" />{aircraft.length}</span><span className="flex items-center gap-1.5"><Radio className="size-3 text-series-teal" />{receivers.length}</span><span className="hidden sm:inline">Signal {healthQuery.data?.freshness?.last_signal_age_s == null ? 'unavailable' : `${Math.round(healthQuery.data.freshness.last_signal_age_s)}s ago`}</span></div></div></WorkspacePanel>}
        secondary={<div className="space-y-4">{focusReceiverModel ? <ReceiverInspector receiver={focusReceiverModel} actions={<><Link href={`/app/receivers?receiver=${encodeURIComponent(focusReceiverModel.key)}`} className={buttonVariants({ variant: 'primary', size: 'sm' })}>Open receiver details</Link>{focusReceiverModel.identity ? <Link href={`/app/registry?receiver=${encodeURIComponent(focusReceiverModel.identity)}`} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>Registry lifecycle</Link> : null}</>} /> : <Inspector title={focusAircraft?.aircraft_id || 'Select a map entity'} subtitle={focusAircraft ? <span>Aircraft updated <RelativeTime timestamp={focusAircraft.timestamp} fallback="recently" /></span> : 'Use a marker or search result'} status={focusAircraft ? <StatusChip label={percent(focusAircraft.quality?.score, 0)} tone={toneFromScore(focusAircraft.quality?.score)} /> : <StatusChip label="Waiting" />}>
          {focusAircraft ? <><div className="border-b border-line p-4"><ConfidenceGauge value={Number(focusAircraft.quality?.score ?? 0)} /></div><FactGrid items={[{ label: 'Position', value: formatCoordinate(focusAircraft.position?.latitude ?? focusAircraft.latitude, focusAircraft.position?.longitude ?? focusAircraft.longitude) }, { label: 'Altitude', value: formatAltitude(focusAircraft.position?.altitude ?? focusAircraft.altitude) }, { label: 'Uncertainty', value: formatDistanceMeters(focusAircraft.quality?.uncertainty_m ?? focusAircraft.uncertainty) }, { label: 'Receivers', value: number(focusAircraft.correlation?.receiver_count ?? focusAircraft.num_receivers) }]} /><div className="border-b border-line p-4"><p className="mb-2 text-xs font-semibold text-ink">Contributing receivers</p><div className="space-y-1">{contributingReceivers.length ? contributingReceivers.map((receiver) => <button key={receiver.key} type="button" onClick={() => selectReceiver(receiver.key)} className="flex min-h-10 w-full items-center gap-2 rounded-md px-2 text-left text-xs text-ink-secondary hover:bg-graphite-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue"><span className="size-1.5 rounded-full bg-series-teal" /><span className="min-w-0 flex-1 truncate">{receiver.label}</span><RelativeTime timestamp={receiver.lastObservationAt} /></button>) : <p className="py-3 text-xs leading-5 text-ink-quiet">No receiver contributions are attached to this localization. Refresh the map or inspect Pipeline diagnostics to understand why.</p>}</div></div></> : <div className="p-6 text-center text-xs leading-5 text-ink-quiet">Aircraft and receiver details appear here immediately after selection.</div>}
        </Inspector>}<WorkspacePanel title="Map status" detail="Current source, transport, and layer state."><ActivityRail items={activityRail} /><div className="border-t border-line p-4"><div className="flex items-center gap-2 text-xs text-ink-secondary">{streamConnected ? <Wifi className="size-3.5 text-healthy" /> : <WifiOff className="size-3.5 text-ink-quiet" />}<span>{streamConnected ? 'Position stream connected' : 'Using interval refresh'}</span></div></div></WorkspacePanel></div>}
      />
    </div>
  );
}
