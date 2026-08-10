import { AppShell } from '@/components/app-shell';
import { PipelinePage } from '@/components/pages/pipeline-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { MetricsData, PipelineData } from '@/lib/types';

export default async function PipelineRoute() {
  const [snapshot, pipeline, metrics] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<PipelineData | null>('/api/pipeline', null),
    fetchJsonSafe<MetricsData | null>('/api/evidence/metrics?hours=24&limit=120', null),
  ]);
  return <AppShell pageKey="pipeline" title="Pipeline" description="Trace failures from receiver identity through published evidence." snapshot={snapshot}><PipelinePage pipeline={pipeline} metrics={metrics} /></AppShell>;
}
