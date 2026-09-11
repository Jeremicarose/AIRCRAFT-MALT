# CKB Spark Grant Analysis and Proposal

> **Direction update (2026-08-20):** This analysis selected an SDK-first
> milestone from the repository evidence available at the time. Subsequent
> product-review feedback correctly identified external demand as the more
> important unverified assumption. The current Spark direction is the
> [CKB Receiver Registry Operator Pilot](CKB_SPARK_PILOT_PROPOSAL.md). The
> SDK-first analysis below is retained as the technical baseline, not as the
> current submission recommendation. The workspace SDK was implemented on
> 2026-09-07; statements below that call it missing are historical findings.

Analysis date: 2026-08-16

Local review target: `b73f2efa92ddcfc41c448491402532b373cc2fa3`

Repository: [Jeremicarose/AIRCRAFT-MALT](https://github.com/Jeremicarose/AIRCRAFT-MALT)

This document separates facts already supported by the repository from work proposed for Spark. Anything described as a target, milestone, or future work does not exist yet.

## 1. Executive Assessment of the Project

The strongest project in this repository is not a production aircraft-tracking service. It is a testnet prototype of a CKB-native receiver identity and lifecycle registry, with MLAT as its first demanding reference application.

The Registry V2 implementation is technically real. It includes a `no_std` Rust type script, CKB-VM transaction tests, a Python record and discovery implementation, lifecycle tooling, and a signed CKB testnet evidence bundle. The contract uses a 32-byte Type-ID-derived identity and keeps that identity stable through update, ownership transfer, and permanent revocation. This is materially deeper than adding a transaction hash to a conventional application.

The MLAT reference is also more than a visual mock. Its replay path runs observations through correlation, clock qualification, the robust solver, SQLite, the Flask API, and an operator frontend. The live path and strict evidence gates are implemented. However, the repository does not contain a physical four-receiver synchronized capture or a trusted aligned reference dataset. The published MLAT accuracy fixture has only three synthetic records. It cannot support a real-world accuracy claim.

The repository is best described as a strong MIT-licensed, pre-release engineering prototype with unusually good self-produced evidence. It is not production-ready, independently audited, mainnet-deployed, or field-proven.

The best Spark milestone is a narrow **CKB Receiver Registry Developer Kit**. It should turn the existing contract and read-only Python adapter into a reusable CCC-based TypeScript SDK that can discover Registry V2 cells and build the complete create, update, transfer, and revoke lifecycle through a normal CKB signer. The milestone should also publish shared cross-language conformance tests and a new SDK-produced testnet evidence bundle.

This is stronger than funding a live MLAT trial because it is CKB-native, does not depend on hardware that is absent from the repository, and leaves a reusable asset even if the aviation project never advances. It is stronger than funding a generic Registry V3 because V3 schema design, migration, contract work, audit risk, and a second integration are too much for a small 4-6 week grant.

### Submission gates

The licensing gate is complete. The remaining submission gate is:

1. The cleaned Registry V2-first baseline is pushed and its exact commit is publicly accessible. The public GitHub page available during this review still showed the older MLAT-first layout. That may be cache or push timing, but reviewers must be able to inspect the same code described here.

## 2. Current Implementation Status

### Status by project area

| Area | What exists | Maturity | Important limit |
|---|---|---|---|
| Repository structure | Contract, registry modules, MLAT reference, tools, tests, evidence, and docs are separated | Complete for the current local baseline | The corresponding public commit was not independently confirmed |
| Frontend | Next.js operator console with overview, localization map, aircraft, receivers, pipeline, metrics, environment, and settings routes | Implemented reference UI | No browser regression, accessibility, or responsive test suite; not part of the current Render deployment |
| Backend | Python runtime for ingest, correlation, solving, persistence, telemetry, and API delivery | Replay integration complete | Large API and database modules; single-node only |
| APIs | Health, readiness, pipeline, evidence, mode, aircraft, positions, receivers, tracks, statistics, map bounds, admin cleanup, and Socket.IO | Implemented and tested | Process-local rate limiting is available for the single-node reference; no shared production limiter or account lockout; some commercial plan code is experimental packaging |
| CKB integration | Testnet contract deployment, lifecycle transactions, RPC/indexer discovery, provenance capture | Functional testnet prototype | No mainnet deployment, independent audit, or general write SDK |
| Smart contract | `no_std` Rust Registry V2 type script | Implemented and CKB-VM tested | JSON and floating-point parsing are complex; schema is receiver-specific |
| Receiver registry | Type-ID identity, exact sequence, immutable label, owner-lock transfer, terminal tombstone | Implemented | Human labels are not globally unique; physical truth is not attested |
| Receiver discovery | Paginated indexer query, schema validation, provenance, stale/future filtering, duplicate identity quarantine | Implemented read-only adapter | Python source module, not a separately released SDK |
| Registry writes | Record generation, transaction templates, Type ID application, lifecycle and evidence scripts | Implemented operator tooling | Capacity balancing, signing, and broadcast still depend on external `ckb-cli`; no CCC integration |
| Receiver lifecycle | Create, update, transfer, revoke, burn rejection, resurrection rejection | Implemented and evidenced on testnet | One historical test identity; final state is revoked |
| Observation ingest | Simulation, WebSocket JSON, command JSONL, Beast adapters, multi-receiver bridge | Implemented adapters | No published physical multi-receiver run |
| Correlation | Message grouping, nanosecond-aware clustering, unique receiver checks, quality metadata | Implemented and tested | Real RF collision and noisy-field behavior are not established |
| MLAT processing | Damped least-squares TDOA solver with ECEF/WGS84 conversion and diagnostic quality values | Implemented and tested | Solver accuracy is proven only on constructed/synthetic observations |
| Aircraft tracking | Position persistence, latest/recent/track API, live map, replay aircraft | Implemented in replay | No public live aircraft dataset |
| Data models | Registry records, receiver provenance, raw signals, correlated groups, solver positions, accounts/plans/keys/usage | Implemented | The Python registry mirror does not yet enforce the Rust contract's `u64` maximum for `sequence` and `updated_at` |
| Storage | SQLite with WAL, indexes, schema setup, position/receiver/statistics/access tables | Implemented single-node storage | No horizontal coordination, formal migrations, backup/restore exercise, or SLO |
| Tests | Python, Rust host, CKB-VM, shared conformance corpus, frontend type check | Strong prototype coverage | No independent contract tests, browser E2E suite, physical field test, or formal verification |
| Deployment | Docker image, three-service Compose topology, replay Render blueprint | Local/reference deployment | Render serves the older replay API/static console, not the current Next frontend; no production SLO |
| Documentation | Architecture, context, ADRs, deployment, evidence, reproducibility, field-trial and security docs | Extensive and unusually candid | Some status counts are stale relative to the current test suite |
| Existing demo | Public hosted replay console and local replay stack | Working replay demonstration | Public mode endpoint says simulation, synthetic, no live registry discovery, not benchmarkable |
| Benchmarks | Deterministic three-record synthetic accuracy fixture; local simulation performance/reliability files | Regression and experimental evidence only | No live accuracy, coverage, statistically useful reliability, or current production benchmark |
| Datasets | Three synthetic MLAT rows plus ignored local SQLite databases | No publishable real dataset | Local databases are untracked runtime state and cannot be grant evidence |
| Registry evidence | Signed deployment/lifecycle RPC data, discovery/API snapshots, seven rejected signed attacks, checksums and verification reports | Strong historical self-produced evidence | Not an audit and not proof of receiver existence or truthful coordinates |
| Security/release | MIT License, pinned workflows, CodeQL configuration, SBOM/attestation workflow, release gate | Implemented release machinery | No audit, first proper Registry V2 release, or confirmed protected-branch enforcement |

### Complete

- Registry V2 lifecycle rules in Rust.
- Type-ID creation and exact one-input/one-output lifecycle rules.
- Immutable Receiver Label and exact sequence increments.
- Ownership transfer through the successor cell's owner lock.
- Terminal revocation with burn and resurrection rejection.
- Python record validation and Type ID calculation.
- Paginated read-only discovery with provenance and duplicate quarantine.
- Signed testnet deployment and one complete lifecycle.
- Deterministic replay pipeline and synthetic benchmark generation.
- Strict live preflight, clock-evidence validation, raw capture, and offline re-solving tools.

### Partially complete

- Developer integration: discovery is available, but write-side use still requires manual transaction/tool knowledge.
- Release readiness: MIT licensing and automation exist, but the audit and public release are missing.
- Frontend verification: type checking and production compilation exist, but browser E2E and accessibility coverage do not.
- Deployment: local Compose is complete for a single host; the hosted deployment is replay-only and older than the local frontend architecture.
- Live ingest: software adapters and guardrails exist; a physical trial does not.

### Prototype or demo

- Registry V2 is a functional, unaudited testnet prototype.
- The public MLAT deployment is a replay demo.
- Access plans, entitlements, and usage metering are experimental product packaging.
- The MLAT frontend is an operator reference, not proof of the registry protocol.

### Simulated

- Hosted aircraft and receiver activity.
- The deterministic accuracy fixture.
- The local performance and 2.3-second reliability captures.
- Known-position solver tests.

### Production-ready

No complete subsystem should currently be presented as a production service. Some individual modules are carefully implemented, but the project as a whole lacks an independent contract audit, mainnet deployment, production SLOs, operational recovery tests, and live field evidence.

### Missing or not started

- Independent security audit and remediation cycle.
- CCC or another maintained developer-facing write SDK.
- Separately versioned and published Registry SDK.
- General physical-infrastructure schema without the `mode-s` requirement.
- Mainnet deployment.
- Physical synchronized four-receiver evidence.
- Trusted aligned aircraft reference dataset.
- Production reliability, disaster recovery, and horizontal scale evidence.
- Current public full-stack deployment of the Next.js frontend.

### Broken or not verified

- No core local test failed during this review.
- A cross-language boundary gap was confirmed outside the current corpus: Python accepts `sequence` and `updated_at` values above `u64::MAX`, while the Rust contract uses `u64`. This can make the off-chain validator approve a record that CKB will reject. The deployed contract is not weakened, but the Python mirror and shared corpus need correction.
- The default Turbopack frontend build could not run in the review sandbox because Turbopack attempted to bind an internal port. A Webpack production compilation succeeded and generated a `BUILD_ID`; TypeScript checking passed. This is an environment-limited verification, not proof that the default build is broken.
- Live CKB RPC re-verification could not be completed from the sandbox because of DNS/TLS environment restrictions. The saved July 30 live report passes and the current offline verifier passes, so the live claim remains historical rather than continuously reconfirmed.
- The public repository page available to the browser showed the older project layout. The local Registry V2-first commit must be confirmed public before submission.
- `docs/PROJECT_STATUS.md` says 122 Python tests and 4 host Rust tests. The current code ran 132 Python tests and 5 host Rust tests. The document is stale, not the tests.

### Verification performed for this analysis

| Check | Result | Qualification |
|---|---|---|
| Python suite | 132 passed | Ran under local Python 3.13.7, not the documented 3.12.11 baseline |
| Rust host tests | 5 passed | Pinned Rust 1.95.0 |
| CKB-VM lifecycle tests | 11 passed | Includes real secp256k1 lock verification and bounded rejection of an oversized record |
| Contract target check | Passed | `riscv64imac-unknown-none-elf` |
| Rust formatting | Passed | `cargo fmt -- --check` |
| Python formatting | 72 files unchanged | Black check |
| Python lint | Passed | Flake8 |
| Python dependency consistency | Passed | `pip check` |
| Frontend type check | Passed | Local Node 20 type check |
| Frontend production compilation | Webpack compiled and produced a build ID | Node 22.22.1; pinned project version is 22.23.1; default Turbopack was sandbox-blocked |
| Registry evidence | Passed | 50 files and 78 offline semantic/hash checks |
| Historical live report | Saved report passes | 83 checks, dated 2026-07-30, not re-run successfully in this environment |
| MLAT benchmark bundle | Passed | 14 files; synthetic regression only |
| Documentation links | Passed | 53 documentation files |
| Hosted demo | Reachable | Explicit replay/simulation, no live CKB discovery, not benchmarkable |

## 3. Strongest Problem Statement

### Ranked problem candidates

#### 1. Registry V2 is proven but not reusable through normal CKB application tooling

CKB developers who want an owner-controlled, discoverable lifecycle for physical receiver identities currently have to understand Registry V2's cell layout, JSON record rules, Type ID creation order, sequence continuity, capacity balancing, and manual `ckb-cli` workflows. The repository supplies a read-only Python adapter, but not a released SDK that discovers records and builds all lifecycle transactions through a maintained wallet abstraction.

This is the strongest Spark problem because it is concrete, visible in the code, CKB-specific, and fixable without depending on outside hardware or invented adoption. The existing MLAT runtime is the concrete first consumer. Other CKB or physical-infrastructure developers are target evaluators, not claimed existing users.

#### 2. Multi-operator receiver networks need shared identity and lifecycle state

A conventional database works when one operator controls every receiver. It becomes a trust bottleneck when different owners need to publish current receiver metadata, transfer ownership, and revoke an identity without giving one central administrator unilateral write authority. Registry V2 demonstrates how CKB cells, owner locks, Type ID, and indexer discovery can provide that shared state.

This is the strongest long-term product problem. Much of the core implementation already exists, so it is not the correct description of new Spark-funded work by itself.

#### 3. MLAT outputs need physical and independently reproducible evidence

An MLAT dashboard can show plausible tracks even when its timing is simulated. A credible live system needs four or more synchronized receivers, saved raw observations, clock uncertainty evidence, and an independent aligned position source. The repository has built the harness but has not executed the trial.

This problem is real, but it is a weaker Spark direction because the repository does not contain the hardware, synchronized receiver network, or trusted reference dataset needed to guarantee completion.

### Selected problem statement

**CKB Registry V2 demonstrates a secure receiver identity lifecycle on testnet, but it is not yet reusable CKB infrastructure because third-party developers still need manual transaction assembly and a repository-internal Python adapter. The missing piece is an open, signer-compatible SDK and conformance package that makes the lifecycle reproducible from a clean checkout.**

### Who experiences the problem

- The current MLAT integrator, which has working read-only discovery but no normal application SDK for registry writes.
- CKB developers evaluating a Type-ID-based identity pattern for receiver or other constrained physical-node applications.
- Developers building CKB-aware operator tools that need to display registry provenance or submit owner-authorized lifecycle changes.

The repository does not prove that any external team currently depends on this registry. The Spark milestone should be presented as validation and reusable developer infrastructure, not as a response to named customers or partnerships.

### Why existing tools do not fully solve it

`ckb-cli` and CCC can build and sign general CKB transactions. They do not know Registry V2's record schema, exact sequence rule, immutable label rule, terminal revocation, Type-ID output placement, or evidence format. The project-specific SDK should use CCC instead of replacing it. Its value is encoding the Registry V2 protocol safely on top of the standard CKB transaction and signer layer.

### Why the problem matters now

The contract and signed testnet evidence already exist. The next credible step is not another dashboard. It is making the proven lifecycle consumable and independently testable by someone other than the author. Without that step, Registry V2 remains a well-documented one-repository prototype.

### What becomes possible

- A developer can install one package and discover validated Registry V2 cells with full provenance.
- An owner can create, update, transfer, or revoke a receiver through a CCC signer without the SDK accepting raw private keys.
- Rust, Python, and TypeScript implementations can be checked against one shared behavior corpus.
- Reviewers can reproduce a fresh testnet lifecycle and verify it offline from saved artifacts.
- The MLAT reference can remain the first integration while the registry becomes a separable CKB developer asset.

## 4. Strongest CKB Value Proposition

### What CKB contributes

| CKB feature | Actual project use | Value |
|---|---|---|
| Cell model | One live Registry Cell represents the current receiver lifecycle state | State is explicit, spendable, and linked through transaction history |
| Lock script | The current cell's lock authorizes update, transfer, and revocation | Ownership uses CKB's normal authorization model rather than a contract administrator key |
| Type script | Registry V2 validates record shape and lifecycle transitions | Invalid sequence, label mutation, burn, duplication, and resurrection are rejected by consensus |
| Type ID | The 32-byte type argument is derived from the first creation input and output index | Each lifecycle receives a stable identity that does not depend on a human label or timestamp |
| Indexer/RPC | Consumers enumerate cells by the deployed registry code hash and validate each record | Discovery is public and does not depend on a project-owned database endpoint |
| Cell data | Receiver metadata, stream information, lifecycle sequence, and optional metadata commitment are stored in the cell | Consumers can read current declared state directly from CKB |
| Transaction history | Create, update, transfer, and revoke transactions form the lifecycle chain | Reviewers can inspect accepted state transitions and owner-lock changes |
| Capacity model | Revocation tombstones remain live cells and continue occupying capacity | Permanent revocation has an explicit economic cost and cannot silently disappear |
| CKB-VM | The Rust type script executes the same lifecycle rules for all transactions | Protocol behavior is enforced on chain rather than trusted to one API server |
| CCC | Proposed Spark SDK will use the maintained signer/transaction layer | The project can integrate with CCC signers without handling raw keys itself |

### Why not use only a traditional database

A database is the better choice for one trusted operator. It is cheaper, faster, easier to query, and easier to change.

CKB becomes justified when several independent owners need a shared registry where:

- each owner authorizes changes with their own CKB lock;
- ownership can transfer without a central database administrator rewriting authority;
- consumers can discover state from public infrastructure;
- the lifecycle is linked to transactions that third parties can inspect;
- revocation cannot be deleted or reversed by the registry host.

The chain does not make receiver coordinates, hardware, clocks, or streams truthful. It proves authorization and state-transition validity. Physical claims still require off-chain evidence.

### Is CKB superficial in the current project?

No. The contract uses CKB-native Type ID semantics, script groups, owner locks, live cells, indexer discovery, and CKB-VM rejection. The signed testnet lifecycle shows these parts working together.

The weak point is usability rather than depth. Registration and mutation still rely on manual tools, and the read adapter is tied to the source repository. A CCC-based SDK directly strengthens the CKB component without pretending that blockchain solves MLAT timing or physical attestation.

### Important CKB limitations

- The current V2 binary requires `mode-s`. It is not a generic infrastructure registry.
- The human Receiver Label is immutable but not globally unique.
- JSON and floating-point record parsing create more consensus complexity than a compact Molecule schema. The current Python mirror also lacks the contract's `u64` upper bounds for `sequence` and `updated_at`.
- The contract is unaudited.
- A tombstone consumes CKB capacity permanently.
- Changing contract behavior requires a new binary, code hash, deployment, and migration policy.

## 5. Three Possible Spark Grant Directions

### Direction A: CKB Receiver Registry Developer Kit

**Problem:** Registry V2 works on testnet but third-party use requires repository knowledge, manual `ckb-cli` flows, and a Python-only read adapter.

**Proposed solution:** Release a CCC-based TypeScript SDK for record validation, Type ID calculation, paginated discovery, and signer-driven create/update/transfer/revoke transactions. Add shared Rust/Python/TypeScript conformance tests and a fresh testnet evidence bundle produced through the SDK.

**Why CKB:** Every deliverable directly exercises cells, locks, type scripts, Type ID, indexer discovery, and transaction lineage.

**Target users:** CKB application developers evaluating receiver identity and lifecycle; the MLAT reference maintainer; developers building registry operator tools.

**Ecosystem value:** A reusable and verifiable example of owner-authorized physical receiver identity on CKB, layered on CCC instead of custom key handling.

**Technical novelty:** The contract itself already exists. The new value is a protocol-aware SDK that safely coordinates CCC input completion with Type ID derivation and preserves the same lifecycle rules across three languages.

**Deliverables:** TypeScript SDK, CCC lifecycle builders, expanded conformance corpus, CI, fresh testnet lifecycle evidence, package/release documentation, and completion report.

**Risks:** CCC API changes, Type ID output-order mistakes, no independent audit, and a possible perception that this duplicates generic CKB SDK functionality.

### Direction B: Generic Physical Infrastructure Registry V3

**Problem:** Registry V2's receiver-specific JSON schema and mandatory `mode-s` capability prevent honest reuse by non-aviation infrastructure.

**Proposed solution:** Specify and implement a domain-neutral binary Registry V3 with Type ID lifecycle, metadata commitments, a generic discovery SDK, migration rules, and a new testnet deployment.

**Why CKB:** The project would turn Type ID cells and owner locks into a reusable physical-node registry primitive.

**Target users:** CKB developers exploring DePIN, IoT, and multi-owner infrastructure registries. These are target users, not current adopters.

**Ecosystem value:** Broader reuse than an aviation-specific receiver schema.

**Technical novelty:** A compact canonical schema, explicit V2/V3 migration boundary, and generic off-chain metadata commitment model.

**Deliverables:** ADR/specification, Molecule schema, contract, CKB-VM tests, SDK, migration vectors, testnet deployment, evidence, and one non-aviation example.

**Risks:** Too much schema, migration, contract, SDK, and integration work for Spark; no independent audit; no proven non-aviation adopter; easy to produce a generic abstraction without a validated use case.

### Direction C: CKB-Registered Physical MLAT Field Trial

**Problem:** The MLAT stack has no public physical synchronized receiver window or real accuracy comparison.

**Proposed solution:** Register four or more physical receivers on CKB testnet, qualify clocks, capture raw Beast observations, solve positions, compare them with an independent reference, and publish a reproducible evidence bundle.

**Why CKB:** CKB supplies receiver identity, ownership, discoverability, and lifecycle provenance for the physical trial.

**Target users:** Aviation-data experimenters and CKB developers studying a real physical infrastructure integration.

**Ecosystem value:** A concrete CKB DePIN-style reference and strong physical validation of the repository.

**Technical novelty:** Linking Type-ID identities and owner state to nanosecond timing evidence and offline MLAT re-solving.

**Deliverables:** Four registered identities, clock artifacts, raw observation dataset, position dataset, reference comparison, reliability window, verification bundle, and report.

**Risks:** The repository contains no qualifying hardware, synchronized network, or aligned reference dataset. Weather, coverage, oscillator quality, and receiver availability can block completion. CKB is supporting infrastructure rather than the main technical deliverable.

## 6. Scoring and Selected Direction

Scores use 1 as weak and 10 as strong.

| Direction | CKB relevance | Ecosystem usefulness | Technical credibility | Grant attractiveness | Feasibility | Verifiability | Long-term potential | Total / 70 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A. Receiver Registry Developer Kit | 10 | 8 | 9 | 9 | 9 | 10 | 8 | **63** |
| B. Generic Registry V3 | 10 | 9 | 7 | 9 | 6 | 8 | 10 | **59** |
| C. Physical MLAT field trial | 6 | 7 | 7 | 8 | 4 | 9 if completed | 8 | **49** |

### Selection

Direction A is selected.

It converts the strongest existing proof into the smallest reusable CKB asset. It does not charge the grant for the already-built contract, MLAT backend, dashboard, or historical evidence. It also avoids promising hardware-dependent results.

Direction B has the highest long-term potential, but it should follow after the V2 developer experience is validated. Direction C should proceed only when the physical receiver and timing prerequisites are already secured before funding.

The accepted CKB Wallet Behaviour Intelligence proposal provides a useful review benchmark. Its committee narrowed the grant to the core reusable asset, required independent verification, removed dashboard and partner work, and approved $900. The same principle applies here: fund the registry developer kit, not the entire aviation and generic-infrastructure vision.

## 7. Recommended Spark Scope

### Current project, not funded again

- Registry V2 Rust contract.
- Existing 5 host tests and 11 CKB-VM tests.
- Existing Python record/discovery modules.
- Existing `ckb-cli` transaction and lifecycle tools.
- Existing July 30 testnet deployment and lifecycle evidence.
- MLAT replay backend, SQLite API, frontend, and synthetic benchmark.
- Live field-trial harness.

### Spark milestone

Build and release a **CKB Receiver Registry V2 Developer Kit** with:

1. A TypeScript SDK based on CCC.
2. Record encoding, validation, Type ID calculation, indexer discovery, and provenance models.
3. Signer-driven builders for create, update, transfer, and revoke.
4. One shared conformance corpus executed by Rust, Python, and TypeScript.
5. A fresh SDK-produced CKB testnet lifecycle and immutable evidence bundle.
6. Reproducible quickstart, API reference, threat/limitation notes, and completion report.

### Explicitly outside Spark

- Contract redesign or new Registry V3 schema.
- Mainnet deployment.
- Independent professional audit.
- Physical receiver hardware or field trial.
- MLAT accuracy, coverage, or reliability claims.
- Dashboard redesign or current Next.js deployment.
- Commercial plans, billing, incentives, reputation, or payments.
- Partner integrations or adoption targets.
- Horizontal scaling and production SLOs.

### Scope constraints

- The SDK will support Registry V2 exactly as deployed. It will not imply generic infrastructure support.
- The SDK will accept a CCC signer or transaction context. It will not accept, store, or log raw private keys.
- Any contract behavior change is out of scope. A discovered contract flaw stops release and is reported; it is not silently patched under the same code hash.
- Testnet evidence demonstrates transaction and discovery behavior, not physical receiver truth.
- No hosted server is required to complete the milestone.

## 8. Deliverables

### Deliverable 1: Open-source Registry V2 TypeScript SDK

A public package in the grant repository containing:

- Registry V2 TypeScript types.
- Canonical record encode/decode and validation.
- Type ID calculation compatible with the Rust contract and Python helper.
- Paginated CKB indexer discovery by deployed code hash.
- Provenance output containing identity args, owner lock, outpoint, block number, sequence, status, and metadata commitment.
- Duplicate live identity quarantine and explicit active/all-record filtering.
- Exact dependency lock and semantic version.

**Acceptance:** A clean checkout can install, build, test, and pack the SDK. The package contains no MLAT runtime dependency.

### Deliverable 2: CCC lifecycle transaction API

SDK operations for:

- create with sequence 0 and a Type-ID-derived identity;
- update with exact sequence increment;
- transfer by changing the successor owner lock while preserving identity and label;
- revoke by creating a terminal tombstone with no stream fields.

The API must use CCC's signer/transaction facilities and must never require the package to manage raw private keys.

**Acceptance:** A reproducible local/devnet test executes all four lifecycle stages. A separate maintainer-run testnet lifecycle uses the same public SDK code.

### Deliverable 3: Cross-language conformance and adversarial suite

Expand the current 22-case shared corpus to at least 40 named cases covering:

- valid and invalid records;
- identity length and Type ID vectors;
- sequence reuse, jump, and overflow boundaries;
- immutable label and timestamp rollback;
- revoked stream rules and terminal revocation;
- duplicate capability and size boundaries;
- malformed, trailing, unknown, and type-confused JSON;
- pagination, duplicate labels, and duplicate live identity behavior.

Run the same corpus in Rust, Python, and TypeScript CI.

**Acceptance:** All three implementations produce the expected result for every shared case. Existing CKB-VM lifecycle tests remain green.

This acceptance target includes correcting the confirmed Python `u64` boundary mismatch so off-chain validation cannot approve an integer the contract cannot decode.

### Deliverable 4: Fresh SDK-produced CKB testnet evidence

Publish a new immutable evidence directory containing:

- exact SDK package version and source commit;
- deployed Registry V2 code hash used;
- create, update, transfer, and revoke transaction hashes;
- saved signed transactions with signatures but no private keys;
- RPC responses and indexer discovery snapshots at every stage;
- owner-lock change and sequence lineage;
- package, source, and artifact checksums;
- offline verification report and a dated live verification report.

**Acceptance:** One new test identity completes sequences 0, 1, 2, and 3; its owner lock changes during transfer; its final accepted state is revoked; the offline verifier passes from a clean checkout.

### Deliverable 5: Reproducibility documentation and completion report

Publish:

- install and five-minute quickstart;
- CCC signer integration example;
- read/discovery example;
- API reference;
- V2 schema and lifecycle explanation;
- security and trust-boundary notes;
- local/devnet reproduction commands;
- testnet explorer links;
- short demonstration video;
- final completion report with exact metrics and limitations.

**Acceptance:** A reviewer can follow the quickstart without private maintainer knowledge and can verify the evidence without the demonstration video.

## 9. Verification Plan

| Deliverable | Independent verification | Required artifact |
|---|---|---|
| Public SDK | Clone exact tag, install locked dependencies, run build/tests, run package build, inspect exported API | Public repository, package lock, versioned package/archive, checksum |
| Record and Type ID compatibility | Run shared corpus under Rust, Python, and TypeScript; compare expected outcomes | Shared JSON corpus, CI logs, local commands |
| Discovery | Run mocked multi-page tests, then query the known testnet code hash and compare stage snapshots | Unit tests, configurable RPC/indexer example, saved snapshots |
| Create | Check transaction output type args match the Type ID derived from first input and output index; check sequence 0 | Transaction hash, signed transaction JSON, RPC response, verifier result |
| Update | Confirm the transaction spends the created cell, preserves identity/label, and sets sequence 1 | Transaction and lineage report |
| Transfer | Confirm the transaction spends the update cell, preserves identity, changes owner lock, and sets sequence 2 | Transaction and owner-lock report |
| Revoke | Confirm the transaction spends the transfer cell, sets `revoked`, removes stream fields, and sets sequence 3 | Transaction, tombstone cell, discovery snapshot |
| Evidence integrity | Re-run offline verifier and checksum validation from the tagged source | Manifest, checksums, verification JSON |
| Live chain existence | Open explorer links or run verifier with `--live` against a public CKB testnet RPC | Explorer links and dated live report |
| Documentation | Follow the quickstart from a clean checkout and compare produced output with the completion report | Quickstart, API docs, release tag, completion report |

### Proposed reproducible command surface

The exact package path may be finalized in Week 1, but completion must provide commands equivalent to:

```bash
npm ci
npm run build
npm test
npm run test:conformance

python3 -m pytest -q tests/registry

cd contracts/registry-v2
make test
make check
```

Evidence verification must remain a single documented command with optional `--live` network re-query.

Screenshots and video are supporting evidence only. Transaction hashes, saved artifacts, test vectors, and reproducible commands are the primary verification path.

## 10. Success Metrics

No benchmark number below is claimed as a current result unless the baseline column says so.

| Metric | Current baseline | Spark target |
|---|---:|---:|
| Public project-specific TypeScript SDKs | 0 | 1 versioned SDK release |
| CCC lifecycle operations | 0 | 4: create, update, transfer, revoke |
| Languages using shared conformance corpus | 2: Rust and Python | 3: Rust, Python, TypeScript |
| Shared conformance cases | 22 | At least 40 |
| Existing contract tests | 5 host + 11 CKB-VM | All remain passing |
| New TypeScript SDK tests | 0 | Passing tests for every public behavior and lifecycle stage |
| Fresh SDK-produced testnet identities | 0 | 1 complete lifecycle identity |
| Fresh accepted Registry V2 lifecycle transactions | 0 | 4 in order |
| Fresh lifecycle sequence | None | Exactly `[0, 1, 2, 3]` |
| Ownership transfers in fresh evidence | 0 | 1 verifiable owner-lock change |
| Terminal revocations in fresh evidence | 0 | 1 final tombstone |
| Evidence verifier result | Existing historical package passes | New SDK package passes offline; dated live report also passes |
| Private keys committed | 0 known | 0 |
| Paid runtime dependencies | None required | $0 paid infrastructure required for verification |
| Clean-checkout reproduction | Existing components have separate commands | One documented end-to-end developer-kit verification path |

Metrics deliberately excluded from this milestone:

- registered physical receiver count;
- aircraft count;
- localization accuracy;
- live throughput and API latency;
- production uptime;
- adoption, partner, or user counts.

The repository cannot currently guarantee or honestly measure those outcomes within this SDK milestone.

## 11. Technical Architecture

### Spark architecture

```text
OFF CHAIN: OWNER APPLICATION

CCC Signer
    |
    v
Registry V2 TypeScript SDK
    |-- validate and encode Receiver Record
    |-- complete inputs and derive Type ID for create
    |-- preserve identity and exact sequence for successors
    |-- construct update / transfer / revoke transactions
    |
    v
Signed CKB transaction
    |
    v
ON CHAIN: CKB TESTNET

Owner Lock authorization
    +
Registry V2 Type Script
    |-- Type ID creation rule
    |-- one-cell lifecycle cardinality
    |-- record schema and bounds
    |-- sequence and label continuity
    |-- terminal revocation
    |
    v
Live Registry Cell
    |
    +-----------------------------> transaction/RPC evidence
    |
    v
CKB Indexer
    |
    v
OFF CHAIN: DISCOVERY AND CONSUMPTION

TypeScript SDK discovery / existing Python discovery
    |-- validate cell data
    |-- key by 32-byte identity args
    |-- retain owner lock, outpoint, block, and sequence
    |-- quarantine duplicate live identities
    |
    v
Validated Receiver Identity and Receiver Record
    |
    v
Receiver network adapter
    |
    v
Observation ingest -> Mode-S correlation -> clock gate -> MLAT solve
    |
    v
SQLite -> Flask API -> Next.js operator frontend
```

### On-chain components

- Registry V2 contract binary and type script.
- The live Registry Cell for each lifecycle.
- Owner lock on the current cell.
- The 32-byte Type ID argument.
- Receiver Record cell data.
- Accepted transaction history and permanent revocation tombstone.

The current record stores receiver coordinates and stream metadata on chain. The contract validates their format and bounds, not their truth.

### Off-chain components in the Spark milestone

- CCC signer supplied by the consuming application.
- TypeScript record codec and validator.
- Transaction builders for all lifecycle operations.
- Indexer discovery and provenance mapping.
- Shared conformance corpus and test runners.
- Evidence capture, checksums, and verifier.

### Existing off-chain reference path

- Receiver feed adapters.
- Raw observation normalization.
- Message correlation.
- Common-clock qualification.
- Robust MLAT solve.
- SQLite storage.
- Flask/Socket.IO API.
- Next.js dashboard.

The MLAT path demonstrates consumption but is not a Spark deliverable in the selected milestone.

### Verification layer

Verification joins four independent forms of evidence:

1. Shared behavior vectors prove that Rust, Python, and TypeScript interpret the protocol consistently.
2. CKB-VM tests prove the on-chain script rejects invalid transaction shapes.
3. Testnet transaction hashes prove that the SDK-built accepted lifecycle was submitted and committed.
4. The offline evidence verifier proves the saved artifacts, identity, sequence, owner-lock change, and tombstone lineage without depending on a live RPC.

### Trust boundary

```text
CKB proves:
  owner authorization + valid lifecycle transition + immutable transaction evidence

CKB does not prove:
  hardware exists + coordinates are surveyed + clock is synchronized + stream is honest
```

## 12. Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Local cleaned commit is not publicly confirmed | Reviewers may inspect the obsolete MLAT-first repository | Push and link the exact baseline commit before proposal submission |
| CCC API changes | SDK examples or signer integration may break | Pin an exact CCC version, commit the lockfile, isolate CCC-specific code, and test the documented transaction pattern |
| Type ID depends on finalized first input and output index | A builder could derive the wrong identity if it calculates too early | Complete/select creation inputs first, use an explicit output index, compare against shared Rust/Python vectors, and test in CKB-VM/devnet |
| Contract is unaudited | SDK usability can increase exposure to an undiscovered contract flaw | Keep testnet/prototype labels, make no mainnet claim, do not change contract behavior, and leave independent audit as a separate milestone |
| JSON/integer/floating-point consensus complexity | Cross-language edge cases may diverge; Python currently accepts sequence/timestamp integers above Rust `u64` | Add explicit `u64::MAX` and overflow vectors, correct the Python mirror, expand type-confusion vectors, and fail closed on any mismatch |
| Generic-infrastructure scope creep | The grant could become a Registry V3 redesign | Keep the package and proposal receiver-specific; require a new ADR, contract, code hash, and grant for V3 |
| Testnet RPC/indexer instability | Live verification may fail even when transactions exist | Use configurable endpoints, save complete RPC/indexer responses, and make offline verification the primary acceptance path |
| Wallet-specific behavior | A transaction may work with one signer but not another | Depend on the CCC signer interface, avoid wallet-specific private-key logic, and document the tested signer environment |
| Private key leakage during testnet evidence | Security incident and invalid public artifacts | Supply signer from the operator environment, scan artifacts, save signatures only, and require `private_keys_included=false` in the manifest |
| Evidence is self-produced | It is weaker than an independent review | Make artifacts reproducible and externally queryable; explicitly avoid calling the package an audit |
| No third-party adopter | Ecosystem usefulness may remain hypothetical | Deliver a small standalone package and one existing MLAT reference integration; do not claim adoption or spend grant time on partner outreach |
| Existing public demo causes confusion | Reviewers may think synthetic positions prove live operation | Exclude the dashboard from deliverables and label the hosted deployment as replay-only in the proposal |
| Funding is too small for all desired work | Schedule pressure can reduce test or documentation quality | Exclude contract redesign, field work, frontend work, hosting, audit, and mainnet; fund only 50 hours of SDK/evidence work |

### Milestone resilience

The milestone remains useful if no future funding arrives. A released SDK, shared conformance corpus, and signed testnet lifecycle are independently reusable and verifiable. The result does not require a future MLAT field trial to justify completion.

## 13. Funding Breakdown

### Developer time

| Task | Hours | Rate | Cost | Description |
|---|---:|---:|---:|---|
| TypeScript records and discovery SDK | 14 | $20/hour | $280 | Types, codec, validation, Type ID compatibility, indexer pagination, provenance, duplicate handling |
| CCC lifecycle transaction API | 18 | $20/hour | $360 | Create, update, transfer, revoke, signer integration, capacity/input/output ordering, local lifecycle test |
| Cross-language conformance and CI | 8 | $20/hour | $160 | Expand corpus to 40+ cases, TypeScript runner, Rust/Python/TypeScript CI |
| Testnet lifecycle and evidence | 6 | $20/hour | $120 | Execute fresh lifecycle, save RPC/indexer/transaction artifacts, checksums and verification report |
| Documentation and release | 4 | $20/hour | $80 | Quickstart, API reference, limitations, package/release, short demo, completion report |
| **Total developer time** | **50** |  | **$1,000** |  |

### Infrastructure and deployment

| Item | Cost | Reason |
|---|---:|---|
| GitHub repository and Actions | $0 | Public repository and available CI are sufficient |
| npm package/archive publication | $0 | Public package publication or GitHub release requires no paid hosting |
| CKB testnet RPC/indexer/explorer | $0 | Public testnet infrastructure is sufficient; endpoints remain configurable |
| Testnet CKB | $0 | Faucet/test tokens have no grant budget value |
| VPS, database, domain | $0 | The SDK and evidence do not require a hosted service |
| **Total infrastructure** | **$0** |  |

### Total grant requested

**$1,000**

This stays at Spark's normal single-category budget. It does not charge for work already present in the repository, hardware, an audit that has not been arranged, or infrastructure the milestone does not need.

## 14. Timeline

### Week 1: Public baseline, SDK contract, and record compatibility

**Technical work**

- Confirm public grant repository and exact baseline commit.
- Confirm the selected open-source license is present.
- Freeze the SDK public API and threat boundaries.
- Implement TypeScript record types, codec, validation, and Type ID vectors.
- Run the existing 22-case corpus in TypeScript.
- Correct the Python `u64` boundary mismatch and add boundary vectors.

**Measurable output**

- Installable SDK skeleton.
- TypeScript passes all existing shared vectors.
- Rust and Python integer boundaries agree.
- Version and dependency lock committed.

**Verification artifact**

- Public commit, CI run, package build, and API design document.

### Week 2: Indexer discovery, provenance, create, and update

**Technical work**

- Implement prefix discovery by Registry V2 code hash.
- Add pagination, active/all-record filtering, record validation, and sorting.
- Preserve identity, owner lock, outpoint, block number, sequence, and metadata hash.
- Add duplicate-label and duplicate-live-identity behavior.
- Implement CCC signer-driven create and update operations.
- Ensure creation derives Type ID after selecting the first input and exact output index.

**Measurable output**

- Multi-page mocked discovery passes.
- Malformed cells are rejected.
- Duplicate identities are quarantined while duplicate labels remain distinct.
- Create and update produce accepted local/devnet transactions.

**Verification artifact**

- Discovery tests, fixture responses, a testnet read example, and local/devnet transactions.

### Week 3: CCC lifecycle completion and conformance expansion

**Technical work**

- Implement signer-driven transfer and revoke operations.
- Add successor validation before signing.
- Execute the full lifecycle on local/devnet CKB.
- Expand the shared corpus from 22 to at least 40 cases.
- Run the corpus in Rust, Python, and TypeScript.

**Measurable output**

- Four lifecycle methods produce accepted local/devnet transactions.
- No raw private-key API exists.
- Identity, label, sequence, owner lock, and tombstone rules match the contract.
- At least 40 shared cases pass in all three languages.

**Verification artifact**

- Local lifecycle transcript, transaction fixtures, automated integration test, and CI matrix.

### Week 4: Testnet lifecycle, evidence freeze, and release

**Technical work**

- Execute one fresh create/update/transfer/revoke lifecycle on CKB testnet through the SDK.
- Capture RPC and indexer state after each accepted transaction.
- Generate the evidence manifest and checksums.
- Complete offline and dated live verification reports.
- Publish the tagged SDK package/archive.
- Finish the quickstart, API reference, limitations, security notes, short demonstration, and formal completion report.

**Measurable output**

- Four ordered testnet lifecycle transactions are committed.
- Transfer changes owner lock and revoke creates the final tombstone.
- Clean-checkout verification succeeds.
- SDK release and evidence bundle are publicly accessible.
- Completion report lists actual metrics, deviations, and residual risks.

**Verification artifact**

- Transaction hashes, signed transaction files, RPC/indexer snapshots, release tag, package checksum, evidence bundle, verifier output, video, and final report.

## 15. CKB Ecosystem Impact

### Realistic beneficiaries

#### CKB application developers

They receive a concrete CCC-based example of a Type-ID lifecycle with discoverable cells, owner-lock transfer, terminal revocation, and cross-language behavior tests. They can study or reuse the receiver-specific SDK without learning the project's internal `ckb-cli` scripts first.

#### Physical receiver network developers

Projects with receiver-like nodes can reuse Registry V2 only if the `mode-s` record fits their domain. Other DePIN or IoT projects can reuse the architectural pattern and test approach, but they cannot honestly use the current contract as a generic registry.

#### MLAT reference maintainers

The existing aviation application gains a normal developer-facing registry integration path. This reduces the gap between its read-only discovery adapter and the complete owner lifecycle.

#### CKB tooling and analytics developers

Tools that choose to decode this specific registry can reuse the record codec and provenance model. No explorer or analytics integration is claimed as committed.

### Why this is reusable infrastructure

- The SDK is separated from MLAT processing.
- The public interface is built on CCC rather than a project-owned key manager.
- The conformance corpus is language-neutral.
- The evidence verifier works from saved public artifacts.
- The reference application is one consumer, not the protocol itself.
- The milestone remains useful without a hosted dashboard.

### Open-source strategy

The grant will publicly release:

- Registry V2 TypeScript SDK source.
- Exact dependency lock.
- Build and package scripts.
- CCC lifecycle implementation.
- Shared conformance corpus and all test runners.
- CI configuration.
- Testnet transactions, RPC/indexer snapshots, checksums, and verification reports.
- Quickstart, API documentation, security notes, and completion report.
- Demonstration video.

The following will not be published:

- Private keys, seed phrases, wallet state, or feed credentials.
- Ignored local SQLite databases.
- Unrelated deployment scratch files.
- A physical MLAT dataset, because none exists for this milestone.

The repository satisfies the open-source licensing precondition under the OSI-approved MIT License.

## 16. Future Work

The following work should not be included in the Spark acceptance criteria:

1. **Independent contract audit and remediation.** A named external reviewer should assess the exact contract commit, JSON/floating-point behavior, CKB transaction shapes, and tombstone model.
2. **Generic Registry V3.** Specify a domain-neutral Molecule schema, capability model, metadata commitment, and migration boundary under a new code hash.
3. **Mainnet release.** Proceed only after audit, remediation, version policy, and release provenance are complete.
4. **Physical MLAT trial.** Secure at least four synchronized receivers and an independent reference before scheduling the evidence window.
5. **Additional SDK languages.** Extract or publish the Python adapter independently and consider Rust/Go clients only after the TypeScript interface is validated.
6. **Human-readable namespace.** Add a separate allocation mechanism only if globally unique labels become a proven requirement.
7. **Hardware attestation and reputation.** Treat physical truth, clock quality, and operator reputation as separate protocols rather than expanding Registry V2 implicitly.
8. **Production operations.** Add rate limiting, migrations, backup/restore tests, SLOs, and scalable storage only for a real service deployment.
9. **Frontend deployment.** Deploy the current Next.js reference separately if an operator console is still useful; it is not registry protocol work.
10. **Incentives and payments.** Defer until a real receiver network and economic model are demonstrated.

## 17. Reviewer Objections and How the Proposal Addresses Them

### 1. Is this actually useful to CKB?

**Objection:** This may be an aviation project asking CKB to fund a dashboard.

**Response:** The funded asset is a standalone CCC-based registry SDK, shared protocol tests, and testnet evidence. MLAT is only the existing reference consumer. No dashboard work is funded.

### 2. Is CKB essential?

**Objection:** Receiver metadata belongs in a database.

**Response:** A database is better for one trusted operator. This proposal is useful only where independent owners need owner-lock authorization, public discovery, transfer, and irreversible lifecycle history. The proposal states that boundary explicitly.

### 3. Is the work already finished?

**Objection:** The repository already has a contract and lifecycle evidence.

**Response:** Those components are the unfunded baseline. The missing deliverable is a released write-capable SDK using normal CKB signer tooling, plus three-language conformance and fresh SDK-produced evidence.

### 4. Does this duplicate CCC or `ckb-cli`?

**Objection:** Generic CKB SDKs already build transactions.

**Response:** The project layers Registry V2 record and lifecycle semantics on CCC. It does not replace signing, RPC, or general transaction construction. The deliverable is protocol-specific safety and reproducibility.

### 5. Is the scope realistic?

**Objection:** Contracts, SDKs, field trials, dashboards, and audits cannot fit five weeks.

**Response:** Only the TypeScript SDK, conformance expansion, testnet lifecycle, evidence, and docs are included. The contract is unchanged. Generic V3, audit, mainnet, MLAT field work, and frontend are excluded.

### 6. Can deliverables be independently verified?

**Objection:** Screenshots and an author's demo are weak proof.

**Response:** Acceptance uses test vectors, CI, signed transactions, RPC/indexer snapshots, checksums, explorer links, and an offline verifier. Video is secondary.

### 7. Is funding justified?

**Objection:** $1,000 may pay for packaging rather than meaningful engineering.

**Response:** The 50-hour breakdown centers on transaction correctness, signer integration, cross-language consensus behavior, and testnet evidence. Infrastructure is budgeted at $0. Completed backend/frontend work is not charged.

### 8. Does this look like infrastructure or merely a demo?

**Objection:** There is only one application and no adopter.

**Response:** The package is separated from MLAT, has a public API and language-neutral corpus, and can be verified without the UI. The proposal does not invent users or adoption. Lack of a third-party adopter remains a real limitation.

### 9. Can the team complete it?

**Objection:** This is a single-maintainer project.

**Response:** The repository already contains the contract, 132 passing Python tests, 15 passing Rust/CKB-VM tests, a signed lifecycle, and an evidence verifier. That is strong execution evidence. Single-maintainer and audit risks remain disclosed.

### 10. Are claims supported?

**Objection:** Synthetic aircraft output and testnet records may be presented as real infrastructure.

**Response:** The proposal makes no live MLAT, physical receiver, accuracy, production, mainnet, or audit claim. Testnet records prove lifecycle behavior only.

### 11. Is the project too broad?

**Objection:** The repository contains registry, MLAT, API, dashboard, and commercial code.

**Response:** The grant boundary is one package and one verification chain. Everything else is baseline or future work.

### 12. What would still make a reviewer reject it?

A fair reviewer may still reject the proposal if:

- the cleaned Registry V2 baseline is not public;
- the SDK API is not specified clearly enough to distinguish it from generic CCC;
- the committee does not see a real need for a receiver-specific registry without an external adopter;
- the proposal implies generic DePIN support despite the `mode-s` requirement;
- the application asks to fund work already in the repository;
- testnet evidence is presented as an audit or physical attestation.

The proposal below addresses each controllable rejection reason. It cannot manufacture external adoption, so it frames the milestone as a small, reusable, independently verifiable developer tool.

### Repository evidence map

Major current-state claims are traceable to:

- [Project README](../README.md)
- [Architecture](../ARCHITECTURE.md)
- [Domain context](../CONTEXT.md)
- [Project status](PROJECT_STATUS.md)
- [Repository audit](audit/REPOSITORY_AUDIT.md)
- [Registry contract](../contracts/registry-v2/src/entry.rs)
- [Registry record rules](../contracts/registry-v2/src/record.rs)
- [CKB-VM lifecycle tests](../contracts/registry-v2/tests/lifecycle.rs)
- [Python registry record](../src/ckb_registry/record.py)
- [Python discovery adapter](../src/ckb_registry/discovery.py)
- [Registry integration guide](registry/INTEGRATION.md)
- [Registry evidence bundle](../evidence/registry-v2-testnet-2026-07-30-final/README.md)
- [Evidence policy](../EVIDENCE.md)
- [MLAT reference status](../reference/mlat/README.md)
- [Physical trial runbook](reference/mlat/FIELD_TRIAL.md)
- [Benchmark limits](reference/mlat/BENCHMARKING.md)
- [Security review request](registry/SECURITY_REVIEW_REQUEST.md)
- [Roadmap](../ROADMAP.md)

External review references:

- [Accepted CKB Wallet Behaviour Intelligence proposal and committee history](https://talk.nervos.org/t/spark-program-ckb-wallet-behaviour-intelligence/10338)
- [Current Spark funding clarification](https://talk.nervos.org/t/spark-program-mini-grant-initiative/8752/4)
- [CCC transaction example pattern](https://docs.ckbccc.com/en/docs/code-examples)

---

## 18. FINAL SPARK GRANT PROPOSAL

# Project Name

CKB Receiver Registry Developer Kit

# Team

- **[@Jeremicarose](https://github.com/Jeremicarose)** - sole maintainer and developer responsible for Registry V2, its testnet evidence, and the MLAT reference implementation.

This is a single-developer project. No partner, auditor, or external adopter is claimed.

**Pre-submission condition:** The repository is MIT licensed. The exact Registry V2-first baseline commit must also be public before this proposal is posted. If reviewers cannot access that baseline, the proposal should not be submitted.

# Project Description

## Problem

CKB Registry V2 already demonstrates a receiver identity lifecycle using CKB cells. Each receiver lifecycle has a 32-byte Type-ID-derived identity, an owner lock, a schema-validated record, an exact sequence, and a permanent revocation tombstone. The repository has CKB-VM tests and a signed CKB testnet create/update/transfer/revoke lifecycle.

The remaining problem is developer usability and reuse.

Today, another CKB developer cannot install a project-specific SDK and use the complete lifecycle through a normal wallet interface. Discovery exists as a repository-internal, read-only Python adapter. Registration and state changes still require transaction templates, manual Type ID application, and external `ckb-cli` knowledge.

Generic CKB tools such as CCC and `ckb-cli` can build and sign transactions, but they do not know Registry V2's rules:

- sequence must begin at zero and increment by exactly one;
- the human Receiver Label cannot change;
- the 32-byte identity must follow CKB's Type ID creation rule;
- ownership transfer changes the successor cell's lock while preserving identity;
- revocation must leave a terminal tombstone;
- burn, duplicate output, and resurrection must fail.

The current 22-case shared corpus also misses an integer boundary mismatch: the Python mirror accepts `sequence` and `updated_at` above Rust's `u64` maximum. This can cause off-chain validation to approve a record the on-chain contract cannot accept.

This keeps Registry V2 as a strong one-repository prototype instead of reusable CKB infrastructure.

The concrete current user is the MLAT reference implementation in this repository. CKB developers building receiver-oriented physical infrastructure are target evaluators, not claimed existing partners or customers.

## Solution

The Spark milestone will deliver an open-source TypeScript developer kit for Registry V2, built on CCC.

The SDK will provide:

- canonical Registry V2 record types, encoding, decoding, and validation;
- Type ID calculation compatible with the Rust contract and Python implementation;
- paginated CKB indexer discovery with owner lock, outpoint, block, sequence, status, and metadata provenance;
- duplicate identity quarantine and explicit active/all-record filtering;
- CCC signer-driven create, update, ownership transfer, and revoke operations;
- a shared conformance corpus executed by Rust, Python, and TypeScript;
- a fresh SDK-produced CKB testnet lifecycle with an offline-verifiable evidence package.

The SDK will accept CCC's signer abstraction. It will not manage, accept, publish, or log raw private keys.

The grant does not fund the already-built contract, MLAT backend, API, dashboard, or historical lifecycle. It also excludes a generic Registry V3, mainnet deployment, contract audit, physical MLAT field trial, commercial features, and partner integration.

CKB is essential only for the shared multi-owner case. A traditional database remains the better solution for one trusted operator. CKB adds value when independent owners need public discovery, owner-lock authorization, transferable control, and a lifecycle that a central registry host cannot silently rewrite or delete.

CKB validates authorization and record transitions. It does not prove that receiver hardware exists, coordinates are true, clocks are synchronized, or streams are honest.

# Expected Deliverables

## 1. Open-Source Registry V2 TypeScript SDK

A versioned public package containing:

- TypeScript types and record codec;
- full Registry V2 validation;
- Type ID calculation;
- paginated indexer discovery;
- identity and lifecycle provenance;
- duplicate live identity quarantine;
- exact dependency lock, build, tests, and package archive.

The package will not depend on the MLAT runtime.

**Acceptance target:** A clean checkout can install, build, test, and pack the SDK.

## 2. CCC Lifecycle Transaction API

Signer-driven operations for:

- create at sequence 0 with a correctly derived Type ID;
- update at the next sequence;
- transfer to a new owner lock while preserving identity and label;
- revoke into a terminal tombstone with no stream fields.

**Acceptance target:** The same public SDK code completes all four operations on local/devnet CKB and one fresh lifecycle on CKB testnet. No raw private-key API is present.

## 3. Cross-Language Conformance Suite

Expand the current shared corpus from 22 to at least 40 named cases. The corpus will cover valid and invalid records, identity and Type ID vectors, `u64::MAX` and overflow boundaries, malformed data, exact sequence rules, label continuity, timestamp rollback, terminal revocation, pagination, duplicate labels, and duplicate live identities. The confirmed Python integer-boundary mismatch will be corrected.

**Acceptance target:** Rust, Python, and TypeScript produce the expected result for every shared case. The existing 5 host tests and 11 CKB-VM tests remain green.

## 4. Fresh CKB Testnet Lifecycle Evidence

An immutable evidence package containing:

- source commit and SDK version;
- Registry V2 deployment code hash;
- create, update, transfer, and revoke transaction hashes;
- signed transaction files without private keys;
- saved RPC responses and indexer discovery snapshots;
- sequence and owner-lock lineage;
- manifest and SHA-256 checksums;
- offline verification report;
- dated live RPC verification report.

**Acceptance target:** One new identity completes sequence `[0, 1, 2, 3]`, changes owner lock during transfer, ends as a revoked tombstone, and passes the offline verifier.

## 5. Documentation and Completion Report

Public documentation covering:

- installation and five-minute quickstart;
- CCC signer integration;
- discovery and lifecycle examples;
- API reference;
- Registry V2 lifecycle and trust boundaries;
- local/devnet reproduction;
- testnet explorer links;
- security limitations;
- a short demonstration video;
- a final report containing actual test counts, transaction hashes, conformance totals, verification results, deviations, and remaining risks.

**Acceptance target:** A reviewer can verify the milestone from a clean checkout without private maintainer guidance.

# How To Verify

## Repository and Package

Reviewers can:

1. Open the public repository and exact release tag.
2. Confirm the OSI-approved license.
3. Install the locked dependency graph.
4. Build and test the SDK.
5. Build the public package/archive and compare its checksum with the release.

The completion report will provide exact commands. They will be equivalent to:

```bash
npm ci
npm run build
npm test
npm run test:conformance
```

## Cross-Language Behavior

Reviewers can run:

```bash
python3 -m pytest -q tests/registry

cd contracts/registry-v2
make test
make check
```

The TypeScript test command will execute the same JSON conformance corpus. The report will state the number of cases and identify every supported implementation.

## Local Lifecycle

The repository will include one documented local/devnet lifecycle command or test. Reviewers can run it with public devnet accounts and confirm:

- sequence 0 creation;
- sequence 1 update;
- sequence 2 ownership transfer;
- sequence 3 revocation;
- stable Type ID and Receiver Label;
- changed owner lock at transfer;
- final tombstone state.

## CKB Testnet Lifecycle

For each accepted operation, reviewers can:

- open the transaction in the CKB testnet explorer;
- inspect the saved signed transaction;
- inspect the saved RPC response;
- confirm that each successor spends the prior Registry Cell;
- compare identity, label, sequence, status, and owner lock;
- run the evidence verifier offline;
- optionally re-query the public testnet RPC with `--live`.

The exact verifier command and bundle path will be published in the completion report.

## Evidence Integrity

The offline verifier will check:

- every declared artifact checksum;
- package and source binding;
- transaction commitment status from saved RPC responses;
- Type ID and code hash consistency;
- exact sequence lineage;
- immutable label and identity;
- owner-lock change;
- terminal revocation;
- discovery snapshots at every lifecycle stage;
- absence of private keys from the manifest and public artifacts.

Screenshots and video will support the walkthrough, but they will not be the primary acceptance evidence.

# Required Funding

## Developer Time

| Task | Hours | Rate | Cost |
|---|---:|---:|---:|
| TypeScript record and discovery SDK | 14 | $20/hour | $280 |
| CCC create/update/transfer/revoke API | 18 | $20/hour | $360 |
| Cross-language conformance and CI | 8 | $20/hour | $160 |
| Testnet lifecycle and evidence | 6 | $20/hour | $120 |
| Documentation, release, demo, and report | 4 | $20/hour | $80 |
| **Total** | **50** |  | **$1,000** |

## Infrastructure & Deployment Costs

| Item | Cost |
|---|---:|
| GitHub repository and Actions | $0 |
| Public package/archive publication | $0 |
| Public CKB testnet RPC/indexer/explorer | $0 |
| VPS, database, and domain | $0 |
| **Total infrastructure** | **$0** |

No hosted server is required for this milestone. Testnet tokens are not assigned a grant budget value.

## Total Grant Requested

**$1,000**

This request stays at Spark's normal single-category budget and funds only new developer-kit work.

# Estimated Completion Time

**Four weeks, 50 developer hours**

## Week 1

- Confirm the public baseline exposes the MIT License.
- Freeze SDK API and trust boundaries.
- Implement TypeScript record codec, validation, and Type ID compatibility.
- Execute the existing 22 shared cases in TypeScript.
- Correct the Python `u64` boundary mismatch.

**Output:** Installable SDK skeleton, locked dependencies, passing current corpus, aligned Rust/Python integer bounds.

**Verification artifact:** Public commit, CI run, package build, API design note.

## Week 2

- Implement paginated indexer discovery.
- Preserve owner lock, identity, outpoint, block, sequence, and metadata provenance.
- Add active/all filtering, malformed cell rejection, duplicate-label handling, and duplicate identity quarantine.
- Implement CCC create and update operations.

**Output:** Tested discovery client and first two signer-driven lifecycle operations.

**Verification artifact:** Multi-page fixtures, automated tests, testnet read example, local/devnet transactions.

## Week 3

- Implement CCC transfer and revoke operations.
- Validate records and successor transitions before signing.
- Execute a complete local/devnet lifecycle.
- Expand the shared corpus to at least 40 cases and run it in Rust, Python, and TypeScript.

**Output:** Four signer-driven lifecycle operations with no raw private-key API and three-language conformance.

**Verification artifact:** Integration test, transaction fixtures, and CI matrix.

## Week 4

- Execute a fresh SDK-produced Registry V2 lifecycle on CKB testnet.
- Capture transaction, RPC, and indexer evidence at each stage.
- Freeze the evidence manifest and checksums.
- Produce offline and dated live verification reports.
- Publish the tagged SDK package/archive.
- Complete quickstart, API reference, security limits, short demo, and completion report.

**Output:** Four committed testnet lifecycle transactions, a public release, and an independently verifiable evidence bundle.

**Verification artifact:** Explorer links, signed transaction files, saved chain responses, release tag, checksum, verifier output, video, and final report.

# Relevance to the CKB Ecosystem

## Meeting Actual Needs in the CKB Ecosystem

CKB provides flexible cells, scripts, locks, Type ID, RPC, and indexer infrastructure. Those primitives are powerful, but a developer still has to encode application-specific lifecycle rules and make them safe to use through normal wallet tooling.

Registry V2 is a concrete receiver-specific example. It shows how a physical infrastructure identity can:

- be created from a unique Type ID;
- carry current declared metadata in a live cell;
- remain controlled by the cell's owner lock;
- update through an exact ordered lifecycle;
- transfer to a new owner without changing identity;
- end in a permanent revocation tombstone;
- be discovered through the CKB indexer;
- retain transaction and owner provenance for independent inspection.

The current repository proves the contract behavior but does not package the complete lifecycle for another developer. The proposed SDK closes that gap.

Realistic beneficiaries are:

- CKB developers studying or building Type-ID lifecycle applications;
- receiver-oriented physical infrastructure prototypes that fit the V2 `mode-s` schema;
- the existing MLAT reference maintainer;
- CKB tools that choose to decode Registry V2 cells.

No third-party adoption, customer, or partner is claimed.

The result is reusable because the SDK, conformance corpus, and evidence verifier are separate from the MLAT solver, database, API, and dashboard.

## Utilizing CKB's Technical Architecture

Registry V2 uses CKB as the shared state and authorization layer rather than storing high-volume radio observations on chain.

- **Cell model:** the current Registry Cell represents the latest lifecycle state.
- **Owner lock:** spending the current cell authorizes update, transfer, or revoke.
- **Type script:** CKB-VM validates schema and lifecycle continuity.
- **Type ID:** the 32-byte type argument supplies a stable identity derived at creation.
- **Transaction history:** accepted transitions provide inspectable state lineage.
- **Indexer:** consumers enumerate records by the deployed Registry V2 code hash.
- **CCC:** the proposed SDK will integrate those rules with a maintained CKB signer and transaction abstraction.

This design keeps observations, MLAT computation, APIs, and dashboards off chain. CKB proves who authorized a valid registry transition. It does not prove physical existence, position, timing, or stream honesty.

For a single trusted receiver operator, a traditional database is simpler and should be preferred. CKB is useful when independent owners and consumers need a shared lifecycle without one central write authority.

# Future Work

The following items are explicitly outside this Spark milestone:

- independent contract audit and remediation;
- generic Molecule-based Registry V3 without the `mode-s` requirement;
- V2-to-V3 migration tooling;
- mainnet deployment;
- Python, Rust, or Go SDK releases beyond the current shared tests;
- physical synchronized four-receiver MLAT trial;
- live aircraft accuracy, coverage, throughput, or reliability claims;
- production storage, rate limiting, SLOs, backup, and recovery;
- current Next.js frontend deployment;
- incentives, payments, reputation, billing, or partner integrations.

These should be considered only after the V2 developer kit is released, independently verified, and used to evaluate whether the registry pattern has real demand beyond its first reference implementation.
