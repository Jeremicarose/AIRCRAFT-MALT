# Spark Program | MLAT Airspace Console

**Tags:** `Spark-Program`

---

## 1. Project Overview

### Project Name

**MLAT Airspace Console**

### One-Sentence Summary

A CKB-based receiver registry and multilateration platform for turning distributed Mode-S timing observations into explainable aviation data outputs with quality, freshness, reliability, and packaging surfaces.

### Project Type

**Developer Tool / Data Infrastructure / Dashboard / Blockchain-Integrated Aviation Platform**

---

## 2. Team Profile

### Core Members

- **Jeremic** — builder / primary developer / product and integration lead

### Background

Current project work includes:

- CKB receiver-registry contract development and deployment
- MLAT runtime design and implementation
- quality/freshness/reliability instrumentation
- benchmark workflow tooling
- dashboard and API product surfaces

Relevant project artifacts:

- GitHub repository: **[add repo URL here]**
- Public forum post draft: [docs/archive/project-history/nervos-talk-post.md](./nervos-talk-post.md)

### Contact Information

- Discord: **[fill in before posting]**
- Email: **[fill in before posting]**
- Telegram: **[fill in before posting]**

> Note: fill these three fields before publishing to Nervos Talk.

---

## 3. Project Background

### Background Description

This proposal comes from a specific infrastructure problem:

- aircraft tracking systems often rely heavily on self-reported aircraft positions
- receiver fleets are frequently managed centrally or informally
- there is a large gap between raw radio observations and usable data products

That gap creates several issues:

- weak coordination of distributed receivers
- difficulty auditing receiver identity and metadata
- fragile integration paths between feed collection and product delivery
- poor packaging of MLAT-style outputs as something a customer could actually use

### Scenario-Based Explanation

A platform team may want to build a regional aviation data product using multiple receivers operated by different contributors.

Today they often end up with:

- spreadsheets for receiver metadata
- private service registries
- custom ingestion logic
- inconsistent receiver identity handling
- raw observations that still need a lot of work before they become usable API output

This project addresses that by separating concerns:

- **CKB** for receiver identity and registry state
- **off-chain processing** for signal correlation and MLAT solving
- **API/dashboard** for quality-aware output delivery

### Ecosystem Relevance

This matters to the CKB ecosystem because it demonstrates a real pattern for using CKB as:

- a decentralized registry
- a metadata ownership layer
- a coordination substrate for distributed infrastructure

It deliberately avoids weak blockchain usage such as:

- storing bulky telemetry directly on-chain

Instead, it uses CKB where it is strongest:

- durable shared state
- externalized identity/ownership
- registry-backed discovery

---

## 4. Solution

### Core Solution

MLAT Airspace Console combines:

- CKB-backed receiver discovery
- live or simulated observation ingress
- correlation and multilateration solving
- quality/freshness/reliability instrumentation
- persistence
- API and dashboard delivery

### User Perspective

Operators and downstream consumers will be able to:

- inspect aircraft position outputs
- understand uncertainty and quality of each estimate
- inspect which receivers supported a result
- differentiate replay/demo versus live outputs
- consume recent positions and history through API or UI

### Differentiation

This project differs from typical alternatives by combining:

- CKB-backed receiver registry workflows
- off-chain MLAT runtime
- benchmark-oriented readiness surfaces
- packaging for public/demo versus premium access

The main differentiation is not “we use blockchain.”

The differentiation is:

- more explainable outputs
- clearer infrastructure separation
- a credible route toward premium aviation data packaging

---

## 5. Technical Approach

### Tech Stack

- **Python** for runtime, API, adapters, and tooling
- **Flask / Flask-SocketIO** for API and streaming surfaces
- **SQLite** for local persistence
- **Rust** for the receiver-registry smart contract
- **CKB testnet** for registry deployment and receiver metadata discovery
- **HTML / CSS / JavaScript** for dashboard and product surfaces

### Architecture Overview

```text
receiver identity / discovery
  -> observation ingress
  -> signal correlation
  -> MLAT solving
  -> quality normalization
  -> SQLite persistence
  -> API / WebSocket / dashboard delivery
```

Main modules:

- `src/network/ckb_discovery.py`
- `src/network/ckb_client.py`
- `src/network/feed_transports.py`
- `src/correlation/correlator.py`
- `src/mlat/robust_solver.py`
- `src/database/mlat_db.py`
- `src/api/rest_api.py`
- `src/production_main.py`

### Key Technical Challenges

#### 1. Correct blockchain role

Challenge:
- avoid using blockchain for bulky telemetry

Approach:
- use CKB only for receiver identity / metadata / ownership workflows

#### 2. Quality-aware output

Challenge:
- raw positions are not enough

Approach:
- attach:
  - quality score
  - uncertainty
  - solver residual
  - receiver count
  - correlation metadata

#### 3. Benchmarkability discipline

Challenge:
- replay/demo output can be mistaken for real proof

Approach:
- explicit readiness and benchmarkability checks
- benchmark/export tooling
- OpenSky comparison workflow

#### 4. Live ingest flexibility

Challenge:
- different live sources may exist

Approach:
- multiple ingest paths:
  - `websocket-json`
  - `command-jsonl`
  - bridge adapter
  - Beast TCP adapter
  - multi-receiver Beast bridge

### Language

- English supported at minimum in documentation and product surfaces

---

## 6. To-Do List

### Week 1

- finalize live ingest path for real observations
- validate local or remote receiver input strategy
- confirm receiver identity mapping for live bridge mode

### Week 2

- connect at least one real observation source
- verify real aircraft identifiers are entering the DB
- verify `synthetic_feed_mode = false`

### Week 3

- connect enough receivers for meaningful MLAT operation
- validate receiver participation and runtime health
- confirm real live outputs are persistence-ready

### Week 4

- export real MLAT positions
- fetch trusted OpenSky reference data
- run first benchmark comparison

### Week 5

- refine benchmark workflow
- evaluate:
  - quality
  - freshness
  - reliability
  - completeness

### Week 6

- improve dashboard/API surfaces based on benchmark findings
- package benchmark results into project-facing documentation

### Week 7

- strengthen payments / packaging surfaces
- prepare a clearer premium data story and usage model

### Week 8

- finalize public-facing project state
- publish benchmark-backed report and reference architecture notes

### Milestones

- **Milestone 1:** real observation ingress connected
- **Milestone 2:** real aircraft positions stored
- **Milestone 3:** first meaningful external benchmark completed
- **Milestone 4:** benchmark-backed product surface refinement completed

---

## 7. Required Funding & Funding Breakdown

### A. Required Funding

**Total Requested:** **$2,000**

### Why this amount

This project is not just pure contract work or pure UI work. It spans:

- smart contract / registry integration
- off-chain runtime and quality instrumentation
- benchmark tooling and external comparison workflow
- live-ingest integration
- product/API/dashboard packaging

That makes it structurally more complex than a simple single-category Spark project.

### B. Funding Breakdown

#### Technical development

- **$1,200**
  - live ingest integration
  - runtime hardening
  - multi-receiver bridge work
  - benchmark workflow execution

#### Benchmarking / validation

- **$400**
  - benchmark tooling usage
  - result validation
  - comparison reporting and analysis

#### Product / documentation / ecosystem packaging

- **$400**
  - dashboard/API refinement
  - public project documentation
  - verification and reporting materials

---

## 8. Deliverables + How To Verify

### A. Deliverables

- [ ] receiver-registry contract and deployment references
- [ ] benchmark-ready MLAT export tooling
- [ ] OpenSky reference fetch + comparison tooling
- [ ] readiness API surface
- [ ] live-ingest bridge path for real observations
- [ ] dashboard/API showing quality-aware outputs
- [ ] documentation for benchmark and live-ingest workflows

### Acceptance Criteria

#### Deliverable 1

Receiver registry is discoverable from CKB testnet.

#### Deliverable 2

MLAT DB positions can be exported into JSONL benchmark format.

#### Deliverable 3

Reference data can be fetched and compared against MLAT output.

#### Deliverable 4

`/api/readiness` returns structured readiness data for:

- quality
- freshness
- reliability
- packaging

#### Deliverable 5

Bridge and Beast tooling can produce normalized JSONL for the runtime.

#### Deliverable 6

Dashboard and API surface expose quality/solver/correlation metadata.

### B. How To Verify

#### Verification steps

Run:

```bash
python -m pytest
```

Check:

```bash
curl http://localhost:5051/api/health
curl http://localhost:5051/api/readiness
curl http://localhost:5051/api/positions/recent?seconds=300&limit=20
```

Benchmark workflow:

```bash
python3 scripts/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output benchmark/mlat.jsonl \
  --seconds 3600

python3 scripts/fetch_opensky_reference.py \
  --output benchmark/reference.jsonl \
  --time 1710000000 \
  --lamin 38.55 \
  --lomin -79.2 \
  --lamax 43.25 \
  --lomax -70.6

python3 scripts/benchmark_mlat_against_reference.py \
  --mlat benchmark/mlat.jsonl \
  --reference benchmark/reference.jsonl
```

#### Expected output

- passing tests
- readiness JSON with structured dimensions
- benchmark JSON output with coverage/error metrics
- dashboard routes loading through `/app/...` and `/dashboard.html`

#### Environment requirements

- Python 3.11+
- CKB testnet RPC/indexer access
- local dependencies from `requirements.txt`
- for live ingest proof: real observation source or Beast endpoint

#### Cost control

Verification can mostly be done through:

- tests
- API responses
- demo/dashboard checks
- benchmark command output

without deep code review as the only validation path.

---

## 9. Current State vs. Funded Work

### Current State

Already completed:

- receiver-registry contract in Rust
- deployed on CKB testnet
- receiver registration and discovery path
- MLAT runtime
- SQLite persistence
- health/statistics/readiness endpoints
- map-first dashboard
- benchmark tooling
- live-ingest scaffolding

### Funded Work

The funding period would specifically cover the delta from current state to:

- real live observation ingress
- benchmarkable live output
- first meaningful external benchmark
- benchmark-backed product refinement
- clearer public ecosystem packaging

### Clear Boundary

Current state is:
- architecture, tooling, and scaffolding

Funded work is:
- live proof
- benchmark proof
- product hardening based on that proof

---

## 10. CKB Alignment

### Connection Points

This project connects to CKB through:

- receiver identity
- receiver metadata discovery
- registry-backed ownership workflows

### Specific Design

The CKB-specific plan is:

- use a receiver-registry contract to store canonical receiver records
- discover receivers from CKB through RPC / indexer workflows
- use that off-chain receiver set as the input to the MLAT runtime

### Honest Declaration

CKB is not being used as the telemetry database.

That is intentional.

It is being used where it is strongest:

- durable shared state
- registry and metadata ownership
- externalized coordination

That makes the project relevant to the CKB ecosystem even though the main signal-processing and product delivery layers remain off-chain.

---

## Final Note

This proposal should be judged honestly:

- strong on architecture
- strong on tooling
- strong on ecosystem-relevant registry design
- not yet fully proven on live benchmark output

The purpose of the Spark funding period would be to push the project across that gap:

from

- benchmark-ready in theory

to

- benchmark-backed in practice
