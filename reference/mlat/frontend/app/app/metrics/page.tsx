import { MetricsPage } from '@/components/pages/metrics-page';
import { fetchJsonSafe } from '@/lib/api';
import type { JsonValue, MetricsData } from '@/lib/types';

type Artifact = Record<string, JsonValue> | null;

export default async function MetricsRoute() {
  const [metrics, performance, reliability] = await Promise.all([
    fetchJsonSafe<MetricsData | null>('/api/evidence/metrics?hours=24&limit=500', null),
    fetchJsonSafe<Artifact>('/api/evidence/performance/latest', null),
    fetchJsonSafe<Artifact>('/api/evidence/reliability/latest', null),
  ]);
  return <><MetricsPage metrics={metrics} performance={performance} reliability={reliability} /></>;
}
