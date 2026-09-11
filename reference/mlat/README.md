# MLAT Reference Implementation

This directory contains the frontend, deterministic benchmark inputs, and field
configuration for an example application that consumes CKB Registry V2. The
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

For a production-style local run, build first and then use the same `start`
command used by the documented workflow. It prepares Next.js standalone assets
automatically and keeps production output separate from the development server,
so the page does not load as unstyled HTML:

```bash
cd reference/mlat/frontend
npm ci
npm run build
npm run start
```

Set `PORT=3011` when another local service is using port 3000. The server is
bound to `0.0.0.0` by default; use `HOSTNAME=127.0.0.1` when it should only be
reachable from the local machine.

Open `http://localhost:3000/app/registry` for the Pudge testnet Registry V2
journey. Discovery works without a wallet against the current immutable
deployment. Create, update, transfer, and revoke open a connected CCC wallet for
explicit approval. The bundled July deployment remains available only for
historical read-only inspection. The application never accepts a private key or
seed phrase, and no browser-signed lifecycle is claimed until one is executed.

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
