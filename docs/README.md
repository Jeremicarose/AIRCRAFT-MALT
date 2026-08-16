# Documentation Index

Root documents are authoritative for repository-wide concerns:

- `README.md`: project identity and verification entry point
- `ARCHITECTURE.md`: implemented topology and trust boundaries
- `CONTEXT.md`: domain vocabulary and invariants
- `DEPLOYMENT.md`: build and deployment procedures
- `REPRODUCIBILITY.md`: locked environments and evidence regeneration
- `EVIDENCE.md`: claim ledger
- `SECURITY.md`: disclosure and threat model
- `CONTRIBUTING.md`: contribution contract
- `ROADMAP.md`: incomplete work only
- `CHANGELOG.md`: implemented history
- `MAINTAINERS.md`: current review and release ownership
- `RELEASE.md`: tag, asset, checksum, SBOM, and attestation process
- `CODE_OF_CONDUCT.md`: participation and enforcement expectations

Domain documentation:

- `docs/registry/`: Registry V2 integration and external review scope
- `docs/reference/mlat/`: MLAT reference ingest, timing, solver, frontend,
  benchmark, and physical field-trial runbook
- `docs/adr/`: accepted architectural decisions
- `docs/audit/`: repository audit and cleanup ledger
- `docs/archive/`: archive policy; obsolete documents are not retained in-tree

When code and documentation conflict, code/tests/evidence define current behavior
and the document must be corrected.
