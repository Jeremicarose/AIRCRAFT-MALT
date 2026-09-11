import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

function git(...args) {
  return execFileSync('git', args, { encoding: 'utf8' }).trim();
}

export const EVIDENCE_ROUTE = '/app/registry';

export default class BrowserEvidenceReporter {
  constructor(options = {}) {
    this.outputFile = process.env.BROWSER_QA_REPORT || options.outputFile || './tmp/browser-qa-report.json';
    this.expectedTests = 0;
    this.results = new Map();
    this.accessibilityViolations = new Map();
  }

  onBegin(_config, suite) {
    this.expectedTests = suite.allTests().length;
  }

  onTestEnd(test, result) {
    this.results.set(test.id, {
      id: test.id,
      title: test.titlePath().join(' > '),
      status: result.status,
      error: result.error?.message ?? null,
    });
    let violationCount = 0;
    for (const attachment of result.attachments) {
      if (attachment.name !== 'axe-serious-critical' || !attachment.body) continue;
      const violations = JSON.parse(attachment.body.toString('utf8'));
      violationCount += Array.isArray(violations) ? violations.length : 1;
    }
    this.accessibilityViolations.set(test.id, violationCount);
  }

  onEnd(result) {
    const sourceCommit = process.env.GITHUB_SHA || git('rev-parse', 'HEAD');
    const sourceTree = git('rev-parse', 'HEAD^{tree}');
    const worktreeClean = git('status', '--porcelain=v1', '--untracked-files=all') === '';
    const completedTests = this.results.size;
    const failures = [...this.results.values()].filter(({ status }) => status !== 'passed');
    const passedTests = completedTests - failures.length;
    const failedTests = completedTests - passedTests;
    const accessibilityViolations = [...this.accessibilityViolations.values()]
      .reduce((total, count) => total + count, 0);
    const passed = result.status === 'passed'
      && this.expectedTests > 0
      && completedTests === this.expectedTests
      && failedTests === 0
      && accessibilityViolations === 0
      && worktreeClean;
    const report = {
      schema_version: 1,
      generated_at: new Date().toISOString(),
      source_commit: sourceCommit,
      source_tree: sourceTree,
      worktree_clean: worktreeClean,
      route: EVIDENCE_ROUTE,
      accessibility_standard: 'WCAG 2 A/AA serious and critical axe findings',
      total_tests: this.expectedTests,
      completed_tests: completedTests,
      passed_tests: passedTests,
      failed_tests: failedTests,
      failures,
      accessibility_violations: accessibilityViolations,
      pass: passed,
    };
    const output = path.resolve(process.cwd(), this.outputFile);
    mkdirSync(path.dirname(output), { recursive: true });
    writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  }
}
