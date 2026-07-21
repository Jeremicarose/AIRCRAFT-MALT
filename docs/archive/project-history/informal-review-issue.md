# Informal Review Request: MLAT Airspace Console / CKB Receiver Registry Project

## Summary

I’m requesting an informal review of **MLAT Airspace Console**, a project that uses **CKB as a receiver registry / identity layer** for a multilateration-based aviation data platform.

The architecture keeps:

- registry / identity on CKB
- observation ingress, MLAT processing, storage, API, and dashboard off-chain

I’m looking for feedback before thinking seriously about a formal grant path.

## Project goal

The goal is to support a distributed receiver network where:

- receiver identity and metadata can be discovered through CKB
- observations can be processed into aircraft positions
- downstream users can consume those outputs through API and dashboard surfaces

## What is working already

### CKB side

- receiver-registry contract built in Rust
- deployed on CKB testnet
- on-chain receiver registration path built
- receiver discovery from chain working

### Off-chain side

- MLAT runtime
- SQLite persistence
- REST API
- dashboard / hosted demo surface
- readiness instrumentation
- benchmark tooling
- live-ingest scaffolding through:
  - command-jsonl bridge
  - Beast TCP adapter
  - multi-receiver bridge launcher

## Current limitation

The main blocker is no longer code architecture.

The main blocker is:

> **no real live observation source is currently connected**

So while the project can demonstrate:

- registry behavior
- product structure
- benchmark workflow

it cannot yet honestly claim real live output quality superiority.

## Questions for review

I’d love feedback on these points:

1. **Is the role of CKB here actually a good fit?**
   - receiver identity / metadata / discovery
   - ownership / coordination
   - not telemetry storage

2. **Does this feel like a useful Nervos infrastructure reference pattern?**
   - on-chain registry
   - off-chain high-throughput processing
   - possible later Fiber-based incentives / billing

3. **What would need to be true before this is grant-worthy?**
   - live data proof?
   - stronger benchmarks?
   - ecosystem integration story?
   - clearer commercialization path?

4. **What is the strongest product framing?**
   - decentralized receiver registry
   - aviation data API
   - MLAT infrastructure
   - control plane for distributed receivers

## Important context

I am trying to stay disciplined about the claims.

At the moment, I do **not** think it is correct to claim:

- more accurate
- more complete
- faster
- better coverage
- better analytics

against incumbents until live benchmark evidence exists.

So this review is mainly about:

- architectural fit
- ecosystem relevance
- and what would make the next stage worth funding

Thanks in advance for any thoughts.
