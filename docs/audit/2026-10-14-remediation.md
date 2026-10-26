# Production-readiness remediation, 14 October 2026

Primary input: [8–13 October review](2026-10-08-production-readiness.md).
Starting branch: `main`; commit: `df82f6cfa23be85eed7ca0f2da61db2fb8409889`.
The workspace already contains the October changes plus unrelated personal work.
The starting hashes/status of 798 files are recorded under ignored
`artifacts/remediation-2026-10-14/`. Historical audit, compact benchmark and synthetic
bundle checksums all verified before editing. No commit, reset, push, deployment,
wallet signing, transaction broadcast or external communication is authorized.

Statuses mean: **PASS** executed successfully; **FAIL** executed and failed;
**BLOCKED** an unavailable dependency/approval/hardware prevents verification;
**NOT RUN** not executed; **ALREADY RESOLVED** existing code and test evidence
confirm the earlier finding is addressed.

## Verified starting checklist

| Review finding / workstream | Starting status | Implementation / verification evidence | Remediation |
|---|---|---|---|
| A01 endpoint credentials and redirects | ALREADY RESOLVED | `ingest/feed_transports.py`, input/transport security tests; 257-test baseline passed | Preserve, recheck regressions |
| A02 persistent provenance and mode isolation | ALREADY RESOLVED | `database.py`, `test_storage_provenance.py`, historical API tests | Add backup/restore verification without relabelling data |
| A03 malformed JSON/frame/time | ALREADY RESOLVED | `ingest/validation.py`, `test_input_security.py` | Verify pilot rejection counters and drop visibility |
| A04 dependency patches | ALREADY RESOLVED | Pinned sharp/source-map/Werkzeug patches and preserved scan evidence | Re-scan advisories; investigate elliptic without downgrade |
| A05 buffer/queue growth, repeated solves | ALREADY RESOLVED | Correlation/storage tests and bounded code | Run process-level observation window; no SLO claim |
| A06 bridge deadlock/shutdown/logging | ALREADY RESOLVED | `test_transport_recovery.py` and bounded child termination | Preserve; failure/partial-feed tests |
| A07 provenance/confidence terminology | ALREADY RESOLVED | Source labels, per-row metadata, uncalibrated quality declaration | Browser checks and immutable benchmark comparison |
| A08 clock/lifecycle qualification | ALREADY RESOLVED | Receiver-state/runtime tests; stale clocks and lifecycle changes reset qualification | Verify operational metrics use qualification, not Registry declarations |
| A09 complete compact benchmark | ALREADY RESOLVED | All 362 events; pinned inputs and reports verified | Compare unchanged solver source and event metrics |
| A10 schema/duplicate storage identity | ALREADY RESOLVED | Atomic schema v2 and replay idempotency tests | Exercise backup, restore, migration rollback and restart |
| A11 input bounds/health | ALREADY RESOLVED | API tests and explicit unobserved frontend health | Reconcile pilot capture with honest frontend health |
| A12 indexer bounds/cycles | ALREADY RESOLVED | Registry tests and bounded reads/cursor history | Additional malformed-response and SDK consistency review |
| A13 image assets/non-root/start command | NOT RUN | Source configuration exists; installed API tested in prior audit | Container build gap reproduced below; strengthen CI execution |
| Frontend image SDK install layer | FAIL | `npm run prepare` in actual manifest/dependency-only layer: TS5058, missing tsconfig | Copy SDK build inputs before lifecycle hook |
| Docker execution | BLOCKED | `docker info`: executable missing | Prepare CI image startup/persistence/shutdown smoke tests |
| Remote CI on a clean new commit | BLOCKED | Worktree is uncommitted; commit/push not authorized | Keep exact reviewable commands and source checksums |
| Independent Registry audit | BLOCKED | Requires an independent reviewer | Additional source review is local engineering review only |
| Wallet/operator lifecycle | BLOCKED | No operator signing authorization | Read-only/local verification and stop-at-wallet procedure |
| Physical receiver campaign / independent truth | BLOCKED | No genuine receiver feeds or independent reference window supplied | Repair/extend existing capture harness and acceptance criteria |
| Solver altitude/error limitations | BLOCKED | Numerical baseline has 92 rejected events and large altitude tail | Preserve solver; measure and disclose, no tuning |
| SQLite backup/restore and target-host recovery | NOT RUN | Prior report contained instructions but no executed restore evidence | Add safe new-destination backup/restore tool and tests |
| Sustained external network/load/SLO | NOT RUN | Prior measurements were short in-process callbacks | Execute bounded process soak; document longer operator procedure |
| Diagnostic export nested allowlist | NOT RUN | Top-level fields are limited; source/qualification JSON is forwarded | Probe nested unexpected fields before changing code |
| Historical evidence integrity | PASS | All three preserved package checksum manifests match | Keep those packages unchanged; write new remediation evidence |

The initial Python baseline executed with Python 3.12.11 and `MLAT_ENV_FILE=/dev/null`:
**257 passed**, exit 0. Commands, exit codes, times and logs are recorded per check
under `artifacts/remediation-2026-10-14/`; the final evidence package will retain the
relevant records and update this checklist with outcomes.

## Execution record

Work is in progress. PASS is not assigned to unexecuted container, hardware,
external audit, wallet or remote CI work.
