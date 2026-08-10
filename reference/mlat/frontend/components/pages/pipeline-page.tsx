'use client';

import { AlertTriangle, ArrowUpRight, Check, FileJson, Lightbulb, Wrench } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ActivityRail, IssueList, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { StatusChip } from '@/components/ui/status-chip';
import { number, titleCase } from '@/lib/format';
import { useOperatorStore } from '@/lib/operator-store';
import type { MetricsData, PipelineData, PipelineStageData, StatusTone } from '@/lib/types';
import { ProgressBar } from '@/components/ui/progress-bar';

const actions: Record<string, string> = {
  registry: 'Verify the Registry V2 type hash, RPC connectivity, and live receiver discovery.',
  ingest: 'Confirm receiver endpoints, transport credentials, and recent signal timestamps.',
  clock: 'Restore receiver synchronization and keep clock uncertainty within the configured limit.',
  correlation: 'Inspect rejected groups and confirm at least four synchronized observations per transmission.',
  solver: 'Review receiver geometry, residual error, and failed solve counters.',
  storage: 'Check database reachability, write latency, and the newest persisted position.',
  api: 'Verify API health, response latency, and frontend origin configuration.',
  dashboard: 'Refresh the console after upstream stages pass and confirm the latest position is visible.',
};

function stageTone(status: string): StatusTone {
  if (status === 'pass') return 'healthy';
  if (status === 'blocked' || status === 'fail') return 'failure';
  return 'attention';
}

export function PipelinePage({ pipeline, metrics }: { pipeline: PipelineData | null; metrics: MetricsData | null }) {
  const stages = pipeline?.stages ?? [];
  const blockers = pipeline?.blockers ?? [];
  const passed = stages.filter((stage) => stage.status === 'pass').length;
  const progress = stages.length ? passed / stages.length * 100 : 0;
  const [selectedStageId, setSelectedStageId] = useState<string | null>(stages.find((stage) => stage.status !== 'pass')?.id ?? stages[0]?.id ?? null);
  const selectedStage = stages.find((stage) => stage.id === selectedStageId) ?? stages[0] ?? null;
  const liveReady = Boolean(pipeline?.live_evidence_ready);
  const operational = Boolean(pipeline?.pipeline_operational);
  const current = metrics?.current ?? {};
  const stateLabel = liveReady ? 'Evidence ready' : operational && blockers.length ? 'Processing active, evidence blocked' : operational ? 'Pipeline processing' : 'Pipeline blocked';
  const stateTone: StatusTone = liveReady ? 'healthy' : operational ? 'attention' : 'failure';

  useEffect(() => {
    setSelectedStageId((currentId) => stages.find((stage) => stage.id === currentId)?.id ?? stages.find((stage) => stage.status !== 'pass')?.id ?? stages[0]?.id ?? null);
  }, [stages]);

  const issueList = blockers.length ? blockers.map((blocker) => ({ title: 'Pipeline blocker', detail: blocker, tone: 'failure' as StatusTone, href: '/app/pipeline', meta: 'Immediate' })) : stages.filter((stage) => stage.status !== 'pass').map((stage) => ({ title: stage.label, detail: stage.detail || 'Stage requires review.', tone: stageTone(stage.status), href: '/app/pipeline', meta: titleCase(stage.status) }));
  const proofLinks = useMemo(() => [
    { label: 'Pipeline state', detail: 'Current stage evidence', href: '/api/pipeline' },
    { label: 'Bounded metrics', detail: `${number(metrics?.sample_count)} samples`, href: '/api/evidence/metrics' },
    { label: 'Benchmark report', detail: String(pipeline?.benchmark?.status ?? 'Not published'), href: '/api/benchmark/latest' },
  ], [metrics?.sample_count, pipeline?.benchmark?.status]);

  const stageTimeline = stages.map((stage) => ({ title: stage.label, detail: stage.detail || `${stage.label} did not report a current explanation.`, tone: stage.id === selectedStage?.id ? 'selection' as StatusTone : stageTone(stage.status), meta: titleCase(stage.status) }));

  useEffect(() => {
    if (!selectedStage) return;
    useOperatorStore.getState().setInvestigationContext({ focus: selectedStage.id, timeRange: 'pipeline' });
    useOperatorStore.getState().setDock({
      entityType: 'pipeline',
      title: selectedStage.label,
      subtitle: 'Pinned from the pipeline debugger.',
      statusLabel: titleCase(selectedStage.status),
      statusTone: stageTone(selectedStage.status),
      facts: [
        { label: 'Progress', value: `${passed}/${stages.length}` },
        { label: 'Live evidence', value: liveReady ? 'Ready' : 'Blocked', tone: liveReady ? 'healthy' : 'attention' },
        { label: 'Blockers', value: number(blockers.length), tone: blockers.length ? 'failure' : 'healthy' },
        { label: 'Solve success', value: `${number(current.solve_success_percent, 1)}%` },
      ],
      timeline: stageTimeline,
      evidence: Object.entries(selectedStage.metrics ?? {}).slice(0, 4).map(([key, value]) => ({ title: titleCase(key), detail: String(value), state: 'Metric', tone: stageTone(selectedStage.status) })),
      actions: [
        { label: 'Open metrics', href: '/app/metrics', tone: 'secondary' },
        { label: 'Open environment', href: '/app/environment', tone: 'primary' },
      ],
    });
    return () => useOperatorStore.getState().setDock(null);
  }, [blockers.length, current.solve_success_percent, liveReady, passed, selectedStage, stageTimeline, stages.length]);

  const activityRail = [
    { title: 'Pipeline readiness', detail: `${Math.round(progress)}% of tracked stages currently pass.`, meta: `${passed}/${stages.length}`, tone: stateTone },
    { title: 'Current blocker count', detail: blockers.length ? `${blockers.length} blocking conditions require operator action.` : 'No blockers are currently reported.', meta: blockers.length ? 'Open' : 'Clear', tone: blockers.length ? 'failure' : 'healthy' as StatusTone },
    { title: 'Evidence posture', detail: liveReady ? 'Live evidence output is ready for publication.' : 'Live evidence remains gated by current stage state.', meta: liveReady ? 'Ready' : 'Blocked', tone: liveReady ? 'trust' : 'attention' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      <WorkspaceHeader eyebrow="Operate" title="Pipeline debugger" description="Stages, blockers, machine-readable proof surfaces, and operator recovery guidance are combined into one interactive failure workspace." status={<StatusChip label={stateLabel} tone={stateTone} />} rail={<SignalMarquee items={[{ label: 'Passing stages', value: `${passed}/${stages.length}`, tone: stateTone }, { label: 'Blockers', value: number(blockers.length), tone: blockers.length ? 'failure' : 'healthy' }, { label: 'Evidence', value: liveReady ? 'Ready' : 'Blocked', tone: liveReady ? 'trust' : 'attention' }, { label: 'Solve success', value: `${number(current.solve_success_percent, 1)}%`, tone: Number(current.solve_success_percent ?? 0) >= 95 ? 'healthy' : 'attention' }]} />} />

      <WorkspaceSplit
        secondaryWidth="340px"
        primary={<div className="space-y-4">
          <WorkspacePanel title="Readiness queue" detail="Ranked blockers and failing stages." tone={issueList[0]?.tone ?? 'healthy'}>
            <IssueList items={issueList.length ? issueList : [{ title: 'Pipeline clear', detail: 'All tracked stages currently report passing state.', tone: 'healthy', href: '/app/metrics' }]} />
          </WorkspacePanel>

          <WorkspacePanel title="Stage timeline" detail="Select a stage to inspect metrics and recommended action." tone="selection">
            <Timeline items={stageTimeline.map((item) => ({ ...item, detail: <button type="button" onClick={() => setSelectedStageId(stages.find((stage) => stage.label === item.title)?.id ?? null)} className="text-left underline-offset-2 hover:underline">{item.detail}</button> }))} />
          </WorkspacePanel>

          <WorkspacePanel title={selectedStage ? `${selectedStage.label} details` : 'Stage details'} detail={selectedStage?.detail || 'Select a stage to inspect current evidence.'} tone={selectedStage ? stageTone(selectedStage.status) : 'neutral'}>
            {selectedStage ? <div className="grid gap-px bg-line md:grid-cols-3"><div className="bg-graphite p-4"><div className="flex items-center gap-2 text-[11px] font-semibold text-ink-secondary"><AlertTriangle className="size-3.5" />What happened</div><p className="mt-2 text-xs leading-5 text-ink-quiet">{selectedStage.detail || `${selectedStage.label} did not report a current explanation.`}</p></div><div className="bg-graphite p-4"><div className="flex items-center gap-2 text-[11px] font-semibold text-ink-secondary"><FileJson className="size-3.5" />Evidence</div><dl className="mt-2 space-y-1.5">{Object.entries(selectedStage.metrics ?? {}).slice(0, 5).map(([key, value]) => <div key={key} className="flex items-center justify-between gap-3"><dt className="truncate text-[11px] text-ink-quiet">{titleCase(key)}</dt><dd className="max-w-[50%] truncate font-mono text-[11px] text-ink-secondary">{String(value)}</dd></div>)}</dl>{!Object.keys(selectedStage.metrics ?? {}).length ? <p className="mt-2 text-xs text-ink-quiet">No stage metrics were attached.</p> : null}</div><div className="bg-graphite p-4"><div className="flex items-center gap-2 text-[11px] font-semibold text-ink-secondary"><Wrench className="size-3.5" />Operator action</div><p className="mt-2 text-xs leading-5 text-ink-quiet">{actions[selectedStage.id] ?? 'Inspect the attached evidence and restore the upstream dependency.'}</p></div></div> : <div className="grid h-40 place-items-center text-xs text-ink-quiet">Pipeline state is unavailable.</div>}
          </WorkspacePanel>
        </div>}
        secondary={<div className="space-y-4">
          <WorkspacePanel title="Debugger status" detail="Current pipeline operating posture." tone={stateTone}>
            <div className="p-4"><div className="mb-2 flex items-center justify-between text-[11px] text-ink-quiet"><span>Readiness</span><span className="font-semibold text-ink-secondary">{Math.round(progress)}%</span></div><ProgressBar value={progress} tone={stateTone} label="Pipeline readiness" /></div>
            <ActivityRail items={activityRail} />
          </WorkspacePanel>

          <WorkspacePanel title="Proof surfaces" detail="Machine-readable evidence and latest bounded metrics." tone="trust">
            <div>{proofLinks.map((link) => <a key={link.label} href={link.href} target="_blank" rel="noreferrer" className="flex items-center gap-3 border-b border-line px-4 py-3 outline-none transition-colors duration-standard last:border-0 hover:bg-graphite-hover/55 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue"><FileJson className="size-4 text-ink-quiet" /><div className="min-w-0 flex-1"><p className="text-xs font-semibold text-ink">{link.label}</p><p className="mt-0.5 truncate text-[11px] text-ink-quiet">{link.detail}</p></div><ArrowUpRight className="size-3.5 text-ink-quiet" /></a>)}</div>
            <div className="border-t border-line p-4"><div className="flex items-start gap-2 text-[11px] leading-5 text-ink-quiet"><Lightbulb className="mt-0.5 size-3.5 shrink-0 text-attention" />Resolve upstream stages before retrying proof generation or evidence publication.</div></div>
          </WorkspacePanel>
        </div>}
      />
    </div>
  );
}
