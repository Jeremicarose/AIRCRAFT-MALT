# Production-readiness review

Audit started 8 October 2026; final review continued 13 October 2026.

## Executive summary

The repository already had a strong Registry V2 lifecycle implementation and
extensive tests. The largest gaps were in the MLAT consumer's trust boundaries,
provenance, resource limits, and interpretation of historical/synthetic results.
Passing tests had not detected several real failures: untrusted feed destinations
receiving credentials, arbitrary timestamps entering correlation, unbounded
deduplication/notification state, repeated solves after partial group expiry,
six historical results overwritten by a timestamp-only storage key, and an
aircraft inspector that stayed empty after a cold start.

Those paths have been hardened and covered by regression tests. The compact
dataset is now bundled with attribution, processed without changing numerical
solver behavior, and inspectable through an isolated historical storage/API/UI
path. Operators can distinguish Registry state, observed operation and explicit
clock qualification. Quality scores are labelled as heuristics.

**This is ready for controlled external validation with the conditions below.
It is not a claim of production live MLAT readiness or an independent security
audit.** No physical receiver, participant, aircraft, or on-chain transaction was
fabricated. No transaction was signed or broadcast during this mission.

## Scope and evidence

- [Initial findings](2026-10-08-initial-audit.md), written before implementation.
- [673-file starting inventory](2026-10-08-file-inventory.csv), with classification,
  disposition, reason and starting checksum for each source/unignored file.
- [Task change ledger](2026-10-08-changes.csv), distinguishing this mission from
  the substantial pre-existing uncommitted changes.
- [Complete compact benchmark](../../evidence/mlat-reference/compact-public-solver-v2/report.json)
  and [interpretation](../mlat/compact-public-solver-benchmark.md).
- [Validation evidence](../../evidence/mlat-reference/production-readiness-2026-10/README.md).

This was a source/runtime audit, not a proof that every possible defect has been
eliminated. Historical signed evidence was preserved. No wallet approval or
external communication was performed.

## Executed validation

| Check | Result |
|---|---|
| Clean Python installation | Python 3.12.11, hash-locked development dependencies; Werkzeug 3.1.9 |
| Python unit/integration/security suite | 257 passed |
| Python formatting/lint | Black and Flake8 pass |
| Python static types | Mypy passes 28 source files using its normal typed-function checking; missing third-party stubs ignored |
| Frontend unit/contract checks | 60 passed |
| Frontend production build/typecheck | Pass; the repository's lint script also invokes TypeScript, not a separate ESLint ruleset |
| TypeScript Registry SDK | 72 passed |
| Rust contract | Build/check and 16 tests pass, including 11 CKB-VM transaction tests |
| Shared protocol conformance | 57 cases, 171 assertions, all three implementations agree |
| Browser suites | 31 synthetic console checks and 2 historical replay checks pass; accessibility included |
| Compact benchmark | 362 events, byte-identical repeat output in the pinned local environment |
| Synthetic evidence bundle | New v3 package reproduces byte-for-byte and verifies its checksums |
| Dependency security | Production Python scan has zero known vulnerabilities; frontend has no moderate/high/critical advisories, with one low advisory propagated through 21 packages |
| CKB connectivity | Read-only live code-cell hash and paginated indexer checks pass with TLS verification |
| Documentation/hygiene | Link/environment/repository checks and git diff whitespace check pass |
| Manual browser review | Synthetic overview/aircraft plus historical successful/rejected events inspected, including mobile and stage navigation |
| Containers / external release | Not executed locally: no Docker engine; updated remote CI has not been run for a new clean commit |

Browser release-evidence reports deliberately retain `pass=false` when the Git
worktree is uncommitted, even though every test passed. This is the existing source
binding requirement, not a hidden failing test. Review/commit and rerun CI before
using these results as release evidence.

## Files removed

**No existing repository file was deleted.** The previous repository cleanup had
already removed competing solver/frontends. The remaining fixtures, historical
bundles, deployment artifacts and pilot work have deliberate uses. The untracked
`job-search/` material and unrelated `opportunity-pipeline/` work belong to the user's pre-existing workspace and was retained.

Two unreferenced executable examples were removed from otherwise required modules:
the database module's standalone `test_mlat.db` demonstration and the network
client's example using a placeholder Registry hash. Searches found no callers or
documented commands depending on either; dedicated tests and supported launchers
cover their useful behavior. Python's optional import fallback for required
dotenv/CORS dependencies was also removed so incomplete installs fail clearly.

## Files added

The exact list is in the task change ledger. The main additions are:

| Files | Purpose |
|---|---|
| `src/mlat_reference/ingest/validation.py` | Bounded strict JSON, integer timestamps, frame/CRC validation and shared clock gate |
| `src/mlat_reference/provenance.py`, `diagnostics.py`, `api/health.py` | Persistent source vocabulary, allowlisted structured events and actionable component health |
| `src/mlat_reference/replay.py`, `tools/mlat/replay_compact_dataset.py`, `run-replay.sh` | Isolated checksum-verified historical processing and read-only API launch |
| `src/mlat_reference/benchmarks/diagnostics.py` | Observe existing solver rejection decisions without changing equations or thresholds |
| `reference/mlat/benchmarks/fixtures/compact-public/` | Unmodified attributed source CSVs for offline reproduction |
| Frontend `/app/replay` route and historical replay page | Event/outcome browsing, stage inspection, geometry and original relative timestamps |
| New Python security/provenance/replay tests and historical browser suite | Regressions at the real ingest, database, API and browser boundaries |
| `tools/mlat/measure_pipeline_envelope.py` | Repeatable measured in-process 4/5/10-receiver workloads |
| Audit, replay and operations documentation; new evidence packages | Executed findings, provenance, checksums and honest readiness limits |

## Important files modified

- **Feed client/transports and base runtime:** exact endpoint allowlisting,
  credential scoping, redirect refusal, strict input validation, bounded child
  shutdown, no secret-bearing stderr/argv logs, no implicit synthetic fallback
  for broken live configuration, stale/out-of-order rejection.
- **Correlator:** bounded buffers and deduplication, batched cleanup, identical
  observation deduplication, conflicting-claim rejection and atomic group removal.
- **Database:** transactional schema version 2, persistent provenance/geometry/
  nanoseconds/event identity, idempotent event storage, mode binding, bounded
  notification queues, correct memory-database initialization and safe retention.
- **Runtime/API:** current receiver qualification and reset on lifecycle changes,
  stored telemetry snapshots, storage failure reporting, source-aware API output,
  bounded aircraft/replay queries, malformed Socket.IO payload rejection and
  allowlisted diagnostic export.
- **Solver:** type annotations/casts only. Removing typing constructs leaves the
  original executable AST unchanged. Full compact accuracy aggregates exactly
  match the initial unchanged-solver run on this host.
- **Frontend:** explicit provenance, clock qualification in the receiver journey,
  heuristic quality wording, no uncalibrated map error circle, mobile keyboard
  focus and automatic aircraft selection after initially empty data.
- **Dependencies/deployment/CI:** patched dependency locks, non-root Python image,
  required public assets/tools in the image, safer build context, new benchmark
  and historical browser CI checks, and new versioned reproducibility bundle.

## Bugs fixed by severity

| Severity | Fixed issues |
|---|---|
| Critical | No confirmed critical defect was identified. This is not a guarantee from an independent audit. |
| High | Registry-controlled feed destinations could receive credentials or target unintended addresses; missing/fractional/malformed timestamps and frames entered ingest; live transport configuration could fall through to synthetic traffic; stored data could be relabelled by a later runtime and synthetic retention could delete unrelated rows; absent telemetry could be called live; two high npm advisories were patched. |
| Medium | Six historical results overwrote other events; processed groups/notification queues grew indefinitely; partially expired groups could solve twice; noisy child stderr could deadlock ingest; child shutdown could wait indefinitely; Registry RPC/cell decoding had missing size bounds and cursor cycles; stale clocks remained qualified; owner/geometry updates retained prior observations; invalid API/Socket.IO inputs were insufficiently checked; schema initialization confused separate memory databases; synthetic aircraft reused transmission times; empty-start aircraft selection stalled; scrollable status content lacked keyboard focus; benchmark statistics had invalid definition-list markup; installed API startup used a development server; a moderate Python dependency advisory was patched. |
| Low | Formatting failure, stale demo/replay terminology, missing environment documentation, missing OSM attribution link and misleading confidence wording. |

## Security improvements

Registry lifecycle and owner-lock logic were preserved. No Type-ID override,
signature bypass, revocation exception or clock gate relaxation was introduced.
Receiver-controlled URLs now require exact operator permission; credentials are
limited to the configured URL and never follow redirects. JSON/frame/time bounds
apply before correlation. Invalid observations cannot refresh operational status.
Historical receivers remain unqualified for live operation.

`sharp` and `source-map-js` were patched according to their
[upstream advisories](https://github.com/advisories/GHSA-wq5f-xc86-pv6w),
[source-map advisory](https://github.com/advisories/GHSA-68fv-2mgg-jv7q).
Werkzeug was updated to 3.1.9 for the
[Windows path-handling advisory](https://github.com/pallets/werkzeug/security/advisories/GHSA-g6x2-hccm-hh4m).
The Python lockfile scan then reported zero known vulnerabilities. The frontend
retains a low-severity elliptic advisory propagated through its wallet dependency
chain; npm's proposed force fix would downgrade the connector and was not applied.

## Performance improvements and limits

The identical 2,000-observation buffer experiment improved from approximately
177–204 ms to 2–3 ms by removing repeated full-buffer scans. This is a local
microbenchmark of a measured bottleneck, not full-system throughput.

Nine in-process scenarios exercised 4, 5 and 10 concurrent synthetic feed callbacks,
three aircraft and 100 events per scenario. Every scenario stored exactly 100
solutions after the duplicate-solve fix. The measured results below include
targets the local process could not sustain.

| Receivers | Target obs/s | Achieved obs/s | Pipeline P95 ms | CPU seconds | Peak process RSS MB |
|---:|---:|---:|---:|---:|---:|
| 4 | 100 | 100.0 | 21.31 | 1.177 | 34.0 |
| 4 | 1000 | 495.8 | 9.45 | 0.783 | 34.2 |
| 4 | 10000 | 478.7 | 9.96 | 0.804 | 34.3 |
| 5 | 100 | 100.0 | 6.46 | 0.389 | 34.4 |
| 5 | 1000 | 999.8 | 4.16 | 0.320 | 34.5 |
| 5 | 10000 | 1562.5 | 3.31 | 0.219 | 34.6 |
| 10 | 100 | 100.0 | 9.46 | 0.612 | 34.7 |
| 10 | 1000 | 999.7 | 7.78 | 0.515 | 34.8 |
| 10 | 10000 | 2657.8 | 5.50 | 0.356 | 34.8 |

The four-receiver path has a different existing solver initialization; its lower
rate was measured and retained. The evidence JSON also contains per-stage median,
P95 and maximum latency, buffer state and write counts. Logging was suppressed.
These are short local runs, not external network load, full logging cost,
production batching latency, long-duration soak tests or multi-node claims.
Peak RSS is cumulative for the process and cannot be read as per-scenario growth.

## UX improvements

The console distinguishes SYNTHETIC, HISTORICAL REPLAY, LIVE and UNKNOWN. Cached
labels retain their original source. Receiver registration, declared capability,
feed freshness and clock qualification are separate. Aircraft solutions expose
contributors, geometry, residual, iterations, source and limitations. Historical
events retain failures and original relative timestamps. The diagnostic page shows
component reasons/actions and exports an allowlisted incident bundle.

Automated browser checks cover keyboard navigation, accessibility, mobile layouts,
map failure isolation, source labelling, cold-start selection and contribution
navigation. Manual browser review supplements those tests. See validation evidence
for screenshots and the exact observed scope.

## MLAT benchmark

**362 total; 270 solved; 92 failed; 74.586% success.** All failed candidates were
rejected for altitude outside -500..15,000 m. The synthetic control passed at
approximately 0.45 m 3D error. Event 5711382 measured approximately 31.46 m horizontal,
21.54 m vertical and 38.13 m 3D error.

| Solved-event error, metres | Median | P95 | Maximum |
|---|---:|---:|---:|
| Horizontal | 59.052 | 295.921 | 961.568 |
| Vertical | 382.416 | 2961.128 | 9612.893 |
| 3D | 399.580 | 2963.702 | 9612.981 |

Residual median/P95/maximum: **5.791 / 20.725 / 128.409 m**.
Successful best-candidate iterations: **11 median, 28.1 P95, 74 maximum**.
Failed best-candidate iterations: **11 median, 25.7 P95, 86 maximum**.
There are 26 distinct receivers across the dataset, five per event. Failed events
more often include a closely spaced receiver pair, but the geometry statistics do
not support assigning one universal cause. Vertical error dominates the tail.

The complete report includes every event, geometry statistics, failure categories,
dataset/fixture/implementation checksums, benchmark version, solver base commit,
explicit worktree-modified flag, Python/NumPy versions and output checksum.
These values are numerical regression evidence, not an accuracy certification.

## Remaining limitations

1. No physical synchronized receiver campaign was performed. Registration,
   location, timing and observation truth are different claims.
2. Compact replay lacks original frames, historical CKB identity and measured
   clock uncertainty. It validates the historical adapter/solver/storage/API/UI,
   not every live acquisition/qualification stage. The debugger inspects recorded
   stages; it is not a real-time replay scheduler.
3. The solver rejects 25.4% of these events and has substantial altitude errors
   on some accepted events. Uncertainty is not calibrated.
4. The Registry contract is testnet-only and has no independent audit. No new
   wallet-signed browser lifecycle or mainnet release was attempted.
5. Docker was unavailable locally. Image changes and updated GitHub workflows
   require their actual CI/container runs before deployment. No deployment was made.
6. SQLite is single-node; the limiter is process-local; external network throughput,
   restart/restore procedures on the target host and long-duration reliability
   still need an operator validation window.
7. Some wallet dependencies retain a low advisory. No blanket claim of absence
   of vulnerabilities is made from automated scans.
8. The initial workspace contained substantial uncommitted work. This mission
   preserved it and leaves reviewable changes; it did not invent a clean Git commit
   or rewrite historical signed evidence.

## Production-readiness classification

| Area | Classification | Meaning |
|---|---|---|
| Solver | READY WITH CONDITIONS | Reproducible numerical baseline; altitude/error limits prevent field-accuracy claims |
| Registry | READY WITH CONDITIONS | Suitable for controlled testnet review; independent contract audit and operator key policy remain necessary |
| Backend | READY WITH CONDITIONS | Tested single-node validation service; deployment/soak/restore conditions remain |
| Frontend | READY WITH CONDITIONS | Built and browser-tested operator console; real wallet lifecycle still needs an external operator |
| Replay | READY WITH CONDITIONS | Compact historical inspection is reproducible; missing raw frame/clock/identity evidence stays explicit |
| Live MLAT | NOT READY | No physical synchronized receiver evidence window |
| CKB integration | READY WITH CONDITIONS | Current immutable code cell and paginated indexer were read successfully; this does not attest hardware truth |
| Deployment | NOT READY | No local Docker engine or fresh external deployment validation for this change |

## Necessary next steps

1. Review and commit the preserved workspace changes, then run the updated CI and
   container checks on that exact commit.
2. Run an independent Registry security review and a controlled wallet lifecycle
   with a real testnet operator.
3. Collect a synchronized physical receiver window with original frames, calibrated
   clocks, geometry evidence and independent position references. Keep the current
   benchmark as the baseline rather than tuning to one selected event.
4. Validate backups, restore, shutdown/restart, transport failures and sustained
   load on the intended single-node deployment before claiming an operational SLO.
