'use client';

import { type DiscoveredReceiver, type RegistryHistoryEvent } from '@aircraft-malt/registry-v2';
import { ccc } from '@ckb-ccc/connector-react';
import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowUpRight, Download, RadioTower, RefreshCw, UserRound } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ReceiverInspector } from '@/components/receiver-inspector';
import { RegistryContractVerification } from '@/components/registry-contract-verification';
import { SectionErrorBoundary } from '@/components/section-error-boundary';
import { SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { RegistryActionPanel } from '@/components/registry-action-panel';
import { SystemFlow } from '@/components/system-flow';
import { Button, buttonVariants } from '@/components/ui/button';
import { DataGrid } from '@/components/ui/data-grid';
import { DataNotice } from '@/components/ui/data-notice';
import { SearchField } from '@/components/ui/search-field';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusChip } from '@/components/ui/status-chip';
import { WalletControl } from '@/components/wallet-control';
import { apiQueryKeys, fetchJson, presentApiError, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import { dataSourceState } from '@/lib/data-source';
import { formatDateTime, number, titleCase, truncateMiddle, u64 } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import { createRegistrySdk, discoveredReceiverToUi, downloadJson, explorerTransactionUrl, registryDirectoryExport, receiverExport, withRegistryTimeout } from '@/lib/registry';
import { mlatStatusPresentation, operationalStatusPresentation, receiverDockState, reconcileReceivers, registryStatusPresentation, summarizeReceiverDirectory, type UnifiedReceiver } from '@/lib/receiver-state';
import type { ModeData, PositionsResponse, ReceiversResponse, RegistryEvidenceData, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

type DirectoryView = 'all' | 'mine' | 'active' | 'revoked';

const columnHelper = createColumnHelper<UnifiedReceiver>();
const EMPTY_RECEIVERS: DiscoveredReceiver[] = [];

function ownerAddress(receiver: DiscoveredReceiver, client: ccc.Client): string {
  return ccc.Address.fromScript(receiver.provenance.ownerLock, client).toString();
}

function ownsReceiver(receiver: DiscoveredReceiver, locks: ccc.Script[]): boolean {
  const owner = ccc.Script.from(receiver.provenance.ownerLock);
  return locks.some((lock) => lock.eq(owner));
}

function lifecycleTone(event: RegistryHistoryEvent): StatusTone {
  if (event.action === 'revoke') return 'failure';
  if (event.action === 'transfer') return 'selection';
  return 'trust';
}

function recordStatusTone(status: string | null): StatusTone {
  if (status === 'online') return 'healthy';
  if (status === 'degraded') return 'attention';
  if (status === 'revoked') return 'failure';
  return 'neutral';
}

function DirectoryLoading() {
  return (
    <div className="space-y-px bg-line" role="status">
      <span className="sr-only">Loading the CKB testnet receiver directory</span>
      <Skeleton className="h-12 rounded-none" />
      <Skeleton className="h-12 rounded-none" />
      <Skeleton className="h-12 rounded-none" />
    </div>
  );
}

function RegistryHistory({ history, loading, error }: { history?: RegistryHistoryEvent[]; loading: boolean; error?: Error | null }) {
  if (loading) return <div className="space-y-3 p-4" aria-label="Loading receiver lifecycle"><Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-12" /></div>;
  if (error) return <div className="p-4"><DataNotice title="Lifecycle history could not be loaded" detail="The current record is still available. Try again after the CKB indexer catches up." /></div>;
  if (!history?.length) return <div className="p-5 text-center text-xs leading-5 text-ink-quiet">No committed lifecycle events were found for this identity. Refresh the directory if this receiver was changed recently.</div>;
  return (
    <Timeline items={history.map((event) => ({
      title: `${titleCase(event.action)} · sequence ${event.record.sequence.toString()}`,
      detail: <span>{formatDateTime(event.record.updated_at)} · owner {truncateMiddle(event.ownerLock.args, 8, 6)} <a href={explorerTransactionUrl(event.transactionHash)} target="_blank" rel="noreferrer" className="ml-1 inline-flex items-center gap-1 font-semibold text-trust-cyan hover:underline">Verify<ArrowUpRight className="size-3" /></a></span>,
      meta: `Block ${event.blockNumber.toString()}`,
      tone: lifecycleTone(event),
    }))} />
  );
}

export function ReceiversPage({
  receiverData,
  selectedReceiverId,
  returnAircraftId,
  modeData,
  registryEvidence,
  positionsData,
  perspective = 'receivers',
}: {
  receiverData: ReceiversResponse | null;
  selectedReceiverId?: string | null;
  returnAircraftId?: string | null;
  modeData: ModeData | null;
  registryEvidence: RegistryEvidenceData | null;
  positionsData?: PositionsResponse;
  perspective?: 'receivers' | 'registry';
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { client, signerInfo, open } = ccc.useCcc();
  const sdk = useMemo(() => createRegistrySdk(client), [client]);
  const storeHydrated = useOperatorStore((state) => state.hasHydrated);
  const setStoreSelectedReceiverId = useOperatorStore((state) => state.setSelectedReceiverId);
  const setDock = useOperatorStore((state) => state.setDock);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const [selectedId, setSelectedId] = useState<string | null>(selectedReceiverId ?? null);
  const [receiverDetailsExpanded, setReceiverDetailsExpanded] = useState(Boolean(selectedReceiverId));
  const [search, setSearch] = useState('');
  const [view, setView] = useState<DirectoryView>(perspective === 'registry' && !selectedReceiverId ? 'active' : 'all');
  const [walletLocks, setWalletLocks] = useState<ccc.Script[]>([]);
  const basePath = perspective === 'registry' ? '/app/registry' : '/app/receivers';
  const sourceAircraftCandidate = returnAircraftId ?? searchParams.get('fromAircraft');
  const sourceAircraftId = sourceAircraftCandidate && /^[0-9A-F]{6}$/.test(sourceAircraftCandidate)
    ? sourceAircraftCandidate
    : null;

  const directoryQuery = useQuery({
    queryKey: ['registry-v2-directory', sdk.discovery.contractCodeHash],
    queryFn: () => withRegistryTimeout(
      sdk.discovery.discover({ includeInactive: true, includeRevoked: true }),
      'CKB testnet registry discovery',
    ),
    staleTime: 15_000,
    retry: false,
    refetchInterval: (query) => query.state.status === 'success' ? 30_000 : false,
  });
  const discovered = directoryQuery.data?.receivers ?? EMPTY_RECEIVERS;
  const registryReceivers = useMemo(() => discovered.map(discoveredReceiverToUi), [discovered]);
  const positionsQuery = useQuery({
    queryKey: apiQueryKeys.positions,
    queryFn: () => fetchJson<PositionsResponse>(PUBLIC_POSITIONS_PATH),
    initialData: positionsData,
    refetchInterval: 15_000,
  });
  const runtimeReceiversQuery = useQuery({
    queryKey: apiQueryKeys.receivers,
    queryFn: () => fetchJson<ReceiversResponse>('/api/receivers'),
    initialData: receiverData ?? undefined,
    refetchInterval: 15_000,
  });
  const runtimeInventoryAvailable = Boolean(runtimeReceiversQuery.data) && !runtimeReceiversQuery.error;
  const registryDirectoryAvailable = directoryQuery.isSuccess && !directoryQuery.error;
  const unifiedReceivers = useMemo(() => reconcileReceivers({
    registryReceivers,
    runtimeReceivers: runtimeReceiversQuery.data?.receivers ?? [],
    positions: positionsQuery.data?.positions ?? [],
    conflictIdentities: directoryQuery.data?.quarantinedIdentities ?? [],
    runtimeInventoryAvailable,
    registryDirectoryAvailable,
  }), [directoryQuery.data?.quarantinedIdentities, positionsQuery.data?.positions, registryDirectoryAvailable, registryReceivers, runtimeInventoryAvailable, runtimeReceiversQuery.data?.receivers]);
  const directoryReceivers = useMemo(
    () => perspective === 'registry'
      ? unifiedReceivers.filter((receiver) => receiver.identity !== null)
      : unifiedReceivers,
    [perspective, unifiedReceivers],
  );

  useEffect(() => {
    let active = true;
    if (!signerInfo) {
      setWalletLocks([]);
      return;
    }
    signerInfo.signer.getAddressObjs()
      .then((addresses) => { if (active) setWalletLocks(addresses.map(({ script }) => script)); })
      .catch(() => { if (active) setWalletLocks([]); });
    return () => { active = false; };
  }, [signerInfo]);

  useEffect(() => {
    if (!selectedReceiverId) return;
    setSelectedId((current) => current === selectedReceiverId ? current : selectedReceiverId);
    setReceiverDetailsExpanded(true);
    if (perspective === 'registry') setView('all');
  }, [perspective, selectedReceiverId]);

  const selectReceiver = useCallback((receiverIdentity: string) => {
    setSelectedId(receiverIdentity);
    setReceiverDetailsExpanded(true);
    setStoreSelectedReceiverId(receiverIdentity);
    const query = new URLSearchParams({ receiver: receiverIdentity });
    if (sourceAircraftId) query.set('fromAircraft', sourceAircraftId);
    router.replace(`${basePath}?${query.toString()}`, { scroll: false });
  }, [basePath, router, setStoreSelectedReceiverId, sourceAircraftId]);

  const ownedIdentities = useMemo(() => new Set(discovered.filter((receiver) => ownsReceiver(receiver, walletLocks)).map((receiver) => receiver.receiver_identity)), [discovered, walletLocks]);
  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return directoryReceivers.filter((receiver) => {
      if (view === 'mine' && !ownedIdentities.has(receiver.identity ?? '')) return false;
      if (view === 'active' && receiver.registryStatus !== 'active') return false;
      if (view === 'revoked' && receiver.registryStatus !== 'revoked') return false;
      return `${receiver.label} ${receiver.identity ?? ''} ${receiver.capabilities.join(' ')}`.toLowerCase().includes(query);
    });
  }, [directoryReceivers, ownedIdentities, search, view]);
  const selectedUi = directoryReceivers.find((receiver) => receiver.key === selectedId) ?? null;
  const selected = discovered.find((receiver) => receiver.receiver_identity === selectedUi?.identity);
  const selectedOwned = Boolean(selected && ownsReceiver(selected, walletLocks));

  const historyQuery = useQuery({
    queryKey: ['registry-v2-history', selected?.receiver_identity],
    queryFn: () => withRegistryTimeout(
      sdk.history.discover(selected!.receiver_identity),
      'CKB testnet lifecycle history',
    ),
    enabled: Boolean(selected),
    staleTime: 30_000,
    retry: false,
  });

  const columns = useMemo<ColumnDef<UnifiedReceiver, any>[]>(() => {
    const receiverColumn = columnHelper.display({ id: 'receiver', header: 'Receiver', size: 220, cell: ({ row }) => <div className="min-w-0"><span className="block truncate font-semibold text-ink">{row.original.label}</span><span className="block truncate font-mono text-[11px] text-ink-quiet">{row.original.identity ? truncateMiddle(row.original.identity, 10, 8) : 'No Registry identity'}</span></div> });
    const ownerColumn = columnHelper.display({ id: 'owner', header: 'Owner', size: 130, cell: ({ row }) => ownedIdentities.has(row.original.identity ?? '') ? <span className="inline-flex items-center gap-1.5 font-semibold text-trust-cyan"><UserRound className="size-3.5" />You</span> : <span className="font-mono text-xs text-ink-secondary">{row.original.ownerLockArgs ? truncateMiddle(row.original.ownerLockArgs, 7, 5) : 'Not available'}</span> });
    if (perspective === 'registry') {
      return [
        receiverColumn,
        columnHelper.display({ id: 'state', header: 'Registry-declared status', size: 150, cell: ({ row }) => <StatusChip label={titleCase(row.original.registryRecordStatus ?? 'unknown')} tone={recordStatusTone(row.original.registryRecordStatus)} /> }),
        ownerColumn,
        columnHelper.display({ id: 'sequence', header: 'Sequence', size: 90, cell: ({ row }) => u64(row.original.registry?.registry?.sequence) }),
        columnHelper.display({ id: 'updated', header: 'Registry updated', size: 170, cell: ({ row }) => row.original.lastRegistryUpdateAt ? formatDateTime(row.original.lastRegistryUpdateAt) : 'Not available' }),
      ];
    }
    return [
      receiverColumn,
      columnHelper.display({ id: 'registry', header: 'Registry', size: 125, cell: ({ row }) => <StatusChip {...registryStatusPresentation(row.original.registryStatus)} /> }),
      columnHelper.display({ id: 'operational', header: 'Operational', size: 125, cell: ({ row }) => <StatusChip {...operationalStatusPresentation(row.original.operationalStatus)} /> }),
      columnHelper.display({ id: 'mlat', header: 'MLAT', size: 140, cell: ({ row }) => <StatusChip {...mlatStatusPresentation(row.original.mlatStatus)} /> }),
      ownerColumn,
      columnHelper.display({ id: 'activity', header: 'Last observation', size: 170, cell: ({ row }) => row.original.lastObservationAt ? formatDateTime(row.original.lastObservationAt) : 'Not available' }),
    ];
  }, [ownedIdentities, perspective]);

  useEffect(() => {
    if (!storeHydrated || !selectedUi) return;
    setStoreSelectedReceiverId(selectedUi.key);
    setInvestigationContext({ focus: selectedUi.key, query: search, timeRange: perspective === 'registry' ? 'lifecycle' : 'recent' });
    const dock = receiverDockState(selectedUi, {
      includeRegistryAction: perspective !== 'registry',
      returnAircraftId: sourceAircraftId,
    });
    if (historyQuery.data?.length) {
      dock.timeline = [
        ...(dock.timeline ?? []),
        ...historyQuery.data.slice(-4).map((event) => ({
          title: `Registry ${titleCase(event.action)}`,
          detail: `Sequence ${event.record.sequence.toString()} at ${formatDateTime(event.record.updated_at)}.`,
          tone: lifecycleTone(event),
        })),
      ];
    }
    if (selected) {
      dock.evidence = [
        ...(dock.evidence ?? []),
        { title: 'Current Registry cell', detail: selected.provenance.outPoint.txHash, state: 'Committed', tone: 'trust' },
      ];
    }
    setDock(dock);
    return () => setDock(null);
  }, [historyQuery.data, perspective, search, selected, selectedUi, setDock, setInvestigationContext, setStoreSelectedReceiverId, sourceAircraftId, storeHydrated]);

  const refreshAfterTransaction = async (receiverIdentity: string) => {
    await queryClient.invalidateQueries({ queryKey: ['registry-v2-directory'] });
    await directoryQuery.refetch();
    await queryClient.invalidateQueries({ queryKey: ['registry-v2-history', receiverIdentity] });
    setView('all');
    selectReceiver(receiverIdentity);
  };

  const exportAll = () => downloadJson('ckb-testnet-receiver-directory.json', registryDirectoryExport(discovered));
  const exportSelected = () => {
    if (!selected) return;
    downloadJson(`${selected.record.receiver_id.toLowerCase()}-registry.json`, receiverExport(selected, historyQuery.data));
  };

  const discoveryFailures = directoryQuery.data?.failures ?? [];
  const runtimeSource = dataSourceState(modeData, { cached: Boolean(runtimeReceiversQuery.error || positionsQuery.error) });
  const replayMode = runtimeSource.kind === 'replay' || runtimeSource.kind === 'simulation';
  const summary = summarizeReceiverDirectory(unifiedReceivers);
  const registryDirectoryEmpty = directoryQuery.isSuccess && discovered.length === 0;
  const registryConnected = directoryQuery.isSuccess && !registryDirectoryEmpty;
  const runtimeError = runtimeReceiversQuery.error
    ? presentApiError(runtimeReceiversQuery.error, 'The MLAT receiver inventory could not be refreshed. Last-known receivers are retained but their operational state is marked unavailable.')
    : null;
  const positionsError = positionsQuery.error
    ? presentApiError(positionsQuery.error, 'Recent aircraft links could not be refreshed. Receiver identity and Registry lifecycle data remain available.')
    : null;
  const selectedInspector = selectedUi ? {
    ...selectedUi,
    ownerLockArgs: selected ? ownerAddress(selected, client) : selectedUi.ownerLockArgs,
  } : null;
  const returnToAircraft = sourceAircraftId ? <Link href={`/app/aircraft?aircraft=${encodeURIComponent(sourceAircraftId)}`} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>Return to {sourceAircraftId}<ArrowUpRight className="size-3.5" /></Link> : null;
  const currentPoolDetail = replayMode
    ? `${summary.currentRuntimePool} current replay or hybrid receivers`
    : `${summary.currentRuntimePool} receivers in current pool`;
  const runtimePoolDetail = summary.staleRuntime
    ? `${currentPoolDetail}; ${summary.staleRuntime} stale`
    : currentPoolDetail;
  const aircraftCount = new Set((positionsQuery.data?.positions ?? []).map((position) => position.aircraft_id)).size;
  const flowNodes = [
    { id: 'receiver', label: 'Receivers', detail: `${summary.registryIdentities} registered identities`, tone: summary.registryIdentities ? 'trust' as const : 'attention' as const, href: '/app/receivers' },
    { id: 'registry', label: 'Registry', detail: directoryQuery.error ? 'CKB refresh failed' : directoryQuery.isLoading ? 'Querying CKB testnet' : registryDirectoryEmpty ? 'No cells returned; check indexer freshness' : 'Connected to CKB testnet', tone: directoryQuery.error ? 'failure' as const : registryConnected ? 'trust' as const : 'attention' as const, href: '/app/registry' },
    { id: 'discovery', label: 'Discovery', detail: directoryQuery.error ? 'Eligibility unverified; Registry receivers excluded' : `${summary.mlatEligible} eligible identities`, tone: directoryQuery.error ? 'failure' as const : summary.mlatEligible ? 'healthy' as const : 'attention' as const, href: '/app/receivers' },
    { id: 'mlat', label: 'MLAT', detail: runtimePoolDetail, tone: summary.currentRuntimePool ? replayMode ? 'replay' as const : 'healthy' as const : 'attention' as const, href: '/app/pipeline' },
    { id: 'aircraft', label: 'Aircraft', detail: `${aircraftCount} localized in five minutes`, tone: aircraftCount ? 'healthy' as const : 'attention' as const, href: '/app/aircraft' },
  ];

  const directoryPanel = (
    <WorkspacePanel
      title={perspective === 'registry' ? 'Registry directory' : 'Receiver inventory'}
      detail={directoryQuery.isLoading && !directoryReceivers.length ? 'Querying Registry V2 cells on CKB testnet' : `${filtered.length} of ${directoryReceivers.length} receivers in this view`}
    >
      <div className="flex flex-col gap-3 border-b border-line p-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex max-w-full overflow-x-auto rounded-md border border-line bg-graphite-raised p-0.5" role="group" aria-label="Directory view">{([
          ['active', 'Active'], ['mine', 'My receivers'], ['revoked', 'Revoked'], ['all', 'All states'],
        ] as const).map(([value, label]) => <button key={value} type="button" aria-pressed={view === value} onClick={() => setView(value)} className={cn('h-8 whitespace-nowrap rounded px-2.5 text-xs font-medium text-ink-quiet outline-none hover:text-ink focus-visible:ring-2 focus-visible:ring-signal-blue', view === value && 'bg-graphite-hover text-ink')}>{label}</button>)}</div>
        <SearchField value={search} onValueChange={setSearch} placeholder="Search label, Type ID, or capability" label="Search receiver directory" rootClassName="w-full sm:w-[310px]" />
      </div>
      {directoryQuery.isLoading && !directoryQuery.data ? <DirectoryLoading /> : view === 'mine' && !signerInfo ? (
        <div className="flex min-h-44 flex-col items-center justify-center px-6 text-center"><UserRound className="mb-3 size-5 text-ink-quiet" /><p className="text-sm font-semibold text-ink">Connect a testnet wallet to find your receivers</p><p className="mt-1 max-w-md text-xs leading-5 text-ink-quiet">Ownership is matched against the complete CKB lock script from your wallet. No address is sent to the MLAT backend.</p><Button className="mt-4" size="sm" variant="primary" onClick={open}>Connect testnet wallet</Button></div>
      ) : (
        <DataGrid data={filtered} columns={columns} getRowId={(row) => row.key} onRowClick={(row) => selectReceiver(row.key)} isRowSelected={(row) => row.key === selectedUi?.key} keyboardColumnLabel={(row) => row.label} emptyLabel={search ? 'No receivers match this search and view. Clear the search or choose another state.' : view === 'mine' ? 'This wallet does not own a current Registry V2 receiver. Connect another wallet or choose All states.' : 'No receivers are available in this view. Refresh the directory or choose another state.'} ariaLabel="Receiver identity and MLAT status directory" height={Math.min(460, Math.max(184, filtered.length * 48))} />
      )}
    </WorkspacePanel>
  );

  const receiverInspectorPanel = (
    <ReceiverInspector
      receiver={selectedInspector}
      operationalSource={runtimeSource}
      perspective={perspective}
      lifecycle={perspective === 'registry' && selected ? <RegistryHistory history={historyQuery.data} loading={historyQuery.isLoading} error={historyQuery.error} /> : undefined}
      actions={selected ? <>{returnToAircraft}<Button size="sm" variant="secondary" onClick={exportSelected}><Download className="size-3.5" />Export record</Button><a href={explorerTransactionUrl(selected.provenance.outPoint.txHash)} target="_blank" rel="noreferrer" className={buttonVariants({ variant: 'secondary', size: 'sm' })}>Verify transaction<ArrowUpRight className="size-3.5" /></a></> : selectedUi ? <><Link href={`/app/localization?receiver=${encodeURIComponent(selectedUi.key)}`} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>Open airspace map<ArrowUpRight className="size-3.5" /></Link>{returnToAircraft}</> : returnToAircraft}
      className="self-start xl:sticky xl:top-20"
      collapsible
      expanded={receiverDetailsExpanded}
      onExpandedChange={setReceiverDetailsExpanded}
    />
  );

  const registryEventsPanel = (
    <WorkspacePanel title="Registry events and MLAT behavior" detail="Registry lifecycle changes have specific operational effects.">
      <Timeline items={[
        { title: 'Receiver registered', detail: 'The identity becomes available to Registry discovery. MLAT still applies status and capability checks.', tone: 'trust' },
        { title: 'Receiver updated', detail: 'Discovery refreshes metadata while the canonical Type ID stays unchanged.', tone: 'selection' },
        { title: 'Receiver transferred', detail: 'Ownership changes, but MLAT and historical aircraft links keep the same canonical identity.', tone: 'trust' },
        { title: 'Receiver revoked', detail: 'Discovery excludes the identity from the active MLAT pool. Historical Registry and aircraft evidence remains inspectable.', tone: 'failure' },
      ]} />
    </WorkspacePanel>
  );

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title={perspective === 'registry' ? 'Receiver Registry' : 'Receivers'}
        description={perspective === 'registry'
          ? 'Discover current owner-authorized records, manage identities you own, and verify lifecycle history.'
          : 'See which registered receivers MLAT can use, which receivers are contributing now, and why any receiver is unavailable or excluded.'}
        status={<StatusChip label={directoryQuery.error ? 'Indexer unavailable' : directoryQuery.isLoading ? 'Querying CKB testnet' : registryDirectoryEmpty ? 'No discoverable records' : 'CKB testnet directory'} tone={directoryQuery.error ? 'failure' : registryDirectoryEmpty ? 'attention' : 'trust'} />}
        actions={<>
          <Button variant="secondary" onClick={() => void directoryQuery.refetch()} disabled={directoryQuery.isFetching}><RefreshCw className={cn('size-4', directoryQuery.isFetching && 'animate-spin')} />Refresh directory</Button>
          <Button variant="secondary" onClick={exportAll} disabled={!discovered.length}><Download className="size-4" />Export JSON</Button>
        </>}
        rail={<SignalMarquee items={perspective === 'registry' ? [
          { label: 'Registry identities', value: directoryQuery.isLoading && !summary.registryIdentities ? 'Loading' : number(summary.registryIdentities), tone: summary.registryIdentities ? 'trust' : 'attention' },
          { label: 'Active', value: number(summary.active), tone: summary.active ? 'trust' : 'neutral' },
          { label: 'Revoked', value: number(summary.revoked), tone: summary.revoked ? 'failure' : 'neutral' },
          { label: 'Owned by wallet', value: signerInfo ? number(ownedIdentities.size) : 'Connect wallet', tone: ownedIdentities.size ? 'trust' : 'neutral' },
          { label: 'Network', value: 'Pudge testnet', tone: 'selection' },
        ] : [
          { label: 'Registry identities', value: directoryQuery.isLoading && !summary.registryIdentities ? 'Loading' : number(summary.registryIdentities), tone: summary.registryIdentities ? 'trust' : 'attention' },
          { label: 'Active', value: number(summary.active), tone: summary.active ? 'trust' : 'neutral' },
          { label: 'Unavailable', value: runtimeInventoryAvailable ? number(summary.unavailable) : 'Unknown', tone: !runtimeInventoryAvailable || summary.unavailable ? 'attention' : 'healthy' },
          { label: 'MLAT eligible', value: number(summary.mlatEligible), tone: summary.mlatEligible ? 'healthy' : 'attention' },
          { label: 'Contributing', value: number(summary.contributing), tone: summary.contributing ? 'healthy' : 'neutral' },
        ]} />}
      />

      {perspective !== 'registry' ? <WorkspacePanel title="Registry to aircraft flow" detail="Each stage uses current Registry, MLAT inventory, and recent localization state." tone={directoryQuery.error ? 'attention' : 'trust'}>
        <SystemFlow nodes={flowNodes} ariaLabel="Receiver Registry to MLAT aircraft flow" />
      </WorkspacePanel> : null}

      {directoryQuery.error ? <DataNotice title={perspective === 'registry' ? 'The Registry directory could not be refreshed' : 'Registry refresh failed; Registry receivers are unavailable'} detail={perspective === 'registry' ? 'The CKB testnet indexer did not return a fresh directory. No replay or MLAT receiver is substituted for an on-chain identity.' : 'The CKB testnet indexer did not return a complete directory. Registry-backed receivers are removed from the active MLAT pool until discovery succeeds again. Earlier aircraft evidence remains visible.'} onRetry={() => void directoryQuery.refetch()} /> : null}
      {runtimeError ? <DataNotice title="Receiver operational state could not be refreshed" detail={runtimeError.detail} technicalDetail={runtimeError.technicalDetail} onRetry={() => void runtimeReceiversQuery.refetch()} /> : null}
      {positionsError ? <DataNotice title="Recent aircraft links could not be refreshed" detail={positionsError.detail} technicalDetail={positionsError.technicalDetail} tone="attention" onRetry={() => void positionsQuery.refetch()} /> : null}
      {registryDirectoryEmpty ? <DataNotice title="No Registry V2 cells were returned" detail="The indexer answered successfully but returned no Registry records. This may be an empty registry or indexer lag; do not treat it as proof that a receiver does not exist." tone="attention" onRetry={() => void directoryQuery.refetch()} /> : null}
      {discoveryFailures.length ? <DataNotice title={`${discoveryFailures.length} registry ${discoveryFailures.length === 1 ? 'cell was' : 'cells were'} quarantined`} detail="The SDK rejected malformed, duplicate, or incomplete data instead of presenting it as a valid receiver." tone="attention" /> : null}

      {perspective === 'registry' ? (
        <div className={cn('grid min-w-0 gap-4', selectedInspector && 'xl:grid-cols-[minmax(0,1fr)_minmax(320px,390px)]')} data-registry-workflow>
          <div className="min-w-0 xl:col-start-1 xl:row-start-1" data-registry-workflow-item="directory"><SectionErrorBoundary title="Registry data unavailable" detail="The receiver directory failed to render. Transaction controls and the rest of the console remain available." resetKey={perspective} diagnosticsHref="/app/environment">{directoryPanel}</SectionErrorBoundary></div>
          {selectedInspector ? <div className="min-w-0 xl:col-start-2 xl:row-span-2 xl:row-start-1" data-registry-workflow-item="receiver-context"><SectionErrorBoundary title="Receiver details unavailable" detail="The selected receiver details failed to render. The directory remains available." resetKey={selectedUi?.key ?? 'none'} diagnosticsHref="/app/environment">{receiverInspectorPanel}</SectionErrorBoundary></div> : null}
          <div className="min-w-0 xl:col-start-1 xl:row-start-2" data-registry-workflow-item="owner-actions">
            <SectionErrorBoundary title="Registry transaction controls unavailable" detail="The wallet action area failed to render. No transaction was submitted by this error." resetKey={selectedUi?.key ?? 'none'} diagnosticsHref="/app/environment"><RegistryActionPanel sdk={sdk} signer={signerInfo?.signer} selected={selected} ownsSelected={selectedOwned} onCommitted={refreshAfterTransaction} /></SectionErrorBoundary>
          </div>
        </div>
      ) : (
        selectedInspector ? <WorkspaceSplit
          secondaryWidth="390px"
          primary={<div className="space-y-4"><SectionErrorBoundary title="Receiver inventory unavailable" detail="The receiver list failed to render. The selected receiver and the rest of the console remain available." resetKey={perspective} diagnosticsHref="/app/environment">{directoryPanel}</SectionErrorBoundary>{registryEventsPanel}</div>}
          secondary={<SectionErrorBoundary title="Receiver details unavailable" detail="The selected receiver details failed to render. The inventory remains available." resetKey={selectedUi?.key ?? 'none'} diagnosticsHref="/app/environment">{receiverInspectorPanel}</SectionErrorBoundary>}
        /> : <div className="space-y-4"><SectionErrorBoundary title="Receiver inventory unavailable" detail="The receiver list failed to render. The rest of the console remains available." resetKey={perspective} diagnosticsHref="/app/environment">{directoryPanel}</SectionErrorBoundary>{registryEventsPanel}</div>
      )}

      {perspective === 'registry' ? <RegistryContractVerification evidence={registryEvidence} mode={modeData} /> : null}
    </div>
  );
}
