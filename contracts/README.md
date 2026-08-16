# CKB Receiver Registry V2

Registry V2 gives each receiver lifecycle a collision-resistant CKB identity
and validates every state transition in the receiver cell's type script.

The security model is:

- **Receiver Identity**: immutable 32-byte type-script argument
- **Receiver Label**: immutable human-readable `receiver_id` in cell data
- **Ownership**: the input cell lock authorizes updates and transfers
- **Lifecycle**: exactly one creation output or one input-to-output update
- **Ordering**: `sequence` increments by exactly one
- **Revocation**: terminal `revoked` tombstone; burning and resurrection fail

The contract uses the Type-ID creation rule implemented by `ckb-std`:

```text
identity = blake2b(first_input_molecule || output_index_le_u64)
```

This prevents two live cells from sharing a Receiver Identity. It does not make
the human Receiver Label globally unique. Discovery keys by Receiver Identity
and may display duplicate labels without merging them.

See [docs/registry/INTEGRATION.md](../docs/registry/INTEGRATION.md) for the
schema, transaction workflows, migration procedure, and threat model.

## Verification

```bash
cd contracts/registry-v2
make test
make check
```

`make test` builds the RISC-V contract and runs both record-invariant tests and
CKB-VM transaction tests through the official `ckb-testtool` harness.
