# Project Status

Status date: 2026-09-14

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
| Fresh immutable testnet lifecycle | COMPLETE | The CKB CLI-signed `data1` deployment, create, update, transfer, revoke, seven rejected attacks, source-review linkage, local CI, and 100 live-chain checks are preserved without private keys | GitHub CI provenance and independent review are still required for a stable release, but not for the factual testnet lifecycle claim |
| Browser/SDK-driven lifecycle | BLOCKED | The SDK and browser journey use the fresh immutable deployment and mutable deployments still fail closed | Connect a funded CCC testnet wallet and approve a new create-update-transfer-revoke rehearsal; no SDK-driven transaction is claimed yet |
| MLAT reference software | PARTIAL | Full 196-test repository Python suite passes; strict live gates and evidence verifier exist | Physical synchronized receiver run and independent reference data are absent |
| Operator frontend | PARTIAL | The shell starts on the Receiver Registry, places MLAT under a secondary reference group, preserves aircraft-receiver return context, and uses the SDK for Registry discovery, export, history, and signer-based lifecycle actions; 20 unit tests and type checking pass, and the Node 22 production build generates 17 routes | Run the current 12-test browser suite from a clean final commit in CI and complete a funded wallet-signed browser run |
| Review evidence for current source | PARTIAL | `evidence/registry-v2-review-2026-09-14-final` is a complete, passing bundle for commit `4fc8fce` and tree `3facd3f`, including 16 checks, 57 conformance cases, exact binary hashes, and 9 clean browser checks | Later frontend commits are outside that bundle; generate a new clean source-bound bundle, then add GitHub CI provenance and independent review |
| Pilot materials | PARTIAL | Browser workflow, readiness gate, owner/coordinator tasks, feedback form, evidence template, proposal, and recruitment research exist | Consent materials, a maintainer wallet rehearsal, recruitment, and observed sessions remain |
| Security/release baseline | PARTIAL | CodeQL, dependency review, SBOM, attestations, locked dependencies, MIT license, protected general release, and protected provenance-backed SDK release workflows exist | The npm organization and first package release need maintainer approval; workflows need a public green run; independent audit is absent; one low upstream npm advisory remains |
| Product demand | MISSING | No customer, partner, participant, revenue, or adoption evidence is claimed | Recruit and run the precommitted product-validation pilot |

## Verification on this tree

- `python3 -m pytest -q`: 196 passed.
- `python3 -m black --check src/ckb_registry src/mlat_reference tools tests`:
  passed.
- `python3 -m flake8 src tools tests`: passed.
- `make test && make check` in `contracts/registry-v2`: 5 host tests,
  11 CKB-VM tests, and the RISC-V contract check passed.
- `npm test && npm run build` in `sdk/typescript`: 70 tests and TypeScript
  compilation passed.
- `npm test` in the frontend: 20 API-error, fail-closed discovery, precision,
  freshness, map-configuration, receiver-reference, standalone-asset, and
  browser-evidence contract tests passed.
- `npm run test:e2e` from the clean Node 22 source commit `4fc8fce` passed all 9 Registry,
  MLAT reference, investigation-flow, accessibility, responsive-layout, asset,
  and security-header checks. The source-bound report records commit `4fc8fce`,
  tree `3facd3f`, a clean worktree, and zero serious or critical accessibility
  findings.
- `python3 tools/registry/generate_registry_v2_conformance_report.py`: 57
  shared cases, 171 runtime assertions, and zero failures.
- `npm run typecheck` and `next build --webpack` in the current frontend passed
  under Node 22 and generated all 17 routes. The current suite enumerates 12
  browser checks, but no passing clean source-bound report is claimed for them.
- `python3 tools/check_documentation.py`: all checked Markdown links passed.
- `npm audit --audit-level=moderate` passed for both npm projects; the known
  low-severity `elliptic` advisory remains documented in `SECURITY.md`.
- `python3 -m pip check`: no broken Python requirements.
- `python3 tools/registry/verify_registry_v2_review_evidence.py --bundle
  evidence/registry-v2-review-2026-09-14-final`: 87 verification checks across
  21 bundled files passed for commit `4fc8fce` and tree `3facd3f`, including the
  clean browser report and exact deployed binary hashes.
- The fresh `data1` lifecycle bundle verifies 50 checksummed files, a passing
  local CI rebuild, and 100 chain, binary, lifecycle, rejection, discovery, API,
  live RPC, and indexer checks. Full release verification now fails only on the
  missing GitHub CI record.
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
- The immutable deployment bundle needs GitHub CI provenance, a release-time live
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
