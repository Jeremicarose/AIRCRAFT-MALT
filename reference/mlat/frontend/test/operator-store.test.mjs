import assert from 'node:assert/strict';
import test from 'node:test';

import { useOperatorStore } from '../lib/operator-store.ts';

test('does not publish a new store state when the investigation dock is unchanged', () => {
  const initialDock = {
    entityType: 'receiver',
    title: 'RECV_TEST_001',
    statusLabel: 'Offline',
    statusTone: 'neutral',
    facts: [{ label: 'Registry', value: 'Active identity', tone: 'trust' }],
  };
  let notifications = 0;
  const unsubscribe = useOperatorStore.subscribe(() => {
    notifications += 1;
  });

  useOperatorStore.getState().setDock(initialDock);
  useOperatorStore.getState().setDock({
    ...initialDock,
    facts: [{ label: 'Registry', value: 'Active identity', tone: 'trust' }],
  });

  unsubscribe();
  useOperatorStore.getState().clearDock();
  assert.equal(notifications, 1);
});

test('does not publish repeated receiver and investigation selections', () => {
  const store = useOperatorStore.getState();
  store.setSelectedReceiverId('receiver-1');
  store.setInvestigationContext({ focus: 'receiver-1', query: '', timeRange: 'recent' });

  let notifications = 0;
  const unsubscribe = useOperatorStore.subscribe(() => {
    notifications += 1;
  });

  useOperatorStore.getState().setSelectedReceiverId('receiver-1');
  useOperatorStore.getState().setInvestigationContext({ focus: 'receiver-1', query: '', timeRange: 'recent' });

  unsubscribe();
  assert.equal(notifications, 0);
});
