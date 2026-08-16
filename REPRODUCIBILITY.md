# Reproducibility

## Supported Baseline

- Python: 3.12.11
- Rust: 1.95.0
- Node.js: 20
- Contract target: `riscv64imac-unknown-none-elf`
- CI runner: Ubuntu 24.04

## Python

`requirements.lock` is the production graph and `requirements-dev.lock` adds the
test graph. Every downloaded distribution is hash-pinned.

```bash
python3 -m pip install --require-hashes -r requirements-dev.lock
python3 -m pip check
python3 -m pytest -q
```

`requirements.txt` is a human-readable compatibility input, not the
reproducible installation source. Update locks with the project’s declared
Python version and review all dependency changes before committing.

## Registry Contract

Rust dependencies are locked by `contracts/registry-v2/Cargo.lock`; the
toolchain is pinned by `rust-toolchain.toml`.

```bash
cd contracts/registry-v2
cargo clean
rustup show
cargo fmt -- --check
make test
make check
sha256sum target/riscv64imac-unknown-none-elf/release/receiver-registry
```

Run `cargo clean` after moving the contract directory because Cargo test
artifacts embed `CARGO_MANIFEST_DIR`.

The 2026-07-30 testnet binary was built on Ubuntu CI and is canonical for that
deployment. The retained local macOS binary has a different hash. Contract builds
are semantically tested across these environments but are not currently
byte-reproducible across platforms.

## Registry Evidence

Offline verification requires only Python standard-library dependencies plus the
saved bundle:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final
```

Live verification performs public RPC requests and is sensitive to external
node availability:

```bash
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final \
  --live
```

The historical package must remain unchanged. Its README intentionally refers
to the source paths at its recorded commit.

## Deterministic MLAT Benchmark

The MLAT benchmark fixture validates matching logic, artifact generation, and
claim labeling. It is synthetic and cannot establish real-world accuracy.

```bash
python3 tools/mlat/run_reproducible_benchmark.py
python3 tools/mlat/run_reproducible_benchmark.py --verify-only
```

The runner copies all source inputs needed to reproduce the output into
`evidence/mlat-reference/reproducible-benchmark-v2/source`, writes canonical
JSON, and verifies every checksum. CI generates the bundle twice, compares the
two byte-for-byte, and compares the result with the committed package.

## Frontend

The frontend uses Node.js 22.23.1 from `.nvmrc`, `npm ci`, and exact direct
dependency versions. It does not download web fonts during the build.

```bash
cd reference/mlat/frontend
npm ci
npm run typecheck
npm run build
```

`node_modules` and `.next` are generated and ignored. The frontend container
uses a Node 22.23.1 Alpine image pinned to an exact multi-architecture digest.

## Containers

The Python base image is digest-pinned. Build without injecting local state:

```bash
docker build --tag ckb-registry-v2-mlat-reference:local .
docker compose build
```

The contract CI currently installs RISC-V GCC from Ubuntu repositories. Package
metadata is recorded in CI logs, but repository snapshots are not pinned.

## Evidence Classes

- **Reproducible**: inputs, tool versions, source, checksums, and deterministic
  regeneration are present.
- **Verifiable**: saved content passes semantic/hash checks but may depend on an
  external historical event.
- **Experimental**: useful local measurements without a controlled claim scope.
- **Live**: physical source and timing provenance pass the strict evidence gates.

Only the first two classes are currently published as durable evidence. The local
MLAT performance/reliability files are explicitly experimental.

## Release Provenance

`.github/workflows/security.yml` creates an SPDX JSON SBOM and attests a source
archive on pushed commits. `.github/workflows/release.yml` is tag-gated and
refuses to publish without `LICENSE`; it rebuilds tests and release artifacts,
generates checksums, and creates GitHub provenance/SBOM attestations.

The workflows use commit-pinned actions. A configured workflow is not evidence
until its public run passes; release consumers must verify the resulting
attestations using the procedure in [RELEASE.md](RELEASE.md).
