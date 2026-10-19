'use client';

import Link from 'next/link';
import { useState } from 'react';
import LazyAirspaceMap from '@/components/lazy-airspace-map';
import { WorkspaceHeader, WorkspacePanel } from '@/components/operations-ui';
import { StatusChip } from '@/components/ui/status-chip';
import { DataNotice } from '@/components/ui/data-notice';
import { buttonVariants } from '@/components/ui/button';
import { number } from '@/lib/format';
import type { Position, Receiver } from '@/lib/types';

export interface ReplayEvent {
  event_id: string;
  ordinal: number;
  aircraft_dataset_id: string;
  solved: boolean;
  source_time_seconds: number;
  source_timestamp_ns: string;
  correlation_id: string;
  diagnostics: { failure_category?: string | null; residual_m?: number; iterations?: number };
  receiver_geometry?: Array<{ receiver_id: string; latitude: number; longitude: number; altitude_m: number }>;
  observations?: Array<{ receiver_id: string; timestamp_ns: string; clock_source: string }>;
  stages?: Array<{ stage: string; status: string; detail: string }>;
  position?: Position | null;
}

export interface ReplayOverview {
  configured: boolean;
  source?: string;
  timestamp_context?: string;
  limitations?: string[];
  event_count?: number;
  successful_solves?: number;
  failed_solves?: number;
  offset?: number;
  events: ReplayEvent[];
}

export function HistoricalReplayPage({ overview, selected, error }: { overview: ReplayOverview | null; selected: ReplayEvent | null; error: string | null }) {
  const [stageIndex, setStageIndex] = useState(0);
  const stages = selected?.stages ?? [];
  const stage = stages[stageIndex];
  const offset = overview?.offset ?? 0;
  const receivers: Receiver[] = (selected?.receiver_geometry ?? []).map((receiver) => ({ ...receiver, altitude: receiver.altitude_m, data_source: 'historical_replay' }));
  return <div className="space-y-4">
    <WorkspaceHeader title="Historical replay" description="Inspect real published arrival timestamps through the historical adapter, unchanged solver, storage, and API." status={<StatusChip label="HISTORICAL REPLAY" tone="replay" />} />
    {error ? <DataNotice title="Replay service unavailable" detail="Check the historical replay API and refresh this page." technicalDetail={error} /> : null}
    {!overview?.configured ? <WorkspacePanel title="Start a historical replay" detail="A separate database keeps historical results out of live operation."><div className="space-y-3 p-4 text-sm text-ink-secondary"><p>Run <code className="font-mono">./run-replay.sh</code>, then configure the frontend API URL to use that service and reload this page.</p><p>The bundled source has 362 events. It contains no original Mode-S frames, CKB identities, or measured per-observation clock uncertainty.</p></div></WorkspacePanel> : <>
      <div className="border border-line bg-graphite-raised p-4 text-sm text-ink-secondary">
        <p className="font-semibold text-ink">{overview.source}</p>
        <p className="mt-2">{number(overview.event_count)} events · {number(overview.successful_solves)} solved · {number(overview.failed_solves)} rejected</p>
        <p className="mt-2 text-xs leading-5">{overview.timestamp_context}</p>
        <p className="mt-2 text-xs leading-5">Grouping is supplied by the dataset. Live frame correlation, Registry identity, and clock qualification remain unvalidated.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(320px,1.2fr)]">
        <WorkspacePanel title="Recorded events" detail="Rejected events stay in the list. Select an event to inspect its evidence.">
          <div className="max-h-[580px] overflow-auto">
            <table className="w-full text-left text-xs"><caption className="sr-only">Historical events and solver outcomes</caption><thead className="sticky top-0 bg-graphite-raised"><tr><th className="p-3">Event</th><th className="p-3">Dataset time</th><th className="p-3">Solver</th></tr></thead><tbody className="divide-y divide-line">{overview.events.map((item) => <tr key={item.event_id} className={selected?.event_id === item.event_id ? 'bg-signal-blue/10' : ''}><td className="p-3"><Link href={`/app/replay?offset=${offset}&event=${item.event_id}`} aria-current={selected?.event_id === item.event_id ? 'true' : undefined} className="rounded-sm font-mono text-signal-blue underline underline-offset-4 focus-visible:outline-2">{item.event_id}</Link></td><td className="p-3 tabular-nums">{number(item.source_time_seconds, 3)} s</td><td className="p-3"><StatusChip label={item.solved ? 'Solved' : 'Rejected'} tone={item.solved ? 'healthy' : 'attention'} /></td></tr>)}</tbody></table>
          </div>
          <nav aria-label="Historical event pages" className="flex flex-wrap justify-between gap-2 border-t border-line p-3">
            {offset > 0 ? <Link className={buttonVariants({ variant: 'secondary', size: 'sm' })} href={`/app/replay?offset=${Math.max(0, offset-50)}`}>Previous events</Link> : <span />}
            {offset+50 < (overview.event_count ?? 0) ? <Link className={buttonVariants({ variant: 'secondary', size: 'sm' })} href={`/app/replay?offset=${offset+50}`}>Next events</Link> : null}
          </nav>
        </WorkspacePanel>
        <div className="min-w-0 space-y-4">
          {selected ? <WorkspacePanel title={`Event ${selected.event_id}`} detail={`Dataset aircraft ${selected.aircraft_dataset_id}. This identifier is not an ICAO address.`}>
            <div className="space-y-4 p-4">
              <ol aria-label="Replay processing stages" className="flex flex-wrap gap-2">{stages.map((item, index) => <li key={item.stage}><button type="button" aria-pressed={index === stageIndex} onClick={() => setStageIndex(index)} className={buttonVariants({ variant: index === stageIndex ? 'primary' : 'secondary', size: 'sm' })}>{index+1}. {item.stage.replaceAll('_', ' ')}</button></li>)}</ol>
              {stage ? <div aria-live="polite" className="min-h-24 border-y border-line py-3"><StatusChip label={stage.status} tone={stage.status === 'REJECTED' ? 'attention' : 'replay'} /><p className="mt-2 text-sm leading-6 text-ink-secondary">{stage.detail}</p></div> : null}
              <div className="flex justify-between gap-2"><button type="button" disabled={stageIndex === 0} className={buttonVariants({ variant: 'secondary', size: 'sm' })} onClick={() => setStageIndex(stageIndex-1)}>Previous stage</button><button type="button" disabled={stageIndex >= stages.length-1} className={buttonVariants({ variant: 'secondary', size: 'sm' })} onClick={() => setStageIndex(stageIndex+1)}>Next stage</button></div>
              <dl className="grid grid-cols-2 gap-3 text-xs"><div><dt className="text-ink-quiet">Source arrival time</dt><dd className="mt-1 break-all font-mono">{selected.source_timestamp_ns} ns</dd></div><div><dt className="text-ink-quiet">Residual</dt><dd className="mt-1">{number(selected.diagnostics.residual_m, 2)} m</dd></div><div><dt className="text-ink-quiet">Best-candidate iteration</dt><dd className="mt-1">{number(selected.diagnostics.iterations)}</dd></div><div><dt className="text-ink-quiet">Receiver observations</dt><dd className="mt-1">{receivers.length}</dd></div></dl>
              {selected.position ? <p className="text-sm text-ink">Calculated position: {number(selected.position.position?.latitude, 6)}°, {number(selected.position.position?.longitude, 6)}°, {number(selected.position.position?.altitude, 1)} m.</p> : <p className="text-sm text-attention">No position was stored: {selected.diagnostics.failure_category?.replaceAll('_', ' ')}. Inspect geometry and timestamps; do not treat a rejected candidate as an aircraft position.</p>}
              <p className="text-xs leading-5 text-ink-secondary">Calibrated uncertainty is unavailable. Residual measures model fit, not the distance from the true aircraft position.</p>
            </div>
          </WorkspacePanel> : null}
          {selected ? <WorkspacePanel title="Historical receiver geometry" detail="Dataset coordinates and original arrival times; no live receiver activity."><LazyAirspaceMap aircraft={selected.position ? [selected.position] : []} receivers={receivers} showUncertainty={false} className="h-64" /><div className="overflow-x-auto focus-visible:outline-2" tabIndex={0} role="region" aria-label="Historical receiver arrival times"><table className="w-full text-left text-xs"><thead><tr><th className="p-3">Receiver</th><th className="p-3">Arrival (ns)</th></tr></thead><tbody>{selected.observations?.map((item) => <tr key={item.receiver_id} className="border-t border-line"><td className="p-3 font-mono">{item.receiver_id}</td><td className="p-3 font-mono">{item.timestamp_ns}</td></tr>)}</tbody></table></div></WorkspacePanel> : null}
        </div>
      </div>
    </>}
  </div>;
}
