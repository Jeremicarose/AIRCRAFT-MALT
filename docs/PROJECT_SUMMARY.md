# Project Summary

## What this repository is building

MLAT Airspace Console is a multilateration product platform for derived aviation outputs.

The repository combines:

- distributed receiver observations
- MLAT correlation and solving
- normalized quality metadata
- local persistence
- operational health and freshness reporting
- API, stream, and dashboard delivery
- public/demo and premium-oriented access controls

The main product story is not blockchain. The main product story is that downstream consumers can inspect aircraft outputs that are more explainable, measurable, and packageable.

## Product outcome

The platform exists to convert timing observations into outputs a customer can use:

- recent positions
- track history
- quality and solver context
- freshness and runtime health
- receiver participation context

That supports product claims around:

- quality
- latency visibility
- reliability visibility
- packaging and access tiers

## High-level architecture

```text
receiver identity / discovery
  -> observation ingress
  -> signal correlation
  -> MLAT solving
  -> quality normalization
  -> SQLite persistence
  -> API / WebSocket / dashboard delivery
```

## Component roles

### MLAT processing
The runtime consumes receiver observations, correlates likely related signals, solves aircraft positions, and attaches normalized metadata that helps downstream users evaluate the estimate.

### Database
The SQLite layer stores aircraft positions, receiver state, operational statistics, and commercial primitives. It is hardened for single-node deployment rather than framed as a multi-node distributed store.

### API
The REST API exposes recent positions, aircraft history, receivers, statistics, and health. Position payloads can include additive `quality`, `solver`, and `correlation` objects.

### Dashboard
The dashboard is map-first and designed to explain one aircraft estimate at a time. It emphasizes uncertainty, quality, receiver support, and mode labeling instead of generic telemetry decoration.

### Commercial controls
The database and API include account, plan, API key, entitlement, and usage concepts so delivery can differ between public/demo and premium consumers.

## Infrastructure role of CKB

CKB fits the architecture as a receiver identity and registry layer.

That can be useful for:

- metadata ownership
- registry-backed discovery
- externalized receiver identity

But it should be presented as supporting infrastructure, not the headline product surface.

## Current maturity

The current repository should be read as:

- test-backed
- production-structured
- single-node operational
- simulation-capable
- hosted-demo-capable
- integration-oriented for live external infrastructure

It should not be overstated as fully proven across live external provider integrations or horizontally scaled multi-node production workloads.

## Validation surfaces

This repository now supports validation across:

- solver-quality normalization
- correlation-quality metadata
- DB persistence of additive fields
- health and statistics endpoints
- plan-aware authorization
- websocket entitlement behavior
- dashboard presentation of quality-aware outputs

## Recommended reading order

1. [README.md](../README.md)
2. [GETTING_STARTED.md](GETTING_STARTED.md)
3. [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
4. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
5. [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md)
