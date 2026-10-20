import { Archive, CheckCircle2, Crosshair, FileJson2, Gauge, Plane, RadioTower, ShieldX, Target } from 'lucide-react';
import { ComparisonBarChart } from '@/components/lazy-charts';
import { SignalMarquee, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { DataNotice } from '@/components/ui/data-notice';
import { buttonVariants } from '@/components/ui/button';
import { StatStrip, type StatItem } from '@/components/ui/stat-strip';
import { StatusChip } from '@/components/ui/status-chip';
import { number, percent } from '@/lib/format';
import { MissionChallenge } from '@/components/missions';
import type { SolverBenchmarkMetricSummary, SolverBenchmarkReport } from '@/lib/types';

function accuracyRow(label: string, metric: SolverBenchmarkMetricSummary | null) {
  return {
    label,
    median: Number(metric?.median ?? 0),
    p95: Number(metric?.p95 ?? 0),
  };
}

function meters(value: unknown, digits = 1) {
  return `${number(value, digits)} m`;
}

export function SolverBenchmarkPage({ report, error }: { report: SolverBenchmarkReport | null; error: string | null }) {
  if (!report) {
    return (
      <div className="space-y-4">
        <WorkspaceHeader
          title="Historical solver accuracy"
          description="The pinned solver benchmark is unavailable. Runtime metrics and Registry evidence remain separate and can still be inspected."
          status={<StatusChip label="Unavailable" tone="failure" />}
        />
        <DataNotice title="Solver benchmark unavailable" detail="No valid compact solver report was returned by the evidence API." technicalDetail={error ?? undefined} />
      </div>
    );
  }

  const dataset = report.compact_dataset;
  const counts = dataset.event_counts;
  const example = report.published_event;
  const control = report.synthetic_control;
  const solveRate = dataset.solve_rate;
  const solvedWidth = `${Math.max(0, Math.min(100, solveRate * 100))}%`;
  const residual = dataset.residual_m;
  const successfulIterations = dataset.iterations?.successful;
  const failureCategories = Object.entries(dataset.failure_categories ?? {});
  const accuracyRows = [
    accuracyRow('Horizontal', dataset.accuracy_m.horizontal),
    accuracyRow('Vertical', dataset.accuracy_m.vertical),
    accuracyRow('3D', dataset.accuracy_m.three_dimensional),
  ];
  const stats: StatItem[] = [
    { label: 'Data source', value: 'Historical', detail: 'Pinned MPyC v0.11 sample', icon: Archive, tone: 'replay' },
    { label: 'Events tested', value: number(counts.total), detail: 'Five receivers per event', icon: Crosshair, tone: 'selection' },
    { label: 'Solve rate', value: percent(solveRate, 1), detail: `${number(counts.solved)} solved, ${number(counts.unsolved)} rejected`, icon: Gauge, tone: 'attention' },
    { label: 'Median horizontal', value: meters(dataset.accuracy_m.horizontal?.median), detail: `p95 ${meters(dataset.accuracy_m.horizontal?.p95)}`, icon: Target, tone: 'trust' },
    { label: 'Median 3D', value: meters(dataset.accuracy_m.three_dimensional?.median), detail: `p95 ${meters(dataset.accuracy_m.three_dimensional?.p95)}`, icon: Plane, tone: 'attention' },
  ];

  return (
    <div className="space-y-4">
      {error ? <DataNotice title="Benchmark refresh warning" detail="The saved benchmark remains visible, but the latest request reported a problem." technicalDetail={error} tone="attention" /> : null}

      <WorkspaceHeader
        title="Historical solver accuracy"
        description="The unchanged numerical solver is compared with aircraft-reported reference positions from a pinned public recording. This page does not describe current aircraft activity."
        status={<><StatusChip label="Historical recording" tone="replay" /><StatusChip label="Solver only" tone="selection" /><StatusChip label="Not live" tone="neutral" /></>}
        actions={<a href="/api/evidence/solver-benchmark/latest?include_events=true" target="_blank" rel="noreferrer" className={buttonVariants({ variant: 'secondary', size: 'sm' })}><FileJson2 className="size-3.5" />Open full JSON</a>}
        rail={<SignalMarquee items={[
          { label: 'Synthetic control', value: control.acceptance?.passed ? 'PASS' : 'FAIL', tone: control.acceptance?.passed ? 'healthy' : 'failure' },
          { label: 'Published example', value: example.event_id, tone: 'trust' },
          { label: 'Sample', value: `${number(counts.total)} events`, tone: 'selection' },
          { label: 'Claim scope', value: 'Solver only', tone: 'replay' },
        ]} />}
      />

      <StatStrip items={stats} layout="five" />
      {!error ? <MissionChallenge kind="benchmark" /> : null}

      <WorkspaceSplit
        secondaryWidth="360px"
        primary={
          <WorkspacePanel title="Accuracy distribution" detail={`Median and 95th-percentile error among the ${number(counts.solved)} events that produced a solution.`} tone="trust">
            <div className="p-3 sm:p-4">
              <ComparisonBarChart
                data={accuracyRows}
                series={[
                  { key: 'median', label: 'Median', color: '#5b9cff' },
                  { key: 'p95', label: '95th percentile', color: '#e6c45d' },
                ]}
                unit=" m"
                height={280}
                ariaLabel="Median and 95th-percentile horizontal, vertical, and three-dimensional position error in metres"
              />
            </div>
          </WorkspacePanel>
        }
        secondary={
          <WorkspacePanel title="Solve outcome" detail="Every source event remains in the denominator." tone="attention">
            <div className="p-5">
              <div className="flex items-end justify-between gap-4">
                <div><p className="text-2xl font-semibold text-ink tabular-nums">{percent(solveRate, 1)}</p><p className="mt-1 text-xs text-ink-quiet">of events produced a position</p></div>
                <StatusChip label={`${number(counts.unsolved)} rejected`} tone="attention" />
              </div>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-failure/25" role="img" aria-label={`${number(counts.solved)} of ${number(counts.total)} events solved`}>
                <div className="h-full rounded-full bg-healthy" style={{ width: solvedWidth }} />
              </div>
              <dl className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-md bg-line">
                <div className="bg-graphite-raised px-3 py-3"><dt className="text-[11px] text-ink-quiet">Solved</dt><dd className="mt-1 text-lg font-semibold text-healthy tabular-nums">{number(counts.solved)}</dd></div>
                <div className="bg-graphite-raised px-3 py-3"><dt className="text-[11px] text-ink-quiet">Rejected</dt><dd className="mt-1 text-lg font-semibold text-attention tabular-nums">{number(counts.unsolved)}</dd></div>
              </dl>
              <p className="mt-4 text-xs leading-5 text-ink-secondary">Accuracy statistics use solved events only. The solve rate shows the rejected events separately so they are not hidden.</p>
            </div>
          </WorkspacePanel>
        }
      />

      <WorkspaceSplit
        secondaryWidth="400px"
        primary={
          <WorkspacePanel title="Benchmark checks" detail="A clean control verifies the benchmark path; one recorded event makes the result inspectable.">
            <div className="divide-y divide-line">
              <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 gap-3"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-healthy" /><div><p className="text-sm font-semibold text-ink">Synthetic exact-propagation control</p><p className="mt-1 text-xs leading-5 text-ink-secondary">Known receiver geometry and ideal arrival times test the numerical path without measurement noise.</p></div></div>
                <div className="flex shrink-0 items-center gap-3"><strong className="text-sm text-ink tabular-nums">{meters(control.errors_m?.three_dimensional, 2)} 3D</strong><StatusChip label={control.acceptance?.passed ? 'PASS' : 'FAIL'} tone={control.acceptance?.passed ? 'healthy' : 'failure'} /></div>
              </div>
              <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 gap-3"><Archive className="mt-0.5 size-4 shrink-0 text-replay" /><div><p className="text-sm font-semibold text-ink">Published event {example.event_id}</p><p className="mt-1 text-xs leading-5 text-ink-secondary">Recorded timestamps from five geographically distinct receivers are compared with the published aircraft position.</p></div></div>
                <div className="shrink-0 text-left sm:text-right"><strong className="block text-sm text-ink tabular-nums">{meters(example.errors_m?.horizontal, 2)} horizontal</strong><span className="mt-1 block text-xs text-ink-quiet">{meters(example.errors_m?.three_dimensional, 2)} 3D</span></div>
              </div>
            </div>
          </WorkspacePanel>
        }
        secondary={
          <WorkspacePanel title="What this measures" detail="The boundary of the evidence shown here." tone="selection">
            <ol className="divide-y divide-line">
              {[
                ['1', 'Pre-grouped observations', 'Five dataset-local receiver timestamps are already associated with one aircraft message.'],
                ['2', 'Numerical MLAT solve', 'The existing robust solver estimates latitude, longitude, and altitude.'],
                ['3', 'Reference comparison', 'The estimate is compared with the aircraft-reported position in the recording.'],
              ].map(([step, title, detail]) => <li key={step} className="flex gap-3 px-4 py-3"><span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-signal-blue/10 text-[11px] font-semibold text-signal-blue">{step}</span><div><p className="text-xs font-semibold text-ink">{title}</p><p className="mt-1 text-xs leading-5 text-ink-secondary">{detail}</p></div></li>)}
            </ol>
          </WorkspacePanel>
        }
      />

      <WorkspacePanel title="Residuals and rejected events" detail="Model fit and rejection reasons are reported separately from position error.">
        <div className="grid gap-4 p-4 text-sm text-ink-secondary sm:grid-cols-2">
          <div>
            {residual
              ? <p>Residual: median {meters(residual.median, 2)}, p95 {meters(residual.p95, 2)}.</p>
              : <p>Residual summary was not included in this report version.</p>}
            {successfulIterations
              ? <p className="mt-2">Best-candidate iterations: median {number(successfulIterations.median)}, p95 {number(successfulIterations.p95, 1)}.</p>
              : <p className="mt-2">Iteration summary was not included in this report version.</p>}
            {dataset.iterations?.definition ? <p className="mt-2 text-xs leading-5">{dataset.iterations.definition}</p> : null}
          </div>
          <div>
            {failureCategories.length
              ? failureCategories.map(([reason, count]) => <p key={reason}>{number(count)} rejected: {reason.replaceAll('_', ' ')}.</p>)
              : <p>Rejection categories were not included in this report version.</p>}
            <p className="mt-2">Maximum 3D error among solved events: {meters(dataset.accuracy_m.three_dimensional?.maximum, 1)}.</p>
            <p className="mt-2 text-xs leading-5">A small residual does not prove a small position error. Inspect the full report and replay before interpreting accuracy.</p>
          </div>
        </div>
      </WorkspacePanel>

      <WorkspacePanel title="Inspectable event geometry" detail={`Historical event ${example.event_id}. Dataset receiver identifiers are not CKB Registry identities.`} tone="replay">
        <div className="grid gap-px bg-line lg:grid-cols-[320px_minmax(0,1fr)]">
          <div className="bg-graphite p-4">
            <div className="flex items-center gap-2"><Plane className="size-4 text-signal-blue" /><h4 className="text-xs font-semibold text-ink">Aircraft reference position</h4></div>
            <dl className="mt-4 space-y-3">
              <div className="flex justify-between gap-4"><dt className="text-xs text-ink-quiet">Latitude</dt><dd className="font-mono text-xs text-ink-secondary">{number(example.ground_truth.latitude, 6)}°</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-xs text-ink-quiet">Longitude</dt><dd className="font-mono text-xs text-ink-secondary">{number(example.ground_truth.longitude, 6)}°</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-xs text-ink-quiet">Altitude</dt><dd className="font-mono text-xs text-ink-secondary">{meters(example.ground_truth.altitude_m, 2)}</dd></div>
            </dl>
            <p className="mt-5 text-xs leading-5 text-ink-secondary">This reference is aircraft-reported ADS-B data, not an independently surveyed position.</p>
          </div>
          <div className="min-w-0 bg-graphite">
            <div className="flex items-center gap-2 border-b border-line px-4 py-3"><RadioTower className="size-4 text-trust-cyan" /><h4 className="text-xs font-semibold text-ink">Five-receiver geometry</h4></div>
            <div className="overflow-x-auto outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue" role="region" aria-label="Receiver geometry table, horizontally scrollable" tabIndex={0}>
              <table className="w-full min-w-[620px] text-left text-xs">
                <thead className="bg-graphite-raised text-ink-quiet"><tr><th className="px-4 py-2.5 font-semibold">Dataset receiver</th><th className="px-4 py-2.5 font-semibold">Latitude</th><th className="px-4 py-2.5 font-semibold">Longitude</th><th className="px-4 py-2.5 font-semibold">Altitude</th></tr></thead>
                <tbody className="divide-y divide-line">{example.receiver_geometry.map((receiver) => <tr key={receiver.receiver_id}><td className="px-4 py-3 font-mono text-ink">{receiver.receiver_id}</td><td className="px-4 py-3 font-mono text-ink-secondary">{number(receiver.latitude, 6)}°</td><td className="px-4 py-3 font-mono text-ink-secondary">{number(receiver.longitude, 6)}°</td><td className="px-4 py-3 font-mono text-ink-secondary">{meters(receiver.altitude_m, 2)}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        </div>
      </WorkspacePanel>

      <WorkspacePanel title="Interpretation boundary" detail="Use the result for solver regression, not as proof of field deployment." tone="attention">
        <div className="grid gap-px bg-line md:grid-cols-2">
          <div className="bg-graphite p-4">
            <div className="flex items-center gap-2"><CheckCircle2 className="size-4 text-healthy" /><h4 className="text-sm font-semibold text-ink">What this measures</h4></div>
            <ul className="mt-3 space-y-2 text-xs leading-5 text-ink-secondary"><li>Numerical solver behavior across 362 historical five-receiver events.</li><li>A sub-metre exact-propagation control.</li><li>Horizontal, vertical, and 3D error against aircraft-reported reference positions.</li></ul>
          </div>
          <div className="bg-graphite p-4">
            <div className="flex items-center gap-2"><ShieldX className="size-4 text-attention" /><h4 className="text-sm font-semibold text-ink">What this does not prove</h4></div>
            <ul className="mt-3 space-y-2 text-xs leading-5 text-ink-secondary"><li>Live receiver operation or complete production-pipeline accuracy.</li><li>CKB Registry ownership, physical receiver existence, or truthful coordinates.</li><li>Per-observation clock attestation, feed honesty, or aviation-safety suitability.</li></ul>
          </div>
        </div>
        <div className="flex flex-col gap-3 border-t border-line px-4 py-3 text-xs text-ink-quiet sm:flex-row sm:items-center sm:justify-between"><p>Source: MPyC v0.11 example derived from LocaRDS, CC BY-SA 4.0.</p><a href={dataset.source.original_dataset} target="_blank" rel="noreferrer" className="w-fit rounded-sm font-medium text-signal-blue outline-none hover:text-[#8db9ff] focus-visible:ring-2 focus-visible:ring-signal-blue">Open source dataset</a></div>
      </WorkspacePanel>
    </div>
  );
}
