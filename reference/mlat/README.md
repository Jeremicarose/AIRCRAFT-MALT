# MLAT Reference Implementation

This directory contains the frontend, deterministic benchmark inputs, and field
configuration for the flagship CKB Registry V2 reference implementation. The
Python backend lives under `src/mlat_reference`; its tools and tests live under
`tools/mlat` and `tests/mlat`.

MLAT demonstrates how Registry V2 identities can be consumed by physical
infrastructure software. It does not make the repository an aviation tracker
product.

## Implemented Path

```text
Registry V2 discovery
  -> receiver selection
  -> WebSocket JSON, command JSONL, Beast, or explicit replay ingest
  -> synchronized-clock qualification
  -> Mode-S correlation
  -> robust MLAT solve
  -> SQLite
  -> Flask API and Next.js operator frontend
```

## Modes

- `simulation`: deterministic receiver/aircraft scenario with synthetic timing
- `command-jsonl`: operator command emits normalized observations
- `websocket-json`: one or more configured receiver/feed endpoints
- `auto`: convenience selection; rejected by strict production mode

Strict mode rejects replay, automatic fallback, demo mode, missing Registry V2
hashes, and missing live evidence gates.

## Run

From repository root:

```bash
cp .env.example .env
python3 -m pip install --require-hashes -r requirements-dev.lock
./run-demo.sh
```

Frontend:

```bash
cd reference/mlat/frontend
npm ci
npm run dev
```

Or run the complete stack:

```bash
docker compose up --build
```

## Test

```bash
python3 -m pytest -q tests/mlat
cd reference/mlat/frontend && npm ci && npm run build
```

## Evidence Status

Implemented and test-backed:

- replay observations flow through the production robust solver
- exact known-position and scenario-footprint solver tests
- integer nanosecond timing preservation
- clock synchronization and uncertainty rejection
- provenance-aware benchmark gates
- deterministic synthetic evidence bundle

Not verified:

- a public physical four-receiver synchronized window
- real-world accuracy against a trusted reference source
- production reliability or coverage
- horizontal scaling

See [Solver and Timing](../../docs/reference/mlat/SOLVER_AND_TIMING.md),
[Live Ingest](../../docs/reference/mlat/LIVE_INGEST.md), and
[Benchmarking](../../docs/reference/mlat/BENCHMARKING.md). The frontend's
[operator scope](../../docs/reference/mlat/OPERATOR_CONSOLE.md) and
[design system](../../docs/reference/mlat/DESIGN_SYSTEM.md) are reference-only
documents.
