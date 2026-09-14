import assert from 'node:assert/strict';
import test from 'node:test';
import { ApiRequestError, presentApiError } from '../lib/api.ts';

test('keeps low-level API failures behind technical details', () => {
  const error = new ApiRequestError('connect ECONNREFUSED 127.0.0.1:5057', 503, '/api/health');
  const presented = presentApiError(error, 'Health could not be checked.');

  assert.equal(presented.detail, 'The service is temporarily unavailable. Existing data may be stale; try again in a moment.');
  assert.match(presented.technicalDetail, /ECONNREFUSED/);
  assert.doesNotMatch(presented.detail, /ECONNREFUSED/);
});

test('explains timeouts and rate limits with a recovery action', () => {
  const timeout = presentApiError(new ApiRequestError('request timed out', 504, '/api/receivers'), 'Fallback');
  const rateLimit = presentApiError(new ApiRequestError('too many requests', 429, '/api/receivers'), 'Fallback');

  assert.match(timeout.detail, /try again/i);
  assert.match(timeout.detail, /stale/i);
  assert.match(rateLimit.detail, /wait a moment/i);
});

test('uses the caller explanation for an unexpected error', () => {
  const presented = presentApiError(new Error('unexpected parser detail'), 'The response could not be processed. Try again.');

  assert.equal(presented.detail, 'The response could not be processed. Try again.');
  assert.equal(presented.technicalDetail, 'unexpected parser detail');
});
