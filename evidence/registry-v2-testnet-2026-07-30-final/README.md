# Registry V2 CKB Testnet Verification Package

## Status

`COMPLETE - OFFLINE AND LIVE VERIFICATION PASS`

The package contains all of the following:

- `manifest.json`
- the exact contract binary under `contract/`
- committed RPC responses for deployment, create, update, transfer, and revoke
- signed transaction files and node rejection responses for every attack
- indexer and application discovery snapshots for each accepted lifecycle state
- API responses
- local and GitHub CI results
- a passing verification report

The machine-readable source of truth is `manifest.json`. Both
`verification-offline.json` and `verification-live.json` report `pass: true`.

## Source baseline

- Repository: `https://github.com/Jeremicarose/AIRCRAFT-MALT`
- Branch: `registry-v2-testnet-evidence`
- Contract source commit: `61ab011`
- Rust toolchain: `1.95.0`
- CKB network: testnet

## Deployment values

These values match the committed deployment transaction and final manifest:

| Artifact | Value |
|---|---|
| Deployment transaction | `0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3` |
| Contract outpoint | deployment transaction output `0x0` |
| Binary SHA-256 | `688fdc5f755029fa3c93365663f0bd2d118d4bacb53340234a1cecb171ad4f77` |
| Binary CKB data hash | `0x9f5ae883bd5039b6eb3544c69a1597214c655bbccdb920e0fb7284c09d3cc645` |
| Registry `code_hash` (`hash_type: type`) | `0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c` |

## Accepted lifecycle

| Stage | Transaction |
|---|---|
| Deploy | [`0x070820e9...c3b3`](https://testnet.explorer.nervos.org/transaction/0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3) |
| Create, sequence 0 | [`0xd25414d6...448d`](https://testnet.explorer.nervos.org/transaction/0xd25414d6f1d1232320a5451157812ba75e299e5e28116db59d3ecb4f008a448d) |
| Update, sequence 1 | [`0x160c5c87...5c35`](https://testnet.explorer.nervos.org/transaction/0x160c5c87d3c5339769d81f6f1a79ed02a4e9067ee57673fed4e2613951425c35) |
| Transfer, sequence 2 | [`0xbdf310c4...8c69`](https://testnet.explorer.nervos.org/transaction/0xbdf310c482c71261b3c254594a034959864b7d3267fda2f8330054bc13a18c69) |
| Revoke, sequence 3 | [`0xc6c6b36d...86a6`](https://testnet.explorer.nervos.org/transaction/0xc6c6b36d813d809644009766a75bd97d4a8f649113fab2f881c3a2373fa586a6) |

- Receiver Identity: `0xcca658ee811707def01d466b16b9b3ee133c3f6952388c78a5f90a5c273749e8`
- Receiver Label: `RECV_REGISTRY_V2_EVIDENCE`
- Initial owner lock arg: `0xeb30e40fe89ea2a602dae6fe88505f6e8ecf7fb1`
- Transferred owner lock arg: `0x0c59f15938213d77d8a41353d73dbb5296b611a6`

## Rejected signed attacks

| Attack | Contract error | Evidence |
|---|---:|---|
| Forged identity creation | `-4` | `responses/attack-forged-identity.json` |
| Sequence jump | `-25` | `responses/attack-sequence-jump.json` |
| Receiver Label mutation | `-27` | `responses/attack-label-mutation.json` |
| Duplicate identity outputs | `-4` | `responses/attack-duplicate-output.json` |
| Identity burn | `-5` | `responses/attack-burn.json` |
| Revocation resurrection | `-28` | `responses/attack-resurrection.json` |
| Tombstone burn | `-5` | `responses/attack-tombstone-burn.json` |

Every corresponding file under `transactions/` contains a secp256k1 signature.
The response file records its signed-file SHA-256 and the public node rejection.

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
tested by GitHub Actions run `30542926542`. The macOS build is retained as
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
