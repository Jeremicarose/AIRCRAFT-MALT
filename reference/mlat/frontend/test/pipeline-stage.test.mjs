import assert from 'node:assert/strict';
import test from 'node:test';

import { pipelineStageForBlocker } from '../lib/pipeline-stage.ts';

const stages = ['registry', 'discovery', 'ingest', 'clock', 'correlation', 'solve', 'storage', 'api'].map((id) => ({ id, label: id, status: 'waiting' }));

test('maps reported pipeline blockers to the stage that explains them', () => {
  assert.equal(pipelineStageForBlocker('CKB registry type hash is not active in this runtime.', stages)?.id, 'registry');
  assert.equal(pipelineStageForBlocker('Observation and solve output is replay/synthetic, not live.', stages)?.id, 'solve');
  assert.equal(pipelineStageForBlocker('Fewer than four receiver clocks meet the timing qualification gate.', stages)?.id, 'clock');
  assert.equal(pipelineStageForBlocker('No publishable external benchmark report is available.', stages)?.id, 'solve');
});

test('leaves an unknown blocker informational instead of inventing a destination', () => {
  assert.equal(pipelineStageForBlocker('A new backend condition was reported.', stages), null);
});
