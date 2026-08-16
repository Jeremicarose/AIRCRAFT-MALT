# Architecture

## Scope

The repository contains one primary product and one reference implementation:

1. **CKB Registry V2**: contract, Python record/discovery modules, lifecycle
   tools, tests, and signed testnet evidence.
2. **MLAT reference**: aviation ingest, correlation, localization, persistence,
   API, frontend, and benchmark tooling consuming Registry V2.

## Registry V2

```text
Owner lock authorization
        |
        v
CKB transaction -----> Registry V2 type script
                           |
                           +-- Type-ID creation rule
                           +-- exact group cardinality
                           +-- record schema validation
                           +-- sequence + label continuity
                           +-- terminal revocation
        |
        v
Live Registry Cell -----> CKB indexer
                              |
                              v
                    ckb_registry.discovery
                              |
                              v
                    consuming adapter/runtime
```

### On-Chain Contract

`contracts/registry-v2` is the authoritative contract implementation.

The type script validates:

- 32-byte type arguments and CKB Type-ID creation
- one create output or one input-to-output transition
- complete JSON consumption with unknown fields rejected
- record field bounds and status/capability vocabulary
- sequence zero on creation and exact `+1` successors
- immutable `receiver_id`
- non-decreasing `updated_at`
- permanent revocation

Ownership authorization remains the responsibility of the input lock. The
contract does not store keys or implement its own signatures.

### Python Registry Modules

`src/ckb_registry/record.py` mirrors the V2 record contract and provides
canonical JSON plus Type-ID calculation.

`src/ckb_registry/discovery.py` is a read-only adapter over CKB RPC/indexer
interfaces. It paginates live cells, extracts identity from type arguments,
validates records, preserves provenance, and quarantines duplicate identities.
It does not sign, broadcast, or simulate.

### Registry Tools

`tools/registry` contains transaction templates, Type-ID application, deployment
configuration, lifecycle execution, and evidence verification. Wallet capacity
balancing and signing still rely on `ckb-cli`; the repository does not vendor it.

## MLAT Reference

```text
Registry V2 discovery
        |
        v
Receiver network adapter <---- explicit replay adapter
        |
        v
JSONL / WebSocket / Beast ingest
        |
        v
Mode-S correlation -> clock qualification -> robust MLAT solve
        |
        v
SQLite WAL -> Flask API / Socket.IO -> Next.js operator frontend
        |
        v
bounded evidence and external-reference benchmark tools
```

### Backend Modules

- `mlat_reference.ingest`: Registry V2 consumer and feed adapters
- `mlat_reference.correlation`: transmission clustering and correlation quality
- `mlat_reference.solver`: the single retained robust MLAT solver
- `mlat_reference.database`: single-node SQLite persistence and access metadata
- `mlat_reference.runtime`: processor orchestration and operational telemetry
- `mlat_reference.api`: REST, readiness, evidence, and optional Socket.IO paths

The previous basic/enhanced solver implementations and demo orchestrator were
deleted. Tests exercise the same robust solver used by the runtime.

### Frontend

`reference/mlat/frontend` is the only retained frontend. It is a separately
built TypeScript/Next.js application. It provides overview, live-map, aircraft,
receiver, pipeline, metrics, environment, and settings routes against the Flask
API. The Flask API no longer serves or silently falls back to the deleted static
HTML application. The console is a reference operator surface, not part of the
Registry V2 protocol.

### Deployment Topology

Docker Compose runs three explicit services:

- processor: owns ingest, correlation, solve, and writes
- API: reads the shared SQLite database and exposes delivery interfaces
- frontend: server-renders and connects to the API

This topology is single-node only. SQLite is shared through a local volume; it
is not a horizontally scalable coordination mechanism.

The Render blueprint is a replay API/processor deployment. It does not build the
Next frontend and must not be presented as a complete hosted product.

## Evidence Architecture

`evidence/registry-v2-testnet-2026-07-30-final` is an immutable historical
package tied to source commit `61ab011` and a CI-built Ubuntu binary. Current
source moves do not rewrite that package.

`evidence/mlat-reference/reproducible-benchmark-v2` is deterministic synthetic
regression evidence. Experimental local performance and reliability captures are
kept separately so they cannot be mistaken for live accuracy evidence.

## Trust Boundaries

- CKB validates authorization and record transitions, not physical truth.
- Owner locks must be selected and operated securely by integrators.
- Stream endpoints and metadata are untrusted inputs to off-chain consumers.
- MLAT command adapters execute an operator-configured executable without a shell.
- API/admin credentials are deployment secrets and are never contract keys.
- Saved evidence is verified by hashes and semantic checks; it is not an audit.

## Known Architectural Constraints

- V2 is receiver- and Mode-S-specific despite the broader infrastructure goal.
- JSON parsing and floating-point coordinates increase contract cycles and schema
  complexity compared with a Molecule-native generic record.
- No independently maintained SDK or write adapter exists.
- Registry contract correctness has no independent audit.
- MLAT live operation depends on four or more physically synchronized receivers.
- The API/database module remains large and should be split only along tested
  domain interfaces, not into pass-through modules.

Architectural decisions are recorded in [docs/adr](docs/adr/).
