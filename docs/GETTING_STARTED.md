# Getting Started

This guide gets you running the current MLAT Airspace Console stack locally and explains how to read what the product is showing you.

Start here if you want to:

- run the API and processor locally
- open the dashboard and hosted product page
- inspect quality-aware aircraft outputs
- understand replay/demo versus live behavior

## What you are running

MLAT Airspace Console turns distributed receiver observations into derived aircraft outputs.

The local stack includes:

- an MLAT processing runtime
- SQLite-backed storage
- a REST API
- a WebSocket live-update surface
- a map-first dashboard
- a product page / hosted walkthrough surface

The system is meant to help you inspect:

- aircraft position estimates
- uncertainty and quality signals
- receiver participation
- freshness and runtime health
- public/demo versus premium behavior in the API

## Quick local setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Start the API:

```bash
mlat-api
```

Start the processor in another terminal:

```bash
mlat-processor
```

Then open:

- `http://localhost:5000/`
- `http://localhost:5000/dashboard.html`
- `http://localhost:5000/api`

## What to click first

The dashboard is intentionally map-first.

Recommended flow:

1. open the dashboard
2. click an aircraft first
3. inspect its path, uncertainty, quality, and receiver count
4. click a receiver after that to understand the support network behind the estimate

This is the fastest way to understand what the product is trying to sell: not raw packets, but explainable aircraft outputs.

## Core runtime flow

```text
receiver observations
  -> signal correlation
  -> MLAT solving
  -> normalized quality metadata
  -> database storage
  -> API / WebSocket / dashboard delivery
```

## What the API now exposes

The API is no longer just a thin demo layer. It can expose:

- recent aircraft positions
- aircraft track history
- receiver state
- operational statistics
- health and freshness details
- plan-aware authorization behavior

Position payloads can include structured metadata such as:

- `quality.score`
- `quality.bucket`
- `solver.method`
- `solver.residual_m`
- `solver.iterations`
- `correlation.time_span_s`
- `correlation.receiver_count`

## Local validation checklist

After starting the stack, validate these endpoints:

```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/receivers
curl http://localhost:5000/api
```

If you have an API key configured, also validate quality-oriented position payloads via recent positions and track endpoints.

## Product modes

Depending on environment configuration, the UI may represent:

- live traffic
- replay traffic
- hosted demo / read-only traffic

The product should label those states clearly before users interpret the map.

## Commercial behavior

The repository now includes account, plan, entitlement, and API key concepts.

That means some endpoints or limits may behave differently for:

- public/demo access
- premium access

Use the API and tests to validate which features require deeper access.

## Where to go next

- [README.md](../README.md) for overall product framing
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture and component roles
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for CKB and feed integration
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for local and hosted deployment guidance
- [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md) for registry-specific details
