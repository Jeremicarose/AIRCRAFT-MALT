import assert from 'node:assert/strict';
import test from 'node:test';
import { receiverReferenceIds, receiverReferencesInclude } from '../lib/receiver-reference.ts';

test('matches a replay correlation ID to its namespaced operational receiver', () => {
  const references = receiverReferenceIds('replay:RECV_NYC_001', null, 'RECV_NYC_001');
  assert.equal(receiverReferencesInclude(references, 'RECV_NYC_001'), true);
});

test('uses only the canonical identity after a receiver is registered', () => {
  const identity = `0x${'ab'.repeat(32)}`;
  const references = receiverReferenceIds(identity, identity, 'RECV_NYC_001');
  assert.equal(receiverReferencesInclude(references, identity.toUpperCase().replace('0X', '0x')), true);
  assert.equal(receiverReferencesInclude(references, 'RECV_NYC_001'), false);
});
