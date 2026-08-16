# CKB Registry V2 Domain Context

## Product

CKB Registry V2 is a verifiable identity and lifecycle registry for physical
infrastructure. The present V2 implementation is a receiver registry with an
aviation-specific record schema. MLAT is its primary reference implementation.

## Language

**Infrastructure Identity**:
An immutable 32-byte CKB type-script argument naming one on-chain lifecycle.
The current tools also call this a Receiver Identity because V2 is
receiver-specific.
_Avoid_: receiver name, label, database ID

**Receiver Label**:
The immutable human-readable `receiver_id` value in a V2 record. It is not a
globally unique security identifier.
_Avoid_: identity, canonical ID

**Receiver Record**:
The schema-versioned JSON bytes stored in a Registry V2 cell. The current schema
contains position, status, capabilities, sequence, stream metadata, and an
optional metadata commitment.
_Avoid_: peer record, generic infrastructure record

**Lifecycle Sequence**:
A strictly increasing integer beginning at zero and incrementing by exactly one
for each accepted successor.
_Avoid_: timestamp version, latest timestamp

**Owner Lock**:
The CKB lock script on the current Registry Cell. Spending the cell authorizes a
lifecycle transition; Registry V2 does not manage private keys.
_Avoid_: contract administrator, registry password

**Ownership Transfer**:
An authorized successor that preserves Infrastructure Identity and Receiver
Label while changing the output cell lock.
_Avoid_: identity replacement

**Revocation Tombstone**:
A terminal Receiver Record with `status=revoked`. It retains the identity and
cannot be updated, resurrected, or burned.
_Avoid_: offline record, deletion

**Registry Cell**:
The live CKB cell whose type script is Registry V2 and whose type arguments are
the Infrastructure Identity.
_Avoid_: database row, account

**Registry Code Hash**:
The script hash of the deployed contract cell's Type ID script, used as the
`code_hash` in registry type scripts. It is not the binary data hash.
_Avoid_: binary hash

**Discovery**:
Indexer-backed enumeration and validation of live Registry Cells. Discovery
keys records by Infrastructure Identity and quarantines duplicate live cells.
_Avoid_: simulation, registration

**Lifecycle Evidence**:
Saved transactions, RPC responses, discovery snapshots, API responses, hashes,
and verification reports demonstrating one concrete deployment lifecycle.
_Avoid_: security audit, proof of physical receiver truth

**MLAT Reference**:
The aviation consumer that discovers Registry V2 receivers, ingests synchronized
Mode-S observations, correlates transmissions, solves positions, stores results,
and exposes an operator API/frontend.
_Avoid_: primary product

**Replay Mode**:
An explicit MLAT-only synthetic data path. Replay results are integration
evidence, never CKB discovery evidence or live field evidence.
_Avoid_: live mode, production data

**Field-Trial Harness**:
The live-ingest and benchmark tooling intended to validate Registry V2 with
physical receivers. The harness exists; a public synchronized four-receiver
window does not.
_Avoid_: completed field trial

## Invariants

- Infrastructure Identity is exactly 32 bytes and follows the CKB Type-ID rule.
- A lifecycle has one create output or one input and one successor output.
- Receiver Label is immutable within a lifecycle.
- Lifecycle Sequence starts at zero and increments by one.
- Revocation is terminal and the tombstone cannot be burned.
- Discovery never substitutes simulated records.
- CKB authorization does not attest hardware existence, location, clock quality,
  or stream honesty.

## Current Scope Constraint

The deployed V2 contract requires a `mode-s` capability. Reuse outside aviation
is a product direction, not an implemented capability. A generalized contract
must use a new version and deployment so existing testnet evidence remains
verifiable.
