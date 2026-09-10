import assert from 'node:assert/strict';
import test from 'node:test';
import { classifyReceiverObservation } from '../lib/receiver-freshness.ts';

test('classifies observations inside the freshness window as fresh', () => {
  assert.equal(classifyReceiverObservation(900, 1000, 120), 'fresh');
  assert.equal(classifyReceiverObservation(880, 1000, 120), 'fresh');
});

test('classifies observations outside the freshness window as stale', () => {
  assert.equal(classifyReceiverObservation(879, 1000, 120), 'stale');
});

test('fails closed for missing, malformed, or non-positive timestamps', () => {
  assert.equal(classifyReceiverObservation(undefined, 1000), 'invalid');
  assert.equal(classifyReceiverObservation('not-a-time', 1000), 'invalid');
  assert.equal(classifyReceiverObservation(0, 1000), 'invalid');
});

test('rejects observations beyond the allowed future clock skew', () => {
  assert.equal(classifyReceiverObservation(1030, 1000), 'fresh');
  assert.equal(classifyReceiverObservation(1031, 1000), 'future');
});
