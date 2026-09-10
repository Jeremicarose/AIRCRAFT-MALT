# Project Status

Status date: 2026-09-09

`COMPLETE` means the repository implementation and its local verification are
complete. It does not mean independently audited, deployed to mainnet, or
validated by external users.

## Actual status matrix

| Area | Status | Evidence | Remaining |
|---|---|---|---|
| Registry V2 contract | COMPLETE | 5 Rust host tests and 11 CKB-VM lifecycle/attack tests; current binary is an undeployed review candidate | Deploy and sign a fresh lifecycle after independent review; mainnet is out of scope |
| Canonical identity path | COMPLETE | `receiver_identity` flows from type args through Python/TypeScript discovery, MLAT persistence/API, config, and UI types | External integrators must preserve the same field |
| V2 record and lifecycle validation | COMPLETE | Rust/Python/TypeScript enforce strict schema, exact sequence, terminal revoke, and `u64` bounds | No protocol change should occur without a new corpus/version review |
| Indexer discovery | COMPLETE | Cursor-exhaustive pagination, script binding, provenance, duplicate quarantine, and historical revoked filtering are tested in Python and TypeScript | Live RPC behavior remains an external service dependency |
| Cross-language corpus | COMPLETE | Corpus version 2 passes 171 Rust/Python/TypeScript assertions across 57 record, identity, Type ID, creation, transition, script, and discovery cases | Add vectors only when protocol scope changes |
| TypeScript SDK | COMPLETE | 69 tests cover codec, discovery, pagination, Type ID, history, immutable deployment binding and binary preflight, mutable-deployment write rejection, CCC-signer lifecycle assembly, the complete documented journey, and public package metadata | Claim the npm scope and approve the first protected release |
| Historical CKB testnet lifecycle | COMPLETE | Frozen 2026-07-30 create-update-transfer-revoke and seven rejected attacks pass the offline verifier | Evidence is historical and uses the older tooling |
| Fresh SDK-driven lifecycle | BLOCKED | The SDK and browser journey are implemented; mutable code deployments fail closed | Requires independent review, an immutable `data1` Pudge deployment, funded wallets, and external signer approvals; no fresh transaction is claimed |
| MLAT reference software | PARTIAL | Full 161-test Python suite passes; strict live gates and evidence verifier exist | Physical synchronized receiver run and independent reference data are absent |
| Operator frontend | PARTIAL | The shell starts with the Receiver directory, preserves selected receiver context, keeps MLAT under a separate reference area, and uses the SDK for discovery, export, history, and signer-based lifecycle actions; focused tests, type check, and production build pass | Complete a funded wallet-signed browser run and add automated accessibility coverage |
| Review evidence bundle | COMPLETE | `evidence/registry-v2-review-2026-09-11-final` binds the current candidate to commit `e7cb2af9` and passes its offline verifier | Regenerate the bundle whenever reviewed source changes; a fresh deployment bundle still requires external signing |
| Pilot materials | PARTIAL | Browser workflow, readiness gate, owner/coordinator tasks, feedback form, evidence template, proposal, and recruitment research exist | Consent materials, a maintainer wallet rehearsal, recruitment, and observed sessions remain |
| Security/release baseline | PARTIAL | CodeQL, dependency review, SBOM, attestations, locked dependencies, MIT license, protected general release, and protected provenance-backed SDK release workflows exist | The npm organization and first package release need maintainer approval; workflows need a public green run; independent audit is absent; one low upstream npm advisory remains |
| Product demand | MISSING | No customer, partner, participant, revenue, or adoption evidence is claimed | Recruit and run the precommitted product-validation pilot |

## Verification on this tree

- `python3 -m pytest -q`: 161 passed.
- `python3 -m black --check src/ckb_registry src/mlat_reference tools tests`:
  77 files unchanged.
- `python3 -m flake8 src tools tests`: passed.
- `make test && make check` in `contracts/registry-v2`: 5 host tests,
  11 CKB-VM tests, and the RISC-V contract check passed.
- `npm test && npm run build` in `sdk/typescript`: 69 tests and TypeScript
  compilation passed.
- `npm test` in the frontend: 7 focused freshness, receiver-reference, and standalone-asset tests passed.
- `python3 tools/registry/generate_registry_v2_conformance_report.py`: 57
  shared cases, 171 runtime assertions, and zero failures.
- `npm run typecheck` and `next build --webpack` in the frontend: passed and
  generated all 16 routes. Turbopack could not run in the restricted local
  environment because its CSS worker was denied permission to bind a helper
  port; the CI environment still uses the normal Next build.
- `python3 tools/check_documentation.py`: 78 Markdown files passed.
- `npm audit --audit-level=moderate`: both npm projects passed the configured
  threshold. The current upstream CKB dependency chain retains the low-severity
  `elliptic` advisory documented in `SECURITY.md`.
- `python3 -m pip check`: no broken Python requirements.
- `python3 tools/registry/verify_registry_v2_review_evidence.py --bundle
  evidence/registry-v2-review-2026-09-11-final`: 17 checks passed, including the
  source commit/tree, candidate binary hashes, conformance report, and external
  signer blocker.
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

- A fresh SDK lifecycle needs an independently reviewed immutable `data1`
  deployment, real CKB testnet signer access, and testnet CKB.
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
