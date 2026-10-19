import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('keeps Registry, operational, and MLAT state separate in receiver details', () => {
  const state = read('lib/receiver-state.ts');
  const inspector = read('components/receiver-inspector.tsx');
  assert.match(state, /ReceiverOperationalStatus/);
  assert.match(inspector, /Registry identity/);
  assert.match(inspector, /Operational state/);
  assert.match(inspector, /MLAT state/);
  assert.match(inspector, /owner-provided metadata/);
});

test('shows the complete registration-to-MLAT journey and a next action', () => {
  const journey = read('components/receiver-readiness-journey.tsx');
  for (const label of [
    'Receiver registered',
    'Registry identity active',
    'Discovered by MLAT runtime',
    'Registry readiness checked',
    'Observation feed available',
    'Qualified for MLAT',
    'Contributing observations',
    'Used in aircraft position',
  ]) assert.match(journey, new RegExp(label));
  assert.match(journey, /Next action:/);
});

test('provides actionable recovery instructions for actual runtime checks', () => {
  const diagnostics = read('components/pages/environment-page.tsx');
  for (const value of [
    'RECEIVER_REGISTRY_TYPE_HASH',
    'RECEIVER_REGISTRY_HASH_TYPE=data1',
    'CKB_RPC_URL',
    'CKB_INDEXER_URL',
    'DEMO_MODE=false',
    'SIMULATE_IF_UNAVAILABLE=false',
    'FOURDSKY_TRANSPORT',
  ]) assert.match(diagnostics, new RegExp(value.replaceAll('.', '\\.')));
  assert.match(diagnostics, /What to do/);
  assert.match(diagnostics, /What success looks like/);
});

test('isolates page sections and maps without exposing raw errors in the UI', () => {
  const shell = read('components/app-shell.tsx');
  const map = read('components/lazy-airspace-map.tsx');
  const receivers = read('components/pages/receivers-page.tsx');
  const boundary = read('components/section-error-boundary.tsx');
  assert.match(shell, /SectionErrorBoundary/);
  assert.match(map, /Map unavailable/);
  assert.match(receivers, /Registry transaction controls unavailable/);
  assert.match(boundary, /console\.error/);
  assert.doesNotMatch(boundary, /error\.message/);
});

