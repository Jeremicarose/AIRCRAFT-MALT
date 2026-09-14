import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const frontendRoot = path.resolve(import.meta.dirname, '..');
const apiSource = fs.readFileSync(path.join(frontendRoot, 'lib/api.ts'), 'utf8');
const apiRouteSource = fs.readFileSync(path.join(frontendRoot, 'app/api/[...path]/route.ts'), 'utf8');
const receiverStateSource = fs.readFileSync(path.join(frontendRoot, 'lib/receiver-state.ts'), 'utf8');
const receiversPageSource = fs.readFileSync(path.join(frontendRoot, 'components/pages/receivers-page.tsx'), 'utf8');

test('bounds browser API requests and preserves readable failure context', () => {
  assert.match(apiSource, /API_REQUEST_TIMEOUT_MS = 12_000/);
  assert.match(apiSource, /AbortSignal\.timeout\(API_REQUEST_TIMEOUT_MS\)/);
  assert.match(apiSource, /new ApiRequestError\(/);
  assert.match(apiRouteSource, /AbortSignal\.any\(\[request\.signal, AbortSignal\.timeout\(API_REQUEST_TIMEOUT_MS\)\]\)/);
});

test('fails closed when Registry discovery is unavailable', () => {
  assert.match(receiverStateSource, /registryDirectoryAvailable\?: boolean/);
  assert.match(receiverStateSource, /registryStatus === 'active' && !registryDirectoryAvailable/);
  assert.match(receiverStateSource, /Registry discovery could not be verified/);
  assert.match(receiversPageSource, /registryDirectoryAvailable,/);
});
