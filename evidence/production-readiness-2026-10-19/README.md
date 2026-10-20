# Local readiness evidence — 19 October 2026

This package records a working-tree audit based on `df82f6c`; it is **not a clean
release attestation**, independent security audit or live receiver campaign.
The full interpretation and gate decisions are in
[the audit](../../docs/production-readiness/audit.md).

- `commands.json`: exact validation arguments, directories, times, exit codes and
  durations, including failed attempts and intentionally failing regression tests.
- `starting-git-status.txt`, `starting-files.json`: pre-edit state and 736 hashes;
  credentials/environment files were excluded from hashing.
- `changes.json`, `current-source-files.json`: changed existing-file hashes and
  final source/document/test identities. Most of the broad Git diff predates this audit.
- `compact-report.json`: unchanged solver, synthetic control, published five-receiver
  event and all 362 historical outcomes, including 92 rejections.
- `load-envelope-report.json`, `process-soak-report.json`: explicitly synthetic local
  measurements, including the unsuccessful restart HTTP sample. Not an SLO or speedup claim.
- `conformance-report.json`: 57 protocol cases / 171 assertions across three languages.
- `saved-chain-report.json`, `live-chain-report.json`, `live-discovery.log`: offline
  and read-only public testnet checks. Zero transactions signed or broadcast.
- `browser-*-report.json`: test results plus the intentionally failing clean-worktree
  provenance condition. Final browser counts: 31 synthetic and 3 historical.
- `manual-browser-review.md`, `historical-rejection-confirmed.png`: limited local
  walkthrough and automation limitation, with direct-load rejection evidence.
- `restore-comparison.json`, backup/restore and installed-entrypoint logs: local
  integrity/provenance and startup/shutdown checks. No target infrastructure migration.
- Advisory reports/logs: fresh Python and npm results. Cargo audit is unavailable;
  no Rust advisory scan or local CodeQL result is implied.

Selected compact validation logs are retained here. Verbose browser/service logs,
temporary databases, isolated environments and generated benchmark bundles remain
in the clearly identified ignored directory `artifacts/readiness-2026-10-19/`.
Sentinel URLs/API keys printed in regression failures are invented test values,
not operational credentials. This package contains public chain identifiers and
synthetic/historical data; do not append private feeds, keys or raw operator logs.

Verify retained files from this directory with `shasum -a 256 -c checksums.sha256`.
Checksum validity establishes file integrity, not correctness of every claim.
Production and full external-release gates remain unpassed.
