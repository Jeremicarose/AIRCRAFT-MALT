# Grant Outline: MLAT Airspace Console

## Working Title

**MLAT Airspace Console: A CKB-Based Receiver Registry And Benchmarkable Aviation Data Platform**

## One-sentence summary

Build a distributed receiver-network platform that uses **CKB for receiver identity and discovery**, off-chain multilateration processing for aircraft outputs, and a product layer for quality-aware aviation data delivery.

## Problem

Today, several problems exist in aviation data infrastructure:

- receiver networks are often coordinated centrally or informally
- not all useful signals come with trustworthy aircraft position data
- there is a gap between raw observations and usable data products

This leads to:

- weak receiver coordination
- fragile integration paths
- limited trust/transparency around network identity
- difficulty packaging outputs as product-ready data

## Proposed solution

Use:

- **CKB** for receiver registry / identity / ownership workflows
- **off-chain services** for observation ingress, correlation, MLAT solving, persistence, and API delivery
- later, potentially **Fiber** for metered delivery or receiver incentives

## What is unique

The uniqueness is not “MLAT exists.”

The interesting combination is:

- CKB-based registry and coordination
- off-chain MLAT runtime
- quality/freshness/reliability instrumentation
- benchmark-ready product architecture

## Current status

### Already built

- receiver-registry contract in Rust
- deployed contract on CKB testnet
- on-chain receiver registration workflow
- receiver discovery from CKB
- MLAT runtime with correlation and solving
- SQLite persistence
- health/statistics/readiness API endpoints
- map-first dashboard and hosted product surface
- benchmark tooling:
  - MLAT export
  - OpenSky reference fetch
  - benchmark comparator
- live-ingest scaffolding:
  - generic bridge adapter
  - Beast TCP adapter
  - multi-receiver Beast bridge

### Not yet proven

- real live aircraft outputs
- external benchmark superiority
- comparative production reliability
- complete real-world receiver coverage

## Why this can matter to Nervos

This project demonstrates a credible role for CKB as:

- a decentralized registry
- an identity/metadata layer
- a coordination substrate for infrastructure systems

It avoids a weak pattern like:

- putting bulky telemetry directly on-chain

and instead uses CKB where it is strongest:

- durable shared state
- verifiable identity/ownership
- coordination

## Why this can matter commercially

If successful, the project could become:

- a premium aviation data API
- a receiver network control plane
- a quality-aware MLAT data product

The long-term value is not raw packets. It is:

- quality
- freshness
- reliability
- packaging

## Main risks

### Technical

- no live source connected yet
- quality not yet benchmarked externally
- multi-receiver real-time MLAT still needs real field validation

### Product

- must prove value against incumbents
- must prove that the CKB role is meaningful to the system

### Business

- needs a clear paying user
- needs real evidence for claims like:
  - more accurate
  - more complete
  - faster
  - better coverage
  - better analytics

## What the grant would help fund

Potential grant-backed work could include:

1. live ingest integration
2. hardware / receiver validation
3. multi-receiver benchmarking
4. production hardening for quality/freshness/reliability reporting
5. ecosystem documentation and reference-architecture publication

## Milestones a future grant could target

### Milestone 1

Connect real live receiver observations into the runtime and persist real aircraft outputs.

### Milestone 2

Run the first meaningful external benchmark against trusted references.

### Milestone 3

Publish measured results for:

- quality
- freshness
- reliability
- benchmarkability

### Milestone 4

Refine the product/API/dashboard around real benchmark-backed output rather than replay/demo-only output.

## Most important near-term next step

Before a full grant proposal, the most important thing is:

> connect a real observation source and generate benchmarkable live output

Without that, the project remains promising but pre-proof.

## Best current honest positioning

This project is currently best positioned as:

> a strong, test-backed MLAT product platform with working CKB registry integration, operational readiness instrumentation, benchmark tooling, and live-ingest scaffolding, still awaiting real observation input for final proof.
