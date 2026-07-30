# Registry V2 CKB Testnet Verification Package

## Status

`PENDING SIGNATURE AND BROADCAST`

This package is complete only when all of the following are present:

- `manifest.json`
- the exact contract binary under `contract/`
- committed RPC responses for deployment, create, update, transfer, and revoke
- signed transaction files and node rejection responses for every attack
- indexer and application discovery snapshots for each accepted lifecycle state
- API responses
- local and GitHub CI results
- a passing verification report

Do not cite the package as testnet evidence while this status is pending.

## Source baseline

- Repository: `https://github.com/Jeremicarose/AIRCRAFT-MALT`
- Branch: `registry-v2-testnet-evidence`
- Contract source commit: `61ab011`
- Rust toolchain: `1.95.0`
- CKB network: testnet

## Pre-broadcast deployment values

These values come from the deterministic unsigned deployment transaction. They
must match the committed transaction and final manifest:

| Artifact | Value |
|---|---|
| Deployment transaction | `0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3` |
| Contract outpoint | deployment transaction output `0x0` |
| Binary SHA-256 | `688fdc5f755029fa3c93365663f0bd2d118d4bacb53340234a1cecb171ad4f77` |
| Binary CKB data hash | `0x9f5ae883bd5039b6eb3544c69a1597214c655bbccdb920e0fb7284c09d3cc645` |
| Registry `code_hash` (`hash_type: type`) | `0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c` |

The binary data hash and registry `code_hash` are intentionally different. The
first hashes the binary bytes. The second is the script hash of the Type ID
script on the deployed contract cell and is the value receiver cells use as
their type-script `code_hash`.

## Reproduce the contract tests

```bash
git checkout 61ab011
cd contracts/receiver-registry
rustup show
cargo fmt -- --check
make test
make check
```

The lifecycle suite executes real `secp256k1_blake160_sighash_all` lock scripts
inside CKB-VM. It does not use Always Success.

The canonical deployment binary is the exact Ubuntu artifact produced and
tested by GitHub Actions run `30506489518`. The macOS build is retained as
`contract/receiver-registry-local-darwin`; it is semantically test-equivalent
but not byte-reproducible because the current Rust/CKB build embeds
platform-specific paths and toolchain details. It is not deployed.

## Verify the completed package

Offline verification checks the saved chain responses, hashes, identity and
sequence lineage, ownership transfer, revocation, signed attack files, node
rejections, discovery snapshots, and API evidence:

```bash
python3 scripts/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final
```

Re-query every accepted transaction from the public RPC:

```bash
python3 scripts/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final \
  --live
```

## Rejected transactions

Rejected attack candidates cannot have committed on-chain transaction hashes.
For each one, the package publishes:

- the fully signed CKB CLI transaction file
- SHA-256 of that signed file
- submission timestamp
- node/CKB-VM rejection response
- expected rejection classification

An attack recorded as accepted makes the lifecycle runner fail immediately and
invalidates the evidence run.

## Independent review

See `docs/REGISTRY_V2_SECURITY_REVIEW_REQUEST.md`. A public request is not an
audit. Only a report by a named independent reviewer changes the review status.
