---
status: accepted
---

# Make Registry V2 the primary product and MLAT the reference implementation

The repository's strongest reusable deliverable is the CKB Registry V2
contract, record/discovery modules, lifecycle tools, and signed testnet evidence.
The aviation runtime consumes that registry and supplies a demanding validation
environment, but its ingest, solver, database, and frontend are not part of the
on-chain registry interface.

The repository therefore presents Registry V2 as the primary product and MLAT
as its flagship reference implementation and field-trial harness.

## Consequences

Registry code, tools, tests, evidence, documentation, and release gates remain
separate from the MLAT reference. Registry discovery cannot import replay data or
silently substitute simulated receivers.

The current V2 contract is still receiver-specific and requires `mode-s`.
General physical-infrastructure support needs a new contract version, code hash,
audit, deployment, and evidence package. Product positioning cannot erase this
implementation constraint.
