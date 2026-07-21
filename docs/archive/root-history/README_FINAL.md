# MLAT Airspace Console

MLAT Airspace Console is an MLAT product platform for delivering explainable aircraft position outputs from distributed receiver timing data.

This repository includes the runtime, storage, API, and map-first product surfaces needed to evaluate the platform around:

- output quality
- operational freshness and latency
- single-node reliability
- public/demo versus premium delivery

It is a strong local and hosted-demo system. It is **not** a claim that every external integration is already proven in live customer environments.

## Product value

Most receiver networks start with raw observations, not directly usable position products. This platform exists to bridge that gap.

It turns distributed observations into:

- recent aircraft positions
- aircraft track history
- structured quality and solver metadata
- health and runtime status
- plan-aware API and stream access

The commercial direction is to package **derived aviation outputs**, not just expose raw transport or registry plumbing.

## Why this repository matters

The useful thing here is the end-to-end composition:

- receiver identity and discovery can live outside the runtime
- feed transport can be swapped independently
- the runtime normalizes solve quality and correlation semantics
- the database and API preserve those semantics for downstream use
- the dashboard explains the product through a map-first workflow
- the API supports public/demo and premium-style access patterns

## Core capabilities

### Quality-aware derived outputs
The position payloads can include:

- `quality.score`
- `quality.bucket`
- `solver.method`
- `solver.residual_m`
- `solver.iterations`
- `correlation.time_span_s`
- `correlation.receiver_count`

### Reliability and operational visibility
The platform includes:

- health and freshness reporting
- runtime timing metrics
- broadcaster/runtime status visibility
- single-node SQLite hardening
- simulation cleanup and statistics support

### Commercial readiness
The API and database include:

- accounts
- plans
- API keys
- entitlements
- usage metering
- plan-aware authorization

## Product surfaces

### Dashboard
The dashboard is designed to explain outputs, not just decorate them:

- click an aircraft first to inspect uncertainty, quality, and recent motion
- use receivers second to understand support and coverage
- keep replay/demo versus live context visible

### REST and WebSocket API
The API exposes recent positions, history, statistics, health, and live updates. Premium-only behavior can be enforced for deeper history, statistics, and streaming access.

### Hosted demo mode
The repository can be deployed as a replay-oriented hosted walkthrough so users can explore the product safely in a read-only environment.

## Architecture

1. **Registry / identity layer**
   - CKB can provide receiver identity and registry semantics.
2. **Feed ingress**
   - simulated or live transports supply receiver observations.
3. **MLAT processing**
   - correlation, solving, normalization, and persistence.
4. **Operational layer**
   - health, statistics, freshness, and cleanup.
5. **Delivery layer**
   - API, WebSocket, dashboard, hosted demo.

CKB is important in this design, but it should be understood as **supporting infrastructure**, not the main product promise.

## Current maturity

This project is currently best described as:

- production-structured
- test-backed
- locally deployable
- simulation-capable
- hosted-demo-capable
- commercially aware

It should not be described as a fully validated horizontally scaled production service.

## Quick start

```bash
pip install -r requirements.txt
python -m pytest
mlat-api
mlat-processor
```

Then open:

- `/` for the product page
- `/dashboard.html` for the console
- `/api` for the API root

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Summary](docs/PROJECT_SUMMARY.md)
- [Integration Guide](docs/INTEGRATION_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [CKB Integration Guide](docs/CKB_INTEGRATION_GUIDE.md)

## Recommended framing

If you are presenting this system, lead with:

1. aircraft outputs
2. quality and trust signals
3. latency and reliability visibility
4. access tiers and packaging
5. registry and transport infrastructure

## License

[Add your license here]
