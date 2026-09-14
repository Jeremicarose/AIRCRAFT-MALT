import assert from 'node:assert/strict';
import test from 'node:test';
import {
  receiverIdentity,
  receiverReferenceIds,
  receiverReferencesInclude,
} from '../lib/receiver-reference.ts';

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

test('requires receiver_identity instead of promoting a human receiver_id', () => {
  const identity = `0x${'AB'.repeat(32)}`;
  assert.equal(receiverIdentity({ receiver_identity: identity }), identity.toLowerCase());
  assert.equal(receiverIdentity({
    data_source: 'ckb_registry',
    receiver_id: identity,
    receiver_identity: null,
  }), null);
});
