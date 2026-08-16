# Roadmap

This roadmap lists uncompleted work only. Dates and funding are intentionally not
promised.

## P0: Release Blockers

- Select and add an OSI-approved license with copyright-holder approval.
- Obtain an independent Registry V2 contract audit and publish the report.
- Decide whether V2 remains an aviation receiver registry or a new generalized
  contract will carry the physical-infrastructure product claim.
- Run and enforce the configured CodeQL, dependency-review, SBOM, and artifact
  attestation workflows on the protected default branch.
- Publish the first license-gated tagged release and verify its assets from a
  separate checkout.

Exit condition: external users can legally evaluate a reviewed, versioned release
without relying on undocumented maintainer knowledge.

## P1: Generic Registry Contract

- Specify a domain-neutral infrastructure record and capability model.
- Prefer a canonical binary schema suitable for deterministic on-chain parsing.
- Define migration from receiver-specific V2 without reinterpreting old cells.
- Add adversarial CKB-VM tests, cycle budgets, and compatibility vectors.
- Deploy under a new code hash and publish a new signed evidence package.
- Extract and publish a separately versioned read-only SDK.

Exit condition: a non-aviation integration can use the registry without a fake
`mode-s` capability or MLAT dependencies.

## P2: Field Validation

- Operate at least four receivers with a documented common-clock discipline.
- Capture integer-nanosecond observations and clock uncertainty metadata.
- Produce a bounded, hashed, independently inspectable live window.
- Align it with a trusted external reference source.
- Publish accuracy, freshness, reliability, and coverage without comparative
  superiority claims unsupported by data.

Exit condition: a third party can reproduce the published field result from the
saved inputs and tools.

## P3: Operational Hardening

- Replace SQLite where multi-node operation is required, or formally scope the
  product to a single node.
- Add rate limiting, structured migrations, backup/restore exercises, and SLOs.
- Pin container bases by digest and snapshot system build dependencies.
- Exercise signed releases, upgrade/rollback runbooks, and compatibility tests.
- Separate the large API/database modules along established domain interfaces
  after end-to-end tests cover those interfaces.

## Deferred

- Mainnet deployment
- Incentives, payments, reputation, and autonomous agents
- Commercial plan enforcement beyond the reference implementation

Deferred items are not part of the current product and must not appear in
completed-feature summaries.
