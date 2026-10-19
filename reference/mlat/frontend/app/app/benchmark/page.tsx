import { AppShell } from '@/components/app-shell';
import { SolverBenchmarkPage } from '@/components/pages/solver-benchmark-page';
import { fetchJsonState, fetchShellSnapshot } from '@/lib/api';
import type { SolverBenchmarkReport } from '@/lib/types';

export default async function BenchmarkRoute() {
  const [snapshot, benchmarkState] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonState<SolverBenchmarkReport | null>('/api/evidence/solver-benchmark/latest', null),
  ]);

  return (
    <AppShell
      pageKey="benchmark"
      title="Accuracy benchmark"
      description="Inspect historical solver accuracy, geometry, and evidence limits."
      snapshot={snapshot}
    >
      <SolverBenchmarkPage report={benchmarkState.data} error={benchmarkState.error} />
    </AppShell>
  );
}
