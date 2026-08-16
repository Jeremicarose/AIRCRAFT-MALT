# Changelog

This project follows a pre-release changelog until the first tagged release.

## Unreleased

### Changed

- Repositioned the repository around CKB Registry V2 as the primary deliverable.
- Isolated the MLAT system as the flagship reference implementation.
- Renamed the contract directory to `contracts/registry-v2`.
- Extracted reusable Python record/discovery code into `src/ckb_registry`.
- Namespaced MLAT backend code under `src/mlat_reference`.
- Split registry and MLAT tooling/tests into explicit directories.
- Made the Next.js application the single MLAT frontend.
- Removed Flask static frontend fallback and separated frontend deployment.
- Moved deterministic and experimental MLAT evidence under `evidence`.
- Replaced duplicated/stale documentation with an authoritative hierarchy.
- Added a frontend CI build and updated all workflows for the new layout.
- Removed build-time Google font downloads from the frontend.
- Changed command ingest to direct executable invocation instead of shell parsing.
- Changed Registry V2 discovery to fail explicitly rather than return simulation.
- Added strict four-receiver launch validation using exact live Registry V2
  identities, reachable Beast endpoints, bounded clock validity, and hashed
  per-receiver timing evidence.
- Added run-scoped raw observation capture and bridge reconnect behavior.
- Added an offline MLAT evidence verifier that checks bundle hashes, links
  positions to raw transmissions, and re-solves positions from saved arrival
  times and registry geometry.
- Added a physical field-trial runbook and exhaustive file-disposition ledger.
- Added commit-pinned CodeQL, dependency review, SPDX SBOM, and artifact
  attestation workflows plus a license-gated release workflow.
- Added explicit maintainer ownership, code ownership, conduct, and release
  policies.
- Added CI documentation-link verification and digest-pinned the frontend Node
  container base.
- Removed the Registry discovery write stub and fake executable example; writes
  remain explicit, externally signed transaction-tool operations.
- Upgraded the frontend to Next.js 16.3.0 and Node.js 22.23.1, resolving the
  PostCSS/Sharp advisory chain reported against the previous production graph.
- Fixed the environment route's Server/Client Component boundary so production
  prerendering no longer attempts to serialize Lucide component functions.
- Removed the redesigned layout's Google Fonts build dependency so a clean
  production build remains offline-capable.

### Removed

- Basic and enhanced legacy MLAT solvers
- Legacy 30-second demo orchestrator
- Static HTML/JavaScript frontend and vendored browser libraries
- Obsolete simulation examples and compatibility adapter
- Nginx configuration for the deleted static frontend
- Stale replay export and misleading `latest` simulation benchmark paths
- Old grant proposals, frontend plans, weekly reports, public updates, and
  conflicting root README copies

### Security

- Admin key comparison now uses constant-time comparison.
- API health output no longer exposes the database filesystem path.
- GitHub Actions retain least-privilege read permissions and immutable action
  pins.

## 0.1.0 - 2026-07-30

- Implemented Registry V2 identity/lifecycle enforcement.
- Published signed CKB testnet lifecycle and rejected-attack evidence.
- Added deterministic synthetic MLAT benchmark evidence and hash-locked CI.

This version label describes the historical development baseline; it was not a
formal packaged release.
