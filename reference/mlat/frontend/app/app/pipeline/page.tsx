import { PipelinePage } from '@/components/pages/pipeline-page';
import { fetchJsonSafe } from '@/lib/api';
import type { MetricsData, PipelineData } from '@/lib/types';

export default async function PipelineRoute() {
  const [pipeline, metrics] = await Promise.all([
    fetchJsonSafe<PipelineData | null>('/api/pipeline', null),
    fetchJsonSafe<MetricsData | null>('/api/evidence/metrics?hours=24&limit=120', null),
  ]);
  return <><PipelinePage pipeline={pipeline} metrics={metrics} /></>;
}
