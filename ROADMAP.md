# Roadmap

This roadmap lists uncompleted work only. Dates and funding are intentionally not
promised.

## P0: Technical Release And Review

- Obtain an independent Registry V2 contract audit and publish the report.
- Run and enforce the configured CodeQL, dependency-review, SBOM, and artifact
  attestation workflows on the protected default branch.
- Produce a fresh create-update-transfer-revoke testnet lifecycle through the
  TypeScript SDK and an external signer. Bind it to one source commit.
- Publish the first tagged release and verify its assets from a
  separate checkout.

Exit condition: external users can legally evaluate a reviewed, versioned release
without relying on undocumented maintainer knowledge.

## P1: Pilot Product Surface

- Add browser, responsive, accessibility, and failure-state tests for that flow.
- Rehearse the participant task and evidence procedure with maintainer-owned
  identities before recruiting participants.

Exit condition: a receiver operator can complete the testnet workflow without
understanding CKB transaction assembly or giving the application a raw key.

## P2: Product Validation

- Recruit eligible receiver operators and network coordinators without claiming
  recruitment channels as partners.
- Run the precommitted operator/coordinator tasks and seven-day follow-up.
- Publish privacy-safe task outcomes, failures, interventions, and the
  continue/change/stop decision.
- Ask whether portability, cross-network identity, owner control, provenance,
  and lifecycle history add value beyond each participant's current network.

Exit condition: the project has evidence about demand and integration effort,
including a negative result if the published thresholds fail.

## P3: Optional Physical MLAT Validation

- Operate at least four receivers with a documented common-clock discipline.
- Capture integer-nanosecond observations and clock uncertainty metadata.
- Produce a bounded, hashed, independently inspectable live window.
- Align it with a trusted external reference source.
- Publish accuracy, freshness, reliability, and coverage without comparative
  superiority claims unsupported by data.

Exit condition: a third party can reproduce the published field result from the
saved inputs and tools.

## P4: Operational Hardening

- Replace SQLite where multi-node operation is required, or formally scope the
  product to a single node.
- Add rate limiting, structured migrations, backup/restore exercises, and SLOs.
- Pin container bases by digest and snapshot system build dependencies.
- Exercise signed releases, upgrade/rollback runbooks, and compatibility tests.
- Separate the large API/database modules along established domain interfaces
  after end-to-end tests cover those interfaces.

## Deferred

- Mainnet deployment
- A generic Registry V3 or non-aviation schema until receiver-market evidence
  justifies broadening the protocol
- Incentives, payments, reputation, and autonomous agents
- Commercial plan enforcement beyond the reference implementation

Deferred items are not part of the current product and must not appear in
completed-feature summaries.
