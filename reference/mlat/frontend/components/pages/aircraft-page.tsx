'use client';

import { useQuery } from '@tanstack/react-query';
import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import { ArrowUpRight, Clock3, Map as MapIcon, RadioTower, Target, Waypoints } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { TrendChart } from '@/components/lazy-charts';
import { ActivityRail, ConfidenceGauge, FactGrid, Inspector, SignalMarquee, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { buttonVariants } from '@/components/ui/button';
import { DataGrid } from '@/components/ui/data-grid';
import { DataNotice } from '@/components/ui/data-notice';
import { RelativeTime } from '@/components/ui/relative-time';
import { SearchField } from '@/components/ui/search-field';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { StatusChip } from '@/components/ui/status-chip';
import { fetchJson, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import { ageSeconds, formatAltitude, formatCoordinate, formatDateTime, formatDistanceMeters, latestPositions, number, percent, toneFromScore } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import { mlatStatusPresentation, receiverDockState, reconcileReceivers, registryStatusPresentation, RECEIVER_IDENTITY_PATTERN } from '@/lib/receiver-state';
import type { ModeData, Position, PositionsResponse, ReceiversResponse, StatusTone } from '@/lib/types';

const columnHelper = createColumnHelper<Position>();
type AircraftFilter = 'all' | 'healthy' | 'attention';
const aircraftFilterOptions: ReadonlyArray<{ value: AircraftFilter; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'healthy', label: 'Healthy' },
  { value: 'attention', label: 'Attention' },
];

export function AircraftPage({ positionsData, positionsError, selectedAircraftId, initialLatest, initialTrack, modeData, receiverData }: { positionsData: PositionsResponse; positionsError: string | null; selectedAircraftId?: string | null; initialLatest: Position | null; initialTrack: PositionsResponse; modeData: ModeData | null; receiverData: ReceiversResponse | null }) {
  const positionsQuery = useQuery({ queryKey: ['positions', 'aircraft'], queryFn: () => fetchJson<PositionsResponse>(PUBLIC_POSITIONS_PATH), initialData: positionsData, refetchInterval: 10_000 });
  const receiversQuery = useQuery({ queryKey: ['receivers'], queryFn: () => fetchJson<ReceiversResponse>('/api/receivers'), initialData: receiverData ?? { receivers: [] }, refetchInterval: 15_000 });
  const rows = useMemo(() => latestPositions(positionsQuery.data.positions ?? []), [positionsQuery.data.positions]);
  const [selectedId, setSelectedId] = useState(selectedAircraftId ?? rows[0]?.aircraft_id ?? null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<AircraftFilter>('all');
  const [inspectedReceiverKey, setInspectedReceiverKey] = useState<string | null>(null);
  const setStoreSelectedAircraftId = useOperatorStore((state) => state.setSelectedAircraftId);
  const setStoreSelectedReceiverId = useOperatorStore((state) => state.setSelectedReceiverId);
  const setRightDockOpen = useOperatorStore((state) => state.setRightDockOpen);
  const setDock = useOperatorStore((state) => state.setDock);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const filteredRows = useMemo(() => rows.filter((row) => {
    const matchesSearch = row.aircraft_id.toLowerCase().includes(search.trim().toLowerCase());
    const healthy = Number(row.quality?.score) >= 0.8 && Number(row.correlation?.receiver_count ?? row.num_receivers) >= 4 && Number(ageSeconds(row.timestamp)) < 90;
    return matchesSearch && (filter === 'all' || (filter === 'healthy' ? healthy : !healthy));
  }), [filter, rows, search]);

  const latestQuery = useQuery({ queryKey: ['aircraft', selectedId, 'latest'], queryFn: () => fetchJson<Position>(`/api/aircraft/${encodeURIComponent(selectedId!)}/latest`), enabled: Boolean(selectedId), initialData: selectedId === initialLatest?.aircraft_id ? initialLatest : undefined, refetchInterval: 10_000 });
  const trackQuery = useQuery({ queryKey: ['aircraft', selectedId, 'track'], queryFn: () => fetchJson<PositionsResponse>(`/api/aircraft/${encodeURIComponent(selectedId!)}/track?limit=120`), enabled: Boolean(selectedId), initialData: selectedId === initialLatest?.aircraft_id ? initialTrack : undefined, refetchInterval: 15_000 });
  const selected = latestQuery.data ?? rows.find((row) => row.aircraft_id === selectedId) ?? null;
  const track = trackQuery.data?.positions ?? [];
  const receivers = receiversQuery.data?.receivers ?? [];

  const columns = useMemo<ColumnDef<Position, any>[]>(() => [
    columnHelper.accessor('aircraft_id', { header: 'Aircraft', size: 120, cell: (info) => <span className="font-mono font-semibold text-ink">{info.getValue()}</span> }),
    columnHelper.display({ id: 'status', header: 'Status', size: 135, cell: ({ row }) => { const age = ageSeconds(row.original.timestamp); const count = Number(row.original.correlation?.receiver_count ?? row.original.num_receivers); const tone: StatusTone = age != null && age > 90 ? 'failure' : count < 4 ? 'attention' : toneFromScore(row.original.quality?.score); return <StatusChip label={tone === 'healthy' ? 'Tracking' : tone === 'failure' ? 'Lost' : 'Degraded'} tone={tone} />; } }),
    columnHelper.display({ id: 'quality', header: 'Confidence', size: 100, cell: ({ row }) => <span className="tabular-nums">{percent(row.original.quality?.score, 0)}</span> }),
    columnHelper.display({ id: 'receivers', header: 'Receivers', size: 90, cell: ({ row }) => number(row.original.correlation?.receiver_count ?? row.original.num_receivers) }),
    columnHelper.accessor('timestamp', { header: 'Updated', size: 110, cell: (info) => <RelativeTime timestamp={info.getValue()} /> }),
  ], []);

  const chartRows = [...track].reverse().map((point, index) => {
    const timestamp = Number(point.timestamp ?? 0);
    return { label: timestamp ? new Date(timestamp * 1000).toISOString().slice(11, 19) : String(index + 1), confidence: Math.round(Number(point.quality?.score ?? 0) * 100), altitude: Number(point.position?.altitude ?? point.altitude ?? 0) };
  });
  const receiverContribution = new Map<string, number>();
  track.forEach((point) => point.correlation?.receiver_ids?.forEach((id) => receiverContribution.set(id, (receiverContribution.get(id) ?? 0) + 1)));
  const receiverModels = useMemo(() => reconcileReceivers({ runtimeReceivers: receivers, positions: track, runtimeInventoryAvailable: !receiversQuery.isError }), [receivers, receiversQuery.isError, track]);
  const inspectedReceiver = receiverModels.find((receiver) => receiver.key === inspectedReceiverKey) ?? null;

  const inspectReceiver = (receiverKey: string) => {
    setInspectedReceiverKey(receiverKey);
    setStoreSelectedReceiverId(receiverKey);
    const receiver = receiverModels.find((item) => item.key === receiverKey);
    if (receiver && selected?.aircraft_id) {
      setDock(receiverDockState(receiver, {
        returnAircraftId: selected.aircraft_id,
        includeRegistryAction: true,
      }));
    }
    setRightDockOpen(true);
  };

  useEffect(() => {
    if (!selected?.aircraft_id) return;
    setStoreSelectedAircraftId(selected.aircraft_id);
    setInvestigationContext({ focus: selected.aircraft_id, query: search, timeRange: 'track' });
    if (inspectedReceiver) {
      setDock(receiverDockState(inspectedReceiver, { returnAircraftId: selected.aircraft_id, includeRegistryAction: true }));
      return () => setDock(null);
    }
    setDock({
      entityType: 'aircraft',
      title: selected.aircraft_id,
      subtitle: 'Pinned from the aircraft investigation workspace.',
      statusLabel: percent(selected.quality?.score, 0),
      statusTone: toneFromScore(selected.quality?.score),
      facts: [
        { label: 'Position', value: formatCoordinate(selected.position?.latitude ?? selected.latitude, selected.position?.longitude ?? selected.longitude) },
        { label: 'Altitude', value: formatAltitude(selected.position?.altitude ?? selected.altitude) },
        { label: 'Residual', value: formatDistanceMeters(selected.solver?.residual_m) },
        { label: 'Receivers', value: number(selected.correlation?.receiver_count ?? selected.num_receivers) },
      ],
      timeline: [
        { title: 'Latest solve', detail: formatDateTime(selected.timestamp), tone: 'healthy' },
        { title: 'Track history', detail: `${track.length} positions are loaded into the current investigation window.`, tone: track.length ? 'selection' : 'attention' },
        { title: 'Receiver geometry', detail: `${receiverContribution.size} receivers contributed across the loaded track.`, tone: receiverContribution.size ? 'healthy' : 'attention' },
      ],
      evidence: [
        { title: 'Solve confidence', detail: `${percent(selected.quality?.score, 0)} with ${formatDistanceMeters(selected.quality?.uncertainty_m ?? selected.uncertainty)} uncertainty.`, state: 'Current', tone: toneFromScore(selected.quality?.score) },
      ],
      actions: [
        { label: 'Open live map', href: `/app/localization?aircraft=${encodeURIComponent(selected.aircraft_id)}`, tone: 'primary' },
        { label: 'Inspect receivers', href: '/app/receivers', tone: 'secondary' },
      ],
    });
    return () => setDock(null);
  }, [inspectedReceiver, receiverContribution.size, search, selected, setDock, setInvestigationContext, setStoreSelectedAircraftId, track.length]);

  const activityRail = [
    { title: 'Track packets', detail: `${track.length} normalized solver outputs are currently available for this aircraft.`, meta: track.length ? 'Loaded' : 'Empty', tone: track.length ? 'healthy' : 'attention' as StatusTone },
    { title: 'Receiver contribution', detail: `${receiverContribution.size} receivers contributed to the loaded timeline.`, meta: `${[...receiverContribution.values()].reduce((sum, value) => sum + value, 0)} solves`, tone: receiverContribution.size ? 'selection' : 'attention' as StatusTone },
    { title: 'Source mode', detail: modeData?.synthetic_feed_mode ? 'Replay or synthetic source is active for this aircraft view.' : 'Operational live source is active for this aircraft view.', meta: modeData?.synthetic_feed_mode ? 'Replay' : 'Live', tone: modeData?.synthetic_feed_mode ? 'replay' : 'healthy' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      {(positionsQuery.error instanceof Error || (positionsError && !positionsQuery.isFetchedAfterMount)) ? <DataNotice title="Aircraft positions are unavailable" detail={positionsQuery.error instanceof Error ? positionsQuery.error.message : positionsError ?? 'The latest position request failed.'} onRetry={() => void positionsQuery.refetch()} /> : null}
      <WorkspaceHeader
        eyebrow="Investigate"
        title="Aircraft investigation workspace"
        description="Trajectory, confidence history, receiver participation, and packet evidence are organized around a single selected aircraft instead of a passive inventory browse."
        status={selected ? <StatusChip label={percent(selected.quality?.score, 0)} tone={toneFromScore(selected.quality?.score)} /> : <StatusChip label="Waiting" />}
        actions={selected ? <Link href={`/app/localization?aircraft=${encodeURIComponent(selected.aircraft_id)}`} className={buttonVariants({ variant: 'secondary' })}><MapIcon className="size-4" />Open live map</Link> : null}
        rail={<SignalMarquee items={[{ label: 'Track points', value: number(track.length), tone: track.length ? 'healthy' : 'attention' }, { label: 'Receivers', value: number(receiverContribution.size), tone: receiverContribution.size >= 4 ? 'healthy' : 'attention' }, { label: 'Filter', value: filter === 'all' ? 'All aircraft' : filter === 'healthy' ? 'Healthy only' : 'Attention only', tone: filter === 'all' ? 'neutral' : 'selection' }, { label: 'Source', value: modeData?.synthetic_feed_mode ? 'Replay' : 'Live', tone: modeData?.synthetic_feed_mode ? 'replay' : 'healthy' }]} />}
      />

      <WorkspaceSplit
        secondaryWidth="340px"
        primary={<div className="min-w-0 space-y-4"><WorkspacePanel title="Trajectory workspace" detail={selected ? `${selected.aircraft_id} position evolution and receiver geometry` : 'Select an aircraft'} action={<Waypoints className="size-4 text-signal-blue" />} tone="trust"><LazyAirspaceMap aircraft={selected ? [selected] : []} receivers={receivers} selectedAircraftId={selected?.aircraft_id} selectedReceiverId={inspectedReceiverKey} onSelectReceiver={inspectReceiver} showReceiverLinks track={track} className="map-trajectory" /></WorkspacePanel><div className="grid gap-4 lg:grid-cols-2"><WorkspacePanel title="Altitude profile" detail="Track altitude over time" tone="healthy"><div className="p-3">{chartRows.length ? <TrendChart data={chartRows} dataKey="altitude" color="#4bb6a3" unit=" m" height={190} ariaLabel="Aircraft altitude over the loaded track" /> : <div className="grid h-[190px] place-items-center text-xs text-ink-quiet">No altitude history.</div>}</div></WorkspacePanel><WorkspacePanel title="Confidence profile" detail="Solve quality over time" tone="selection"><div className="p-3">{chartRows.length ? <TrendChart data={chartRows} dataKey="confidence" unit="%" height={190} /> : <div className="grid h-[190px] place-items-center text-xs text-ink-quiet">No confidence history.</div>}</div></WorkspacePanel></div><WorkspacePanel title="Aircraft queue" detail={`${filteredRows.length} aircraft in the current solve window`} tone="selection" action={<div className="flex flex-wrap gap-2"><SearchField value={search} onValueChange={setSearch} placeholder="Search ICAO identifier" label="Search aircraft" rootClassName="w-[220px]" /><SegmentedControl label="Aircraft status filter" value={filter} options={aircraftFilterOptions} onValueChange={setFilter} /></div>}><DataGrid data={filteredRows} columns={columns} getRowId={(row) => row.aircraft_id} onRowClick={(row) => { setInspectedReceiverKey(null); setSelectedId(row.aircraft_id); }} isRowSelected={(row) => row.aircraft_id === selectedId} keyboardColumnLabel={(row) => row.aircraft_id} emptyLabel="No aircraft match this view." ariaLabel="Aircraft inventory" height={Math.min(368, Math.max(184, filteredRows.length * 46))} /></WorkspacePanel><WorkspacePanel title="Position packets" detail="Normalized solver outputs; raw Mode-S payloads are not exposed by this API." tone="attention"><div className="divide-y divide-line">{track.slice(0, 8).map((point, index) => <div key={`${point.timestamp}-${index}`} className="grid grid-cols-[72px_minmax(0,1.4fr)_minmax(0,0.8fr)_minmax(0,0.8fr)] gap-3 px-4 py-3 text-[11px]"><span className="font-mono text-ink-quiet">{point.timestamp ? new Date(point.timestamp * 1000).toISOString().slice(11, 19) : 'n/a'}</span><span className="truncate text-ink-secondary">{formatCoordinate(point.position?.latitude ?? point.latitude, point.position?.longitude ?? point.longitude)}</span><span className="truncate text-ink-quiet">{formatAltitude(point.position?.altitude ?? point.altitude)}</span><span className="truncate text-ink-quiet">{formatDistanceMeters(point.solver?.residual_m)}</span></div>)}{!track.length ? <div className="grid h-32 place-items-center text-xs text-ink-quiet">No position packets are available.</div> : null}</div></WorkspacePanel></div>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Investigation rail" detail="Current timeline, source mode, and contribution posture." tone="selection"><ActivityRail items={activityRail} /></WorkspacePanel><Inspector title={selected?.aircraft_id ?? 'No aircraft selected'} subtitle={selected ? formatDateTime(selected.timestamp) : 'Select an aircraft to investigate'} status={selected ? <StatusChip label={percent(selected.quality?.score, 0)} tone={toneFromScore(selected.quality?.score)} /> : <StatusChip label="Waiting" />} className="self-start xl:sticky xl:top-20">{selected ? <><div className="border-b border-line p-4"><ConfidenceGauge value={Number(selected.quality?.score ?? 0)} /></div><FactGrid items={[{ label: 'Position', value: formatCoordinate(selected.position?.latitude ?? selected.latitude, selected.position?.longitude ?? selected.longitude) }, { label: 'Altitude', value: formatAltitude(selected.position?.altitude ?? selected.altitude) }, { label: 'Uncertainty', value: formatDistanceMeters(selected.quality?.uncertainty_m ?? selected.uncertainty) }, { label: 'Residual', value: formatDistanceMeters(selected.solver?.residual_m) }]} /><div className="border-b border-line"><div className="flex items-center justify-between px-4 py-3"><div><p className="text-xs font-semibold text-ink">Contributing receivers</p><p className="mt-0.5 text-[11px] text-ink-quiet">Open a receiver to trace its Registry identity</p></div><RadioTower className="size-3.5 text-ink-quiet" /></div><div className="divide-y divide-line">{[...receiverContribution.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([id, count]) => { const receiver = receiverModels.find((item) => item.key === id); const registryState = receiver ? registryStatusPresentation(receiver.registryStatus) : null; const mlatState = receiver ? mlatStatusPresentation(receiver.mlatStatus) : null; const content = <><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-ink">{receiver?.label ?? id}</p><p className="mt-0.5 truncate font-mono text-[10px] text-ink-quiet">{RECEIVER_IDENTITY_PATTERN.test(id) ? id : 'No canonical Registry identity'}</p></div><div className="hidden flex-col items-end gap-1 sm:flex">{registryState ? <StatusChip {...registryState} /> : null}{mlatState ? <StatusChip {...mlatState} /> : <span className="text-[10px] text-ink-quiet">{count} solves</span>}</div><ArrowUpRight className="size-3.5 shrink-0 text-ink-quiet" /></>; return receiver ? <button key={id} type="button" aria-label={`Inspect receiver ${receiver.label}`} aria-describedby={`receiver-contribution-status-${id}`} onClick={() => inspectReceiver(id)} className="flex min-h-14 w-full items-center gap-3 px-4 py-2 text-left outline-none hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">{content}<span id={`receiver-contribution-status-${id}`} className="sr-only">Registry: {registryState?.label ?? 'Status unavailable'}. MLAT: {mlatState?.label ?? 'Status unavailable'}. {count} contributing solves.</span></button> : RECEIVER_IDENTITY_PATTERN.test(id) ? <Link key={id} href={`/app/registry?receiver=${encodeURIComponent(id)}`} className="flex min-h-14 items-center gap-3 px-4 py-2 outline-none hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">{content}</Link> : <div key={id} className="flex min-h-14 items-center gap-3 px-4 py-2">{content}</div>; })}{!receiverContribution.size ? <p className="px-4 py-5 text-xs text-ink-quiet">No receiver contribution IDs are available for this track.</p> : null}</div></div><div className="border-b border-line p-4"><p className="text-xs font-semibold text-ink">Evidence chain</p><div className="mt-3 grid grid-cols-3 gap-2 text-center"><div><Clock3 className="mx-auto size-3.5 text-ink-quiet" /><strong className="mt-1 block text-xs text-ink">{track.length}</strong><span className="text-[10px] text-ink-quiet">positions</span></div><div><Target className="mx-auto size-3.5 text-ink-quiet" /><strong className="mt-1 block text-xs text-ink">{number(selected.solver?.iterations)}</strong><span className="text-[10px] text-ink-quiet">iterations</span></div><div><RadioTower className="mx-auto size-3.5 text-ink-quiet" /><strong className="mt-1 block text-xs text-ink">{number(selected.correlation?.receiver_count ?? selected.num_receivers)}</strong><span className="text-[10px] text-ink-quiet">receivers</span></div></div></div><div className="p-4"><StatusChip label={modeData?.synthetic_feed_mode ? 'Replay source' : 'Operational source'} tone={modeData?.synthetic_feed_mode ? 'replay' : 'healthy'} /></div></> : <div className="p-6 text-center text-xs text-ink-quiet">No aircraft is available in the current window.</div>}</Inspector></div>}
      />
    </div>
  );
}
