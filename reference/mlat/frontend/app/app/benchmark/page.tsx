import { SolverBenchmarkPage } from '@/components/pages/solver-benchmark-page';
import { fetchJsonState } from '@/lib/api';
import type { SolverBenchmarkReport } from '@/lib/types';

export default async function BenchmarkRoute() {
  const [benchmarkState] = await Promise.all([
    fetchJsonState<SolverBenchmarkReport | null>('/api/evidence/solver-benchmark/latest', null),
  ]);

  return (
    <>
      <SolverBenchmarkPage report={benchmarkState.data} error={benchmarkState.error} />
    </>
  );
}
