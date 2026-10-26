# Test plan and execution record

19 October 2026. The [audit](audit.md) distinguishes the starting baseline from
repairs. Exact argument arrays, working directories, UTC times, durations, exit
codes and logs are in `artifacts/readiness-2026-10-19/`; `commands.json` is the
combined ledger. The dated evidence directory referenced by the audit retains
the principal records. Failed attempts are preserved, not overwritten.

## Environments and commands

Commands below run from the repository root unless a directory is stated.
`python` means Python 3.12.11 with `MLAT_ENV_FILE=/dev/null`; npm uses Node
22.23.1. The baseline used `artifacts/audit/venv`; the final full suite also ran
in a newly created `artifacts/readiness-2026-10-19/venv` installed from the lock.

| Check / exact command | Outcome |
| --- | --- |
| `python -m pytest -q` | Baseline: 276 passed, exit 0. Final full run: 293 passed, exit 0. |
| `python -m black --check src/ckb_registry src/mlat_reference tools tests` | Baseline exit 1, four existing files; after formatting, exit 0. |
| `python -m flake8 src/ckb_registry src/mlat_reference tools tests` | Baseline and final exit 0. |
| `python -m mypy src --ignore-missing-imports` | Baseline exporter error repaired. A new fallback Socket.IO typing error was caught and fixed; final exit 0. Untyped bodies and missing third-party stubs are not fully checked. |
| `uv --native-tls --cache-dir artifacts/audit/uv-cache pip sync --python artifacts/readiness-2026-10-19/venv/bin/python --require-hashes requirements-dev.lock` | Clean install exit 0. Initial sandbox DNS failure retained separately. |
| `uv --cache-dir artifacts/audit/uv-cache pip check --python artifacts/readiness-2026-10-19/venv/bin/python` | Exit 0. Baseline `python -m pip check` could not run because pip was absent. |
| `uv --cache-dir artifacts/audit/uv-cache pip install --python artifacts/readiness-2026-10-19/venv/bin/python --no-deps --no-build-isolation .` | Wheel built and installed, exit 0. |
| SDK: `npm test` | Baseline 73; final 78 tests passed, exit 0, including TypeScript compilation. |
| Frontend: `npm test` | 60 passed, exit 0. |
| Frontend: `npm run build`; `npm run typecheck` | Exit 0; production build repeated after SDK repair. `npm run lint` is the same TypeScript command, not ESLint. |
| Contract: `make test`; `make check`; `cargo fmt -- --check` | Exit 0; 5 library and 11 CKB-VM tests. No contract edits. |
| `python tools/registry/generate_registry_v2_conformance_report.py --output artifacts/readiness-2026-10-19/conformance-report.json` | 57 cases / 171 assertions agree across Rust, Python and TypeScript, exit 0. |
| `python tools/registry/verify_registry_v2_evidence.py --bundle evidence/registry-v2-testnet-2026-09-11-data1-final --saved-chain-only --output artifacts/readiness-2026-10-19/saved-chain-report.json` | Exit 0; saved evidence, no network claims. |
| Same verifier with `--live-chain-only --output artifacts/readiness-2026-10-19/live-chain-report.json` | Exit 0; public node confirms recorded transaction bodies and live immutable code cell. GitHub provenance intentionally not checked by this mode. |
| `PYTHONPATH=src python artifacts/readiness-2026-10-19/verify_discovery.py` | Exit 0; two node-verified records, one revoked, zero quarantined; no transactions signed. |
| `python -m pip_audit --disable-pip --no-deps -r requirements.lock --format json --output artifacts/readiness-2026-10-19/python-advisories-report.json` in isolated locked scanner environment | Exit 0; no known vulnerabilities. First attempt ran before scanner installation finished and failed; retained. |
| Frontend and SDK: `npm audit --audit-level=moderate --json` | Exit 0; 21 and 4 low-severity affected dependency nodes respectively, zero moderate/high/critical. These include transitive paths from elliptic, not 25 distinct flaws. |
| Frontend: `npm run test:e2e:prepared` | 31 passed, exit 0, synthetic services. |
| Frontend: `npm run test:e2e:replay` | Initial 2 passed; expanded navigation suite 3 passed, exit 0. |
| `python tools/mlat/run_process_soak.py --duration-seconds 120 --interval-seconds 1 --output-dir artifacts/readiness-2026-10-19/process-soak` | Exit 0; startup, real HTTP, restart, persistence and shutdown. One failed sample during restart is retained. |
| `docker info` | BLOCKED: executable absent; no container execution claim. |
| Contract: `cargo audit --version` | Exit 101: cargo-audit is not installed; Rust vulnerability scanning remains unexecuted. |

Fresh SDK and frontend `npm ci --no-audit --cache /tmp/mlat-readiness-npm-cache`
installations also succeeded in `artifacts/readiness-2026-10-19/clean-js/`, using
source copies without node_modules or environment files and separate empty npm
user/global configuration files. This is a materialized working-tree setup, not
a claim that an uncommitted change exists in a clean Git revision.
The first isolated frontend `npm run build` failed because the image's copied
source layout omitted public pilot PNG imports. After adding those assets to the
Dockerfile and isolated layout, `npm run build` exited 0 from freshly installed
dependencies. Actual Docker execution is still blocked.

Browser commands set `PLAYWRIGHT_PYTHON_DIR` to the fresh environment and distinct
`BROWSER_QA_REPORT` paths. Historical mode also sets `PLAYWRIGHT_DATA_MODE=historical`.
Reports have zero failed tests, but **`pass=false` for release provenance** because
`worktree_clean=false`. A passing command does not override this release gate.

The final installed `mlat-api` was also started from outside the source tree,
with source `PYTHONPATH` removed, in a fresh temporary database. Liveness and
diagnostics returned 200 with UNKNOWN provenance, and shutdown exited 0.
Actual backup/restore CLI copies of the historical database retained 270 positions,
362 events, HISTORICAL_REPLAY provenance and SQLite integrity `ok`.

Formatting commands and exploratory browser operations are also described in
the audit/change ledger. Benchmark commands and numerical results are in
[benchmark results](benchmark-results.md). Documentation/environment/repository
checks and `git diff --check` form the final hygiene checks.

## Regression coverage and fault scenarios

| Boundary | Permanent checks |
| --- | --- |
| Actual contract transitions | `contracts/registry-v2/tests/lifecycle.rs`: creation, duplicate outputs, oversized records, immutable labels, sequence, wrong signatures, transfer, revocation, resurrection and burn rejection |
| RPC/indexer | `tests/registry/test_discovery_authority.py`: spent/unknown cells, altered bytes/owner/type, RPC outage, scan timeout, pending-observation removal; existing pagination/conflict tests |
| SDK authorization | `sdk/typescript/test/{conformance,lifecycle}.test.ts`: fresh node evidence for reads and transaction preparation, deadlines, signer/network/owner checks |
| Full local pipeline | `tests/mlat/test_registry_pipeline_e2e.py`: mocked node+indexer → discovery → bound JSON → clocks → correlation → actual solver → SQLite → Flask API, then spent cells excluded while indexer remains stale. All stored results are SYNTHETIC. |
| Feed attacks and ordering | `test_input_security.py`, `test_feed_transports.py`, `test_correlator.py`: malformed/deep/oversized JSON, duplicate keys, invalid frame/time/clock, spoofing, duplicate/out-of-order records, bounded buffers |
| Feed recovery | `test_transport_recovery.py`, `test_runtime_guardrails.py`: redirects, failures/reconnects, noisy child stderr, bounded termination, registry outage and return |
| Clock and geometry | `test_failure_recovery.py`, `test_solver.py`, `test_production_mlat_pipeline.py`: insufficient/coincident geometry, missing clocks, nanoseconds, coordinate conversion, physical output checks |
| Storage | `test_database.py`, `test_storage_provenance.py`, `test_backup_recovery.py`: identity/deduplication, mode isolation, concurrent threads, migration rollback, WAL backup, no-overwrite restore, provenance retained |
| API/auth/diagnostics | `test_api.py`, `test_remediation_security.py`, `test_api_provenance.py`: admin keys, plan bounds, CORS, rate limiting, malformed inputs, four streaming revocation/expiry cases, storage outage, subscription bounds, sensitive-value sentinels |
| Browser | Existing synthetic and historical Playwright suites: source labels, access controls, loading/empty/error states, mobile/keyboard and accessibility, rejected historical events |

No percentage line/branch coverage was collected; the project does not configure
a coverage gate. Passing 293 tests is not 100% path coverage. Major untested paths:
physical timing hardware, real network partitions under sustained load, current
signed wallet operations, chain reorganizations, target-host crash/power loss,
disk exhaustion under production load, distributed workers and incident response.

## API review inventory

| Routes | Access and validation | Limits / disclosure |
| --- | --- | --- |
| `/healthz`, `/api/health`, `/api/readiness` | Public process/component evidence | Liveness is not full readiness; registry health uses last completed discovery |
| `/api/system/mode`, `/api/pipeline`, `/api/diagnostics/bundle` | Public operational read; diagnostic allowlist | Do not expose private deployments without an authenticated gateway |
| `/api/benchmark/latest`, `/api/evidence/solver-benchmark/latest`, `/api/evidence/performance/latest`, `/api/evidence/reliability/latest`, `/api/evidence/metrics`, `/api/registry/evidence` | Public bounded local report reads | Missing/invalid evidence is unavailable, not a success; no request-controlled file path |
| `/api/receivers` | Public current runtime inventory | Includes coordinates/owner public chain metadata; not a complete registry history; no pagination for this capacity-limited runtime inventory |
| `/api/aircraft`, `/api/positions/recent` | Public with plan-dependent history/count limits | Aircraft time window ≤86,400 s; recent positions ≤100 public / ≤1,000 premium |
| `/api/aircraft/<id>/track`, `/latest` | Parameterized lookups; finite bounds for track history | Track ≤250 public / ≤5,000 premium; public latest/coordinates are a deliberate disclosure |
| `/api/replay`, `/api/replay/events/<id>` | Historical mode required for list; bounded page/offset and numeric event IDs | Dataset provenance remains historical; no wallet identity claim |
| `/api/statistics` | Premium API access | Operational aggregate; strengthen deployment-specific query/rate policy before exposure |
| `/api/admin/cleanup` | POST, disabled by default, constant-time admin secret comparison, JSON days 1..365 | Destructive local maintenance; never enabled for external testers |
| `/`, `/api`, `/dashboard`, `/dashboard.html`, `/app[/<path>]` | Landing/documentation or frontend routing responses | No legacy hidden dashboard fallback |
| Socket.IO `connect`, `subscribe_aircraft`, position events | Subscription requires active key/account/streaming plan/entitlement; rechecked on delivery | Per-session/total subscription bounds; edge connection/event limits still needed |

## Operator-only acceptance campaign

Fresh testnet writes remain NOT RUN: signing and capacity spending are outside
this mission's authorization. With a separately approved test wallet, exercise
create → discover → update → transfer → wrong-owner rejection → revoke → restart
and verify the tombstone and runtime exclusion. Two identical labels are allowed;
reusing the same Type ID as an independent creation is not. Save transaction IDs,
node/indexer captures, source commit and SDK version; never save wallet secrets.

For live MLAT, obtain authorization for at least four suitably placed receivers,
surveyed or otherwise evidenced locations, common timebase and measured clock
uncertainty. Capture complete frames and integer arrival times, introduce one
controlled feed outage and revoke one test identity, then compare to an appropriate
independent reference. Agree expected event rates, outage policy and accuracy
thresholds before collecting data. Synthetic/historical results cannot satisfy it.
