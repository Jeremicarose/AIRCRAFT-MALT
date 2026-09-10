import assert from 'node:assert/strict';
import test from 'node:test';

import { formatDateTime, u64 } from '../lib/format.ts';

test('formats the complete u64 range without JavaScript number rounding', () => {
  assert.equal(u64('18446744073709551615'), '18,446,744,073,709,551,615');
  assert.equal(u64('18446744073709551616'), 'n/a');
  assert.equal(u64(9_007_199_254_740_992), 'n/a');
});

test('does not round an out-of-range Registry timestamp into a different date', () => {
  assert.equal(formatDateTime('18446744073709551615'), '18446744073709551615');
});
