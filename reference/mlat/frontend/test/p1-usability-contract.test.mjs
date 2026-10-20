import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('keeps persistent context out of actionable notifications', () => {
  const center = read('components/ui/notification-center.tsx');
  const notices = read('lib/operator-notices.ts');
  assert.match(center, /Errors and warnings that require action/);
  assert.doesNotMatch(notices, /Pinned aircraft context|Pinned receiver context|Replay source active/);
});

test('pipeline blockers select explanatory stages instead of linking to the same page', () => {
  const pipeline = read('components/pages/pipeline-page.tsx');
  assert.match(pipeline, /pipelineStageForBlocker/);
  assert.match(pipeline, /onSelect: stage \? \(\) => inspectStage/);
  assert.match(pipeline, /setSelectedStageId\(id\)/);
  assert.doesNotMatch(pipeline, /detail: blocker[\s\S]{0,180}href: '\/app\/pipeline'/);
});

test('contract verification explains values, sources, purpose, result, and trust boundary', () => {
  const verification = read('components/registry-contract-verification.tsx');
  for (const label of ['Name', 'Value', 'Purpose', 'Source', 'Status', 'Expected contract code hash', 'Runtime contract code hash', 'Deployment transaction', 'Trust boundary']) {
    assert.match(verification, new RegExp(label));
  }
  assert.match(verification, /does not prove a physical receiver exists/);
});

test('aircraft contributors expose source, Registry state, and operational state separately', () => {
  const contributors = read('components/aircraft-contributors.tsx');
  assert.match(contributors, /MLAT solution → contributing receivers/);
  assert.match(contributors, /REPLAY CONTRIBUTION/);
  assert.match(contributors, /Registry:/);
  assert.match(contributors, /Operational:/);
  assert.match(contributors, /Contributing receivers unavailable/);
});
