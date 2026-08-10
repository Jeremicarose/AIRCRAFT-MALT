import { AppShell } from '@/components/app-shell';
import { OverviewPage } from '@/components/pages/overview-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { JsonValue, PipelineData, PositionsResponse, ReadinessData } from '@/lib/types';

export default async function OverviewRoute() {
  const [snapshot, readiness, benchmark, positionsData, pipeline] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<ReadinessData | null>('/api/readiness', null),
    fetchJsonSafe<Record<string, JsonValue> | null>('/api/benchmark/latest', null),
    fetchJsonSafe<PositionsResponse>('/api/positions/recent?seconds=600&limit=250', { positions: [] }),
    fetchJsonSafe<PipelineData | null>('/api/pipeline', null),
  ]);
  return <AppShell pageKey="overview" title="Overview" description="Current airspace, infrastructure health, and evidence readiness." snapshot={snapshot}><OverviewPage snapshot={snapshot} readiness={readiness} benchmark={benchmark} positionsData={positionsData} initialPipeline={pipeline} /></AppShell>;
}
