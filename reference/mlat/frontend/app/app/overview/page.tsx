import { OverviewPage } from '@/components/pages/overview-page';
import { fetchJsonSafe, fetchJsonState, fetchShellSnapshot, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import type { JsonValue, PipelineData, PositionsResponse, ReadinessData } from '@/lib/types';

export default async function OverviewRoute() {
  const [snapshot, readiness, benchmark, positionsState, pipeline] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<ReadinessData | null>('/api/readiness', null),
    fetchJsonSafe<Record<string, JsonValue> | null>('/api/benchmark/latest', null),
    fetchJsonState<PositionsResponse>(PUBLIC_POSITIONS_PATH, { positions: [] }),
    fetchJsonSafe<PipelineData | null>('/api/pipeline', null),
  ]);
  return <><OverviewPage snapshot={snapshot} readiness={readiness} benchmark={benchmark} positionsData={positionsState.data} positionsError={positionsState.error} initialPipeline={pipeline} /></>;
}
