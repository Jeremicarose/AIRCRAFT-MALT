# Production readiness audit — 19 October 2026

Final assessment: Gate A passes local internal validation; Gates B and C have
not passed. The initial findings and plan below were recorded before application
edits and are retained as the starting assessment.
This report assesses the working tree based on `df82f6c`, on `main`, including
substantial pre-existing uncommitted October work. It does not assess only HEAD.
Starting status and SHA-256 hashes are preserved in
`artifacts/readiness-2026-10-19/starting-git-status.txt` and `starting-files.json`.
Earlier reports and all historical evidence are retained. No deployment, wallet
operation, external operator contact, or production migration is part of this run.

Readiness packet: [architecture/data flow](architecture-and-data-flow.md),
[security threat model](security-threat-model.md), [test plan/results](test-plan.md),
[benchmarks](benchmark-results.md), [deployment/recovery](deployment-and-recovery.md),
[tester guide](external-tester-guide.md), and [release checklist](release-checklist.md).

## Initial findings and priorities

| ID | Priority | Finding and consequence | Planned acceptance evidence |
| --- | --- | --- | --- |
| R01 | High | Python and SDK discovery trust indexer cell contents without checking current node liveness. A stale indexer can keep a spent/revoked record eligible. | Reproduce stale active cell; require trusted node verification, reject changed bytes/lock/type, fail closed on RPC failure; lifecycle regressions remain green. |
| R02 | High investigation | Discovery has per-request and page bounds, but a slow refresh can leave the old receiver set usable throughout many requests. | Bound the complete refresh; exercise an outage/timeout and confirm old geometry and pending observations are removed. |
| R03 | Medium | Diagnostic exports restrict field names but include untrusted free-form clock-source strings. The nested exporter also fails mypy. | Probe sensitive values through the real export endpoint, constrain output, preserve useful clock status, pass static checks. |
| R04 | Medium | Four pre-existing files fail Black; one exporter assignment fails mypy. | Run the exact failing checks after scoped repairs. No numerical solver changes. |
| R05 | Medium | Existing audit environment has no pip module. Its successful tests do not establish a clean dependency installation. | New isolated install using hash-locked requirements; dependency consistency check and recorded versions. |
| R06 | Production blocker | Prior report permits conditional external validation, but a clean source-bound release and executed container recovery evidence are absent. Docker executable is unavailable locally. | Retain local results, verify clean setup where possible, leave container/target-host gates blocked until executed. |
| R07 | Production blocker | No supplied authorized physical multi-receiver campaign or independent live reference truth. | Preserve explicit synthetic/historical labels; do not assert live MLAT accuracy. |
| R08 | Production blocker | Solver historical altitude errors and rejections are material. Quality scores are uncalibrated. | Repeat all 362 historical events, five-receiver MPyC fixture, synthetic control; preserve failures and report all error axes. |
| R09 | External participation | Fresh signed testnet lifecycle spends capacity and requires an operator wallet. The mission forbids spending funds. | Execute offline contract/SDK/evidence checks and read-only testnet verification; document the unexecuted signed lifecycle separately. |
| R10 | Production gap | Public API/read exposure, single-process limiter, Socket.IO subscriptions, SQLite retention and backup ownership require deployment-specific policy. | Inventory all routes and trust boundaries, run existing access/recovery tests, disclose policy and operational limits. |
| R11 | Production gap | Independent contract review, sustained representative load, alert routing, restore on target host, incident ownership are not established by repository tests. | Explicit release checklist with evidence requirements and no inferred passes. |

No confirmed critical defect has been identified at this point. That statement is
limited to the work reviewed; it is not an independent security certification.

## Baseline recorded before fixes

Each command has an immutable `<check>.json` record (arguments, working directory,
UTC start, duration, exit status) and `<check>.log` under
`artifacts/readiness-2026-10-19/`. Runs use `MLAT_ENV_FILE=/dev/null`, Python
3.12.11 from `artifacts/audit/venv`, and Node 22.23.1. Default shell versions differ
(Python 3.13.7 / Node 20.19.6) and are not used as the supported baseline.

Initial results: Python **276 passed**; SDK **73 passed**; contract build and
**16 tests passed**; Flake8 passed. Black failed on four existing files. Mypy
failed on one exporter assignment. `python -m pip check` failed because this
environment has no pip module, rather than because a dependency conflict was
demonstrated. Frontend production build and remaining checks are pending.

## Implementation plan and phase acceptance

1. **Baseline and architecture.** Read configuration, entry points, ADRs, old
   evidence and workflow commands. Record current results and source hashes;
   document chain/feed/storage/browser trust boundaries before repairs.
2. **Security and correctness.** Reproduce R01–R03 at the real consumer/export
   boundaries. Make minimal changes, with tests that fail before and pass after.
   Preserve the deployed contract, signatures, data fixtures and solver equations.
3. **Registry lifecycle.** Run CKB-VM lifecycle, SDK authorization/conformance,
   runtime revocation/outage/restart tests and saved evidence verification. Read-only
   testnet checks must be explicitly distinguished from fresh wallet operations.
4. **MLAT qualification and benchmarks.** Verify frame identity, integer timing,
   clock bounds, current receiver geometry and isolation of replay. Repeat the
   unchanged numerical solver benchmark twice; retain the full historical failures.
5. **Failure and recovery.** Run transport/reconnect, SQLite migration/backup,
   retention, concurrency and process restart tests. Measure a bounded synthetic
   load and state its duration, latency, memory and failure limits.
6. **API, dashboard and diagnostics.** Check endpoint access/input bounds, export
   redaction, production frontend build, unit tests and synthetic/historical browser
   suites. No cosmetic redesign is needed for the audit.
7. **Reproducible setup and operations.** Provide safe local test configuration,
   installation, replay/demo, diagnostic export, backup/restore and reset steps.
   Separate operator-only live/testnet/deployment steps from offline instructions.
8. **Final verification.** Re-run affected and full checks, inspect only this run's
   delta against the starting hashes, preserve exact command outcomes, and assess
   Gates A/B/C independently. Unavailable infrastructure remains blocked.

## Evidence interpretation

`PASS` means the named command actually completed with its expected result.
`FAIL` means it ran and failed. `BLOCKED` means a needed capability or permission
is unavailable. `NOT RUN` is never a pass. Existing failures are distinguished from
new regressions. A historical signed transaction is evidence of that transaction,
not a transaction performed during this audit. CKB records authorization and
lifecycle; it does not prove receiver existence, location, clock accuracy or truth.

## Completed phases and result

| Phase | Work completed and acceptance result |
| --- | --- |
| 1. Baseline / architecture | Inventoried 736 starting files, dirty `main` and recent commits; inspected ADRs, configuration, deployment, contract/SDK, processor, API/storage and frontend. Reproduced baseline failures before changes. |
| 2. Security / correctness | R01 stale cells, altered owner/data/type, node outage; R02 whole-scan deadline; R03 diagnostic URL leakage reproduced before fixes. Fixed with permanent Python/SDK regressions. Fixed formatting/type failures without changing solver behavior. |
| 3. Lifecycle / revocation | Contract/SDK/conformance pass. Actual public node confirms saved lifecycle/code cell; repaired discovery verified two records, one revoked. Added runtime test proving stale indexer records cannot keep observations buffered after node revocation. No signed transactions. |
| 4. Qualification / benchmarks | Original solver and all starting fixture hashes unchanged. Two compact runs and two synthetic bundles match byte-for-byte. All 362 historical outcomes retained. |
| 5. End-to-end / recovery | Added synthetic mock-chain → JSON → qualification → correlation → solver → SQLite → API regression. Existing failures/reconnect/migration tests pass. Two-minute process restart and actual backup/restore CLI pass; restored historical counts 270 positions / 362 events and mode preserved. |
| 6. API / UI / diagnostics | API/route/threat review; 31 synthetic and now 3 historical browser tests pass. New actual link/pagination regression resolved manual automation uncertainty. Diagnostic export sanitization and continued-stream authorization repaired. No frontend redesign. |
| 7. Setup / operations | Eight requested documents, safe test environment, tester scenarios/feedback/reset and deployment/backup/rollback procedures provided. Fresh locked Python environment and package installation verified. |
| 8. Final verification | 293 Python, 78 SDK, 60 frontend unit, 16 contract tests; 57 shared cases / 171 assertions; build/type/format/lint/docs checks pass. Unavailable deployment/physical/independent evidence remains explicitly blocked. |

The final evidence index is [the dated evidence README](../../evidence/production-readiness-2026-10-19/README.md).
Exact commands and failure history are in its command ledger; local full logs and
temporary databases remain under `artifacts/readiness-2026-10-19/`.

### Additional verified finding: continued streaming after access revocation

The initial endpoint review led to a high-priority authorization defect: joining
a Socket.IO room checked access once, but subsequent broadcasts did not. Four
new tests demonstrated continued delivery after key revocation, account
suspension, entitlement revocation or expiry. The API now checks current database
authorization before each delivery, removes unauthorized room members and
withholds delivery if storage cannot verify access. Only internal key IDs are
retained; subscription state is bounded and discarded on disconnect. All four
cases, storage-outage and state-bound regressions pass.

### Changes made by this run

| Files / components | Change and reason | Verification |
| --- | --- | --- |
| Python discovery; TypeScript discovery/lifecycle | Cross-check node liveness, complete output and data; bound scans; keep RPC failure outside record-skipping logic | Red/green regressions, real read-only testnet, protocol/lifecycle suites |
| API and database access lookup | Revalidate active streaming access by stored key ID, remove unauthorized subscriptions, bound/clean up state | Four revocation cases, database outage, 100-subscription boundary, existing payload/access tests |
| Diagnostic export and feed/discovery logs | Omit arbitrary clock-source export; stop echoing untrusted receiver IDs/parser/RPC error text; fix exporter typing | Sentinel URL regressions and static checks |
| Existing conformance adapters/tests | Supply matching mock node responses for the strengthened boundary; corpus unchanged | All three implementations still agree on 171 assertions |
| Runtime, existing recovery/soak files | Formatting only; pre-existing geometry/recovery work preserved | Black and full regression suite; no new solver equations |
| Pipeline measurement tool | Add P99 latency to existing output | Nine measured scenarios; no speedup claimed |
| Frontend Dockerfile | Copy public pilot diagram assets imported from outside the frontend directory; the original build stage omitted them | Isolated build reproduced missing-image errors; corrected build layout rechecked. Docker execution remains unavailable. |
| New registry-authority and chain-to-API tests; historical browser navigation test | Exercise gaps missed by the starting suite | 293 Python / 3 historical browser checks pass |
| Readiness documents, safe example and README link | Make setup, evidence scope, operating limits and release blockers reviewable | Documentation/environment/hygiene checks |

The majority of the broad Git diff predates this run. Starting hashes and the
dated change ledger distinguish these scoped edits. No existing repository file,
historical evidence package, contract deployment or benchmark fixture was deleted
or replaced. No commit, push, deployment or migration of real infrastructure occurred.

### Results and failures retained

The final isolated dependency/build check found another high-priority packaging
defect: `/pilot` imports two PNGs from `docs/pilot/assets`, but the frontend image
builder copied only SDK and frontend directories. The clean layout failed with
both missing-image imports. The Dockerfile now copies the required public assets;
the repaired build layout then completed `npm run build` with exit 0 from freshly
installed dependencies. This is separate from unavailable Docker execution.

Initial suite: **276 passed**. Final full Python suite: **293 passed**. The current
SDK has **78** passing tests, frontend unit suite **60**, contract **16**, browser
**31 synthetic + 3 historical**. Frontend production build and typecheck pass.
Black/Flake8/mypy pass; mypy explicitly leaves untyped function bodies and missing
third-party stub detail outside its checked scope.

Intentional red tests, the initial static failures, sandbox DNS failure, missing
pip, an isolated npm configuration collision corrected before installation, an early scanner attempt before installation completed, a missing node method
in an old SDK mock, a transient fallback-type error introduced then corrected,
and the first new end-to-end fixture's unintended demo receiver top-up are all
retained. The last fixture was configured to avoid automatic top-up; assertions
and benchmark data were not weakened. Cargo audit is not installed (availability
command exit 101); Rust advisory scanning and CodeQL are not claimed.

Python's fresh advisory scan reports zero known vulnerabilities. Npm reports only
low-severity transitive wallet dependency advisories (21 frontend / 4 SDK affected
nodes), with no moderate/high/critical advisories. No forced dependency downgrade
was made. Dedicated whole-history secret scanning was not performed.

The historical benchmark remains **270/362 solved**, with **92 rejected** and a
**2963.7 m P95 3D error** among solved events. Local load measurements and the
restart sample are experimental. They do not establish production accuracy,
availability or a performance improvement.

### Remaining blockers

1. Review/commit the working tree and run clean source-bound CI, container startup,
   persistence, restore and rollback on the intended host. Docker is unavailable here.
2. Obtain separately authorized fresh testnet lifecycle evidence and independent
   security review. Existing history/read-only checks do not replace these.
3. Validate authorized physical receivers, their clocks/geometry and a suitable
   reference window; establish deployment access/retention policy, sustained load,
   monitoring/incident ownership and acceptable accuracy, especially altitude.

See the [release checklist](release-checklist.md) for each gate's unchecked items.
The application is better prepared for review and local controlled testing; it
is **not declared production-ready or fully released for external testing**.
