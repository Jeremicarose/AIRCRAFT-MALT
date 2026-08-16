# Project Status

Status date: 2026-08-05

## Completed

- Registry V2 lifecycle semantics are implemented in a `no_std` Rust contract.
- Type-ID identity creation, update continuity, owner-lock transfer, and terminal
  revocation have CKB-VM transaction coverage.
- Python record encoding, validation, Type-ID calculation, and indexer discovery
  are implemented.
- Registry deployment/lifecycle/evidence tools are implemented.
- A signed create-update-transfer-revoke lifecycle was committed on CKB testnet.
- Seven signed attack transactions were rejected and retained with node errors.
- Deterministic synthetic MLAT benchmark generation is implemented.
- Strict physical-trial preflight, per-receiver clock evidence validation,
  run-scoped raw observation capture, and offline position re-solving are
  implemented.

## Implemented

- **Contract**: functional receiver-specific Registry V2 binary.
- **Discovery**: read-only paginated RPC/indexer adapter with provenance and
  duplicate-identity quarantine.
- **Tooling**: record generation, transaction templates, deployment config,
  lifecycle execution, and evidence verification.
- **MLAT reference backend**: explicit replay/live modes, JSONL and WebSocket
  ingest, Beast adapters, correlation, robust solving, SQLite persistence,
  readiness/evidence APIs, access tiers, and optional Socket.IO updates.
- **MLAT reference frontend**: Next.js operator interface covering overview,
  localization, aircraft, receivers, pipeline, metrics, and environment.
- **Infrastructure**: hash-locked Python dependencies, npm lock, Cargo lock,
  contract and repository CI, Docker images, Compose, and a replay Render
  blueprint.
- **Release tooling**: commit-pinned CodeQL and dependency review, SPDX SBOM
  generation, artifact attestations, a license-gated tag workflow, maintainers,
  code ownership, conduct rules, and a release checklist.

Implemented does not mean independently audited, horizontally scalable, or
field-proven.

## Verified

- 4 host-side Rust record tests pass.
- 10 CKB-VM transaction/lifecycle tests pass.
- 122 Python tests pass under the hash-locked development graph, including the
  Socket.IO realtime API path.
- The Next.js 16.3.0 production build passes under Node.js 22.23.1 without
  network font downloads.
- The locked production frontend graph reports zero npm audit vulnerabilities
  as checked on 2026-08-05.
- Offline verification of the signed Registry V2 evidence package passes.
- The deterministic MLAT benchmark bundle passes its checksum and claim-scope
  verifier.
- Operational evidence tests verify that stored positions link to the same raw
  Mode-S transmission and can be recalculated from bundled receiver geometry
  and integer arrival timestamps.

The testnet evidence recorded a passing live RPC verification on 2026-07-30.
That is historical evidence, not a continuous monitoring claim.

## Reproducible

- Python production and development graphs are hash-locked for Python 3.12.11.
- Rust dependencies and toolchain are pinned.
- The synthetic MLAT regression bundle is byte-identical across repeated runs
  in the same defined environment.
- GitHub Actions are pinned to full commit SHAs and use read-only repository
  permissions.
- The deployed Registry V2 binary is retained with SHA-256 and CKB data hash.

Not fully reproducible:

- Contract binaries differ across host platforms because the current build can
  embed host-specific paths/toolchain details. The deployed Ubuntu CI artifact
  is canonical; the macOS binary is evidence only.
- The frontend container base image is digest-pinned. Updating it still requires
  a reviewed build and frontend regression run.
- Ubuntu package installation for the RISC-V GCC toolchain is not snapshot-pinned.

## Operational

- The recorded Registry V2 deployment and lifecycle transactions exist on CKB
  testnet.
- The local replay stack can run processor, API, and frontend workflows.
- Strict live startup fails closed when configured live prerequisites are absent.
- A read-only testnet discovery query on 2026-08-04 returned zero active
  receiver identities under the deployed Registry V2 code hash. This is a
  dated observation, not continuous monitoring.

Not operationally established:

- no maintained production deployment or SLO
- no public synchronized multi-receiver MLAT window
- no disaster-recovery exercise
- no horizontal scale test
- no release, upgrade, or rollback procedure exercised against users

## Experimental

- Physical live MLAT ingest
- Physical execution of the multi-receiver Beast and clock-evidence harness
- External OpenSky accuracy comparison
- Local simulation performance and 2-second reliability captures
- API plans, entitlements, and usage metering as product packaging
- Physical operator validation of the MLAT frontend beyond local replay

## Not Started

- General physical-infrastructure schema without the `mode-s` requirement
- Independently versioned Python SDK distribution
- Generic write/signing library
- Mainnet deployment
- Independent contract audit
- First tagged release and independently verified SBOM/provenance artifacts
- Compatibility policy and semantic versioning guarantees

## Blocked

- **Open-source release**: the copyright holder has not selected a license.
- **Generic infrastructure claim**: the deployed V2 schema is receiver-specific
  and requires `mode-s`; changing it requires a new contract version/deployment.
- **Live MLAT evidence**: software capture and verification are implemented;
  execution still requires at least four active Registry V2 receivers on a
  qualified common clock plus an aligned trusted reference dataset.
- **Security readiness**: requires an independent audit and remediation cycle.

## Future Work

Future work is ordered in [ROADMAP.md](../ROADMAP.md). No roadmap item should be
described as complete until code, tests, and evidence are merged.
