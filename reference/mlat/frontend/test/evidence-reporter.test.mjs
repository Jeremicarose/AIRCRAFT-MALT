import assert from 'node:assert/strict';
import { readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

import BrowserEvidenceReporter, { EVIDENCE_ROUTE } from './e2e/evidence-reporter.mjs';

test('browser evidence fails closed and records test and accessibility failures', () => {
  const output = path.join(tmpdir(), `registry-browser-evidence-${process.pid}.json`);
  const reporter = new BrowserEvidenceReporter({ outputFile: output });

  reporter.onBegin({}, { allTests: () => [{ id: 'registry-accessibility' }] });
  reporter.onTestEnd({
    id: 'registry-accessibility',
    titlePath: () => ['registry-accessibility.spec.mjs', 'has no violations'],
  }, {
    status: 'failed',
    error: { message: 'Expected no violations' },
    attachments: [{
      name: 'axe-serious-critical',
      body: Buffer.from(JSON.stringify([{ id: 'color-contrast' }])),
    }],
  });
  reporter.onEnd({ status: 'failed' });

  const evidence = JSON.parse(readFileSync(output, 'utf8'));
  assert.equal(evidence.schema_version, 1);
  assert.equal(evidence.pass, false);
  assert.equal(evidence.total_tests, 1);
  assert.equal(evidence.completed_tests, 1);
  assert.equal(evidence.passed_tests, 0);
  assert.equal(evidence.failed_tests, 1);
  assert.deepEqual(evidence.failures, [{
    id: 'registry-accessibility',
    title: 'registry-accessibility.spec.mjs > has no violations',
    status: 'failed',
    error: 'Expected no violations',
  }]);
  assert.equal(evidence.accessibility_violations, 1);
  assert.equal(evidence.route, EVIDENCE_ROUTE);
  assert.match(evidence.source_commit, /^[0-9a-f]{40}$/);

  rmSync(output);
});
