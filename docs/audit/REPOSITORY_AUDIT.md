# Repository Audit And Cleanup Ledger

Audit date: 2026-07-31; refreshed 2026-08-05

Scope: all tracked files; untracked frontend/source work; ignored databases,
deployment scratch, caches, compiler output, dependency trees, and nested
`ckb-cli` checkout; Git history and workflows; contract, Python, JavaScript,
tests, evidence, configuration, scripts, and documentation.

## Executive Summary

The repository contained two competing project identities:

- the historical root documentation described an MLAT aviation product and
  explicitly demoted CKB Registry V2 to supporting infrastructure;
- the newest implementation/evidence made Registry V2 the strongest standalone
  deliverable: a tested CKB contract, Python discovery adapter, lifecycle tools,
  and signed testnet verification package.

The implemented project today is **CKB Registry V2 with an MLAT reference
implementation**. That position is technically defensible only with an explicit
constraint: the current V2 record and contract remain aviation-specific and
require `mode-s`. A domain-neutral physical-infrastructure registry is future
work.

The cleanup removes duplicate solvers/frontends, stale product and grant copy,
old proposals, generated replay output, legacy adapters, and conflicting docs.
Production registry code, reference MLAT code, tools, tests, and evidence now
have separate locations.

Release readiness is blocked by the absence of a license and independent
contract audit. Grant readiness is materially improved by the signed testnet
package, but generic-infrastructure and live-field claims must remain limited.

## Actual Project

### Primary Product

Registry V2 currently consists of:

- `contracts/registry-v2`: `no_std` receiver lifecycle type script
- `src/ckb_registry`: canonical record/Type-ID helpers and read-only discovery
- `tools/registry`: deployment, lifecycle, and evidence tools
- `tests/registry`: off-chain contract-mirror and tooling tests
- `evidence/registry-v2-testnet-2026-07-30-final`: signed lifecycle package

### Supporting Components

- hash-locked Python packaging
- pinned Rust toolchain and Cargo lock
- contract security workflow
- repository CI and deterministic benchmark workflow
- Docker/Compose and replay Render configuration

### Reference Implementation

The MLAT reference includes explicit feed modes, timestamp qualification,
correlation, robust solving, SQLite, Flask APIs, and a Next.js operator frontend.

### Experimental Modules

- Beast clock calibration/configuration
- command and WebSocket live ingest
- physical MLAT field evidence capture
- local simulation performance/reliability artifacts
- plans/entitlements/usage metering in the MLAT API

### Current Maturity

- **Contract**: functional testnet prototype with strong automated lifecycle tests
- **Registry adapter**: usable read-only implementation, not a released SDK
- **Evidence**: unusually strong for a prototype, but self-produced and unaudited
- **MLAT reference**: integration-complete for replay; live field validation absent
- **Field-trial harness**: strict launch, raw-input capture, hashed timing
  evidence, and offline re-solving are implemented; no physical run is published
- **Operations**: single-node local/reference deployment, not production service
- **Community**: pre-release and unlicensed

## Audit Scores

Scores reflect the cleaned repository, not the pre-audit tree.

The exact path-by-path transition is maintained in
[File Disposition Ledger](FILE_DISPOSITION.md).

| Area | Score | Rationale |
|---|---:|---|
| Repository health | 82/100 | clear ownership/layout, locks/tests/evidence; ignored local state remains large |
| Documentation health | 91/100 | one authoritative hierarchy with explicit claim boundaries |
| Maintainability | 80/100 | duplicate implementations removed; API/database modules remain large |
| Reproducibility | 85/100 | locked graphs and deterministic evidence; cross-platform contract bytes differ |
| Security | 72/100 | good lifecycle tests/evidence and configured scans; no audit or rate limit, and new scans are not yet proven green |
| Ecosystem readiness | 62/100 | CKB-native evidence is strong; no license, released SDK, or generic schema |
| Grant readiness | 74/100 | signed testnet proof; independent review and field trial still missing |

## Repository Findings

### Critical Release Blockers

1. No `LICENSE` exists. The repository is not legally open source.
2. The stated physical-infrastructure identity exceeds the current schema: Rust
   and Python require `mode-s`, and record names are receiver-specific.
3. Registry V2 has no independent security audit.

### High-Priority Findings

1. No public synchronized four-receiver MLAT window exists. The strict harness
   and verifier are implemented, but replay or an unexecuted runbook is not an
   operational field trial result.
2. `ckb-cli` is an ignored 768 MB nested clone at commit
   `a3450f91aaebf97e98d517c8d9aad872dc21c9db` with a local modification in
   `ckb-signer/src/keystore/error.rs`; it is not reproducible project source.
3. Contract binaries are not byte-identical across Ubuntu and macOS builds.
4. The API/database implementations are 1,500+/1,200+ line modules with broad
   responsibilities and limited migration abstraction.
5. CodeQL, dependency review, SBOM, and release attestation workflows are now
   configured but have not yet produced public results for the reorganized tree.

### Medium-Priority Findings

1. The API uses a deployment-wide admin token and has no rate limiting.
2. TLS verification can be disabled by configuration.
3. Docker Compose shares SQLite through local bind mounts and cannot scale out.
4. The frontend image base is now digest-pinned; digest updates still require a
   reviewed build and frontend regression run.
5. The contract CI installs RISC-V GCC from mutable Ubuntu repositories.
6. The TypeScript frontend has no automated accessibility, responsive, or
   browser-level regression suite; the retained screenshots are desktop-only.
7. Render deploys only replay API/processor, not the reference frontend.

## Stale And Incorrect Content

Every item below was removed or replaced because it contradicted code, duplicated
an authority, described completed plans, or inflated maturity.

### Deleted Documentation

- `docs/DEPLOYMENT_GUIDE.md`: duplicated deployment instructions and referenced
  the deleted Flask/static frontend.
- `docs/GETTING_STARTED.md`: MLAT-first product identity and obsolete URLs.
- `docs/PROJECT_SUMMARY.md`: explicitly made Registry V2 supporting
  infrastructure rather than the product.
- `docs/PUBLIC_PROGRESS_UPDATE.md`: time-sensitive promotional copy and old
  `.html` routes.
- `docs/INTEGRATION_GUIDE.md`: duplicated MLAT integration material.
- `docs/BENCHMARK_DATA_FORMAT.md`, `docs/BENCHMARK_REPORT_TEMPLATE.md`, and
  `docs/READINESS_BENCHMARK.md`: overlapping benchmark explanations/templates.
- `docs/GRANT_DEMO_SCRIPT.md` and `docs/GRANT_EVIDENCE_RUNBOOK.md`: grant-specific
  presentation material mixed with operator documentation.
- `docs/REPRODUCIBILITY.md`: superseded by root `REPRODUCIBILITY.md`.
- `docs/informal-review-issue.md`: explicitly superseded duplicate.
- `docs/archive/project-history/**`: old grant proposals, audit proposals,
  frontend plan, social post, weekly status, and development logs; Git history
  preserves them without polluting current search.
- `docs/archive/root-history/**`: legacy README/product/“implementation complete”
  claims, including false production-ready language.
- `docs/project-history/SPARK_GRANT_PROPOSAL.md`: obsolete proposal, including V1
  future-work language conflicting with implemented V2.

### Updated Or Relocated Documentation

- `README.md`: rewritten from MLAT product page to Registry V2 entry point.
- `CONTEXT.md`: rewritten around Registry V2 domain language and constraints.
- `docs/CKB_INTEGRATION_GUIDE.md` -> `docs/registry/INTEGRATION.md`.
- `docs/REGISTRY_V2_SECURITY_REVIEW_REQUEST.md` ->
  `docs/registry/SECURITY_REVIEW_REQUEST.md`.
- `docs/MLAT_SOLVER_AND_TIMING.md` ->
  `docs/reference/mlat/SOLVER_AND_TIMING.md`.
- `docs/MULTI_RECEIVER_RUNTIME.md` -> `docs/reference/mlat/LIVE_INGEST.md`.
- `docs/READSB_BEAST_JSONL_MAPPING.md` ->
  `docs/reference/mlat/BEAST_TIMING.md`.
- `docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json` ->
  `reference/mlat/config/beast-receivers.example.json`.

## Technical Debt Removed

### Duplicate/Dead Python

- Registry discovery's throwing write stub and fake executable example: removed
  so the read-only adapter cannot imply it accepts private keys or registrations.
- `src/mlat/solver.py`: basic solver used only by legacy demo.
- `src/mlat/enhanced_solver.py`: separate simulation-only solver.
- `src/main.py`: second 30-second orchestrator, not production runtime.
- `src/network/neuron_client.py`: deprecated adapter that only raised an error.
- `examples/simple_demo.py` and `examples/simulation_demo.py`: legacy solvers and
  duplicate simulation logic.
- `examples/bridge.py`: weaker duplicate of `tools/mlat/bridge_adapter.py`.

### Duplicate Frontend

- `src/visualization/**`: static multi-page frontend, vendored Leaflet and
  Socket.IO, agent/payment placeholders, and compatibility routes.
- `nginx.conf`: served only the deleted static frontend.

The Next.js application under `reference/mlat/frontend` is authoritative. Flask
no longer serves static UI assets.

### Misleading Generated Output

- `benchmark/mlat.jsonl`: 4,466 replay rows with synthetic aircraft identifiers,
  zero quality, and no immutable evidence manifest.
- `benchmark/performance-latest.json` and `benchmark/reliability-latest.json`:
  moved and renamed as experimental local simulation measurements.
- downloaded CI checksum-only directories under the Registry evidence `ci/`
  folder: unreferenced duplicates not covered by the canonical manifest.

## Cleanup Classification

The categories below explain the decisions. The exhaustive transition for all
235 pre-audit tracked paths and all 283 final repository paths is in the
[File Disposition Ledger](FILE_DISPOSITION.md).

### SAFE TO DELETE (completed)

- `src/main.py`
- `src/mlat/solver.py`
- `src/mlat/enhanced_solver.py`
- `src/network/neuron_client.py`
- `src/visualization/**`
- `examples/**`
- `nginx.conf`
- `start.sh`
- `benchmark/mlat.jsonl`
- obsolete documentation listed above
- unmanifested duplicate CI checksum directories

### SAFE TO DELETE (local generated state, not executed)

- `.pytest_cache/**`
- `**/__pycache__/**` and `*.pyc`
- `contracts/registry-v2/target/**`
- `reference/mlat/frontend/.next/**`
- `reference/mlat/frontend/node_modules/**`
- test/debug SQLite files under `data/`

These are ignored and reproducible from source. They remain only as local
workspace state where useful.

### SAFE TO ARCHIVE OUTSIDE THE REPOSITORY

- `deploy/**` operator scratch, after confirming no unpublished key ceremony or
  deployment metadata is needed. The canonical V2 deployment files already
  exist in the signed evidence package.
- local SQLite databases if an operator needs private diagnostics. They have no
  manifests and do not qualify as public evidence.

### SAFE TO MOVE (completed)

- `contracts/receiver-registry` -> `contracts/registry-v2`
- registry record/discovery modules -> `src/ckb_registry`
- MLAT backend modules -> `src/mlat_reference`
- registry scripts -> `tools/registry`
- MLAT scripts -> `tools/mlat`
- registry tests -> `tests/registry`
- MLAT tests -> `tests/mlat`
- `frontend` -> `reference/mlat/frontend`
- benchmark fixtures -> `reference/mlat/benchmarks/fixtures`
- deterministic benchmark -> `evidence/mlat-reference/reproducible-benchmark-v1`

### UPDATE REQUIRED (completed)

- `.env.example`
- `.github/workflows/registry-v2.yml`
- `.github/workflows/reproducibility.yml`
- `Dockerfile`, `docker-compose.yml`, `render.yaml`, `render-entrypoint.sh`
- `run-demo.sh`, `run-live.sh`
- `pyproject.toml`
- all imports, subprocess paths, documentation links, and frontend identity copy

### KEEP

- `contracts/registry-v2/**` source, lock, toolchain, and tests
- `src/ckb_registry/**`
- `tools/registry/**`
- `tests/registry/**`
- `evidence/registry-v2-testnet-2026-07-30-final/**`
- `src/mlat_reference/**` as the flagship reference implementation
- `reference/mlat/**` excluding generated dependencies/build caches
- `tools/mlat/**`
- `tests/mlat/**`
- `evidence/mlat-reference/reproducible-benchmark-v1/**`
- hash-locked Python requirements and frontend/Cargo lockfiles
- root authoritative documentation and `docs/adr/**`

### NEEDS REVIEW

- `LICENSE`: copyright holder must select it; no technical default is safe.
- `ckb-cli/`: local modified upstream clone; preserve until the owner decides
  whether the modification matters, then delete and document a pinned install.
- `.env`: local secrets/configuration; never commit.
- `data/mlat_data.db` and `data/mlat_demo.db`: large local runtime state; delete or
  privately archive after owner confirmation.
- `deploy/**`: ignored deployment scratch with V1/V2/V3 and duplicate July 30
  attempts; canonical public evidence is already retained.
- generic schema direction: requires an ADR and new contract release.
- Render public URL: verify externally before publishing it as operational.

## Recommended Final Structure

This is the implemented target tree (generated/ignored state omitted):

```text
.
|-- .github/workflows/
|   |-- registry-v2.yml
|   |-- reproducibility.yml
|   |-- security.yml
|   `-- release.yml
|-- contracts/
|   `-- registry-v2/{src,tests,.cargo}
|-- src/
|   |-- ckb_registry/
|   `-- mlat_reference/{api,correlation,database,ingest,solver}
|-- tools/
|   |-- registry/
|   `-- mlat/
|-- tests/
|   |-- registry/
|   `-- mlat/
|-- reference/mlat/
|   |-- frontend/
|   |-- benchmarks/fixtures/
|   `-- config/
|-- evidence/
|   |-- registry-v2-testnet-2026-07-30-final/
|   `-- mlat-reference/{reproducible-benchmark-v1,experimental}
|-- docs/
|   |-- registry/
|   |-- reference/mlat/
|   |-- adr/
|   |-- audit/
|   `-- archive/README.md
|-- README.md
|-- ARCHITECTURE.md
|-- CONTEXT.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- REPRODUCIBILITY.md
|-- DEPLOYMENT.md
|-- EVIDENCE.md
|-- ROADMAP.md
|-- MAINTAINERS.md
|-- RELEASE.md
|-- CODE_OF_CONDUCT.md
`-- CHANGELOG.md
```

## Prioritized Implementation Roadmap

1. **License and governance**: select a license and publish supported-version
   commitments; maintainer, conduct, disclosure, and release policies now exist.
2. **Independent audit**: review contract and Python mirror; publish findings and
   remediation evidence.
3. **Resolve product/schema mismatch**: design a domain-neutral successor,
   preserve V2 evidence, deploy under a new code hash.
4. **Supply-chain release**: obtain green CodeQL/dependency/SBOM runs, digest-pin
   remaining containers, and exercise the signed tag workflow.
5. **Field evidence**: synchronized receivers, reference data, bounded hashed
   live package, and conservative published metrics.
6. **Operational hardening**: rate limits, migrations, backups/restores, SLOs,
   alerts, upgrade/rollback, and a scale decision.
7. **Module deepening**: split API/database responsibilities only after stable
   domain interfaces have end-to-end coverage.

See [ROADMAP.md](../../ROADMAP.md) for exit conditions.
