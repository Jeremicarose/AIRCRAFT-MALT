# Release gates — 19 October 2026

**Gate A: PASS for the local internal-validation scope.**
**Gate B: NOT PASSED; remaining release/operator evidence is required.**
**Gate C: NOT PASSED. No production-readiness claim is made.**

The dated checklist below preserves the original audit assessment. Subsequent
clean-source, frontend and container results are recorded in the
[20 October follow-up](../../evidence/console-experience-2026-10-20/README.md).
Publication and an explicitly labelled hosted demo were authorized afterward;
that authorization does not satisfy the remaining operational or physical gates.

Each gate is independent. A configured workflow, historical signed transaction or
passing synthetic solve does not satisfy a later gate. This assessment applies to
the audited working tree, not to the unchanged committed HEAD.

## Gate A — Internal validation

- [x] Starting failures preserved: 276 passing Python tests, four formatting
  failures, one type error, missing pip in the old environment. Repairs and failed
  intermediate attempts are distinguished in the command ledger.
- [x] Confirmed security/correctness defects repaired with regressions: node-backed
  registry authority, bounded discovery, diagnostic/log input leakage, and streaming
  authorization revocation/expiry. No confirmed critical issue remains in reviewed scope.
- [x] Final Python suite: 293 passed; SDK: 78; frontend unit: 60; CKB contract: 16;
  protocol agreement: 57 cases / 171 assertions. Formatting, lint and type checks pass.
- [x] Synthetic and all 362 historical events reproduce; five-receiver fixture
  preserved; 92 failures and reference limitations explicitly retained.
- [x] Full pipeline exercised through a mocked-chain synthetic integration and
  real synthetic/historical service/browser tests. Test observations remain synthetic.
- [x] Startup, shutdown, restart, migration rollback and local backup/restore are
  tested/documented. Two-minute process test preserved a stored position across restart.
- [x] Dependency/advisory results and partial static-analysis scope disclosed.

Limits: no coverage percentage, no production crash/power-loss test, no independent
review. Gate A is an engineering test result, not a proof of absence of defects.

## Gate B — Controlled external testing

- [x] Safe loopback test configuration and reproducible guide provided.
- [x] Fresh locked Python installation and package build; production frontend build;
  31 synthetic and 3 historical browser/accessibility checks pass locally.
- [x] Replay/live/synthetic labels and missing clock/registry evidence remain explicit.
- [x] Shareable diagnostic endpoint tested with sensitive-value sentinels; known
  limitations, retention and feedback/reset procedures disclosed.
- [x] Local contract/SDK failure cases and runtime revocation pass; public node
  confirms the historical lifecycle and immutable deployment; repaired discovery
  directly verified two records, including one revoked.
- [ ] Review and preserve the large pre-existing uncommitted changes and this run's
  additions in a controlled revision. Repeat clean-checkout/browser CI against that
  revision. Current browser reports correctly have `worktree_clean=false`, `pass=false`.
- [ ] Execute the tester guide from that clean revision in a fresh environment,
  including container checks if containers are offered to testers.
- [ ] Complete a freshly authorized testnet owner-wallet lifecycle and record its
  failures/recovery. Not run here because the mission excludes signing/spending.
- [ ] Assign an operator to accept tester reports and approve any real feed access.

Local offline walkthroughs are available now. Gate B as requested includes more
than an offline demo, so it remains unpassed until the unchecked evidence exists.

## Gate C — Production consideration

- [ ] Independent security/contract review and approved owner-lock policy.
- [ ] Actual deployment on target infrastructure verified, including non-root
  permissions, TLS, access control, secrets, edge HTTP/WebSocket limits and quotas.
- [ ] Monitoring, alert thresholds/routing, operational ownership and incident
  response rehearsal. Prove registry age, feed/clock health, queue/drop counts,
  storage errors, solver rejections, latency and disk pressure are observed.
- [ ] Scheduled encrypted off-host backups, measured restore, application/schema
  rollback and recovery objectives verified on the target host.
- [ ] Representative sustained load/soak, network partitions and disk/crash recovery.
- [ ] A documented chain-confirmation/reorganization policy and measured registry
  scan capacity. Public RPC dependence and polling delay must be accepted explicitly.
- [ ] Private-data exposure and live/usage/receiver retention approved for the actual
  deployment. The current public read API cannot be assumed private.
- [ ] Real multi-receiver frames, surveyed/evidenced geometry, independently qualified
  clocks and suitable reference truth if live MLAT is claimed.
- [ ] Accuracy acceptance criteria met, including vertical error and rejection rate;
  current historical tail does not support a high-accuracy production claim.
- [ ] Clean immutable release artifacts, current CI, SBOM/provenance and rollback
  package verified. No unresolved critical/high defect without explicit mitigation.

## Three highest-priority remaining blockers

1. **Reviewable release and deployment evidence:** the workspace is uncommitted,
   source-bound browser release reports fail that requirement, Docker is absent,
   and target-host build/start/restore/rollback remain unexecuted.
2. **Authorized external lifecycle and independent security review:** no fresh
   operator-wallet campaign or independent contract audit was performed. Saved
   and read-only testnet evidence cannot substitute for either.
3. **Physical MLAT and operational validation:** no authorized synchronized receiver
   campaign or independent reference window, substantial historical altitude error,
   and no sustained target-host operational/incident evidence.
