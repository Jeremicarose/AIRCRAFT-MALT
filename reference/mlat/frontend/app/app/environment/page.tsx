import { AppShell } from '@/components/app-shell';
import { EnvironmentPage } from '@/components/pages/environment-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { HealthData, ReadinessData } from '@/lib/types';

export default async function EnvironmentRoute() {
  const [snapshot, health, readiness] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<HealthData | null>('/api/health', null),
    fetchJsonSafe<ReadinessData | null>('/api/readiness', null),
  ]);
  return <AppShell pageKey="environment" title="Environment" description="Review deployment mode, connectivity, registry, and production readiness." snapshot={snapshot}><EnvironmentPage modeData={snapshot.modeData} health={health} readiness={readiness} /></AppShell>;
}
