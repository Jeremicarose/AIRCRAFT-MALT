# MLAT Airspace Console

The project localizes aircraft from distributed receiver timing observations and
uses CKB to publish durable receiver identities and their current operational
metadata.

## Language

**Receiver Identity**:
An immutable 32-byte CKB type-script argument that names one receiver lifecycle.
_Avoid_: Receiver name, receiver ID

**Receiver Label**:
A human-readable, immutable label stored in a Receiver Record. It is not a
globally unique security identifier.
_Avoid_: Identity, canonical ID

**Receiver Record**:
The versioned on-chain metadata associated with one Receiver Identity.
_Avoid_: Peer record, registry entry

**Lifecycle Sequence**:
A strictly increasing integer that orders authorized Receiver Record updates.
_Avoid_: Timestamp version, latest timestamp

**Ownership Transfer**:
An update that preserves Receiver Identity and Receiver Label while changing the
output cell lock under authorization from the previous owner lock.
_Avoid_: Identity replacement

**Revocation Tombstone**:
A terminal Receiver Record whose `revoked` status permanently prevents further
updates while retaining the Receiver Identity on chain.
_Avoid_: Offline record, deletion
