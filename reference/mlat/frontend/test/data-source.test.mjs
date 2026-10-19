import assert from 'node:assert/strict';
import test from 'node:test';

import { dataSourceState } from '../lib/data-source.ts';

test('classifies deterministic demo data as synthetic even when timestamps are recent', () => {
  const source = dataSourceState({ mode: 'demo', demo_mode: true, synthetic_feed_mode: true, runtime_status: 'active' });
  assert.equal(source.label, 'SYNTHETIC');
  assert.match(source.detail, /not live receiver evidence/);
});

test('keeps simulation separate from replay', () => {
  const source = dataSourceState({ mode: 'simulation', simulation_mode: true, synthetic_feed_mode: true, runtime_status: 'active' });
  assert.equal(source.label, 'SYNTHETIC');
  assert.match(source.detail, /Synthetic demonstration observations/);
});

test('requires an explicitly active live runtime before using the live label', () => {
  assert.equal(dataSourceState({ mode: 'configured_live', runtime_status: 'unavailable' }).label, 'UNKNOWN');
  assert.equal(dataSourceState({ mode: 'live', runtime_status: 'active' }).label, 'LIVE');
});

test('marks last-known data as cached after a failed refresh', () => {
  const source = dataSourceState({ mode: 'live', runtime_status: 'active' }, { cached: true });
  assert.equal(source.label, 'LIVE (CACHED)');
});



test('stored provenance overrides the current runtime mode', () => {
  assert.equal(dataSourceState({ mode: 'live', runtime_status: 'active', data_provenance: 'SYNTHETIC' }).label, 'SYNTHETIC');
  assert.equal(dataSourceState({ mode: 'live', runtime_status: 'active', data_provenance: 'UNKNOWN' }).label, 'UNKNOWN');
  assert.equal(dataSourceState({ data_provenance: 'HISTORICAL_REPLAY' }).label, 'HISTORICAL REPLAY');
});
