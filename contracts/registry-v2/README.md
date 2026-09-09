# Receiver Registry V2 Contract

This `no_std` Rust contract enforces immutable Type-ID receiver
identities, exact lifecycle cardinality, sequence ordering, ownership-transfer
continuity, and terminal revocation.

## Build and test

```bash
make test
make check
```

`make test` performs a release build for
`riscv64imac-unknown-none-elf`, runs four host-side invariant tests, and executes
ten transaction tests in CKB-VM with `ckb-testtool`.

The transaction tests cover:

- valid Type-ID creation
- forged creation identity rejection
- valid update and owner-lock transfer
- wrong-owner signature rejection
- sequence-jump rejection
- burn rejection
- terminal revocation and resurrection rejection
- duplicate registry-output rejection

Registry cell data is limited to 16 KiB. It must use strict UTF-8 JSON number
syntax and must not contain JSON escape sequences inside strings. These rules
avoid different decoded values between the contract's `no_std` JSON parser and
off-chain JSON runtimes. Python and TypeScript enforce the same wire rules.

The shared conformance adapter can be run directly with:

```bash
cargo run --locked --example conformance -- \
  ../../tests/registry/fixtures/registry_v2_conformance.json
```

Build only the deployable binary with:

```bash
make build
```

Output:

```text
target/riscv64imac-unknown-none-elf/release/receiver-registry
```

Deploy Registry V2 as a new contract. V1 cells with empty type arguments are
not compatible and must not be queried under the V2 code hash.
