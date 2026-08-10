'use client';

import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, Database, Plane, RadioTower, ShieldCheck, TriangleAlert, Workflow } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo } from 'react';
import { ActivityFeed } from '@/components/activity-feed';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { ActivityRail, ConfidenceGauge, FactGrid, Inspector, IssueList, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { buttonVariants } from '@/components/ui/button';
import { StatStrip, type StatItem } from '@/components/ui/stat-strip';
import { StatusChip } from '@/components/ui/status-chip';
import { fetchJson } from '@/lib/api';
import { formatAltitude, formatCoordinate, formatDistanceMeters, latestPositions, number, percent, toneFromFreshness, toneFromScore } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { JsonValue, PipelineData, PositionsResponse, ReadinessData, ReceiversResponse, ShellSnapshot, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

interface OverviewPageProps {
  snapshot: ShellSnapshot;
  readiness: ReadinessData | null;
  benchmark: Record<string, JsonValue> | null;
  positionsData: PositionsResponse;
  initialPipeline: PipelineData | null;
}

export function OverviewPage({ snapshot, readiness, benchmark, positionsData, initialPipeline }: OverviewPageProps) {
  const positionsQuery = useQuery({ queryKey: ['positions', 'overview'], queryFn: () => fetchJson<PositionsResponse>('/api/positions/recent?seconds=600&limit=250'), initialData: positionsData, refetchInterval: 10_000 });
  const receiversQuery = useQuery({ queryKey: ['receivers', 'overview'], queryFn: () => fetchJson<ReceiversResponse>('/api/receivers'), initialData: snapshot.receiverData ?? { receivers: [] }, refetchInterval: 15_000 });
  const pipelineQuery = useQuery({ queryKey: ['pipeline', 'overview'], queryFn: () => fetchJson<PipelineData>('/api/pipeline'), initialData: initialPipeline ?? undefined, refetchInterval: 15_000 });
  const aircraft = useMemo(() => latestPositions(positionsQuery.data.positions ?? []), [positionsQuery.data.positions]);
  const receivers = receiversQuery.data.receivers ?? [];
  const selectedId = useOperatorStore((state) => state.selectedAircraftId);
  const setSelectedId = useOperatorStore((state) => state.setSelectedAircraftId);
  const setDock = useOperatorStore((state) => state.setDock);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const selected = aircraft.find((item) => item.aircraft_id === selectedId) ?? aircraft[0] ?? null;
  const mode = snapshot.modeData;
  const health = snapshot.healthData;
  const pipeline = pipelineQuery.data;
  const isReplay = Boolean(mode?.demo_mode || mode?.simulation_mode || mode?.synthetic_feed_mode);
  const evidenceReady = Boolean(readiness?.ready && mode?.benchmarkable_output);
  const signalAge = health?.freshness?.last_signal_age_s;
  const storeAge = health?.freshness?.last_store_age_s;
  const activeReceivers = Number(readiness?.dimensions?.reliability?.active_receivers ?? receivers.length);
  const systemTone: StatusTone = !mode ? 'failure' : isReplay ? 'replay' : readiness?.ready ? 'healthy' : 'attention';
  const systemLabel = !mode ? 'System unavailable' : isReplay ? 'Replay operations' : readiness?.ready ? 'System operational' : 'Attention required';
  const blockers = pipeline?.blockers ?? [];
  const alerts = [
    ...blockers.slice(0, 3).map((detail) => ({ title: 'Pipeline blocker', detail, tone: 'failure' as StatusTone, href: '/app/pipeline' })),
    signalAge == null ? { title: 'Signal freshness', detail: 'No current signal timestamp is available.', tone: 'failure' as StatusTone, href: '/app/environment' } : signalAge > 60 ? { title: 'Signal freshness', detail: `Latest signal is ${Math.round(signalAge)} seconds old.`, tone: 'attention' as StatusTone, href: '/app/environment' } : null,
    activeReceivers < 4 ? { title: 'Receiver geometry', detail: `${activeReceivers} active receivers, four are required for a solve.`, tone: 'failure' as StatusTone, href: '/app/receivers' } : null,
  ].filter(Boolean) as Array<{ title: string; detail: string; tone: StatusTone; href: string }>;

  const evidenceSteps = [
    { title: 'Receiver identity', detail: mode?.receiver_registry_type_hash ? 'Registry V2 type hash configured' : 'Registry trust configuration pending', tone: mode?.receiver_registry_type_hash ? 'healthy' as StatusTone : 'attention' as StatusTone },
    { title: 'Receiver participation', detail: `${activeReceivers} active of ${receivers.length} visible`, tone: activeReceivers >= 4 ? 'healthy' as StatusTone : 'failure' as StatusTone },
    { title: 'Position solving', detail: aircraft.length ? `${aircraft.length} aircraft in the current air picture` : 'No current solved positions', tone: aircraft.length ? 'healthy' as StatusTone : 'attention' as StatusTone },
    { title: 'Evidence readiness', detail: evidenceReady ? 'Current output passes publication gates' : 'Evidence remains constrained', tone: evidenceReady ? 'healthy' as StatusTone : 'attention' as StatusTone },
  ];
  const summaryStats: StatItem[] = [
    { label: 'Aircraft', value: number(aircraft.length), detail: storeAge == null ? 'No current solve' : `Latest solve ${Math.round(storeAge)}s ago`, icon: Plane, tone: toneFromFreshness(storeAge, 20, 90) },
    { label: 'Receivers', value: `${number(activeReceivers)}/${number(receivers.length)}`, detail: activeReceivers >= 4 ? 'Solve geometry available' : 'Below solve minimum', icon: RadioTower, tone: activeReceivers >= 4 ? 'healthy' : 'failure' },
    { label: 'Pipeline', value: pipeline?.pipeline_operational ? 'Operational' : 'Blocked', detail: `${pipeline?.stages?.filter((stage) => stage.status === 'pass').length ?? 0}/${pipeline?.stages?.length ?? 0} stages passing`, icon: Workflow, tone: pipeline?.pipeline_operational ? 'healthy' : 'attention' },
    { label: 'Registry', value: mode?.receiver_registry_type_hash ? 'Verified' : 'Pending', detail: mode?.registry_discovery_live ? 'Live discovery' : 'Trust configuration', icon: Database, tone: mode?.receiver_registry_type_hash ? 'trust' : 'attention' },
  ];

  const liveRail: Array<{ title: string; detail: string; meta: string; tone: StatusTone; href: string }> = [
    { title: 'Air picture', detail: `${aircraft.length} aircraft in the current ten-minute window.`, meta: storeAge == null ? 'Awaiting solve' : `${Math.round(storeAge)}s`, tone: aircraft.length ? 'healthy' : 'attention', href: '/app/localization' },
    { title: 'Receiver fleet', detail: `${activeReceivers} active receivers contribute to current localization.`, meta: `${receivers.length} visible`, tone: activeReceivers >= 4 ? 'healthy' : 'failure', href: '/app/receivers' },
    { title: 'Evidence posture', detail: evidenceReady ? 'Output is benchmarkable and ready for review.' : 'Evidence gates remain constrained.', meta: evidenceReady ? 'Ready' : 'Pending', tone: evidenceReady ? 'trust' : 'attention', href: '/app/pipeline' },
  ];

  useEffect(() => {
    if (selected) setSelectedId(selected.aircraft_id);
  }, [selected?.aircraft_id]);

  useEffect(() => {
    setInvestigationContext({ focus: selected?.aircraft_id ?? alerts[0]?.title ?? 'overview' });
    setDock({
      entityType: 'overview',
      title: selected?.aircraft_id ?? 'Overview posture',
      subtitle: selected ? 'Pinned aircraft from the operational landing page.' : 'Shared console summary for the current operating window.',
      statusLabel: selected ? percent(selected.quality?.score, 0) : systemLabel,
      statusTone: selected ? toneFromScore(selected.quality?.score) : systemTone,
      facts: selected ? [
        { label: 'Position', value: formatCoordinate(selected.position?.latitude ?? selected.latitude, selected.position?.longitude ?? selected.longitude) },
        { label: 'Altitude', value: formatAltitude(selected.position?.altitude ?? selected.altitude) },
        { label: 'Uncertainty', value: formatDistanceMeters(selected.quality?.uncertainty_m ?? selected.uncertainty) },
        { label: 'Receivers', value: number(selected.correlation?.receiver_count ?? selected.num_receivers) },
      ] : [
        { label: 'System', value: systemLabel, tone: systemTone },
        { label: 'Aircraft', value: number(aircraft.length) },
        { label: 'Receivers', value: `${number(activeReceivers)}/${number(receivers.length)}` },
        { label: 'Evidence', value: evidenceReady ? 'Ready' : 'Pending', tone: evidenceReady ? 'trust' : 'attention' },
      ],
      timeline: evidenceSteps,
      evidence: alerts.length ? alerts.map((alert) => ({ title: alert.title, detail: alert.detail, state: 'Open', tone: alert.tone })) : [{ title: 'Operator attention', detail: 'No priority issues are currently ranked on the overview page.', state: 'Clear', tone: 'healthy' }],
      actions: [
        { label: 'Open live map', href: '/app/localization', tone: 'primary' },
        { label: 'Inspect pipeline', href: '/app/pipeline', tone: 'secondary' },
      ],
    });
    return () => setDock(null);
  }, [activeReceivers, aircraft.length, evidenceReady, receivers.length, selected, setDock, setInvestigationContext, systemLabel, systemTone]);

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        eyebrow="Operate"
        title="Operational landing page"
        description={alerts.length ? alerts[0].detail : 'Maps, evidence posture, and ranked issues stay connected so an operator can move from system health to a concrete aircraft or receiver investigation without losing context.'}
        status={<StatusChip label={systemLabel} tone={systemTone} />}
        actions={<Link href={alerts.length ? '/app/pipeline' : '/app/localization'} className={buttonVariants({ variant: alerts.length ? 'primary' : 'secondary' })}>{alerts.length ? 'Investigate issue' : 'Open live map'}<ArrowRight className="size-4" /></Link>}
        rail={<SignalMarquee items={[{ label: 'Tracked aircraft', value: number(aircraft.length), tone: aircraft.length ? 'healthy' : 'attention' }, { label: 'Active receivers', value: `${number(activeReceivers)}/${number(receivers.length)}`, tone: activeReceivers >= 4 ? 'healthy' : 'failure' }, { label: 'Evidence posture', value: evidenceReady ? 'Ready' : 'Constrained', tone: evidenceReady ? 'trust' : 'attention' }, { label: 'Pipeline blockers', value: number(blockers.length), tone: blockers.length ? 'failure' : 'healthy' }]} />}
      />

      <StatStrip items={summaryStats} />

      <WorkspaceSplit
        secondaryWidth="420px"
        primary={<WorkspacePanel title="Operational map" detail="The overview now starts with a live spatial canvas instead of a static summary." tone="trust"><div className="relative overflow-hidden"><div className="absolute left-4 top-4 z-dropdown flex items-center gap-2 rounded-md border border-line bg-graphite/90 px-3 py-2 shadow-map backdrop-blur-sm"><span className="size-1.5 rounded-full bg-healthy" /><span className="text-xs font-semibold text-ink">Current airspace</span><span className="text-[11px] text-ink-quiet">{aircraft.length} tracked</span></div><LazyAirspaceMap aircraft={aircraft} receivers={receivers} selectedAircraftId={selected?.aircraft_id} onSelectAircraft={setSelectedId} className="map-overview" /></div></WorkspacePanel>}
        secondary={<WorkspacePanel title="Ranked attention queue" detail="The highest priority issues and state changes are surfaced first." tone={alerts.length ? alerts[0].tone : 'healthy'}><IssueList items={alerts.length ? alerts : [{ title: 'System clear', detail: 'Aircraft localization, receiver participation, and evidence gates are within operating thresholds.', tone: 'healthy', href: '/app/localization' }]} /><div className="border-t border-line"><ActivityRail items={liveRail} /></div></WorkspacePanel>}
      />

      <WorkspaceSplit
        secondaryWidth="340px"
        primary={<div className="space-y-4">
          <WorkspacePanel title="Live activity" detail="Receiver heartbeats and solved positions remain navigable investigation pivots.">
            <ActivityFeed aircraft={aircraft} receivers={receivers} />
          </WorkspacePanel>
          <WorkspacePanel title="Evidence path" detail="Trust, receiver participation, position solving, and publication posture." tone={evidenceReady ? 'trust' : 'attention'}>
            <Timeline items={evidenceSteps} />
          </WorkspacePanel>
        </div>}
        secondary={<Inspector title={selected?.aircraft_id ?? 'No aircraft selected'} subtitle={selected ? 'Pinned from the overview air picture' : 'Select an aircraft to inspect the latest solve'} status={selected ? <StatusChip label={percent(selected.quality?.score, 0)} tone={toneFromScore(selected.quality?.score)} /> : <StatusChip label="Waiting" />} className="self-start xl:sticky xl:top-20">
          {selected ? <><div className="border-b border-line p-4"><ConfidenceGauge value={Number(selected.quality?.score ?? 0)} /></div><FactGrid items={[{ label: 'Position', value: formatCoordinate(selected.position?.latitude ?? selected.latitude, selected.position?.longitude ?? selected.longitude) }, { label: 'Altitude', value: formatAltitude(selected.position?.altitude ?? selected.altitude) }, { label: 'Uncertainty', value: formatDistanceMeters(selected.quality?.uncertainty_m ?? selected.uncertainty) }, { label: 'Receivers', value: number(selected.correlation?.receiver_count ?? selected.num_receivers) }]} /></> : <div className="p-4 text-xs text-ink-quiet">No solved aircraft position is available.</div>}
          <div className="border-b border-line p-4"><p className="mb-3 text-xs font-semibold text-ink">Recommended next move</p><Link href={alerts.length ? '/app/pipeline' : `/app/aircraft?aircraft=${encodeURIComponent(selected?.aircraft_id ?? '')}`} className={buttonVariants({ variant: alerts.length ? 'primary' : 'secondary', size: 'sm' })}>{alerts.length ? 'Open pipeline debugger' : 'Open aircraft investigation'}</Link></div>
          <div className="p-4"><div className="flex items-start gap-2 text-xs leading-5 text-ink-quiet"><ShieldCheck className={cn('mt-0.5 size-3.5 shrink-0', evidenceReady ? 'text-trust-cyan' : 'text-attention')} />{String(benchmark?.evidence_status ?? (evidenceReady ? 'Current output can support evidence review.' : 'Publication gates remain constrained.'))}</div></div>
        </Inspector>}
      />
    </div>
  );
}
