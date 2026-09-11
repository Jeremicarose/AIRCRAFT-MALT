# Pilot Readiness Gate

This gate turns the five pilot prerequisites into repeatable checks. It does
not sign transactions, request private keys, or claim that a physical receiver
feed exists.

## 1. Immutable Deployment

Build the current contract, publish its binary hash, and deploy it with a
maintainer-controlled funded CKB testnet account. The Registry cells must use
`hash_type=data1`; the historical `type` deployment is read-only.

After the deployment transaction is confirmed, verify the code cell before
configuring the browser:

```bash
python tools/registry/verify_data1_deployment.py \
  --contract-tx-hash 0x... \
  --contract-index 0 \
  --code-hash 0x... \
  --binary contracts/registry-v2/target/riscv64imac-unknown-none-elf/release/receiver-registry \
  --output artifacts/data1-deployment.json
```

The verifier checks that the outpoint is live and that its cell data hashes to
the configured code hash. It performs no signing or spending operation.

Configure all three public frontend values together only after this check:

```text
NEXT_PUBLIC_REGISTRY_CODE_HASH=0x...
NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH=0x...
NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX=0
```

## 2. Wallet Lifecycle

Run the exact built frontend and use a supported Pudge wallet. Approve one
create, update, transfer, and revoke sequence. Preserve each transaction hash
and verify the canonical Type ID, sequence, owner lock, and final revoked
tombstone through independent RPC reads. Never request a seed phrase or private
key.

The SDK verifies the data1 dependency before asking the wallet to sign. A
committed transaction that is not yet indexed must be treated as pending, not
as a reason to resubmit.

## 3. Indexer Health

After create or revoke, compare the expected live cell with the public indexer:

```bash
python tools/registry/check_registry_indexer_health.py \
  --contract-code-hash 0x... \
  --hash-type data1 \
  --receiver-identity 0x... \
  --expected-tx-hash 0x... \
  --expected-index 0 \
  --output artifacts/indexer-health.json
```

`indexer_lag` means direct RPC sees a live cell but the indexer does not. The
pilot must stop at this state; the application must not silently turn it into a
healthy empty directory.

## 4. Live MLAT Gate

Prepare four independently operated receivers with Registry Type IDs, stream
endpoints, clock evidence, and a new raw observation log. Run:

```bash
python tools/mlat/check_live_ingest_readiness.py \
  --receiver-config receiver-clocks.local.json \
  --require-ready \
  --output logs/live-preflight.json
```

Only continue when the report says `ready_for_real_live_ingest: true`. Replay
mode cannot satisfy this gate.

## 5. Clean Evidence

Use the manually triggered GitHub workflow `Pilot Readiness Evidence` after
committing the source. It runs the clean-clone Registry, SDK, MLAT, frontend,
contract, and conformance checks and uploads the evidence bundle. Optional
deployment and indexer inputs add the two live checks above.

The workflow can prove reproducibility. It cannot manufacture wallet approvals,
testnet funds, or physical receiver observations; those remain explicit
external prerequisites.
