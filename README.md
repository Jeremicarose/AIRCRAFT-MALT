# MLAT Airspace Console

MLAT Airspace Console is a product-oriented multilateration platform for turning distributed Mode-S timing observations into explainable aircraft position outputs.

## Public progress

This repository is the public development record for the MLAT Airspace receiver
control plane. The hosted configuration is intentionally a **read-only replay
demo**: it demonstrates receiver discovery, observation processing, MLAT output,
storage, public APIs, pipeline provenance, and system metrics without claiming
that replay traffic is live receiver evidence.

- **Current proof:** end-to-end replay pipeline, provenance-aware evidence gates,
  operational metrics, performance baselines, and responsive operator views
- **Current limitation:** no public synchronized live receiver window has been
  captured and compared with a trusted external reference source
- **Safest positioning:** decentralized receiver registry and aviation data
  control plane, with CKB identity/discovery and off-chain MLAT processing

[Deploy the read-only demo on Render](https://render.com/deploy?repo=https://github.com/Jeremicarose/AIRCRAFT-MALT)

After deployment, reviewers should open these routes first:

```text
/app/pipeline.html
/app/analytics.html
/api/pipeline
/api/evidence/metrics
```

The latest shareable project update is maintained in
[docs/PUBLIC_PROGRESS_UPDATE.md](docs/PUBLIC_PROGRESS_UPDATE.md).

The system is built around four things customers can evaluate directly:

- **quality** — each position can include normalized quality, solver, and correlation metadata
- **latency** — the runtime exposes freshness and timing signals so operators can judge how current outputs are
- **reliability** — the stack includes health, runtime, and operational metrics instead of acting like a one-off demo
- **packaging** — the API and streaming surfaces can distinguish public/demo access from premium access

CKB remains part of the architecture, but as supporting infrastructure for receiver identity and registry workflows rather than the headline product.

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
   - CKB-backed registry workflows can provide receiver identity and metadata.
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

It should **not** be described as a fully proven multi-node production system, and the CKB and 4DSky integrations should still be treated as integration work rather than guaranteed turnkey deployment.

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
pip install -r requirements.txt
```

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

Then open `http://localhost:5057/app/overview.html`. The launcher gives the
processor and API the same database and stops the complete stack if either
process fails.

The evidence surfaces are:

- `http://localhost:5057/app/pipeline.html` for the receiver-to-dashboard trace
- `http://localhost:5057/app/analytics.html` for throughput, freshness,
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

- product page: `http://localhost:5000/`
- dashboard: `http://localhost:5000/dashboard.html`
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
- [Grant Evidence Runbook](docs/GRANT_EVIDENCE_RUNBOOK.md)
- [Five-Minute Evidence Demo](docs/GRANT_DEMO_SCRIPT.md)

## Positioning note

The product story should be read in this order:

1. derived aviation outputs
2. quality, latency, and reliability
3. access tiers and packaging
4. infrastructure choices such as CKB and feed adapters

That is the intended framing of this repository.

## License

[Add your license here]
