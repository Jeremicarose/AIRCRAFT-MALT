'use client';

import { Cable, Database, FileCheck2, MonitorDot, RadioTower, Satellite, Server, ShieldCheck, Workflow } from 'lucide-react';
import { useEffect } from 'react';
import { ActivityRail, SignalMarquee, Timeline, WorkspaceHeader, WorkspacePanel, WorkspaceSplit } from '@/components/operations-ui';
import { titleCase, truncateMiddle } from '@/lib/format';
import type { HealthData, ModeData, ReadinessData, StatusTone } from '@/lib/types';
import { useOperatorStore } from '@/lib/operator-store';
import { StatusChip, StatusIcon } from '@/components/ui/status-chip';

function ConfigurationRow({ icon: Icon, label, value, detail, tone = 'neutral', mono = false }: { icon: typeof Server; label: string; value: string; detail: string; tone?: StatusTone; mono?: boolean }) {
  return <div className="grid gap-3 border-b border-line px-4 py-3 last:border-0 sm:grid-cols-[28px_minmax(0,1fr)_auto] sm:items-center"><span className="flex size-7 items-center justify-center rounded-md bg-graphite-raised"><Icon className="size-3.5 text-ink-quiet" /></span><div><p className="text-xs font-semibold text-ink">{label}</p><p className="mt-1 text-pretty text-[11px] leading-4 text-ink-quiet">{detail}</p></div><div className="flex items-center gap-2 pl-10 sm:pl-0"><span className={mono ? 'max-w-[220px] truncate font-mono text-xs text-ink-secondary' : 'text-xs font-medium text-ink-secondary'} title={value}>{value}</span><StatusIcon tone={tone} label={`${label}: ${tone}`} className="size-6" /></div></div>;
}

export function EnvironmentPage({ modeData, health, readiness }: { modeData: ModeData | null; health: HealthData | null; readiness: ReadinessData | null }) {
  const isReplay = Boolean(modeData?.demo_mode || modeData?.simulation_mode || modeData?.synthetic_feed_mode);
  const registryHash = modeData?.receiver_registry_type_hash;
  const runtimeReady = modeData?.runtime_status === 'active';
  const readinessTimeline = [
    { title: 'Runtime initialized', detail: runtimeReady ? 'Processor is active and reporting telemetry.' : 'Processor runtime is not active.', tone: runtimeReady ? 'healthy' as StatusTone : 'failure' as StatusTone },
    { title: 'Receiver discovery', detail: modeData?.registry_discovery_live ? 'Live Registry V2 discovery is active.' : 'Receiver discovery is not currently live.', tone: modeData?.registry_discovery_live ? 'healthy' as StatusTone : 'attention' as StatusTone },
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
        { label: 'Mode', value: isReplay ? 'Replay' : titleCase(modeData?.mode), tone: isReplay ? 'replay' : 'healthy' },
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
    { title: 'Discovery', detail: modeData?.registry_discovery_live ? 'Registry discovery is live.' : 'Registry discovery is not active.', meta: modeData?.registry_discovery_live ? 'Live' : 'Idle', tone: modeData?.registry_discovery_live ? 'trust' : 'attention' as StatusTone },
    { title: 'Evidence gates', detail: readiness?.ready ? 'Deployment currently satisfies readiness gates.' : 'One or more readiness dimensions remain incomplete.', meta: readiness?.ready ? 'Pass' : 'Review', tone: readiness?.ready ? 'healthy' : 'attention' as StatusTone },
  ];

  return (
    <div className="space-y-4">
      <WorkspaceHeader eyebrow="System" title="Topology and dependency workspace" description="Environment is now organized around deployment topology, trust boundaries, and readiness dependencies rather than a passive configuration readout." status={<StatusChip label={runtimeReady ? 'Runtime active' : 'Runtime offline'} tone={runtimeReady ? 'healthy' : 'failure'} />} rail={<SignalMarquee items={[{ label: 'Runtime', value: runtimeReady ? 'Active' : 'Offline', tone: runtimeReady ? 'healthy' : 'failure' }, { label: 'Discovery', value: modeData?.registry_discovery_live ? 'Live' : 'Idle', tone: modeData?.registry_discovery_live ? 'trust' : 'attention' }, { label: 'Evidence', value: readiness?.ready ? 'Ready' : 'Review', tone: readiness?.ready ? 'healthy' : 'attention' }, { label: 'Mode', value: isReplay ? 'Replay' : titleCase(modeData?.mode), tone: isReplay ? 'replay' : 'selection' }]} />} />

      <WorkspaceSplit
        secondaryWidth="380px"
        primary={<div className="space-y-4"><WorkspacePanel title="Deployment configuration" detail="Runtime, connectivity, identity, and evidence controls." tone={runtimeReady ? 'healthy' : 'failure'}><ConfigurationRow icon={Server} label="Runtime" value={titleCase(modeData?.runtime_status)} detail="Processor status reported by the control plane." tone={runtimeReady ? 'healthy' : 'failure'} /><ConfigurationRow icon={Satellite} label="Operating mode" value={isReplay ? 'Replay' : titleCase(modeData?.mode)} detail="Replay remains separate from live output and evidence." tone={isReplay ? 'replay' : modeData?.mode === 'live' ? 'healthy' : 'attention'} /><ConfigurationRow icon={Cable} label="Receiver transport" value={titleCase(modeData?.configured_transport)} detail="Configured source acquisition transport." tone={modeData?.configured_transport ? 'healthy' : 'failure'} /><ConfigurationRow icon={Database} label="Registry type hash" value={truncateMiddle(registryHash, 12, 10)} detail="CKB type hash used to discover receiver identities." tone={registryHash ? 'trust' : 'failure'} mono /><ConfigurationRow icon={ShieldCheck} label="Production enforcement" value={modeData?.strict_production_mode ? 'Strict' : 'Standard'} detail="Strict mode rejects synthetic fallbacks and incomplete trust." tone={modeData?.strict_production_mode ? 'healthy' : 'neutral'} /><ConfigurationRow icon={FileCheck2} label="Evidence output" value={modeData?.benchmarkable_output ? 'Benchmarkable' : 'Constrained'} detail="Whether current output may support benchmark interpretation." tone={modeData?.benchmarkable_output ? 'healthy' : 'attention'} /></WorkspacePanel><WorkspacePanel title="Dependency topology" detail="Receiver transport through evidence publication." tone="trust"><div className="grid gap-px bg-line md:grid-cols-5">{[{ icon: RadioTower, label: 'Receivers', detail: titleCase(modeData?.configured_transport), tone: isReplay ? 'replay' : modeData?.configured_transport ? 'healthy' : 'failure' }, { icon: Satellite, label: 'MLAT ingest', detail: runtimeReady ? 'Active' : 'Offline', tone: runtimeReady ? 'healthy' : 'failure' }, { icon: Workflow, label: 'Solver', detail: readiness?.dimensions?.quality?.ready ? 'Ready' : 'Review', tone: readiness?.dimensions?.quality?.ready ? 'healthy' : 'attention' }, { icon: FileCheck2, label: 'Evidence', detail: modeData?.benchmarkable_output ? 'Ready' : 'Constrained', tone: modeData?.benchmarkable_output ? 'healthy' : 'attention' }, { icon: MonitorDot, label: 'Console', detail: health?.status ? titleCase(health.status) : 'Connected', tone: health ? 'healthy' : 'failure' }].map((node) => { const Icon = node.icon; return <div key={node.label} className="bg-graphite px-4 py-5 text-center"><span className="mx-auto flex size-10 items-center justify-center rounded-full bg-graphite-raised"><Icon className="size-4 text-ink-secondary" /></span><p className="mt-3 text-xs font-semibold text-ink">{node.label}</p><p className="mt-1 text-[11px] text-ink-quiet">{node.detail}</p><div className="mt-3"><StatusChip label={node.tone === 'healthy' ? 'Healthy' : node.tone === 'failure' ? 'Failure' : node.tone === 'replay' ? 'Replay' : 'Review'} tone={node.tone as StatusTone} /></div></div>; })}</div></WorkspacePanel></div>}
        secondary={<div className="space-y-4"><WorkspacePanel title="Environment signals" detail="Runtime, discovery, and readiness summary." tone={runtimeReady ? 'healthy' : 'failure'}><ActivityRail items={activityRail} /></WorkspacePanel><WorkspacePanel title="Readiness timeline" detail="Current deployment progression." tone={readiness?.ready ? 'healthy' : 'attention'}><Timeline items={readinessTimeline} /></WorkspacePanel></div>}
      />
    </div>
  );
}
