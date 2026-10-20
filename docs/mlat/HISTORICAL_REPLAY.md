# Historical replay

**VALIDATED locally:** the bundled compact source can be read, verified,
numerically solved, stored, served by the API, and inspected in the frontend.
**NOT YET VALIDATED:** live raw-frame correlation, historical CKB binding,
per-observation clock accuracy, and physical receiver truth.

## Start

Install the locked dependencies with Python 3.12.11. Activate that environment,
then run from the repository root:

```bash
./run-replay.sh
```

The command verifies the bundled source checksums, processes all 362 events,
stores every outcome in `data/mlat_historical.db`, and starts the API on port
5058. Set `MLAT_API_INTERNAL_URL=http://127.0.0.1:5058` before starting the frontend.
Open `/app/replay`. Select an event and use **Next stage** to inspect the recorded
processing decisions. This steps through recorded results; it does not pretend
to control a physical receiver or replay wall-clock time in real time.

For a batch run without a server:

```bash
python tools/mlat/replay_compact_dataset.py --database /tmp/historical.db
```

Repeating the same source is idempotent. A database already bound to another
runtime mode is rejected. Replay never changes receiver `last_seen` into a current
heartbeat. Historical receivers have no invented CKB identity and remain
UNQUALIFIED for live MLAT.

## What the source actually contains

The MPyC v0.11 extract of LocaRDS supplies event IDs, dataset-local aircraft and
receiver IDs, receiver coordinates, grouped arrival timestamps and
aircraft-reported reference positions. Arrival times are relative nanoseconds;
the source does not supply a UTC epoch. Original Mode-S frames and per-observation
clock uncertainties are absent. The upstream selection describes GPS timing,
which is not independent clock attestation.

The historical adapter therefore labels correlation as `PUBLISHED_GROUP` and
receiver qualification as `BENCHMARK_ONLY`. It shares the actual numerical solver,
SQLite storage, API serialization and console. It deliberately does not feed
invented frames through the live correlator or mark missing clocks qualified.

The source contains distinct event IDs sharing aircraft/time pairs. Storage keeps
the correlation ID in its unique key so those outcomes are not overwritten.
All 270 successful source events and 92 failed events remain inspectable.

## API

- `GET /api/replay?limit=50&offset=0`: bounded event summaries and source context.
- `GET /api/replay/events/5711382`: observations, geometry, stages and stored result.
- `GET /api/system/mode`: persistent `data_provenance=HISTORICAL_REPLAY`.
- `GET /api/diagnostics/bundle`: allowlisted context and diagnostics without secrets.

The normal recent-position endpoints retain their wall-time meaning. Historical
inspection uses the dedicated replay endpoints, avoiding the fiction that old
observations are current live aircraft. Source timestamps are never rewritten.

## Reproduce and interpret

Run `python tools/mlat/run_compact_solver_benchmark.py` for error distributions,
failure categories, geometry statistics, revision/runtime metadata and checksums.
See [benchmark](compact-public-solver-benchmark.md) and
[input contract](data-source-contract.md). The CSV files and their attributed
transformed outputs retain the upstream CC BY-SA 4.0 data licence.
