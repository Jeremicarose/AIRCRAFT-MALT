import { AppShell } from '@/components/app-shell';
import { MetricsPage } from '@/components/pages/metrics-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { JsonValue, MetricsData } from '@/lib/types';

type Artifact = Record<string, JsonValue> | null;

export default async function MetricsRoute() {
  const [snapshot, metrics, performance, reliability] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<MetricsData | null>('/api/evidence/metrics?hours=24&limit=500', null),
    fetchJsonSafe<Artifact>('/api/evidence/performance/latest', null),
    fetchJsonSafe<Artifact>('/api/evidence/reliability/latest', null),
  ]);
  return <AppShell pageKey="metrics" title="Metrics" description="Observe latency, throughput, solve quality, availability, and system load." snapshot={snapshot}><MetricsPage metrics={metrics} performance={performance} reliability={reliability} /></AppShell>;
}
