# MLAT Airspace Console

MLAT Airspace Console is a product-oriented multilateration platform for turning distributed Mode-S timing observations into explainable aircraft position outputs.

## Public progress

This repository is the public development record for the MLAT Airspace receiver
control plane. The hosted configuration is intentionally a **read-only replay
demo**: it demonstrates receiver discovery, observation processing, MLAT output,
storage, public APIs, pipeline provenance, and system metrics without claiming
that replay traffic is live receiver evidence.

- **Current proof:** end-to-end replay observations localized by the production
  MLAT solver, exact noiseless solver tests, precision-safe timestamp handling,
  provenance-aware evidence gates, and operational metrics
- **Current limitation:** no public synchronized live receiver window has been
  captured and compared with a trusted external reference source
- **Safest positioning:** decentralized receiver registry and aviation data
  control plane, with CKB identity/discovery and off-chain MLAT processing

[Open the public read-only replay demo](https://mlat-hosted-demo.onrender.com/app/overview)

> Render Free sleeps after 15 minutes without traffic. The first visit can show
> Render's loading screen for about one minute while the service wakes; the demo
> then opens automatically. Refresh once if the loading tab was already open.

[Deploy the read-only demo on Render](https://render.com/deploy?repo=https://github.com/Jeremicarose/AIRCRAFT-MALT)

The public Blueprint uses Render Free and regenerates replay data after service
restarts. No persistent production data is stored by this walkthrough.

Reviewers should open these surfaces first:

- [Evidence pipeline](https://mlat-hosted-demo.onrender.com/app/pipeline)
- [System metrics](https://mlat-hosted-demo.onrender.com/app/analytics)
- [Pipeline JSON](https://mlat-hosted-demo.onrender.com/api/pipeline)
- [Public metrics JSON](https://mlat-hosted-demo.onrender.com/api/evidence/metrics)

The latest shareable project update is maintained in
[docs/PUBLIC_PROGRESS_UPDATE.md](docs/PUBLIC_PROGRESS_UPDATE.md).

The system is built around four things customers can evaluate directly:

- **quality** — each position can include normalized quality, solver, and correlation metadata
- **latency** — the runtime exposes freshness and timing signals so operators can judge how current outputs are
- **reliability** — the stack includes health, runtime, and operational metrics instead of acting like a one-off demo
- **packaging** — the API and streaming surfaces can distinguish public/demo access from premium access

CKB remains part of the architecture as Registry V2: immutable Type-ID-style
receiver identities, owner-lock authorization, ordered record updates, explicit
ownership transfer, and terminal revocation. It is supporting infrastructure
rather than the headline product.

## What the product does

The platform accepts receiver observations, correlates signals that likely came from the same aircraft transmission, solves multilateration positions, stores those outputs, and exposes them through:

- a REST API
- a WebSocket live-update path
- a map-first dashboard
- a hosted replay/demo surface

The most practical first live ingest path in the current repo is the
`command-jsonl` transport mode, which lets a local decoder or bridge command
stream newline-delimited JSON observations into the runtime without requiring a
hosted websocket integration on day one.

The replay path does not copy scenario coordinates into position output. It
generates receiver arrival times, runs correlation and the production solver,
then stores the estimate. Replay remains synthetic and non-benchmarkable. Live
MLAT additionally requires at least four receivers with qualified integer
nanosecond timestamps on a common clock; network arrival time is rejected.

Instead of selling raw packet transport, the product direction is to sell **derived aviation outputs** that are easier to inspect, trust, and package.

## What makes the outputs useful

Recent work in this repository focuses on product-grade output semantics:

- normalized `quality.score` and `quality.bucket`
- structured `solver` metadata such as method, residual, and iterations
- structured `correlation` metadata such as time span and receiver count
- operational health and freshness reporting
- plan-aware API access and usage metering

That means consumers can evaluate not only *where* the system says an aircraft is, but also *how trustworthy and current that estimate appears to be*.

## Product surfaces

### Dashboard
The dashboard is map-first and designed to explain one estimate at a time:

- select an aircraft to inspect its recent path, uncertainty, quality, and receiver support
- inspect receivers after that to understand the network behind the estimate
- distinguish replay/demo versus live contexts clearly

### API
The API exposes recent positions, aircraft history, receiver state, statistics, and health endpoints. Position payloads now include additive quality/solver/correlation metadata for downstream consumers.

### Commercial controls
The API supports:

- accounts
- plans
- API keys
- entitlements
- usage metering

The current model separates:

- **public/demo** access for shallow, restricted exploration
- **premium** access for deeper history, premium statistics, and live-stream features

## Architecture at a glance

The stack is intentionally split so product value sits above infrastructure details:

1. **Receiver identity and discovery**
   - CKB Registry V2 provides collision-resistant lifecycle identities,
     owner-authorized updates/transfers, sequence ordering, and revocation.
2. **Feed ingress**
   - live or simulated transports provide receiver observations.
3. **Correlation and MLAT solving**
   - the runtime groups observations and calculates aircraft positions.
4. **Persistence and operations**
   - SQLite-backed storage, health reporting, runtime metrics, and retention behavior.
5. **Delivery surfaces**
   - API, WebSocket updates, dashboard, and hosted replay/demo.

## Current maturity

This repository is strongest today as:

- a **test-backed local MLAT product platform**
- a **simulation-capable and hosted-demo-capable stack**
- a **single-node operational deployment** with SQLite hardening
- a **commercially-aware API surface** with plans, entitlements, and metering

It should **not** be described as a fully proven multi-node production system.
Registry V2 now has a signed CKB testnet lifecycle and public verification
package; live receiver timing and 4DSky integration still require physical
multi-receiver evidence.

Registry V2 evidence:

- [testnet verification package](evidence/registry-v2-testnet-2026-07-30-final/README.md)
- [external security review request](docs/REGISTRY_V2_SECURITY_REVIEW_REQUEST.md)
- deployment transaction `0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3`
- registry code hash `0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c`

## Operating modes

The repository supports two deliberately different runtime postures:

- **Demo / replay mode**: explicit opt-in for walkthroughs, staged traffic, or hosted sample deployments.
- **Production-intended live mode**: enable `STRICT_PRODUCTION_MODE=true` so startup fails closed unless live ingest is explicitly configured.

Strict production mode rejects these silent-fallback combinations during settings load and startup:

- `DEMO_MODE=true`
- `FOURDSKY_TRANSPORT=simulation`
- `FOURDSKY_TRANSPORT=auto`
- `SIMULATE_IF_UNAVAILABLE=true`

Use demo/replay defaults only when you intentionally want a non-live environment.

## Quick start

### Install dependencies

```bash
python -m pip install --require-hashes -r requirements-dev.lock
```

Python is pinned by `.python-version`. `requirements.lock` contains the
production dependency graph and `requirements-dev.lock` adds the exact test and
development graph. See [Reproducibility](docs/REPRODUCIBILITY.md).

### Run tests

```bash
python -m pytest
```

### Run locally

For a local demo/replay workflow, keep `STRICT_PRODUCTION_MODE=false` and use the hosted demo or simulation settings.

Start the complete local demo (processor, API, and UI) with one command:

```bash
./run-demo.sh
```

Then run the Next.js frontend from `frontend/`:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000/app/overview`. The launcher gives the processor and API the same database and stops the backend stack if either
process fails.

The evidence surfaces are:

- `http://localhost:3000/app/pipeline` for the receiver-to-dashboard trace
- `http://localhost:3000/app/analytics` for throughput, freshness,
  reliability, memory, latency, and benchmark artifacts
- `http://localhost:5057/api/pipeline` and
  `http://localhost:5057/api/evidence/metrics` for machine-readable evidence

For a production-intended live workflow, set at minimum:

```bash
STRICT_PRODUCTION_MODE=true
FOURDSKY_TRANSPORT=command-jsonl
SIMULATE_IF_UNAVAILABLE=false
DEMO_MODE=false
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_HASH
FOURDSKY_BRIDGE_COMMAND="python3 scripts/bridge_adapter.py --source stdin"
FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED=true
MAX_CLOCK_UNCERTAINTY_NS=100
```

The strict live launcher checks the bridge source, CKB registry type hash,
fallback settings, and benchmarkability gate before starting:

```bash
./run-live.sh
```

It exits without starting the stack when a live-evidence prerequisite is
missing. A configured remote receiver source that cannot be probed locally must
be explicitly attested with `FOURDSKY_EXTERNAL_SOURCE_ATTESTED=true`.

### Capture benchmarks and evidence

Generate and verify the byte-reproducible synthetic regression benchmark:

```bash
python3 scripts/run_reproducible_benchmark.py
python3 scripts/run_reproducible_benchmark.py --verify-only
```

This deterministic artifact validates the benchmark implementation and evidence
format. It does not count as synchronized live receiver evidence.

Publish a reproducible local operational baseline:

```bash
python3 scripts/benchmark_operational_performance.py \
  --api-base http://127.0.0.1:5057
```

Measure API, receiver, and freshness reliability over a bounded window:

```bash
python3 scripts/capture_reliability_window.py \
  --api-base http://127.0.0.1:5057 \
  --duration-seconds 300
```

After the strict live pipeline is passing and an aligned reference JSONL file
exists, create the complete hashed grant bundle:

```bash
python3 scripts/capture_grant_evidence.py \
  --db data/mlat_live.db \
  --reference benchmark/reference-opensky.jsonl \
  --reference-source OpenSky \
  --region "Northeast corridor"
```

### Open the UI

- frontend landing page: `http://localhost:3000/`
- frontend dashboard redirect: `http://localhost:3000/dashboard`
- frontend overview: `http://localhost:3000/app/overview`
- frontend localization: `http://localhost:3000/app/localization`
- API root: `http://localhost:5000/api`

## Key capabilities

- MLAT solving with normalized output metadata
- signal correlation with quality-oriented metadata
- recent position, latest position, and aircraft track APIs
- health, freshness, and operational statistics endpoints
- versioned public benchmark evidence at `/api/benchmark/latest`
- explicit receiver-to-dashboard evidence at `/api/pipeline`
- bounded operational history at `/api/evidence/metrics`
- performance and reliability artifacts at `/api/evidence/performance/latest`
  and `/api/evidence/reliability/latest`
- event-driven local broadcast path with DB fallback
- public/demo versus premium API behavior
- hosted replay/demo mode for product walkthroughs

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Summary](docs/PROJECT_SUMMARY.md)
- [Integration Guide](docs/INTEGRATION_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [CKB Integration Guide](docs/CKB_INTEGRATION_GUIDE.md)
- [MLAT Solver and Timing Evidence](docs/MLAT_SOLVER_AND_TIMING.md)
- [Multi-Receiver Beast Runtime](docs/MULTI_RECEIVER_RUNTIME.md)
- [Grant Evidence Runbook](docs/GRANT_EVIDENCE_RUNBOOK.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Five-Minute Evidence Demo](docs/GRANT_DEMO_SCRIPT.md)
- [Archived project history and planning notes](docs/archive/)

## Positioning note

The product story should be read in this order:

1. derived aviation outputs
2. quality, latency, and reliability
3. access tiers and packaging
4. infrastructure choices such as CKB and feed adapters

That is the intended framing of this repository.

## License

[Add your license here]
