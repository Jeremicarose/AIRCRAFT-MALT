import assert from 'node:assert/strict';
import test from 'node:test';

import { assessRegistryContract } from '../lib/contract-verification.ts';

const evidence = {
  schema_version: 1,
  source: 'saved_testnet_evidence',
  live_query: false,
  network: 'CKB testnet',
  status: 'complete',
  generated_at: '2026-09-11T03:56:36Z',
  private_keys_included: false,
  contract: { code_hash: '0xabc', hash_type: 'data1', deployment_transaction: '0xdef' },
  receiver: { receiver_identity: '0x123', receiver_label: 'RECV_TEST' },
  lifecycle: [],
};

test('does not call saved evidence a live verification when runtime configuration is absent', () => {
  const result = assessRegistryContract(evidence, { receiver_registry_type_hash: '', receiver_registry_hash_type: 'data1' });
  assert.equal(result.result, 'not_configured');
  assert.equal(result.label, 'NOT CONFIGURED');
  assert.match(result.nextAction, /RECEIVER_REGISTRY_TYPE_HASH/);
});

test('reports the expected and actual configuration mismatch', () => {
  const result = assessRegistryContract(evidence, { receiver_registry_type_hash: '0x999', receiver_registry_hash_type: 'data1', registry_code_immutable: true });
  assert.equal(result.result, 'mismatch');
  assert.equal(result.label, 'MISMATCH');
});

test('uses configuration match language for matching immutable values', () => {
  const result = assessRegistryContract(evidence, { receiver_registry_type_hash: '0xABC', receiver_registry_hash_type: 'data1', registry_code_immutable: true, registry_discovery_live: false });
  assert.equal(result.result, 'match');
  assert.equal(result.label, 'CONFIGURATION MATCH');
  assert.match(result.explanation, /does not perform a new live CKB query/);
});
