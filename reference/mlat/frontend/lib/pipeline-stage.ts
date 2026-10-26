import type { PipelineStageData } from '@/lib/types';

const blockerStageRules: Array<{ pattern: RegExp; stageId: string }> = [
  { pattern: /registry type hash|registry code hash/i, stageId: 'registry' },
  { pattern: /receiver discovery/i, stageId: 'discovery' },
  { pattern: /fresh receiver observations|observation source/i, stageId: 'ingest' },
  { pattern: /receiver clocks|timing qualification/i, stageId: 'clock' },
  { pattern: /correlat|synchronized observations/i, stageId: 'correlation' },
  { pattern: /replay|synthetic|benchmark|publishable external/i, stageId: 'solve' },
  { pattern: /position storage|persist/i, stageId: 'storage' },
  { pattern: /public api/i, stageId: 'api' },
];

export function pipelineStageForBlocker(blocker: string, stages: PipelineStageData[]): PipelineStageData | null {
  const rule = blockerStageRules.find(({ pattern }) => pattern.test(blocker));
  return rule ? stages.find((stage) => stage.id === rule.stageId) ?? null : null;
}
