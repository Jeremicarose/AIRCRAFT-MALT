import assert from 'node:assert/strict';
import test from 'node:test';
import { missions, missionProgress, validCompletions, totalMissionPoints } from '../lib/missions.ts';
import { useMissionStore } from '../lib/mission-store.ts';

test('unknown and duplicated saved entries cannot inflate progress', () => {
  assert.deepEqual(validCompletions(['source', 'source', 'wallet-funded', {}, 'replay']), ['source', 'replay']);
  assert.equal(missionProgress(['source', 'source']).points, 25);
  assert.equal(missionProgress(null).points, 0);
  assert.equal(missionProgress(missions.map(({ id }) => id)).points, totalMissionPoints);
  assert.equal(totalMissionPoints, 300);
});

test('missions award once, remain paused when disabled and reset only learning progress', () => {
  useMissionStore.setState({ hydrated: true, enabled: true, completed: [], latest: null });
  const store = useMissionStore.getState();
  store.complete('receiver');
  store.complete('receiver');
  assert.equal(missionProgress(useMissionStore.getState().completed).points, 50);
  store.setEnabled(false);
  store.complete('diagnostics');
  assert.deepEqual(useMissionStore.getState().completed, ['receiver']);
  store.setEnabled(true);
  store.complete('diagnostics');
  assert.equal(missionProgress(useMissionStore.getState().completed).points, 100);
  store.dismiss();
  assert.equal(useMissionStore.getState().latest, null);
  assert.equal(useMissionStore.getState().completed.length, 2);
  store.reset();
  assert.deepEqual(useMissionStore.getState().completed, []);
});

test('rehydration sanitizes saved progress and cannot replace store actions', () => {
  const current = useMissionStore.getState();
  const restored = useMissionStore.persist.getOptions().merge({ completed: ['source', 'source', 'production'], enabled: false, complete: 'untrusted', latest: 'source', wallet: 'secret' }, current);
  assert.deepEqual(restored.completed, ['source']);
  assert.equal(restored.enabled, false);
  assert.equal(restored.complete, current.complete);
  assert.equal(restored.latest, null);
  assert.equal('wallet' in restored, false);
});
