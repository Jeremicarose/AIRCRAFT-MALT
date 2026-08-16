# CKB Registry V2

CKB Registry V2 is a verifiable identity and lifecycle registry for physical
infrastructure. It uses CKB cells to bind an immutable identity to an
owner-authorized, ordered record lifecycle with permanent revocation.

The MLAT aviation stack in this repository is the primary reference
implementation, validation environment, and field-trial harness. It is not the
primary product.

## Current Status

Registry V2 currently provides:

- a `no_std` Rust type script for create, update, ownership transfer, and revoke
- Type-ID-derived 32-byte identities
- exact sequence progression and immutable receiver labels
- terminal revocation tombstones; burn and resurrection are rejected
- Python record validation and paginated CKB indexer discovery
- transaction generation, lifecycle, and evidence verification tools
- 14 Rust tests, including 10 CKB-VM transaction tests
- a signed CKB testnet lifecycle and rejected-attack evidence package
- strict physical-trial launch and evidence tooling that fails closed without
  four active identities, qualified clocks, reachable feeds, and raw capture

The current contract is not yet a general physical-infrastructure schema. Its
record vocabulary is receiver-specific and it requires the `mode-s` capability.
Generalizing the schema requires a new reviewed contract version and deployment;
it cannot be claimed from the present binary.

The contract has not received an independent security audit. The repository also
does not yet contain an open-source license, so it is not legally ready for
third-party use or redistribution.

See [Project Status](docs/PROJECT_STATUS.md) for the complete status matrix and
[Repository Audit](docs/audit/REPOSITORY_AUDIT.md) for cleanup decisions and
readiness scores. The exact old-to-new path decisions are in the
[File Disposition Ledger](docs/audit/FILE_DISPOSITION.md).

## Architecture

```text
CKB transaction
  -> Registry V2 type script
  -> live registry cell
  -> Python record validation and indexer discovery
  -> consuming infrastructure adapter
  -> MLAT reference runtime (flagship integration)
```

The contract and Python registry modules are the reusable implementation. MLAT
ingest, correlation, solving, persistence, API, and frontend are isolated as a
consumer of that registry.

See [Architecture](ARCHITECTURE.md) and [Domain Context](CONTEXT.md).

## Repository Layout

```text
contracts/registry-v2/          Registry V2 Rust contract and CKB-VM tests
src/ckb_registry/               Python record and discovery implementation
tools/registry/                 Build, deployment, lifecycle, and evidence tools
tests/registry/                 Off-chain registry and tooling tests
evidence/registry-v2-*/         Immutable signed testnet evidence

src/mlat_reference/             MLAT reference backend
reference/mlat/frontend/        MLAT reference Next.js frontend
reference/mlat/benchmarks/      Deterministic benchmark inputs
reference/mlat/config/          Example field-trial configuration
tools/mlat/                     Ingest and benchmark tools
tests/mlat/                     MLAT reference tests
evidence/mlat-reference/        Reproducible and experimental MLAT evidence

docs/                           Authoritative documentation and decisions
.github/workflows/              Contract security and repository CI
```

## Verify Registry V2

Python dependencies are hash-locked for Python 3.12.11:

```bash
python3 -m pip install --require-hashes -r requirements-dev.lock
python3 -m pytest -q tests/registry
```

Build and execute the contract in CKB-VM:

```bash
cd contracts/registry-v2
rustup show
cargo fmt -- --check
make test
make check
```

Verify the committed testnet evidence without network access:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final
```

Add `--live` to re-query the accepted transactions from the configured public
CKB RPC endpoint.

The evidence package records:

- deployment transaction `0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3`
- deployed registry code hash `0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c`
- accepted create, update, transfer, and revoke transactions
- seven signed transactions rejected by CKB-VM

See [Evidence](EVIDENCE.md) for claim boundaries.

## Use The Python Registry Modules

```python
from ckb_registry import CKBConfig, CKBPeerDiscovery

discovery = CKBPeerDiscovery(
    CKBConfig(
        ckb_rpc_url="https://testnet.ckb.dev/rpc",
        ckb_indexer_url="https://testnet.ckb.dev/indexer",
        receiver_registry_type_hash="0x...",
    )
)
```

The discovery module never returns simulated receivers. Simulation is owned by
the MLAT reference adapter and cannot be mistaken for CKB discovery.

See the [Registry Integration Guide](docs/registry/INTEGRATION.md).

## Run The MLAT Reference

Copy the environment template and select an explicit mode:

```bash
cp .env.example .env
```

Start the local replay reference:

```bash
./run-demo.sh
```

In another terminal, start the frontend:

```bash
cd reference/mlat/frontend
npm ci
npm run dev
```

The API defaults to `http://127.0.0.1:5057`; the frontend defaults to
`http://127.0.0.1:3000`. Docker Compose runs the processor, API, and built
frontend as separate services:

```bash
docker compose up --build
```

The replay path is synthetic. It is useful for integration regression testing
but is not live receiver or real-world accuracy evidence. See the
[MLAT Reference README](reference/mlat/README.md).

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Project Status](docs/PROJECT_STATUS.md)
- [Deployment](DEPLOYMENT.md)
- [Reproducibility](REPRODUCIBILITY.md)
- [Evidence](EVIDENCE.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Maintainers](MAINTAINERS.md)
- [Release Process](RELEASE.md)
- [Code Of Conduct](CODE_OF_CONDUCT.md)

## License

No license has been selected. Until a `LICENSE` file is added by the copyright
holder, the code is not open source and external reuse is not authorized.
