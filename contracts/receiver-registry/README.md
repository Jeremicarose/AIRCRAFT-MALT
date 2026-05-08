# Receiver Registry Contract Project

This is the local Rust contract project for the CKB receiver registry.

It validates the canonical JSON receiver-record schema used by:

- [src/network/ckb_discovery.py](/Users/jeremicarose/Downloads/mlat-system%202/src/network/ckb_discovery.py:23)

## Files

- `Cargo.toml`: contract crate configuration
- `.cargo/config.toml`: CKB target configuration
- `rust-toolchain.toml`: Rust toolchain/target pin
- `src/error.rs`: validation error codes
- `src/record.rs`: canonical receiver record schema and validation rules
- `src/entry.rs`: contract validation entrypoint
- `src/main.rs`: CKB VM program entry

## Build Locally

Install the RISC-V target:

```bash
rustup target add riscv64imac-unknown-none-elf
```

Run unit tests:

```bash
cd contracts/receiver-registry
make test
```

Note:
- `make test` runs on your local host target
- it does **not** use the bare-metal CKB target
- this is intentional so normal Rust unit tests work

Check the contract for the CKB target:

```bash
make check
```

Build the release binary:

```bash
make build
```

Expected output binary:

```bash
target/riscv64imac-unknown-none-elf/release/receiver-registry
```

## Deploy

This repo does not yet include a full `Capsule.toml` workspace or deployment script.
Use your existing Capsule workflow, or add one once you decide on your final CKB deployment environment.

Deployment requires:

1. build the release binary
2. deploy it to CKB
3. save the resulting type hash
4. set `RECEIVER_REGISTRY_TYPE_HASH` in the MLAT app `.env`

## Validation Scope

The contract validates:

- `receiver_id`
- `latitude`
- `longitude`
- `altitude`
- `status`
- `capabilities`
- `timestamp`
- optional `stream_protocol`
- optional `stream_format`

Ownership remains a lock-script concern.
