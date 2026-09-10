# Spark Program | CKB Receiver Registry SDK

> **Superseded draft:** Product-validation feedback showed that the next Spark
> application should test demand with receiver operators before packaging a
> developer SDK. The current review draft is
> [CKB Receiver Registry Operator Pilot](CKB_SPARK_PILOT_PROPOSAL.md). This file
> is retained to show the earlier technical direction. The workspace SDK it
> proposed was implemented on 2026-09-07 and is no longer a funding milestone.

## 1. Project name and summary

**Project name:** CKB Receiver Registry SDK

**One-line summary:** A TypeScript SDK built on CCC that lets developers discover, create, update, transfer, and revoke Registry V2 receiver identities through normal CKB signers, with the same lifecycle rules verified in Rust, Python, and TypeScript.

Registry V2 already exists as a tested CKB type script and has completed one signed lifecycle on CKB testnet. The Spark-funded scope is the missing developer integration layer: an installable SDK, cross-language conformance suite, fresh SDK-produced testnet lifecycle, and reproducible evidence package.

The MLAT dashboard, aircraft tracking pipeline, physical receiver deployment, live aviation data, and mainnet deployment are not part of this grant.

## 2. Team profile

**Applicant:** Jeremic_Arose

**GitHub:** [Jeremicarose](https://github.com/Jeremicarose)

**Role:** Solo developer and maintainer of Registry V2 and the MLAT reference implementation.

**Contact:** @Jeremic_Arose on Nervos Talk or @Jeremicarose through GitHub

**Repository:** [Jeremicarose/AIRCRAFT-MALT](https://github.com/Jeremicarose/AIRCRAFT-MALT)

**Public project discussion:** [MLAT Airspace Console - CKB-Based Receiver Registry for Aviation Data Infrastructure](https://talk.nervos.org/t/mlat-airspace-console-ckb-based-receiver-registry-for-aviation-data-infrastructure/10438)

**Relevant existing work:**

- Rust `no_std` Registry V2 type script for CKB-VM.
- Host and CKB-VM lifecycle tests.
- Python record validation and CKB indexer discovery.
- Manual `ckb-cli` lifecycle tooling.
- Signed CKB testnet create, update, transfer, and revoke evidence.
- MLAT reference application that consumes registry discovery off chain.
- MIT-licensed public codebase with contributor, security, release, and deployment documentation.

This is a solo application. No partner, external adopter, auditor, or production deployment is claimed.

## 3. Project background and problem statement

CKB has the primitives needed to represent infrastructure identity: cells hold state, lock scripts represent ownership, type scripts enforce transition rules, Type ID gives a stable identity, and the indexer makes live cells discoverable.

Registry V2 applies those primitives to Mode S aircraft receivers. A receiver record has a stable 32-byte Type-ID-derived identity, an owner lock, an immutable Receiver Label, an exact sequence number, declared metadata, and a permanent revocation tombstone.

The contract and one testnet lifecycle already work. The missing part is a normal developer interface.

Today, another developer must understand the repository's Python adapter, manually construct transaction templates, apply CKB's Type ID creation rule, and use external `ckb-cli` commands. Generic CKB libraries can build and sign transactions, but they do not know Registry V2's rules:

- creation must begin at sequence `0`;
- each update must increment the sequence by exactly one;
- Receiver Label and identity cannot change;
- transfer changes the owner lock without changing identity;
- revocation must produce a terminal tombstone;
- burn, duplicate output, and resurrection must fail.

There is also a confirmed compatibility gap. The Rust contract stores `sequence` and `updated_at` as `u64`, while the current Python validator accepts integers above `u64::MAX`. This means off-chain code can approve a value that the on-chain contract cannot decode.

The problem is therefore specific: **Registry V2 is a working CKB prototype, but it is not yet an installable, signer-compatible, independently reproducible developer tool.**

The current reference user is the MLAT application in this repository. Other CKB or physical-infrastructure developers are potential evaluators, not claimed existing users.

## 4. Solution approach

The project will ship `ckb-receiver-registry-sdk`, a TypeScript package built on CCC. TypeScript is the funded integration layer because CCC already provides maintained CKB transaction and signer primitives for browser and Node.js applications. The repository's current Python path supports discovery, but not signer-driven lifecycle transactions.

### Relationship to CKB-CCC

CKB-CCC provides the general machinery for connecting wallets, collecting cells, building transactions, calculating fees, signing, and submitting transactions. This project will use those capabilities rather than recreate them.

CCC does not define the Receiver Registry V2 protocol. The SDK adds the registry-specific record codec, lifecycle transition rules, Type ID identity handling, indexer discovery, provenance metadata, and duplicate-identity quarantine. It also provides a shared compatibility corpus so the TypeScript, Python, and Rust implementations can be checked against the same bytes and failure cases.

The funded asset is therefore not another generic CCC transaction wrapper. It is a reusable implementation of one concrete CKB cell protocol, with tests and on-chain evidence showing that independent implementations agree on its identity and lifecycle rules.

The SDK will provide:

- canonical Registry V2 types, encoding, decoding, and validation;
- Type ID calculation compatible with the existing Rust and Python implementations;
- paginated CKB indexer discovery with transaction and owner provenance;
- explicit active/all filtering and duplicate live-identity quarantine;
- CCC signer-driven create, update, ownership transfer, and revoke operations;
- one shared conformance corpus executed by Rust, Python, and TypeScript;
- one fresh end-to-end lifecycle on CKB testnet, created through the SDK;
- an offline-verifiable evidence bundle, documentation, and tagged release.

Four design choices keep the milestone narrow:

1. **CCC signer integration:** the SDK accepts CCC's signer abstraction. It does not accept, store, publish, or log raw private keys.
2. **Registry V2 only:** the grant packages the contract that already exists. It does not redesign the schema or fund a generic Registry V3.
3. **Cross-language rules:** shared JSON vectors prevent the Rust contract, Python consumer, and TypeScript SDK from silently disagreeing.
4. **Evidence before interface polish:** explorer links, transaction files, saved RPC responses, checksums, and automated verification are primary evidence. Screenshots are supporting material only.

## 5. Technical architecture

```text
Developer application
        |
        v
CKB Receiver Registry SDK (TypeScript)
  - record codec and validation
  - Type ID calculation
  - discovery and provenance
  - lifecycle transaction builders
        |
        +---- CCC signer ----> CKB transaction submission
        |
        +---- CKB indexer ---> live Registry V2 discovery
                                  |
                                  v
                         Registry V2 cell on CKB
                         - owner lock authorizes changes
                         - type script validates lifecycle
                         - Type ID remains stable
                                  |
                                  v
                         Off-chain consumers
                         - MLAT reference application
                         - independent registry tools
```

CKB stores identity, declared metadata, ownership, and lifecycle state. Receiver observations, aircraft positions, MLAT computation, databases, APIs, and dashboards remain off chain.

CKB proves that an owner authorized a contract-valid transition. It does not prove that a physical receiver exists, that its coordinates are true, that its clock is synchronized, or that its radio observations are honest.

## 6. Weekly execution plan

| Week | Focus | Concrete output | Verification artifact |
|---|---|---|---|
| 1 | TypeScript package foundation, record codec, validation, Type ID compatibility, and Python `u64` fix | Installable package skeleton; current 22 shared cases pass in TypeScript; Rust/Python integer bounds agree | Public commit, locked dependencies, CI run, package archive, boundary tests |
| 2 | Paginated discovery, provenance, filters, duplicate handling, and CCC create/update operations | Tested discovery client and first two signer-driven lifecycle operations | Multi-page fixtures, discovery tests, local/devnet create/update transactions |
| 3 | CCC transfer/revoke operations and expanded conformance corpus | Full local/devnet sequence `[0, 1, 2, 3]`; at least 40 shared cases pass in Rust, Python, and TypeScript | Integration test, transaction fixtures, three-language CI matrix |
| 4 | Fresh CKB testnet lifecycle, release, evidence, documentation, and final report | Tagged package release; four committed testnet transactions; reproducible evidence bundle and tutorial | Explorer links, signed transaction files, saved RPC/indexer responses, checksums, verifier report, short demo |

**Duration:** Four weeks, solo.

The schedule deliberately excludes frontend work, live MLAT deployment, partner integration, contract redesign, and mainnet release.

## 7. Funding requirements

**Total request: $1,000.**

| Work item | Hours / rate | Subtotal |
|---|---:|---:|
| TypeScript record, Type ID, and discovery SDK | 14h x $20/hour | $280 |
| CCC create, update, transfer, and revoke API | 18h x $20/hour | $360 |
| Shared conformance suite and CI | 8h x $20/hour | $160 |
| Testnet lifecycle and evidence package | 6h x $20/hour | $120 |
| Documentation, release, demo, and completion report | 4h x $20/hour | $80 |
| **Total developer time** | **50 hours** | **$1,000** |

Infrastructure cost is **$0**. The milestone uses the public GitHub repository, GitHub Actions, a public npm package with a matching GitHub release archive, and public CKB testnet RPC, indexer, and explorer services. It requires no VPS, paid database, or domain.

## 8. Deliverables and verification methods

| Deliverable | Acceptance condition | How a reviewer verifies it |
|---|---|---|
| Versioned TypeScript SDK | Public npm package and matching GitHub release archive; clean checkout installs, builds, tests, and packs | Install the published version; run the release's documented `npm ci`, build, test, conformance, and pack commands; compare the archive checksum with the release |
| CCC lifecycle API | Public SDK code creates, updates, transfers, and revokes a Registry V2 identity; no raw private-key API exists | Run the local/devnet integration test; inspect exported API and transaction fixtures |
| Cross-language conformance suite | At least 40 named cases produce the expected result in Rust, Python, and TypeScript; includes `u64::MAX` and overflow behavior | Run the three CI jobs or execute the documented Rust, Python, and TypeScript commands locally |
| Fresh CKB testnet lifecycle | One new identity follows sequence `[0, 1, 2, 3]`, changes owner during transfer, and ends as a revoked tombstone | Open the four explorer links; confirm each successor spends the previous cell; compare identity, label, sequence, status, and owner lock |
| Evidence package | Source commit, SDK version, transaction files, saved RPC/indexer responses, manifest, and checksums are complete and contain no private keys | Run the offline verifier; optionally repeat live RPC verification; compare every file against the manifest |
| Documentation and report | A third party can reproduce discovery and the lifecycle without maintainer guidance | Follow the quickstart from a clean checkout; review API reference, trust boundaries, test totals, transaction hashes, deviations, and remaining risks |

Expected verification commands will be published in the tagged release and will include equivalents of:

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

The completion report will provide the exact evidence bundle path and offline/live verifier commands. A demonstration video will help reviewers follow the process, but it will not replace source, tests, or on-chain evidence.

## 9. Current state versus funded scope

**Already shipped - not funded by this grant:**

- Registry V2 Rust contract.
- Contract record and lifecycle rules.
- Four Rust host tests and ten CKB-VM lifecycle tests.
- Python validation and read-only discovery adapter.
- Current 22-case shared conformance corpus.
- Manual `ckb-cli` lifecycle tooling.
- Existing signed CKB testnet create/update/transfer/revoke evidence.
- MLAT backend, database, API, dashboard, replay mode, and synthetic demo tooling.

**Funded by this grant:**

- Installable TypeScript Registry V2 SDK.
- CCC signer-driven lifecycle operations.
- Python `u64` boundary correction.
- At least 40 cross-language conformance cases.
- Fresh SDK-produced CKB testnet lifecycle.
- Tagged release, reproducible evidence, quickstart, API reference, demo, and completion report.

**Explicitly not funded:**

- work already listed as shipped;
- new MLAT or dashboard features;
- physical receiver deployment or synchronized field trial;
- claims about live aircraft accuracy, coverage, freshness, or reliability;
- Registry V3 or a generic schema redesign;
- mainnet deployment or security audit;
- payments, rewards, reputation, billing, and partner integrations.

## 10. CKB ecosystem alignment

This project demonstrates a concrete CKB pattern: a physical-infrastructure identity can be represented by a live cell, controlled by an owner lock, constrained by a type script, kept stable through Type ID, transferred between owners, revoked permanently, and discovered through the indexer.

The SDK makes that pattern usable through normal TypeScript and CCC tooling. The contract, SDK, shared test vectors, and evidence verifier are separate from the MLAT solver and dashboard. Developers can inspect them without running the aviation application.

Realistic beneficiaries are:

- CKB developers studying Type ID, owner-authorized cell lifecycles, and indexer discovery;
- Mode S receiver-network prototypes that need the Registry V2 schema;
- the existing MLAT reference implementation;
- CKB tools that choose to decode or inspect Registry V2 cells.

No broader adoption is assumed. Registry V2 remains receiver-specific.

A traditional database is simpler for one trusted operator and should be used in that case. CKB becomes useful when independent receiver owners and consumers need shared discovery, transferable control, and a lifecycle that one registry host cannot silently rewrite or delete.

## 11. Open-source commitment

The repository and all original Spark-funded deliverables will remain public
under the OSI-approved [MIT License](../LICENSE). Development will be visible in
the public repository during the grant, followed by a tagged release and a
matching public package archive at completion.

The public release will include the SDK source, Registry V2 contract source,
shared conformance corpus, tests, examples, evidence verifier, deployment and
reproduction instructions, API documentation, and completion report.

Private keys, seed phrases, wallet state, feed credentials, ignored local
databases, and unrelated deployment scratch files will not be published.
Third-party dependencies and tools retain their own licenses.

## 12. Post-grant maintenance

The release will document the supported Registry V2 contract code hash, CCC version, CKB network, package version, and known security limits. Compatibility changes will be recorded in the changelog.

For six months after completion, the maintainer will provide best-effort fixes for reproducible correctness bugs within the documented Registry V2 SDK scope. This is not an SLA and does not include new schemas, mainnet deployment, audit work, frontend work, or MLAT expansion.

Any larger Registry V3, multi-domain registry, or production hardening effort would require separate evidence of demand and separate funding.

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| CCC or CKB testnet APIs change during implementation | Transaction builders or testnet steps may need adjustment | Pin exact dependency versions, keep transaction logic behind a small adapter, and record supported versions in the release |
| Type ID depends on creation transaction input and output index | An output-order error can create the wrong identity | Use shared known-answer vectors and assert output position before signing |
| Rust, Python, and TypeScript validators disagree | Off-chain software may accept records rejected on chain | Run one shared corpus in all three implementations, including integer boundaries and malformed inputs |
| Public RPC/indexer is unavailable during review | Live verification may temporarily fail | Save RPC/indexer responses, transaction files, explorer links, and checksums so the bundle remains verifiable offline |
| Registry metadata is mistaken for proof of hardware truth | Users may over-trust coordinates or operational claims | Document that records are owner assertions; no physical-existence, location, timing, or signal-honesty claim is made |
| Contract is unaudited | Mainnet use could expose funds or identity state to unknown risks | Keep the milestone on testnet and label the contract experimental; mainnet remains audit-gated |
| Reviewed code is not visible in the public repository | Reviewers cannot inspect the promised baseline | Treat public baseline publication as a proposal-submission gate |

## 14. Out of scope

To keep evaluation clear, this grant does not cover a new contract, generic registry protocol, mainnet deployment, audit, hosted registry service, production SLA, current dashboard deployment, live aircraft feed, physical receiver trial, MLAT accuracy benchmark, wallet UI, payments, incentives, partner integrations, or commercial rollout.

Those items are deliberately deferred. The Spark milestone succeeds if an independent reviewer can install one SDK, execute the Registry V2 lifecycle through CCC, verify the same rules across three languages, and inspect a fresh lifecycle on CKB testnet.
