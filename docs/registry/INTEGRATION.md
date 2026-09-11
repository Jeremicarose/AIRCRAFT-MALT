# CKB Receiver Registry V2 Integration Guide

## Security objective

Registry V2 uses CKB cells to publish a durable Receiver Identity, current
Receiver Record, and owner lock. The contract prevents identity duplication,
unauthorized state continuity changes, sequence rollback, deletion, and
revocation reversal.

CKB proves who is authorized to update a registry cell and which state
transitions are valid. It does not prove that a physical receiver exists, that
its coordinates are honest, or that its clock is synchronized. Those claims
need separate operational evidence.

## Historical public testnet deployment

The first Registry V2 deployment and signed lifecycle were verified on CKB
testnet on 2026-07-30:

- deployment transaction: `0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3`
- contract outpoint: deployment output `0x0`
- registry `code_hash`: `0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c`
- binary CKB data hash: `0x9f5ae883bd5039b6eb3544c69a1597214c655bbccdb920e0fb7284c09d3cc645`
- binary SHA-256: `688fdc5f755029fa3c93365663f0bd2d118d4bacb53340234a1cecb171ad4f77`
- evidence Receiver Identity: `0xcca658ee811707def01d466b16b9b3ee133c3f6952388c78a5f90a5c273749e8`

The TypeScript SDK exports these exact deployment values as
`REGISTRY_V2_PUDGE_2026_07_30`. Its deployment test compares the constant with
the signed evidence manifest. This historical constant is retained for
read-only review; it is not the SDK's current testnet default.

The create, update, transfer, and revoke transactions plus all signed rejected
attacks are indexed in
`evidence/registry-v2-testnet-2026-07-30-final/README.md`. Verify the saved
package and re-query the live RPC with:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final \
  --live
```

The saved evidence bundle is immutable and remains valid evidence for source
commit `61ab011de58397cb8d6ca3cecb5c659c69e2fc8c`. The deployment itself uses
`hash_type=type`, so its contract implementation cell can be replaced under the
same type hash. It is therefore historical and read-only in the current SDK and
frontend. Do not use the historical deployment outpoint as the dependency for
the current binary.

## Current immutable public testnet deployment

The current contract candidate was deployed on Pudge with an immutable `data1`
binding and exercised through a CKB CLI-signed lifecycle:

- deployment transaction: `0xc2241446c19b61293b0901f801898ebeade7df9f4fd52669fc1eeebebee450bf`
- contract output index: `0x0`
- registry `code_hash`: `0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa`
- binary SHA-256: `087a8b19ca99170d8d1e8c018b749259ce067ad3cb1cc8cef3b4a490ccae0465`
- evidence Receiver Identity: `0x1d6855f20486a023c92df0c613a3141e385f3766c4c844d2935fe18cfcf220ce`

The evidence in `evidence/registry-v2-testnet-2026-09-11-data1-final`
contains create, update, transfer, revoke, and seven signed rejected attacks.
It passes fresh public-RPC verification without containing private keys. This
proves the deployed lifecycle, but it is not a TypeScript SDK or browser-signer
run and the contract has not been independently audited.

## Identity model

A Receiver Identity is the exact 32-byte argument of the Registry V2 type
script. Creation follows CKB's Type-ID rule:

```text
blake2b(first_input_molecule || output_index_le_u64)
```

The contract requires exactly 32 argument bytes and validates the creation hash
using `ckb-std::type_id`. The script argument remains unchanged automatically
because CKB groups inputs and outputs by the complete type script.

The JSON `receiver_id` is a human Receiver Label. It remains immutable during
the lifecycle but is not globally unique. Consumers must key by the 32-byte
Receiver Identity, never by the label or record timestamp.

## Receiver Record schema

```json
{
  "schema_version": 2,
  "receiver_id": "RECV_NYC_001",
  "latitude": 40.7128,
  "longitude": -74.006,
  "altitude": 10.0,
  "status": "online",
  "capabilities": ["mode-s", "mlat"],
  "sequence": 0,
  "updated_at": 1700000000,
  "stream_endpoint": "wss://feed.example/ws",
  "stream_protocol": "websocket-json",
  "stream_format": "json",
  "metadata_hash": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Important invariants:

- `schema_version` is exactly `2`.
- `receiver_id` is 1-64 uppercase ASCII identifier characters.
- capabilities contain 1-8 unique lowercase identifiers and include `mode-s`.
- `sequence` is `0` at creation and increments by exactly one.
- `sequence` and `updated_at` use exact unsigned 64-bit integer syntax;
  `updated_at` must be at least `1`.
- cell data is at most 16 KiB and uses strict UTF-8 JSON.
- JSON string escape sequences are rejected. Producers must emit the intended
  UTF-8 characters directly instead of escaped alternatives.
- `updated_at` is positive and cannot move backwards, but never resolves
  identity conflicts.
- status is `online`, `offline`, `degraded`, or `revoked`.
- a revoked record cannot advertise a stream.
- unknown JSON fields and trailing bytes are rejected.
- arbitrary metadata stays off chain; `metadata_hash` can commit to it.

## Lifecycle transitions

| Group inputs | Group outputs | Meaning | Result |
|---:|---:|---|---|
| 0 | 1 | Creation with derived Type ID and sequence 0 | Allowed |
| 1 | 1 | Metadata update with next sequence | Allowed |
| 1 | 1 | Ownership transfer by changing output lock | Allowed |
| 1 | 1 | Transition to `revoked` | Allowed |
| 1 | 0 | Burn/delete | Rejected |
| 0 | 2 or 1 | Duplicate mint/output | Rejected |
| 1 | 1 | Update after revocation | Rejected |

An ownership transfer is authorized by the previous input lock. The type script
does not contain private keys and does not bypass lock verification. Use a
reviewed CKB lock such as the network's standard secp256k1 lock or a deliberate
multisig/OmniLock policy.

## Discovery behavior

`CKBPeerDiscovery` queries all V2 cells with indexer pagination and extracts the
identity from `output.type.args`. It:

- keys cache and runtime receivers by Receiver Identity
- never chooses a record by self-declared timestamp
- keeps duplicate Receiver Labels as distinct identities
- quarantines duplicate live cells for the same identity
- rejects malformed identities and can apply an explicitly configured record-age
  policy; lifecycle `updated_at` is not treated as a heartbeat by default
- retains owner lock, outpoint, sequence, block number, and metadata hash as
  provenance

Use `RECEIVER_REGISTRY_HASH_TYPE=data1` with the current deployment. Set `type`
only when deliberately inspecting the historical 2026-07-30 cells. The
configured hash type must match the deployed receiver-cell script exactly.

Live feed adapters must put the immutable `0x...` Receiver Identity in their
`receiver_id` field. The Receiver Label is display metadata only.

## Application workflow

TypeScript application developers should use the
[SDK journey](../../sdk/typescript/README.md):

```text
install -> configure signer -> create -> discover -> update -> transfer
        -> discover transferred identity -> revoke -> verify
```

With a reviewed immutable `data1` deployment configured, the SDK accepts a CCC
wallet signer and a recipient's public Pudge address. It derives Type IDs and
lifecycle fields, builds and balances transactions, adds the contract
dependency, submits through the wallet, and waits for public indexer visibility.
This path does not require `ckb-cli`, a raw private key, or manual transaction
JSON. The current SDK default uses the immutable deployment. The historical
July deployment remains discovery-only and every SDK write method rejects it
before wallet approval.

The first-use problems and their verification evidence are recorded in the
[SDK developer journey review](SDK_DEVELOPER_JOURNEY_REVIEW.md).

The reference frontend exposes this exact testnet workflow at
`/app/registry`. Its owner-action panel passes application fields to the SDK,
submits the prepared transaction through the connected CCC wallet, and waits
for the exact output to become visible through the public indexer. It does not
derive sequences, timestamps, Type IDs, or recipient lock scripts itself. The
bundled defaults identify the current immutable deployment. Owner actions
remain unavailable until a supported Pudge wallet is connected. Deployers may
override the defaults only by supplying all three `NEXT_PUBLIC_REGISTRY_*`
values together.

## Build and verify

```bash
cd contracts/registry-v2
make test
make check
```

The test suite builds the deployable RISC-V binary and executes transaction
tests in CKB-VM using `ckb-testtool`.

## Low-level contract maintainer tooling

The commands below expose record and transaction internals for contract
development and evidence review. They are not the application SDK workflow.
Application developers should not need them.

### Creation

Generate a sequence-zero Receiver Record:

```bash
python3 tools/registry/generate_receiver_registry_record.py \
  --receiver-id RECV_NYC_001 \
  --latitude 40.7128 \
  --longitude -74.006 \
  --altitude 10 \
  --capability mode-s \
  --capability mlat \
  --sequence 0
```

Generate the output template:

```bash
python3 tools/registry/generate_receiver_registration_tx_template.py \
  --lock-arg 0xYOUR_OWNER_LOCK_ARG \
  --code-hash 0xYOUR_V2_CONTRACT_BINARY_DATA_HASH \
  --hash-type data1
```

Add the funding input and receiver output to the transaction first. Then derive
and apply the creation identity:

```bash
python3 tools/registry/apply_receiver_type_script.py \
  --tx-file deploy/receiver-registration-tx.json \
  --contract-tx-hash 0xYOUR_CONTRACT_DEPLOY_TX
```

The script calculates the exact Type ID from the transaction's first input and
the selected registry output index. Never submit a Registry V2 creation output
with empty arguments.

### Update, transfer, and revocation

Spend the current registry cell, preserve its type script, increment sequence by
one, and provide exactly one replacement output.

For tooling that applies an existing identity explicitly:

```bash
python3 tools/registry/apply_receiver_type_script.py \
  --tx-file deploy/receiver-update-tx.json \
  --receiver-identity 0xYOUR_EXISTING_32_BYTE_IDENTITY \
  --contract-tx-hash 0xYOUR_CONTRACT_DEPLOY_TX
```

- Update: retain owner lock and write the next valid record.
- Transfer: write the next valid record under the new owner's output lock. The
  old owner must authorize spending the input.
- Revoke: write the next sequence with `status=revoked` and no stream fields.

Revocation is permanent. The tombstone cannot be burned or changed later.

## V1 migration

Registry V1 used empty type arguments and selected duplicate labels by newest
timestamp. V1 and V2 must use different deployed code hashes.

Migration procedure:

1. Deploy the V2 binary and record its code hash and contract outpoint.
2. Create a V2 identity for every receiver under its current authorized owner.
3. Update feed adapters to emit the new immutable identity.
4. Set `RECEIVER_REGISTRY_TYPE_HASH` and `RECEIVER_REGISTRY_HASH_TYPE` to the
   exact V2 deployment script values.
5. Verify discovery provenance and receiver counts.
6. Mark V1 records offline where possible; never merge V1 and V2 query results.

No automatic migration can preserve V1 uniqueness because V1 never established
a collision-resistant identity in the first place.

## Remaining limitations

- The V2 record is receiver-specific and requires the `mode-s` capability. It
  does not yet implement a generic physical-infrastructure schema.
- Receiver Labels are not globally unique.
- Contract correctness is test-backed but not independently audited.
- The TypeScript SDK assembles lifecycle transactions through CKB-CCC signer
  abstractions and is configured for a protected public npm release. The first
  publish still needs npm scope ownership and maintainer approval. The
  repository retains `ckb-cli` only for the older evidence workflow.
- Physical receiver, location, feed, and timing attestations remain off-chain
  responsibilities.
