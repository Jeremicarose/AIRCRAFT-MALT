import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('presents the compact solver report as historical evidence rather than live state', () => {
  const page = read('components/pages/solver-benchmark-page.tsx');
  const orientation = read('components/data-source-banner.tsx');

  for (const label of [
    'Historical recording',
    'Solver only',
    'Not live',
    'Accuracy distribution',
    'Solve outcome',
    'Residuals and rejected events',
    'Inspectable event geometry',
    'What this measures',
    'What this does not prove',
  ]) assert.match(page, new RegExp(label));

  assert.match(page, /receiver_geometry/);
  assert.match(page, /residual_m/);
  assert.match(page, /failure_categories/);
  assert.match(page, /was not included in this report version/);
  assert.match(orientation, /pageKey === 'benchmark'/);
  assert.match(orientation, /HISTORICAL RECORDING/);
});

test('exposes the benchmark through navigation and the validated evidence API', () => {
  const route = read('app/app/benchmark/page.tsx');
  const routes = read('lib/routes.ts');
  const api = read('lib/api.ts');

  assert.match(route, /\/api\/evidence\/solver-benchmark\/latest/);
  assert.match(routes, /Accuracy benchmark/);
  assert.match(api, /solverBenchmark/);
});
