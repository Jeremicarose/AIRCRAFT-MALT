# MLAT Airspace Console: CKB-Based Receiver Registry For Aviation Data Infrastructure

## Overview

I’ve been building **MLAT Airspace Console**, a multilateration-focused aviation data platform that uses **CKB as a receiver registry / identity layer** while keeping signal ingestion, multilateration processing, storage, and delivery off-chain.

The project is aimed at a specific problem:

- aircraft and receiver data systems are often centralized
- receiver fleets are hard to coordinate cleanly
- raw observations are not the same thing as usable aircraft outputs

The goal is to build a system where:

- receiver identity and metadata can live in a decentralized registry
- aircraft observations can be processed into explainable outputs
- downstream users can consume those outputs through an API and dashboard

## Why CKB

In this architecture, **CKB is not the telemetry database**.

It is being used for:

- receiver identity
- receiver metadata
- registry-backed discovery
- ownership and coordination workflows

That feels like a much better fit than trying to push aircraft tracking data directly on-chain.

## What is already working

### CKB / registry layer

- receiver-registry contract built in Rust
- deployed to **CKB testnet**
- on-chain receiver registration path working
- receiver discovery from CKB working

### Runtime / product layer

- MLAT runtime for correlation and solving
- SQLite persistence for:
  - positions
  - receivers
  - statistics
- REST API for:
  - health
  - positions
  - track history
  - receivers
  - statistics
  - readiness
- map-first dashboard and hosted product/demo UI

### Readiness / benchmark layer

- internal readiness instrumentation around:
  - quality
  - latency / freshness
  - reliability
  - packaging
- benchmark tooling:
  - export MLAT data
  - fetch OpenSky reference data
  - compare outputs

## Important current limitation

The main blocker is no longer architecture or tooling.

The main blocker is:

> **lack of real live observation input**

I have built:

- command-jsonl bridge support
- generic bridge adapter
- Beast TCP adapter
- multi-receiver Beast bridge

But I currently do **not** have:

- local SDR hardware
- remote Beast endpoints
- or another real live feed source

So the system can currently prove:

- registry architecture
- control-plane behavior
- API/dashboard structure
- benchmark workflow

But it cannot yet honestly prove:

- live MLAT accuracy
- completeness
- freshness superiority
- reliability superiority
- better coverage than incumbents

## Why I think this is still interesting for the ecosystem

I think this project is interesting for Nervos because it demonstrates a concrete pattern:

- use CKB for decentralized infrastructure registry/state
- use off-chain systems for high-throughput computation and delivery
- potentially use **Fiber later** for low-cost access settlement or receiver incentives

That pattern could apply beyond aviation.

## What I’d like feedback on

I’d especially like ecosystem and core-dev feedback on:

1. whether the role of **CKB** here is justified and well-scoped
2. whether this feels like a valid infrastructure use case for Nervos
3. what would need to be true before this becomes a strong grant candidate
4. whether the current product direction should lean more toward:
   - receiver-network control plane
   - aviation data API product
   - or benchmarkable MLAT infrastructure

## Current next steps

- obtain real observation input
- move from replay/simulation output to live aircraft outputs
- run the first meaningful external benchmark
- continue refining the commercial/data-product packaging

If useful, I can also share:

- the current dashboard/demo
- the benchmark/readiness docs
- the bridge/adapter path for live ingest

---

Happy to hear thoughts, criticism, and suggestions.
