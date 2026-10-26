# Initial production-readiness audit, 8 October 2026

This records the application **before this audit's implementation changes**.
The starting commit is `df82f6c`; the workspace already contains substantial
uncommitted frontend, API, benchmark, and pilot-documentation work. Those changes
are inputs to this review, not changes produced by this mission. No existing
work, private configuration, or historical evidence is discarded.

## Architecture and scope

Registry V2 is the primary product. Rust enforces Type-ID creation, owner-lock
authorization, exact sequence progression, immutable receiver labels, and
terminal revocation. Python and TypeScript validate and discover registry cells.
The MLAT reference consumes discovered identity and geometry, reads JSONL or
WebSocket observations, correlates identical frames, qualifies clocks, runs the
single robust solver, persists SQLite rows, and serves a Flask/Next.js console.

The demo generates synthetic propagation times. It is not a historical capture.
The compact MPyC/LocaRDS source contains 362 already-grouped historical events;
it has no original Mode-S frames, no CKB identities, and no per-observation clock
uncertainty. It supports solver validation. Any replay adapter must explicitly
expose these missing stages rather than invent their evidence.

The file inventory is [the accompanying CSV](2026-10-08-file-inventory.csv).
Each pre-existing version-controlled or unignored file has a classification,
disposition, reason, size, and checksum. Dependency trees, compiler caches,
private databases/configuration, and the ignored local `ckb-cli` checkout are
local generated/operator state, not application source. Existing signed and
hashed evidence bundles are retained. No obsolete-file deletion is justified
merely by filename or lack of a direct Python import.

## Executed baseline

| Check | Observed result |
|---|---|
| Python | 211 tests pass, Python 3.13.7 (local interpreter differs from pinned 3.12.11) |
| Python formatting | FAIL: `src/mlat_reference/api/rest_api.py` |
| Python lint | Pass |
| Python dependency consistency | Pass |
| Frontend unit/contract tests | 59 pass on pinned Node 22.23.1 |
| SDK tests/build | 72 pass |
| Rust contract | Build and 16 tests pass, including 11 CKB-VM lifecycle tests |
| Next.js production build | Pass |
| Documentation links | Pass, 111 Markdown files |
| Environment documentation | Pass, 89 discovered variables |
| Repository release hygiene / secret-pattern scan | Pass; this is not a complete secret or security audit |
| Compact historical solver baseline | 270/362 solved, 92 rejected, 74.59% success |
| npm vulnerability database | 2 high advisories, 21 low dependency-chain entries, zero critical |
| Browser E2E | Initial sandbox attempt could not bind test ports; rerun authorized and in progress |
| Current CKB RPC/indexer | Pending read-only connectivity checks |
| Physical receiver MLAT | Not validated; no connected physical receiver window supplied |
| Container build | Docker is not installed locally; not validated |

## Findings, ordered by impact

| ID | Severity | Finding and consequence | Evidence |
|---|---|---|---|
| A01 | High | Registry-controlled WebSocket endpoints inherit deployment auth headers and subscription payloads. A registry owner can select an unintended network destination or receive credentials. | `ingest/feed_transports.py`: `create_tasks`, `_stream_via_websocket` |
| A02 | High | Positions have no persisted data provenance. Current runtime mode determines interpretation of old rows. Synthetic cleanup deletes all old positions. Restarting or reusing a DB can mislabel or delete another mode's data. | `database/database.py`: positions schema, `cleanup_simulation_data`; `api/rest_api.py`: `_build_position_payload` |
| A03 | High | Feed parsing accepts duplicate JSON keys, truncates fractional nanoseconds, repairs missing/invalid timestamps with wall time, accepts arbitrary frame text, and has no explicit observation-size/depth policy. A far-future timestamp can evict valid correlation data. | Reproduction accepted `not-a-mode-s-frame` without a timestamp and converted 123.75 ns to 123 ns |
| A04 | High | `sharp` <0.35.5 and `source-map-js` <1.2.2 have high advisories in the installed dependency graph. | npm audit, GHSA-wq5f-xc86-pv6w and GHSA-68fv-2mgg-jv7q |
| A05 | Medium | Correlation's processed-group set and the database notification queue grow without bounds. Separate processor/API processes do not share the queue. | Reproduction retained 1,000 dedup entries with only 12 buffered observations; unbounded `queue.Queue()` |
| A06 | Medium | A bridge's stderr is only drained after stdout closes; a noisy child can block. Shutdown waits indefinitely for a child that ignores terminate. Command lines and stderr can disclose secrets in logs. | `CommandJsonlFeedTransport._stream_via_command` |
| A07 | High | `/api/pipeline` labels absent telemetry live by default. The frontend calls synthetic demo data recorded replay. Stored positions expose neither provenance nor the limitations of heuristic uncertainty. | `provenance_mode = ... else "live"`; `lib/data-source.ts` demo precedence |
| A08 | Medium | Receiver UI eligibility depends on published capability/status, not per-receiver clock qualification. Clock-qualified counts do not expire when a receiver stops sending. | `lib/receiver-state.ts`; `runtime.py:receiver_clock_status` |
| A09 | Medium | Compact report lacks residual/iteration summaries, failure categories, geometry statistics, runtime/solver revision and output checksum. Full source files are external; one fixture test hardcodes the selected historical error too tightly. | `benchmarks/compact_solver.py`; `tests/mlat/test_compact_solver_benchmark.py` |
| A10 | Medium | Database schema cache is keyed only by path, so recreating a file or a new `:memory:` connection may skip schema initialization. General integrity failures are treated as duplicate positions. | `_SCHEMA_READY_PATHS`; `store_position` |
| A11 | Medium | API aircraft query accepts unbounded/malformed time windows; Socket.IO subscription assumes a mapping and valid scalar fields. Health/pipeline claims exceed what is actually probed. | `get_aircraft_list`, `handle_subscribe`, `get_pipeline_evidence` |
| A12 | Medium | Registry RPC responses are read without a byte bound and oversized cell hex is decoded before checking decoded size. Pagination detects only consecutive repeated cursors. | `ckb_registry/discovery.py` |
| A13 | Medium | Database/API production packaging lacks some evidence/tools and currently runs Python as root. Installation claims have not been rerun under the pinned Python runtime. | Root Dockerfile and local environment |

## Existing guarantees to preserve

- Contract cardinality, Type-ID rule, exact sequence, owner-lock authorization,
  permanent tombstones, shared conformance corpus, and immutable `data1` binding.
- Strict registry JSON parsing and duplicate-identity quarantine.
- Integer timestamp subtraction in the solver; keep the numerical solver
  unchanged while generating the full historical reference.
- Explicit live startup guards; no simulation as a substitute for live validation.
- Prepared wallet actions, public-coordinate privacy notices, and no raw keys in SDK.
- Parameterized SQL, bounded position query limits, admin disabled by default,
  configured CORS, map text nodes instead of injected HTML, and map error isolation.

## Implementation order and validation

1. Reproduce and fix feed trust, input validation, subprocess/resource bounds,
   and dependency advisories, with regression tests at the actual boundaries.
2. Persist provenance and separate database modes. Preserve old rows as UNKNOWN;
   never infer their origin from the process now reading them.
3. Make the compact benchmark self-contained and complete. Preserve the baseline
   numerical solver, every failed event, licensing, and checksum evidence.
4. Add isolated historical replay, making dataset event grouping and missing
   raw-frame/clock/registry evidence explicit. Share the real solver, storage,
   API, and frontend while keeping production qualification strict.
5. Expose current qualification, actionable component health, safe structured
   diagnostics, solution provenance/geometry, and operator UI improvements.
6. Measure bounded 4/5/10-receiver workloads, update deployment/docs, then rerun
   tests, builds, benchmark, security checks, browser E2E and manual browser review.

Passing local tests does not establish external security audit, mainnet readiness,
physical receiver authenticity, surveyed positions, clock accuracy, or live field
performance. The final report must state these limitations and all failed checks.
