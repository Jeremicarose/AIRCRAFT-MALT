'use client';

import { Cable, Check, Database, FileCheck2, MonitorDot, RadioTower, Satellite, Server, ShieldCheck, TriangleAlert, Workflow } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { ActivityRail, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { titleCase, truncateMiddle } from '@/lib/format';
import type { HealthData, ModeData, ReadinessData, StatusTone } from '@/lib/types';
import { useOperatorStore } from '@/lib/operator-store';
import { StatusChip, StatusIcon } from '@/components/ui/status-chip';
import { DataNotice } from '@/components/ui/data-notice';
import { Skeleton } from '@/components/ui/skeleton';
import { apiQueryKeys, fetchJson, presentApiError } from '@/lib/api';
import { dataSourceState } from '@/lib/data-source';
import { cn } from '@/lib/utils';

function ConfigurationRow({ icon: Icon, label, value, detail, tone = 'neutral', mono = false }: { icon: typeof Server; label: string; value: string; detail: string; tone?: StatusTone; mono?: boolean }) {
  return <div className="grid gap-3 border-b border-line px-4 py-3 last:border-0 sm:grid-cols-[28px_minmax(0,1fr)_auto] sm:items-center"><span className="flex size-7 items-center justify-center rounded-md bg-graphite-raised"><Icon className="size-3.5 text-ink-quiet" /></span><div><p className="text-xs font-semibold text-ink">{label}</p><p className="mt-1 text-pretty text-xs leading-5 text-ink-quiet">{detail}</p></div><div className="flex items-center gap-2 pl-10 sm:pl-0"><span className={mono ? 'max-w-[220px] truncate font-mono text-xs text-ink-secondary' : 'text-xs font-medium text-ink-secondary'} title={value}>{value}</span><StatusIcon tone={tone} label={`${label}: ${tone}`} className="size-6" /></div></div>;
}

interface RecoveryCheckData {
  check: string;
  ready: boolean;
  reason: string;
  action: string;
  expected: string;
}

function RecoveryCheck({ item }: { item: RecoveryCheckData }) {
  const Icon = item.ready ? Check : TriangleAlert;
  return (
    <article className="bg-graphite p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span className={cn('flex size-7 shrink-0 items-center justify-center rounded-full', item.ready ? 'bg-healthy/10 text-healthy' : 'bg-attention/10 text-attention')} aria-hidden="true"><Icon className="size-3.5" /></span>
          <div><h3 className="text-sm font-semibold text-ink">{item.check}</h3><p className="mt-1 text-xs leading-5 text-ink-secondary">{item.reason}</p></div>
        </div>
        <StatusChip label={item.ready ? 'Ready' : 'Not ready'} tone={item.ready ? 'healthy' : 'attention'} />
      </div>
      <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-2">
        <div><dt className="font-semibold text-ink">What to do</dt><dd className="mt-1 leading-5 text-ink-quiet">{item.action}</dd></div>
        <div><dt className="font-semibold text-ink">What success looks like</dt><dd className="mt-1 leading-5 text-ink-quiet">{item.expected}</dd></div>
      </dl>
    </article>
  );
}

export function EnvironmentPage({ modeData: initialModeData, health: initialHealth, readiness: initialReadiness }: { modeData: ModeData | null; health: HealthData | null; readiness: ReadinessData | null }) {
  const modeQuery = useQuery({ queryKey: apiQueryKeys.mode, queryFn: () => fetchJson<ModeData>('/api/system/mode'), initialData: initialModeData ?? undefined });
  const healthQuery = useQuery({ queryKey: apiQueryKeys.health, queryFn: () => fetchJson<HealthData>('/api/health'), initialData: initialHealth ?? undefined });
  const readinessQuery = useQuery({ queryKey: apiQueryKeys.readiness, queryFn: () => fetchJson<ReadinessData>('/api/readiness'), initialData: initialReadiness ?? undefined, refetchInterval: 30_000 });
  const modeData = modeQuery.data ?? null;
  const health = healthQuery.data ?? null;
  const readiness = readinessQuery.data ?? null;
  const source = dataSourceState(modeData, { cached: Boolean(modeQuery.error || healthQuery.error) });
  const isReplay = source.kind === 'replay' || source.kind === 'simulation';
  const registryHash = modeData?.receiver_registry_type_hash;
  const runtimeReady = modeData?.runtime_status === 'active';
  const reliability = readiness?.dimensions?.reliability ?? {};
  const clock = readiness?.dimensions?.clock ?? {};
  const activeReceivers = Number(reliability.active_receivers ?? 0);
  const synchronizedReceivers = Number(clock.synchronized_receivers ?? 0);
  const signalFresh = reliability.signal_fresh === true;
  const registryReady = Boolean(registryHash && modeData?.registry_discovery_live);
  const liveSourceReady = source.kind === 'live';
  const recoveryChecks: RecoveryCheckData[] = [
    {
      check: 'MLAT runtime',
      ready: runtimeReady,
      reason: runtimeReady ? 'The processor is active and reporting fresh telemetry.' : `The processor reports ${modeData?.runtime_status ?? 'no runtime status'}.`,
      action: runtimeReady ? 'No action required.' : 'Start or restart the MLAT processor and API with the same DATABASE_PATH, then refresh Diagnostics.',
      expected: 'Runtime changes to Ready and fresh telemetry appears.',
    },
    {
      check: 'Backend Registry discovery',
      ready: registryReady,
      reason: !registryHash ? 'RECEIVER_REGISTRY_TYPE_HASH is not configured in the MLAT runtime.' : modeData?.registry_discovery_live ? 'The runtime is discovering current Registry V2 cells.' : 'A Registry code hash is configured, but current CKB discovery has not succeeded.',
      action: registryReady ? 'No action required.' : 'Set RECEIVER_REGISTRY_TYPE_HASH to the exact Registry V2 code hash and RECEIVER_REGISTRY_HASH_TYPE=data1. Confirm CKB_RPC_URL and CKB_INDEXER_URL are reachable, then restart the MLAT processor and API.',
      expected: 'This check changes to Ready and canonical Registry identities appear in the MLAT receiver inventory.',
    },
    {
      check: 'Observation source',
      ready: liveSourceReady,
      reason: liveSourceReady ? 'The runtime reports current receiver observations.' : `${source.label}: ${source.detail}`,
      action: liveSourceReady ? 'No action required.' : 'For live operation, set DEMO_MODE=false and SIMULATE_IF_UNAVAILABLE=false. Configure FOURDSKY_TRANSPORT plus FOURDSKY_ENDPOINT or FOURDSKY_BRIDGE_COMMAND, then restart the MLAT processor.',
      expected: 'Observation source changes to LIVE. Replay or synthetic records are not relabeled as live.',
    },
    {
      check: 'Fresh receiver observations',
      ready: signalFresh,
      reason: signalFresh ? 'The runtime reports a fresh receiver signal.' : 'No fresh receiver observation is reaching the solve path.',
      action: signalFresh ? 'No action required.' : 'Check the configured feed endpoint or bridge process, its credentials, and recent source timestamps. Restore the feed, then refresh Diagnostics.',
      expected: 'Signal freshness passes and the ingest stage begins processing current observations.',
    },
    {
      check: 'Receiver geometry and clocks',
      ready: activeReceivers >= 4 && synchronizedReceivers >= 4,
      reason: `${activeReceivers} active receiver${activeReceivers === 1 ? '' : 's'} and ${synchronizedReceivers} clock-qualified receiver${synchronizedReceivers === 1 ? '' : 's'} are reported. A solve requires at least four qualified observations.`,
      action: activeReceivers >= 4 && synchronizedReceivers >= 4 ? 'No action required.' : 'Connect at least four eligible receiver feeds and provide the configured clock qualification evidence. Do not mark clocks synchronized without real evidence.',
      expected: 'At least four active, clock-qualified receivers reach correlation and solve stages.',
    },
    {
      check: 'Publishable evidence',
      ready: Boolean(readiness?.ready && modeData?.benchmarkable_output),
      reason: readiness?.ready && modeData?.benchmarkable_output ? 'All current readiness and provenance gates pass.' : 'Current output is constrained by one or more upstream readiness or provenance checks.',
      action: readiness?.ready && modeData?.benchmarkable_output ? 'No action required.' : 'Resolve the failed checks above, allow new non-synthetic positions to be stored, then refresh Pipeline and Diagnostics.',
      expected: 'Evidence changes to Ready only after genuine current observations pass all configured gates.',
    },
  ];
  const readinessTimeline = [
    { title: 'Runtime initialized', detail: runtimeReady ? 'Processor is active and reporting telemetry.' : 'Processor runtime is not active.', tone: runtimeReady ? 'healthy' as StatusTone : 'failure' as StatusTone },
    { title: 'Receiver discovery', detail: modeData?.registry_discovery_live ? 'The backend is reading current Registry V2 cells from CKB.' : 'The backend is not currently reading Registry V2 cells from CKB.', tone: modeData?.registry_discovery_live ? 'healthy' as StatusTone : 'attention' as StatusTone },
    { title: 'Evidence gates', detail: readiness?.ready ? 'Quality, freshness, reliability, and clock gates pass.' : 'At least one production evidence gate is incomplete.', tone: readiness?.ready ? 'healthy' as StatusTone : 'attention' as StatusTone },
    { title: 'Production posture', detail: modeData?.strict_production_mode ? 'Strict production enforcement enabled.' : 'Standard enforcement allows non-production operation.', tone: modeData?.strict_production_mode ? 'healthy' as StatusTone : 'neutral' as StatusTone },
  ];

  useEffect(() => {
    useOperatorStore.getState().setInvestigationContext({ focus: 'environment', timeRange: 'environment' });
    useOperatorStore.getState().setDock({
      entityType: 'environment',
      title: 'Deployment topology',
      subtitle: 'Pinned from the environment workspace.',
      statusLabel: runtimeReady ? 'Runtime active' : 'Runtime offline',
      statusTone: runtimeReady ? 'healthy' : 'failure',
      facts: [
        { label: 'Source', value: source.label, tone: source.tone },
        { label: 'Transport', value: titleCase(modeData?.configured_transport), tone: modeData?.configured_transport ? 'healthy' : 'failure' },
        { label: 'Registry hash', value: truncateMiddle(registryHash, 12, 10), mono: true, tone: registryHash ? 'trust' : 'failure' },
        { label: 'Evidence', value: modeData?.benchmarkable_output ? 'Benchmarkable' : 'Constrained', tone: modeData?.benchmarkable_output ? 'healthy' : 'attention' },
      ],
      timeline: readinessTimeline,
      evidence: [
        { title: 'Trust boundary', detail: 'CKB establishes receiver identity and authorized lifecycle transitions. Receiver location, clock quality, and stream honesty remain operational evidence.', state: 'Context', tone: 'trust' },
      ],
      actions: [
        { label: 'Open receivers', href: '/app/receivers', tone: 'secondary' },
        { label: 'Open pipeline', href: '/app/pipeline', tone: 'primary' },
      ],
    });
    return () => useOperatorStore.getState().setDock(null);
  }, [isReplay, modeData?.benchmarkable_output, modeData?.configured_transport, modeData?.mode, readinessTimeline, registryHash, runtimeReady]);

  const activityRail = [
    { title: 'Runtime', detail: runtimeReady ? 'Processor is active and healthy.' : 'Processor runtime is not active.', meta: titleCase(modeData?.runtime_status), tone: runtimeReady ? 'healthy' : 'failure' as StatusTone },
    { title: 'Discovery', detail: modeData?.registry_discovery_live ? 'The backend is reading current CKB Registry cells.' : 'Backend Registry discovery is not active.', meta: modeData?.registry_discovery_live ? 'Connected' : 'Idle', tone: modeData?.registry_discovery_live ? 'trust' : 'attention' as StatusTone },
    { title: 'Evidence gates', detail: readiness?.ready ? 'Deployment currently satisfies readiness gates.' : 'One or more readiness dimensions remain incomplete.', meta: readiness?.ready ? 'Pass' : 'Review', tone: readiness?.ready ? 'healthy' : 'attention' as StatusTone },
  ];
  const connectionFailure = modeQuery.error ?? healthQuery.error;
  const connectionError = connectionFailure ? presentApiError(connectionFailure, 'Deployment health could not be refreshed. Last-known configuration remains visible and may be stale.') : null;
  const readinessError = readinessQuery.error ? presentApiError(readinessQuery.error, 'Readiness evidence could not be refreshed. Runtime configuration remains available.') : null;

  if (modeQuery.isLoading && healthQuery.isLoading && !modeData && !health) {
    return <div className="space-y-3" role="status" aria-label="Loading diagnostics"><Skeleton className="h-24 border border-line" /><Skeleton className="h-[440px] border border-line" /><span className="sr-only">Loading deployment diagnostics</span></div>;
  }

  return (
    <div className="space-y-4">
      {connectionError ? <DataNotice title="Deployment health could not be refreshed" detail={connectionError.detail} technicalDetail={connectionError.technicalDetail} onRetry={() => void Promise.all([modeQuery.refetch(), healthQuery.refetch()])} /> : null}
      {readinessError ? <DataNotice title="Readiness evidence could not be refreshed" detail={readinessError.detail} technicalDetail={readinessError.technicalDetail} tone="attention" onRetry={() => void readinessQuery.refetch()} /> : null}
      <WorkspaceHeader title="Topology and dependencies" description="Review runtime connectivity, Registry discovery, trust boundaries, and the evidence gates required for production use." status={<StatusChip label={connectionError ? 'Status unverified' : runtimeReady ? 'Runtime active' : 'Runtime offline'} tone={connectionError ? 'attention' : runtimeReady ? 'healthy' : 'failure'} />} rail={<SignalMarquee items={[{ label: 'Runtime', value: connectionError ? 'Unverified' : runtimeReady ? 'Active' : 'Offline', tone: connectionError ? 'attention' : runtimeReady ? 'healthy' : 'failure' }, { label: 'Discovery', value: modeData?.registry_discovery_live ? 'Connected' : 'Idle', tone: modeData?.registry_discovery_live ? 'trust' : 'attention' }, { label: 'Registry code', value: modeData?.registry_code_immutable ? 'Immutable' : 'Historical mutable', tone: modeData?.registry_code_immutable ? 'healthy' : 'attention' }, { label: 'Source', value: source.label, tone: source.tone }]} />} />

      {health?.components?.length ? <WorkspacePanel title="Component health" detail="Each state describes observed evidence and its limits." action={<a href="/api/diagnostics/bundle" download="mlat-diagnostics.json" className="rounded-sm text-xs text-signal-blue underline focus-visible:outline-2">Export diagnostics</a>}><div className="divide-y divide-line">{health.components.map((component) => <div key={component.component} className="grid gap-2 px-4 py-3 sm:grid-cols-[140px_140px_minmax(0,1fr)]"><p className="text-sm font-semibold text-ink">{component.component.replaceAll('_', ' ')}</p><div><StatusChip label={component.status} tone={component.status === 'HEALTHY' ? 'healthy' : component.status === 'FAILED' ? 'failure' : 'attention'} /></div><div className="text-xs leading-5 text-ink-secondary"><p>{component.reason}</p><p className="mt-1">Action: {component.action}</p></div></div>)}</div></WorkspacePanel> : null}

      <WorkspacePanel title="Recovery checks" detail="Each check explains what failed, why it matters, what to change, and how to confirm recovery." tone={recoveryChecks.every((item) => item.ready) ? 'healthy' : 'attention'}>
        <div className="grid gap-px bg-line lg:grid-cols-2">{recoveryChecks.map((item) => <RecoveryCheck key={item.check} item={item} />)}</div>
      </WorkspacePanel>

      <WorkspaceSplit
        secondaryWidth="380px"
        primary={<div className="space-y-4"><WorkspacePanel title="Deployment configuration" detail="Runtime, connectivity, identity, and evidence controls." tone={runtimeReady ? 'healthy' : 'failure'}><ConfigurationRow icon={Server} label="Runtime" value={titleCase(modeData?.runtime_status)} detail="Processor status reported by the control plane." tone={runtimeReady ? 'healthy' : 'failure'} /><ConfigurationRow icon={Satellite} label="Observation source" value={source.label} detail={source.detail} tone={source.tone} /><ConfigurationRow icon={Cable} label="Receiver transport" value={titleCase(modeData?.configured_transport)} detail="Configured source acquisition transport." tone={modeData?.configured_transport ? 'healthy' : 'failure'} /><ConfigurationRow icon={Database} label="Registry code hash" value={truncateMiddle(registryHash, 12, 10)} detail="RECEIVER_REGISTRY_TYPE_HASH used by the backend to discover exact Registry V2 scripts." tone={registryHash ? 'trust' : 'failure'} mono /><ConfigurationRow icon={ShieldCheck} label="Registry code binding" value={modeData?.registry_code_immutable ? 'Immutable data1' : 'Historical mutable type'} detail={modeData?.registry_code_immutable ? 'The deployed binary hash is part of every Registry script.' : 'This deployment is for historical read-only compatibility and must not be used for live lifecycle actions.'} tone={modeData?.registry_code_immutable ? 'healthy' : 'attention'} /><ConfigurationRow icon={ShieldCheck} label="Production enforcement" value={modeData?.strict_production_mode ? 'Strict' : 'Standard'} detail="Strict mode rejects synthetic fallbacks and incomplete trust." tone={modeData?.strict_production_mode ? 'healthy' : 'neutral'} /><ConfigurationRow icon={FileCheck2} label="Evidence output" value={modeData?.benchmarkable_output ? 'Benchmarkable' : 'Constrained'} detail="Whether current output may support benchmark interpretation." tone={modeData?.benchmarkable_output ? 'healthy' : 'attention'} /></WorkspacePanel><WorkspacePanel title="Dependency topology" detail="Receiver transport through evidence publication." tone="trust"><div className="grid gap-px bg-line md:grid-cols-5">{[{ icon: RadioTower, label: 'Receivers', detail: titleCase(modeData?.configured_transport), tone: isReplay ? 'replay' : modeData?.configured_transport ? 'healthy' : 'failure' }, { icon: Satellite, label: 'MLAT ingest', detail: runtimeReady ? 'Active' : 'Offline', tone: runtimeReady ? 'healthy' : 'failure' }, { icon: Workflow, label: 'Solver', detail: readiness?.dimensions?.quality?.ready ? 'Ready' : 'Review', tone: readiness?.dimensions?.quality?.ready ? 'healthy' : 'attention' }, { icon: FileCheck2, label: 'Evidence', detail: modeData?.benchmarkable_output ? 'Ready' : 'Constrained', tone: modeData?.benchmarkable_output ? 'healthy' : 'attention' }, { icon: MonitorDot, label: 'Console', detail: health?.status ? titleCase(health.status) : 'Connected', tone: health ? 'healthy' : 'failure' }].map((node) => { const Icon = node.icon; return <div key={node.label} className="bg-graphite px-4 py-5 text-center"><span className="mx-auto flex size-10 items-center justify-center rounded-full bg-graphite-raised"><Icon className="size-4 text-ink-secondary" /></span><p className="mt-3 text-xs font-semibold text-ink">{node.label}</p><p className="mt-1 text-xs text-ink-quiet">{node.detail}</p><div className="mt-3"><StatusChip label={node.tone === 'healthy' ? 'Healthy' : node.tone === 'failure' ? 'Failure' : node.tone === 'replay' ? source.label : 'Review'} tone={node.tone as StatusTone} /></div></div>; })}</div></WorkspacePanel></div>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Environment signals" detail="Runtime, discovery, and readiness summary." tone={runtimeReady ? 'healthy' : 'failure'}><ActivityRail items={activityRail} /></WorkspacePanel><WorkspacePanel title="Readiness timeline" detail="Current deployment progression." tone={readiness?.ready ? 'healthy' : 'attention'}><Timeline items={readinessTimeline} /></WorkspacePanel></div>}
      />
    </div>
  );
}
