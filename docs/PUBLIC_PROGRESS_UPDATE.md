# Public Progress Update

## Short version

MLAT Airspace now has a public, test-backed receiver-to-dashboard evidence
surface. CKB is used as the receiver identity, registry, and discovery layer;
ADS-B observations, correlation, MLAT solving, persistence, and delivery remain
off-chain.

The current hosted experience is deliberately labeled as replay. It lets
reviewers inspect the complete processing path, public APIs, freshness,
throughput, latency, memory, reliability sampling, and evidence gates without
presenting simulated traffic as live proof.

The next external milestone is one synchronized live receiver window with at
least four receivers, followed by comparison against a named trusted reference
source and publication of the hashed evidence bundle.

## Share text

> Public progress update for MLAT Airspace: the receiver-to-dashboard evidence
> pipeline, operational metrics, provenance gates, and reproducible performance
> tooling are now available. CKB provides receiver identity and discovery while
> observations and MLAT processing remain off-chain. The hosted walkthrough is
> explicitly replay-based; synchronized live receiver evidence and an external
> accuracy comparison are the next milestone. Explore the public demo:
> https://mlat-hosted-demo.onrender.com/app/pipeline.html

## Reviewer links

- Overview: https://mlat-hosted-demo.onrender.com/app/overview.html
- Evidence pipeline: https://mlat-hosted-demo.onrender.com/app/pipeline.html
- System metrics: https://mlat-hosted-demo.onrender.com/app/analytics.html
- Pipeline JSON: https://mlat-hosted-demo.onrender.com/api/pipeline
- Public metrics JSON: https://mlat-hosted-demo.onrender.com/api/evidence/metrics

## What is proven today

- canonical receiver and solver metadata move through the runtime and API
- replay observations exercise correlation, solving, storage, and delivery
- pipeline stages and UI surfaces label replay and live provenance separately
- operational performance and sampled reliability reports are reproducible
- strict live startup and grant capture fail closed when evidence gates are absent

## What is not yet proven

- public synchronized live receiver ingest
- real-world MLAT accuracy against a named reference source
- long-window live receiver and API availability
- comparative superiority over incumbent aviation data services
