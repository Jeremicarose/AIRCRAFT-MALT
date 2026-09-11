# Registry V2 Immutable Testnet Evidence

## Status

`CHAIN LIFECYCLE VERIFIED OFFLINE AND LIVE; RELEASE CI PROVENANCE PENDING`

This bundle records a CKB Pudge testnet deployment using immutable
`hash_type=data1`, followed by create, update, transfer, and terminal revoke
transactions. It also records seven signed attack transactions rejected by the
deployed contract.

The transactions were prepared and submitted by the repository's CKB CLI
lifecycle tool. They are not evidence of a TypeScript-SDK or browser wallet run;
that separate signer workflow still requires an external wallet approval.

The saved transaction bodies, contract binary, lifecycle lineage, discovery
snapshots, API snapshots, and rejection responses pass the repository verifier.
The saved live report re-queries all accepted transactions, and the real-indexer
report confirms exhaustive exact-identity and code-hash-prefix pagination.
The bundle is not complete release evidence yet because clean local and GitHub
CI records have not been added. The normal verifier intentionally fails until
those provenance files exist.

No private key, seed phrase, or mnemonic is included. Transaction witnesses and
signatures are public chain evidence and cannot be used to recover an owner key.

## Deployment

| Item | Value |
|---|---|
| Network | CKB Pudge testnet |
| Deployment transaction | `0xc2241446c19b61293b0901f801898ebeade7df9f4fd52669fc1eeebebee450bf` |
| Contract output index | `0x0` |
| Registry hash type | `data1` |
| Contract CKB data hash | `0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa` |
| Contract SHA-256 | `087a8b19ca99170d8d1e8c018b749259ce067ad3cb1cc8cef3b4a490ccae0465` |
| Lifecycle tooling commit | `13662bfd2d7a6e6162d551b2982fe3e61fca4f23` |

The receiver Type Script uses the contract data hash above as its `code_hash`.
This binds receiver cells to the exact deployed binary bytes rather than to a
mutable Type Script identity.

## Accepted Lifecycle

| Stage | Transaction |
|---|---|
| Create | `0x3b78cd8aeac8d55ff07a17f7d9f8fca97ca4aaec5824a07d9d54a58cb0dd64a1` |
| Update | `0x33f02d9d9c2dada3d3473014492c39c1fe344fd5d3c887a465fbaf72191f0597` |
| Transfer | `0xd58ce0337f175fc53152a73b709f4da1a924c082328d3494f3637f7c44ea59a8` |
| Revoke | `0x9a34483db911e9238f022dd84a7eb0fafb224a2424d7e646ba29cde10e625626` |

Receiver Identity:
`0x1d6855f20486a023c92df0c613a3141e385f3766c4c844d2935fe18cfcf220ce`

The saved records preserve the identity and label, advance sequence numbers
from 0 through 3, change the owner lock during transfer, and end in the revoked
tombstone state.

## Verification

Full offline release verification requires checksums plus local and GitHub CI
provenance:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-09-11-data1-final
```

The public RPC can be queried again without claiming that CI provenance is present:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-09-11-data1-final \
  --live-chain-only
```

`--live-chain-only` does not make the bundle release-ready. A stable release
still requires clean source-bound CI evidence, independent security review,
browser evidence, and a healthy public deployment.
