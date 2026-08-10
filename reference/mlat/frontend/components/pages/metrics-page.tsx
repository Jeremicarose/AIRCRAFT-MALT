'use client';

import { Activity, Clock3, Cpu, Gauge, MemoryStick, RadioTower, ServerCog, TriangleAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { DistributionChart, MultiLineChart, Sparkline, TrendChart } from '@/components/lazy-charts';
import { ActivityRail, SignalMarquee, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { StatStrip, type StatItem } from '@/components/ui/stat-strip';
import { StatusChip } from '@/components/ui/status-chip';
import { number } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { JsonValue, MetricsData, StatusTone } from '@/lib/types';

export type Artifact = Record<string, JsonValue> | null;
type Range = '1h' | '6h' | '24h';

const rangeOptions: ReadonlyArray<{ value: Range; label: string }> = [
  { value: '1h', label: '1h' },
  { value: '6h', label: '6h' },
  { value: '24h', label: '24h' },
];

function histogram(values: number[], bins = 10) {
  const valid = values.filter(Number.isFinite);
  if (!valid.length) return [];
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const width = max === min ? 1 : (max - min) / bins;
  return Array.from({ length: bins }, (_, index) => {
    const start = min + index * width;
    const end = index === bins - 1 ? max + Number.EPSILON : start + width;
    return { label: start < 1 ? start.toFixed(2) : start.toFixed(1), samples: valid.filter((value) => value >= start && value < end).length };
  });
}

function EmptyChart({ height = 220 }: { height?: number }) {
  return <div style={{ height }} className="grid place-items-center text-xs text-ink-quiet">No samples in this range.</div>;
}

export function MetricsPage({ metrics, performance, reliability }: { metrics: MetricsData | null; performance: Artifact; reliability: Artifact }) {
  const [range, setRange] = useState<Range>('24h');
  const history = metrics?.history ?? [];
  const limit = range === '1h' ? 12 : range === '6h' ? 72 : history.length;
  const chartData = useMemo(() => history.slice(-limit).map((row, index) => {
    const timestamp = Number(row.timestamp ?? row.created_at ?? index);
    return { ...row, label: Number.isFinite(timestamp) && timestamp > 1_000_000 ? new Date(timestamp * 1000).toISOString().slice(11, 19) : String(index + 1) };
  }), [history, limit]);
  const current = metrics?.current ?? {};
  const reliabilityMetrics = reliability?.metrics && typeof reliability.metrics === 'object' && !Array.isArray(reliability.metrics) ? reliability.metrics : null;
  const latencyDistribution = useMemo(() => histogram(chartData.map((row) => Number((row as Record<string, unknown>).avg_store_latency_ms))), [chartData]);
  const solveSuccess = Number(current.solve_success_percent ?? 0);
  const activeReceivers = Number(current.active_receivers ?? 0);
  const failedSolves = Number(current.failed_solves ?? 0);
  const apiLatency = performance?.metrics && typeof performance.metrics === 'object' && !Array.isArray(performance.metrics) ? performance.metrics : null;
  const apiP95 = apiLatency && typeof apiLatency === 'object' && !Array.isArray(apiLatency) ? (apiLatency as Record<string, JsonValue>).api_latency_ms : null;
  const apiP95Value = apiP95 && typeof apiP95 === 'object' && !Array.isArray(apiP95) ? (apiP95 as Record<string, JsonValue>).p95 : null;

  useEffect(() => {
    useOperatorStore.getState().setInvestigationContext({ focus: 'metrics', timeRange: range });
    useOperatorStore.getState().setDock({
      entityType: 'metrics',
      title: 'Observability workbench',
      subtitle: 'Pinned from the metrics workspace.',
      statusLabel: `${number(solveSuccess, 1)}% solve success`,
      statusTone: solveSuccess >= 99 ? 'healthy' : solveSuccess >= 95 ? 'attention' : 'failure',
      facts: [
        { label: 'Samples', value: number(metrics?.sample_count) },
        { label: 'Active receivers', value: number(activeReceivers), tone: activeReceivers >= 4 ? 'healthy' : 'failure' },
        { label: 'Store latency', value: `${number(current.avg_store_latency_ms, 2)} ms` },
        { label: 'Failed solves', value: number(failedSolves), tone: failedSolves ? 'attention' : 'healthy' },
      ],
      timeline: [
        { title: 'Current range', detail: `Charts are scoped to the ${range} investigation window.`, tone: 'selection' },
        { title: 'Throughput', detail: `${number(current.signals_per_minute)} observations/min and ${number(current.positions_per_minute, 1)} positions/min.`, tone: 'healthy' },
        { title: 'Resource posture', detail: `${number(current.process_rss_mb, 1)} MB RSS with ${number(current.last_store_age_s, 1)} seconds of latest-store age.`, tone: 'attention' },
      ],
      evidence: [
        { title: 'API latency p95', detail: `${number(apiP95Value, 2)} ms`, state: 'Performance', tone: 'selection' },
      ],
      actions: [
        { label: 'Open pipeline', href: '/app/pipeline', tone: 'primary' },
        { label: 'Open environment', href: '/app/environment', tone: 'secondary' },
      ],
    });
    return () => useOperatorStore.getState().setDock(null);
  }, [activeReceivers, apiP95Value, current.avg_store_latency_ms, current.last_store_age_s, current.positions_per_minute, current.process_rss_mb, current.signals_per_minute, failedSolves, metrics?.sample_count, range, solveSuccess]);

  const counters: StatItem[] = [
    { label: 'Observations / min', value: number(current.signals_per_minute), icon: Activity, visualization: chartData.length ? <Sparkline data={chartData} dataKey="signals_per_minute" color="#5b9cff" /> : undefined },
    { label: 'Positions / min', value: number(current.positions_per_minute, 1), icon: Gauge, visualization: chartData.length ? <Sparkline data={chartData} dataKey="positions_per_minute" color="#4bb6a3" /> : undefined },
    { label: 'Solve success', value: `${number(solveSuccess, 1)}%`, tone: solveSuccess >= 99 ? 'healthy' : solveSuccess >= 95 ? 'attention' : 'failure', icon: Gauge, visualization: chartData.length ? <Sparkline data={chartData} dataKey="solve_success_percent" color="#4fd18b" /> : undefined },
    { label: 'Active receivers', value: number(activeReceivers), tone: activeReceivers >= 4 ? 'healthy' : 'failure', icon: RadioTower, visualization: chartData.length ? <Sparkline data={chartData} dataKey="active_receivers" color="#9b8cf4" /> : undefined },
    { label: 'Process memory', value: `${number(current.process_rss_mb, 1)} MB`, icon: MemoryStick, visualization: chartData.length ? <Sparkline data={chartData} dataKey="process_rss_mb" color="#c7a85b" /> : undefined },
  ];

  const activityRail = [
    { title: 'Sampling', detail: `${number(metrics?.sample_count)} samples are retained for this workbench.`, meta: range, tone: chartData.length ? 'healthy' : 'attention' as StatusTone },
    { title: 'Failure pressure', detail: `${number(failedSolves)} failed solves and ${number(current.rejected_groups)} rejected groups in the latest snapshot.`, meta: failedSolves ? 'Review' : 'Clear', tone: failedSolves ? 'attention' : 'healthy' as StatusTone },
    { title: 'Availability artifact', detail: `${number((reliabilityMetrics as Record<string, JsonValue> | null)?.api_availability_percent, 2)}% API availability in the latest reliability evidence.`, meta: 'Reliability', tone: 'trust' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      <WorkspaceHeader eyebrow="Operate" title="Observability workbench" description="Metrics are organized around primary analysis surfaces: throughput, latency, resource envelope, and failure pressure instead of a generic chart grid." status={<StatusChip label={chartData.length ? 'Sampling' : 'Waiting'} tone={chartData.length ? 'healthy' : 'attention'} />} actions={<SegmentedControl label="Metrics time range" value={range} options={rangeOptions} onValueChange={setRange} className="bg-graphite" />} rail={<SignalMarquee items={[{ label: 'Solve success', value: `${number(solveSuccess, 1)}%`, tone: solveSuccess >= 99 ? 'healthy' : solveSuccess >= 95 ? 'attention' : 'failure' }, { label: 'Active receivers', value: number(activeReceivers), tone: activeReceivers >= 4 ? 'healthy' : 'failure' }, { label: 'Failed solves', value: number(failedSolves), tone: failedSolves ? 'attention' : 'healthy' }, { label: 'Range', value: range, tone: 'selection' }]} />} />

      <StatStrip items={counters} layout="five" />

      <WorkspaceSplit
        secondaryWidth="380px"
        primary={<WorkspacePanel title="Pipeline throughput" detail={`${number(current.signals_per_minute)} observations/min / ${number(current.positions_per_minute, 1)} positions/min`} tone="trust"><div className="p-3">{chartData.length ? <MultiLineChart data={chartData} series={[{ key: 'signals_per_minute', color: '#5b9cff', label: 'Observations/min' }, { key: 'positions_per_minute', color: '#4bb6a3', label: 'Positions/min' }]} height={320} ariaLabel="Observation and position throughput over time" /> : <EmptyChart height={320} />}</div></WorkspacePanel>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Workbench signals" detail="Current activity and evidence posture." tone={failedSolves ? 'attention' : 'healthy'}><ActivityRail items={activityRail} /></WorkspacePanel><WorkspacePanel title="Processing latency" detail={`${number(current.avg_store_latency_ms, 2)} ms current store latency`} tone="selection"><div className="p-3">{chartData.length ? <MultiLineChart data={chartData} series={[{ key: 'avg_ingest_latency_ms', color: '#5b9cff', label: 'Ingest ms' }, { key: 'avg_store_latency_ms', color: '#9b8cf4', label: 'Store ms' }]} height={160} ariaLabel="Ingest and store latency over time" /> : <EmptyChart height={160} />}</div></WorkspacePanel></div>}
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <WorkspacePanel title="MLAT solve quality" detail={`${number(solveSuccess, 1)}% current success`}><div className="p-3">{chartData.length ? <MultiLineChart data={chartData} series={[{ key: 'solve_success_percent', color: '#4bb6a3', label: 'Solve success %' }, { key: 'avg_uncertainty_m', color: '#c7a85b', label: 'Uncertainty m' }]} height={220} ariaLabel="Solve success and uncertainty over time" /> : <EmptyChart height={220} />}</div></WorkspacePanel>
        <WorkspacePanel title="Receiver availability" detail={`${number(activeReceivers)} active receivers`}><div className="p-3">{chartData.length ? <TrendChart data={chartData} dataKey="active_receivers" color="#9b8cf4" height={220} ariaLabel="Active receiver availability over time" /> : <EmptyChart height={220} />}</div></WorkspacePanel>
        <WorkspacePanel title="Failure pressure" detail={`${number(failedSolves)} failed solves / ${number(current.rejected_groups)} rejected groups`}><div className="p-3">{chartData.length ? <MultiLineChart data={chartData} series={[{ key: 'failed_solves', color: '#ef6b72', label: 'Failed solves' }, { key: 'rejected_groups', color: '#e6c45d', label: 'Rejected groups' }]} height={220} ariaLabel="Failed solves and rejected groups over time" /> : <EmptyChart height={220} />}</div></WorkspacePanel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <WorkspacePanel title="Resource envelope" detail="Memory pressure, position freshness, and store-latency distribution.">
          <div className="grid gap-px bg-line md:grid-cols-3"><div className="bg-graphite p-3"><p className="px-2 pt-1 text-[11px] font-semibold text-ink-secondary">Process memory</p>{chartData.length ? <TrendChart data={chartData} dataKey="process_rss_mb" color="#c7a85b" unit=" MB" height={180} ariaLabel="Process memory over time" /> : <EmptyChart height={180} />}</div><div className="bg-graphite p-3"><p className="px-2 pt-1 text-[11px] font-semibold text-ink-secondary">Position age</p>{chartData.length ? <TrendChart data={chartData} dataKey="last_store_age_s" color="#5b9cff" unit=" s" height={180} ariaLabel="Latest position age over time" /> : <EmptyChart height={180} />}</div><div className="bg-graphite p-3"><p className="px-2 pt-1 text-[11px] font-semibold text-ink-secondary">Store distribution</p>{latencyDistribution.length ? <DistributionChart data={latencyDistribution} dataKey="samples" color="#4bb6a3" height={180} ariaLabel="Store latency sample distribution" /> : <EmptyChart height={180} />}</div></div>
        </WorkspacePanel>

        <WorkspacePanel title="Service objectives" detail="Latest verified performance and reliability evidence.">
          <div className="divide-y divide-line">
            {[{ icon: Clock3, label: 'API latency p95', value: `${number(apiP95Value, 2)} ms`, detail: 'Latest bounded performance artifact.', tone: 'selection' as StatusTone }, { icon: ServerCog, label: 'API availability', value: `${number((reliabilityMetrics as Record<string, JsonValue> | null)?.api_availability_percent, 2)}%`, detail: 'Availability reported by reliability evidence.', tone: 'healthy' as StatusTone }, { icon: RadioTower, label: 'Receiver uptime', value: `${number((reliabilityMetrics as Record<string, JsonValue> | null)?.receiver_availability_percent, 2)}%`, detail: 'Receiver availability in the latest evidence window.', tone: 'healthy' as StatusTone }, { icon: Cpu, label: 'CPU telemetry', value: 'Not emitted', detail: 'Processor CPU sampling is not exposed by the evidence API.', tone: 'attention' as StatusTone }].map((row) => { const Icon = row.icon; return <div key={row.label} className="flex items-start gap-3 px-4 py-3.5"><Icon className="mt-0.5 size-4 text-ink-quiet" /><div className="min-w-0 flex-1"><p className="text-xs font-semibold text-ink">{row.label}</p><p className="mt-1 text-[11px] leading-4 text-ink-quiet">{row.detail}</p></div><div className="text-right"><strong className="text-xs font-semibold text-ink-secondary tabular-nums">{row.value}</strong><div className="mt-1"><StatusChip label={row.tone === 'healthy' ? 'On target' : row.tone === 'selection' ? 'Observed' : 'Gap'} tone={row.tone} /></div></div></div>; })}
          </div>
        </WorkspacePanel>
      </section>
    </div>
  );
}
