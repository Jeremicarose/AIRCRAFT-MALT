'use client';

import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import { Link2, Map, RadioTower, ShieldCheck, Waves } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { ActivityRail, FactGrid, Inspector, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { buttonVariants } from '@/components/ui/button';
import { DataGrid } from '@/components/ui/data-grid';
import { SearchField } from '@/components/ui/search-field';
import { StatusChip } from '@/components/ui/status-chip';
import { formatCoordinate, formatDateTime, latestPositions, number, relativeTime, toneFromFreshness, truncateMiddle } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { ModeData, Position, Receiver, ReceiversResponse, StatusTone } from '@/lib/types';

const columnHelper = createColumnHelper<Receiver>();

function receiverTone(receiver: Receiver): StatusTone {
  if (String(receiver.status).toLowerCase() !== 'online') return 'failure';
  return toneFromFreshness(receiver.last_seen == null ? null : Math.max(0, Date.now() / 1000 - receiver.last_seen), 90, 300);
}

export function ReceiversPage({ receiverData, aircraftData, selectedReceiverId, modeData }: { receiverData: ReceiversResponse | null; aircraftData: Position[]; selectedReceiverId?: string | null; modeData: ModeData | null }) {
  const receivers = receiverData?.receivers ?? [];
  const [selectedId, setSelectedId] = useState(selectedReceiverId ?? receivers[0]?.receiver_id ?? null);
  const [search, setSearch] = useState('');
  const setStoreSelectedReceiverId = useOperatorStore((state) => state.setSelectedReceiverId);
  const setDock = useOperatorStore((state) => state.setDock);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);

  const filtered = useMemo(() => receivers.filter((receiver) => `${receiver.receiver_id} ${receiver.receiver_label ?? ''} ${receiver.identity_id ?? ''} ${(receiver.capabilities ?? []).join(' ')}`.toLowerCase().includes(search.trim().toLowerCase())), [receivers, search]);
  const selected = filtered.find((receiver) => receiver.receiver_id === selectedId) ?? receivers.find((receiver) => receiver.receiver_id === selectedId) ?? filtered[0] ?? null;
  const relatedAircraft = selected ? aircraftData.filter((position) => position.correlation?.receiver_ids?.includes(selected.receiver_id)) : [];
  const airPicture = latestPositions(relatedAircraft);
  const onlineCount = receivers.filter((receiver) => receiverTone(receiver) === 'healthy').length;
  const trustedCount = receivers.filter((receiver) => receiver.registry?.metadata_hash || receiver.identity_id).length;

  const columns = useMemo<ColumnDef<Receiver, any>[]>(() => [
    columnHelper.accessor('receiver_id', { header: 'Receiver', size: 180, cell: (info) => <span className="font-mono font-semibold text-ink">{info.getValue()}</span> }),
    columnHelper.display({ id: 'status', header: 'Status', size: 120, cell: ({ row }) => { const tone = receiverTone(row.original); return <StatusChip label={tone === 'healthy' ? 'Online' : tone === 'attention' ? 'Stale' : 'Offline'} tone={tone} />; } }),
    columnHelper.display({ id: 'trust', header: 'Trust', size: 110, cell: ({ row }) => <StatusChip label={row.original.registry?.metadata_hash || row.original.identity_id ? 'Verified' : 'Pending'} tone={row.original.registry?.metadata_hash || row.original.identity_id ? 'trust' : 'attention'} /> }),
    columnHelper.display({ id: 'coverage', header: 'Coverage', size: 100, cell: ({ row }) => number(latestPositions(aircraftData.filter((position) => position.correlation?.receiver_ids?.includes(row.original.receiver_id))).length) }),
    columnHelper.display({ id: 'updated', header: 'Last seen', size: 110, cell: ({ row }) => row.original.last_seen ? relativeTime(row.original.last_seen) : 'n/a' }),
  ], [aircraftData]);

  useEffect(() => {
    if (!selected?.receiver_id) return;
    setStoreSelectedReceiverId(selected.receiver_id);
    setInvestigationContext({ focus: selected.receiver_id, query: search, timeRange: 'fleet' });
    setDock({
      entityType: 'receiver',
      title: selected.receiver_id,
      subtitle: 'Pinned from the receiver fleet workspace.',
      statusLabel: String(selected.status || 'Unknown'),
      statusTone: receiverTone(selected),
      facts: [
        { label: 'Coordinates', value: formatCoordinate(selected.latitude, selected.longitude) },
        { label: 'Identity', value: selected.identity_id ?? 'Pending', mono: true, tone: selected.identity_id ? 'trust' : 'attention' },
        { label: 'Metadata hash', value: truncateMiddle(selected.registry?.metadata_hash, 10, 8), mono: true, tone: selected.registry?.metadata_hash ? 'trust' : 'attention' },
        { label: 'Coverage', value: `${number(airPicture.length)} aircraft` },
      ],
      timeline: [
        { title: 'Availability', detail: receiverTone(selected) === 'healthy' ? 'Receiver heartbeat is current.' : 'Receiver heartbeat is stale or absent.', tone: receiverTone(selected) },
        { title: 'Registry trust', detail: selected.registry?.metadata_hash ? 'Receiver metadata is anchored in Registry V2.' : 'Registry metadata is not yet attached.', tone: selected.registry?.metadata_hash ? 'trust' : 'attention' },
        { title: 'Capabilities', detail: selected.capabilities?.length ? selected.capabilities.join(', ') : 'No capability metadata published.', tone: selected.capabilities?.length ? 'selection' : 'attention' },
      ],
      evidence: [
        { title: 'Owner lock args', detail: selected.registry?.owner_lock_args ?? 'Unavailable', state: 'Registry', tone: selected.registry?.owner_lock_args ? 'trust' : 'attention' },
      ],
      actions: [
        { label: 'Open live map', href: '/app/localization', tone: 'primary' },
        { label: 'Open environment', href: '/app/environment', tone: 'secondary' },
      ],
    });
    return () => setDock(null);
  }, [airPicture.length, search, selected, setDock, setInvestigationContext, setStoreSelectedReceiverId]);

  const activityRail = [
    { title: 'Online fleet', detail: `${onlineCount} receivers currently report healthy heartbeats.`, meta: `${receivers.length} total`, tone: onlineCount >= 4 ? 'healthy' : 'attention' as StatusTone },
    { title: 'Trust posture', detail: `${trustedCount} receivers expose registry or identity metadata.`, meta: `${receivers.length - trustedCount} pending`, tone: trustedCount ? 'trust' : 'attention' as StatusTone },
    { title: 'Search scope', detail: search ? `Filtering fleet by “${search}”.` : 'Showing the complete fleet inventory.', meta: search ? 'Filtered' : 'All', tone: search ? 'selection' : 'neutral' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      <WorkspaceHeader eyebrow="Investigate" title="Fleet health and trust operations" description="Receivers are organized as an operational workspace for availability, trust, and geographic contribution instead of a passive inventory list." status={<StatusChip label={`${onlineCount}/${receivers.length} healthy`} tone={onlineCount >= 4 ? 'healthy' : 'attention'} />} actions={<Link href="/app/localization" className={buttonVariants({ variant: 'secondary' })}><Map className="size-4" />Open live map</Link>} rail={<SignalMarquee items={[{ label: 'Healthy', value: `${onlineCount}/${receivers.length}`, tone: onlineCount >= 4 ? 'healthy' : 'attention' }, { label: 'Trusted', value: number(trustedCount), tone: trustedCount ? 'trust' : 'attention' }, { label: 'Coverage', value: number(airPicture.length), tone: airPicture.length ? 'selection' : 'neutral' }, { label: 'Mode', value: modeData?.synthetic_feed_mode ? 'Replay' : 'Live', tone: modeData?.synthetic_feed_mode ? 'replay' : 'healthy' }]} />} />

      <WorkspaceSplit
        secondaryWidth="340px"
        primary={<div className="space-y-4"><WorkspacePanel title="Receiver fleet" detail={`${filtered.length} receivers in the current view`} tone="selection" action={<SearchField value={search} onValueChange={setSearch} placeholder="Search receiver, label, or identity" label="Search receivers" rootClassName="w-[240px]" />}><DataGrid data={filtered} columns={columns} getRowId={(row) => row.receiver_id} onRowClick={(row) => setSelectedId(row.receiver_id)} isRowSelected={(row) => row.receiver_id === selectedId} keyboardColumnLabel={(row) => row.receiver_id} emptyLabel="No receivers match this view." ariaLabel="Receiver fleet" height={Math.min(420, Math.max(184, filtered.length * 46))} /></WorkspacePanel><WorkspacePanel title="Coverage and supporting traffic" detail="Aircraft recently associated with the selected receiver." tone="trust"><LazyAirspaceMap aircraft={airPicture} receivers={receivers} selectedReceiverId={selected?.receiver_id} onSelectReceiver={setSelectedId} showReceiverLinks={false} showUncertainty={false} coveragePositions={relatedAircraft} className="map-coverage" /></WorkspacePanel><WorkspacePanel title="Receiver posture timeline" detail="Current availability and trust state across the visible fleet." tone="selection"><Timeline items={filtered.slice(0, 8).map((receiver) => ({ title: receiver.receiver_id, detail: `${receiver.status || 'Unknown'} · ${receiver.identity_id ? 'Identity published' : 'Identity pending'}`, tone: receiver.registry?.metadata_hash ? 'trust' : receiverTone(receiver), meta: receiver.last_seen ? relativeTime(receiver.last_seen) : 'n/a' }))} /></WorkspacePanel></div>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Fleet signals" detail="Operational summary for the current view." tone={onlineCount >= 4 ? 'healthy' : 'attention'}><ActivityRail items={activityRail} /></WorkspacePanel><Inspector title={selected?.receiver_id ?? 'No receiver selected'} subtitle={selected ? formatDateTime(selected.last_seen ?? selected.updated_at) : 'Select a receiver to inspect'} status={selected ? <StatusChip label={selected.registry?.metadata_hash ? 'Trusted' : 'Pending trust'} tone={selected.registry?.metadata_hash ? 'trust' : 'attention'} /> : <StatusChip label="Waiting" />} className="self-start xl:sticky xl:top-20">{selected ? <><FactGrid items={[{ label: 'Coordinates', value: formatCoordinate(selected.latitude, selected.longitude) }, { label: 'Identity', value: selected.identity_id ?? 'Pending', mono: true }, { label: 'Registry seq', value: number(selected.registry?.sequence) }, { label: 'Coverage', value: `${number(airPicture.length)} aircraft` }]} /><div className="border-b border-line p-4"><div className="mb-3 flex items-center gap-2"><ShieldCheck className="size-4 text-trust-cyan" /><p className="text-xs font-semibold text-ink">Registry evidence</p></div><div className="space-y-2 text-xs leading-5 text-ink-quiet"><p>{selected.registry?.metadata_hash ? 'Metadata hash is attached to this receiver record.' : 'Metadata hash has not been published for this receiver.'}</p><p className="font-mono text-[11px] text-ink-secondary">{selected.registry?.metadata_hash ?? 'metadata-hash-unavailable'}</p></div></div><div className="p-4"><div className="grid grid-cols-3 gap-2 text-center text-xs"><div className="rounded-md border border-line bg-graphite-raised/45 px-2 py-3"><Waves className="mx-auto size-3.5 text-healthy" /><strong className="mt-1 block text-ink">{String(selected.status || 'n/a')}</strong><span className="text-[10px] text-ink-quiet">status</span></div><div className="rounded-md border border-line bg-graphite-raised/45 px-2 py-3"><Link2 className="mx-auto size-3.5 text-signal-blue" /><strong className="mt-1 block text-ink">{number(selected.capabilities?.length)}</strong><span className="text-[10px] text-ink-quiet">caps</span></div><div className="rounded-md border border-line bg-graphite-raised/45 px-2 py-3"><RadioTower className="mx-auto size-3.5 text-series-teal" /><strong className="mt-1 block text-ink">{number(airPicture.length)}</strong><span className="text-[10px] text-ink-quiet">aircraft</span></div></div></div></> : <div className="p-6 text-center text-xs text-ink-quiet">Select a receiver to inspect trust and availability evidence.</div>}</Inspector></div>}
      />
    </div>
  );
}
