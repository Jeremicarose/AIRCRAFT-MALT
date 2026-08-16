# Evidence

## Evidence Policy

Evidence is retained only when it supports a bounded, reproducible, or
independently verifiable claim. Filenames such as `latest` do not make a local
capture authoritative.

Evidence does not replace an independent security audit or prove physical-world
metadata.

## Registry V2 Testnet Package

Path: `evidence/registry-v2-testnet-2026-07-30-final`

Status: complete historical package; offline and recorded live verification pass.

It contains:

- canonical Ubuntu CI contract binary and local macOS comparison binary
- deployment, create, update, transfer, and revoke RPC responses
- signed accepted transactions
- seven signed rejected attack transactions and node responses
- indexer and application discovery snapshots
- API responses
- local and GitHub CI metadata
- manifest, checksums, and offline/live verification reports

Supported claims:

- one Registry V2 binary was deployed to CKB testnet
- one identity completed the accepted lifecycle in order
- owner lock changed during the transfer
- the revocation tombstone is the final accepted state
- the captured attack transactions were signed and rejected with the recorded
  contract errors

Unsupported claims:

- independent audit or formal verification
- mainnet readiness
- truthful receiver location, custody, timing, or stream data
- generic non-aviation schema support
- continuous availability of public RPC providers

Verify offline:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final
```

## MLAT Deterministic Package

Path: `evidence/mlat-reference/reproducible-benchmark-v2`

Status: byte-reproducible synthetic regression evidence.

The previous `reproducible-benchmark-v1` package remains unchanged as
historical evidence from the earlier dependency lock set.

Supported claims:

- the benchmark tool performs deterministic one-to-one timestamp matching
- generated JSON and checksums are stable for the saved fixtures/source
- evidence labeling prevents the fixture from being marked live/publishable

Unsupported claims:

- live receiver accuracy
- actual airspace coverage
- comparison with OpenSky or another incumbent
- clock synchronization performance

## Experimental MLAT Evidence

Path: `evidence/mlat-reference/experimental`

The performance baseline was captured on a dirty macOS worktree using simulation.
The reliability file contains three samples over about two seconds. Both are
retained as historical local measurements, not release benchmarks.

They must not be surfaced as current operational or grant evidence.

## MLAT UI Review

Path: `evidence/mlat-reference/ui-review-2026-08-05`

Status: validation-only desktop screenshot package captured from a dirty
worktree before the TypeScript redesign was committed. The package records route
rendering and visible state only. It does not establish live operation, solver
accuracy, accessibility conformance, responsive behavior, or backend data
integrity. Its manifest and checksum file make the capture reviewable without
expanding its claim scope.

## Missing Evidence

- independent Registry V2 audit report
- generalized physical-infrastructure integration
- synchronized physical four-receiver MLAT input
- aligned trusted reference dataset
- statistically useful live reliability window
- disaster recovery and rollback exercise
- mainnet deployment
- signed release/SBOM/provenance attestations

## Adding Evidence

New evidence must include:

- immutable input files or public transaction identifiers
- source commit and dirty-worktree status
- toolchain/dependency versions
- exact commands
- hashes for all artifacts
- explicit claim scope and limitations
- a verifier that fails closed on provenance mismatch

For a physical MLAT trial, use `tools/mlat/capture_grant_evidence.py`. Its V2
bundle additionally pins the strict preflight, exact receiver config,
per-receiver clock qualification artifacts, raw Beast-derived observations,
live registry/API snapshots, solver output, reference data, and reliability
measurements. `tools/mlat/verify_live_evidence.py` verifies all hashes and
re-solves every exported position from the raw arrival times and captured
receiver geometry.

Never rewrite a historical evidence directory. Publish a new dated/versioned
directory and link it from this document.
