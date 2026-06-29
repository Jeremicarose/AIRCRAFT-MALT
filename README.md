# MLAT Airspace Console

MLAT Airspace Console is a product-oriented multilateration platform for turning distributed Mode-S timing observations into explainable aircraft position outputs.

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

API:

```bash
mlat-api
```

Processor:

```bash
mlat-processor
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
- event-driven local broadcast path with DB fallback
- public/demo versus premium API behavior
- hosted replay/demo mode for product walkthroughs

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Summary](docs/PROJECT_SUMMARY.md)
- [Integration Guide](docs/INTEGRATION_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [CKB Integration Guide](docs/CKB_INTEGRATION_GUIDE.md)

## Positioning note

The product story should be read in this order:

1. derived aviation outputs
2. quality, latency, and reliability
3. access tiers and packaging
4. infrastructure choices such as CKB and feed adapters

That is the intended framing of this repository.

## License

[Add your license here]
