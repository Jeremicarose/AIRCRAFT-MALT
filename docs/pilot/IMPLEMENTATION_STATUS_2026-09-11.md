# Pilot Readiness Implementation Status

This document records what the repository now automates for the pilot-readiness
recommendation. It does not claim that an external pilot participant or
physical receiver hardware exists.

## Implemented

- `.env.example` now pins the verified immutable Pudge `data1` deployment,
  labels it testnet-only and unaudited, and disables mutable code by default.
- `tools/registry/verify_data1_deployment.py` verifies a supplied deployment
  outpoint is live and that its cell data hashes to the supplied data1 code
  hash. It can also compare a local contract binary and writes JSON evidence.
- `tools/registry/check_registry_indexer_health.py` compares bounded,
  cursor-paginated indexer results with direct RPC, reports indexer lag and
  stale results, rejects malformed cursors, and fails closed on duplicate
  canonical identities.
- `.github/workflows/pilot-readiness.yml` provides a manual clean-clone
  evidence run. Optional deployment and receiver inputs add the two live
  checks without putting keys in CI.
- `docs/pilot/READINESS_GATE.md` documents the operator sequence and the exact
  commands required for deployment verification, indexer monitoring, live
  preflight, and reproducible evidence.
- The source-bound evidence generator includes these readiness scripts, tests,
  configuration, workflow, and runbook in its review manifest.
- Environment documentation scanning now ignores generated build trees and the
  CI-only `GITHUB_REF_NAME` metadata is documented.

## Verified In This Worktree

| Check | Result |
|---|---|
| Python backend, Registry, MLAT, and readiness tests | 194 passed |
| Rust Registry unit/lifecycle tests | 16 passed |
| Rust RISC-V target check | passed |
| TypeScript SDK build and tests | 70 passed |
| Frontend typecheck | passed |
| Frontend production build | passed |
| Frontend unit and evidence-contract tests on the required Node 22 runtime | 13 passed |
| Registry, MLAT reference, investigation, accessibility, mobile, asset, and header browser checks | 9 checks implemented; no retained clean passing report certifies the current source |
| Documentation and environment checks | passed |

The fresh `data1` bundle records a funded deployment and complete signed
lifecycle. It verifies 48 checksummed files and passes 100 chain and semantic
checks, including a fresh public-RPC query, when CI provenance is explicitly
excluded. Full release evidence verification remains blocked on missing
local/GitHub CI records.

The locally built current contract binary was also fingerprinted:

```text
sha256:       087a8b19ca99170d8d1e8c018b749259ce067ad3cb1cc8cef3b4a490ccae0465
CKB data1:    0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa
```

Those hashes identify both the source-bound build and the binary recorded
in the immutable testnet deployment bundle.

## Not Verified

- The immutable deployment and signed lifecycle are recorded, but their bundle
  still needs clean local/GitHub CI provenance and an independent review tied to
  the deployed binary hashes.
- No real create/update/transfer/revoke browser lifecycle was performed in
  this environment because no wallet was connected. The fresh CKB CLI-signed
  lifecycle is labeled separately and is not presented as browser or SDK proof.
- The fresh real-indexer report passes exhaustive exact and prefix pagination
  for the evidence identity. The monitor remains required because a third-party
  indexer can lag or regress after that capture.
- Four synchronized physical receiver feeds and strict live MLAT preflight
  were not available. Demo or replay data cannot satisfy that gate.
- The clean-clone workflow must be run from a committed clean revision. The
  current worktree contains unrelated in-progress changes, so no clean-clone
  result is claimed from this local directory.

## External Completion Sequence

1. Commit the source and publish clean local/GitHub CI provenance for the
   existing immutable lifecycle bundle.
2. Obtain independent review of the exact deployed binary hashes.
3. Configure all three frontend deployment variables from that verified
   outpoint, connect a testnet wallet, and preserve the transaction hashes for
   create, update, transfer, and revoke.
4. Run the indexer health monitor after each lifecycle transition. Stop when
   it reports `indexer_lag`, `stale_indexer`, or an unavailable/malformed
   response; do not treat an empty directory as success.
5. Configure four real receiver sources and clock evidence, then require
   `check_live_ingest_readiness.py --require-ready` to pass before claiming
   Registry-to-MLAT live behavior.
6. Run the `Pilot Readiness Evidence` workflow from the resulting clean commit
   and publish its artifact with the transaction hashes, canonical identities,
   status, sequence, owners, and timestamps.
