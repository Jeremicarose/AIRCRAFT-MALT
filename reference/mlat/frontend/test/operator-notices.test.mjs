import assert from 'node:assert/strict';
import test from 'node:test';

import { operatorNotices } from '../lib/operator-notices.ts';

const baseSnapshot = {
  modeData: {
    mode: 'demo',
    demo_mode: true,
    runtime_status: 'active',
    receiver_registry_type_hash: '',
  },
  healthData: { status: 'ok' },
  aircraftData: { count: 3 },
  receiverData: { count: 9, receivers: [] },
};

test('keeps replay mode out of the actionable notification list', () => {
  const notices = operatorNotices(baseSnapshot);
  assert.deepEqual(notices.map((notice) => notice.id), ['registry']);
  assert.equal(notices[0].severity, 'warning');
});

test('does not claim insufficient geometry when receiver data is unavailable', () => {
  const notices = operatorNotices({ ...baseSnapshot, receiverData: null });
  assert.equal(notices.some((notice) => notice.id === 'receivers'), false);
});

test('reports insufficient receiver geometry once with an actionable destination', () => {
  const notices = operatorNotices({ ...baseSnapshot, receiverData: { count: 3, receivers: [] } });
  const geometry = notices.filter((notice) => notice.id === 'receivers');
  assert.equal(geometry.length, 1);
  assert.equal(geometry[0].severity, 'error');
  assert.equal(geometry[0].href, '/app/pipeline');
});
