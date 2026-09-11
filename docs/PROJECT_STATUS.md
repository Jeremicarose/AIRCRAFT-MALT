# Project Status

Status date: 2026-09-11

`COMPLETE` means the repository implementation and its local verification are
complete. It does not mean independently audited, deployed to mainnet, or
validated by external users.

## Actual status matrix

| Area | Status | Evidence | Remaining |
|---|---|---|---|
| Registry V2 contract | COMPLETE | 5 Rust host tests and 11 CKB-VM lifecycle/attack tests; the candidate binary is deployed immutably on Pudge testnet | Obtain independent review of the exact deployed binary; mainnet is out of scope |
| Canonical identity path | COMPLETE | `receiver_identity` flows from type args through Python/TypeScript discovery, MLAT persistence/API, config, and UI types | External integrators must preserve the same field |
| V2 record and lifecycle validation | COMPLETE | Rust/Python/TypeScript enforce strict schema, exact sequence, terminal revoke, and `u64` bounds | No protocol change should occur without a new corpus/version review |
| Indexer discovery | COMPLETE | Cursor-exhaustive pagination, script binding, provenance, duplicate quarantine, and historical revoked filtering are tested in Python and TypeScript | Live RPC behavior remains an external service dependency |
| Cross-language corpus | COMPLETE | Corpus version 2 passes 171 Rust/Python/TypeScript assertions across 57 record, identity, Type ID, creation, transition, script, and discovery cases | Add vectors only when protocol scope changes |
| TypeScript SDK | COMPLETE | 70 tests cover codec, discovery, pagination, Type ID, history, immutable deployment binding and binary preflight, mutable-deployment write rejection, CCC-signer lifecycle assembly, the complete documented journey, and public package metadata | Claim the npm scope and approve the first protected release |
| Historical CKB testnet lifecycle | COMPLETE | Frozen 2026-07-30 create-update-transfer-revoke and seven rejected attacks pass the offline verifier | Evidence is historical and uses the older tooling |
| Fresh immutable testnet lifecycle | COMPLETE | The CKB CLI-signed `data1` deployment, create, update, transfer, revoke, seven rejected attacks, source-review linkage, and 100 live-chain checks are preserved without private keys | Clean CI provenance and independent review are still required for a stable release, but not for the factual testnet lifecycle claim |
| Browser/SDK-driven lifecycle | BLOCKED | The SDK and browser journey use the fresh immutable deployment and mutable deployments still fail closed | Connect a funded CCC testnet wallet and approve a new create-update-transfer-revoke rehearsal; no SDK-driven transaction is claimed yet |
| MLAT reference software | PARTIAL | Full 188-test repository Python suite passes; strict live gates and evidence verifier exist | Physical synchronized receiver run and independent reference data are absent |
| Operator frontend | PARTIAL | The shell starts with the Receiver Registry, places MLAT under a secondary reference group, preserves aircraft-receiver return context, and uses the SDK for discovery, export, history, and signer-based lifecycle actions; 13 unit tests, type checking, the production build, and 9 local browser checks pass | Repeat the browser checks on the current clean source, preserve the source-bound report, and complete a funded wallet-signed browser run |
| Review evidence bundle | PARTIAL | Source-bound generation and verification are implemented; earlier bundles were invalidated by later source fixes | Regenerate and verify the bundle after the final source commit |
| Pilot materials | PARTIAL | Browser workflow, readiness gate, owner/coordinator tasks, feedback form, evidence template, proposal, and recruitment research exist | Consent materials, a maintainer wallet rehearsal, recruitment, and observed sessions remain |
| Security/release baseline | PARTIAL | CodeQL, dependency review, SBOM, attestations, locked dependencies, MIT license, protected general release, and protected provenance-backed SDK release workflows exist | The npm organization and first package release need maintainer approval; workflows need a public green run; independent audit is absent; one low upstream npm advisory remains |
| Product demand | MISSING | No customer, partner, participant, revenue, or adoption evidence is claimed | Recruit and run the precommitted product-validation pilot |

## Verification on this tree

- `python3 -m pytest -q`: 188 passed.
- `python3 -m black --check src/ckb_registry src/mlat_reference tools tests`:
  passed.
- `python3 -m flake8 src tools tests`: passed.
- `make test && make check` in `contracts/registry-v2`: 5 host tests,
  11 CKB-VM tests, and the RISC-V contract check passed.
- `npm test && npm run build` in `sdk/typescript`: 70 tests and TypeScript
  compilation passed.
- `npm test` in the frontend: 13 precision, freshness, receiver-reference,
  standalone-asset, and browser-evidence contract tests passed.
- `npm run test:e2e:prepared` in the frontend defines 9 Registry, MLAT
  reference, investigation-flow, accessibility, responsive-layout, asset, and
  security-header checks. A complete clean run against the current source is
  still required before release.
- `python3 tools/registry/generate_registry_v2_conformance_report.py`: 57
  shared cases, 171 runtime assertions, and zero failures.
- `npm run typecheck` and `next build --webpack` in the frontend: passed and
  generated all 16 routes. Turbopack could not run in the restricted local
  environment because its CSS worker was denied permission to bind a helper
  port; the CI environment still uses the normal Next build.
- `python3 tools/check_documentation.py`: all checked Markdown links passed.
- `npm audit --audit-level=moderate`: both npm projects passed the configured
  threshold. The current upstream CKB dependency chain retains the low-severity
  `elliptic` advisory documented in `SECURITY.md`.
- `python3 -m pip check`: no broken Python requirements.
- `python3 tools/registry/verify_registry_v2_review_evidence.py --bundle
  evidence/registry-v2-review-2026-09-12-final`: 17 checks passed for its pinned
  source commit/tree, candidate binary hashes, conformance report, and external
  signer blocker. It predates the current frontend and immutable deployment
  defaults, so a replacement bundle is still required for this tree.
- The fresh `data1` lifecycle bundle verifies 48 checksummed files and passes
  100 chain, binary, lifecycle, rejection, discovery, API, live RPC, and
  indexer checks when CI provenance is explicitly excluded. Full release
  verification still fails on the missing local and GitHub CI records.
These are local results. Public CI results must be checked after the commits are
pushed.

## Claim boundaries

- The deployed V2 schema is receiver-specific and requires `mode-s`. It is not
  a general physical-infrastructure protocol.
- CKB proves the authorized record lifecycle. It does not prove that hardware,
  coordinates, streams, timing, or participant statements are truthful.
- The MLAT replay and deterministic benchmark are software evidence, not live
  receiver accuracy evidence.
- The testnet contract is unaudited. Nothing in this repository is an
  air-traffic-control or aviation-safety service.
- The TypeScript SDK is configured as a public package, but cannot be installed
  from npm until the maintainer claims the scope and approves its first release.

## External blockers

- A browser/SDK lifecycle needs a connected funded CCC wallet and explicit
  approvals from the current and recipient owners.
- The immutable deployment bundle needs clean CI provenance, a release-time live
  recheck, and independent review attesting the exact deployed binary hashes.
- The first npm release needs ownership of the `aircraft-malt` npm scope and a
  maintainer-approved `npm-release` environment run.
- A physical MLAT trial needs at least four receivers on qualified common clocks
  plus aligned independent aircraft reference data.
- Product validation needs consenting receiver operators and network
  coordinators. Recruitment channels are not partners.
- Security readiness needs an independent contract reviewer and remediation
  cycle.
- Release provenance needs a pushed tag so GitHub can execute the attestation
  workflow against the final commit.

Remaining work is ordered in [ROADMAP.md](../ROADMAP.md). No external result
should be marked complete until its evidence is committed or linked.
