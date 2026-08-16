# Contributing

This repository is accepting technical review and patches, but it is not yet a
legally complete open-source project because no license has been selected. Do not
assume a right to redistribute the code until a `LICENSE` file is added.

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Current
review and release ownership is listed in [MAINTAINERS.md](MAINTAINERS.md).

## Development Setup

Required toolchains:

- Python 3.12.11 (see `.python-version`)
- Rust 1.95.0 (see `contracts/registry-v2/rust-toolchain.toml`)
- bare-metal RISC-V GCC for the deployable contract target
- Node.js 22.23.1 (see `.nvmrc`) for the MLAT reference frontend
- Docker with Compose for the complete reference stack

Install the exact Python development graph:

```bash
python3 -m pip install --require-hashes -r requirements-dev.lock
```

Install the exact frontend graph:

```bash
cd reference/mlat/frontend
npm ci
```

## Required Checks

Run checks relevant to the changed area. Before submitting a cross-cutting
change, run all of them.

```bash
python3 -m black --check src/ckb_registry src/mlat_reference tools tests
python3 -m flake8 src/ckb_registry src/mlat_reference tools tests
python3 -m pytest -q
python3 tools/check_documentation.py
python3 tools/mlat/run_reproducible_benchmark.py --verify-only
python3 tools/registry/verify_registry_v2_evidence.py \
  --bundle evidence/registry-v2-testnet-2026-07-30-final
```

```bash
cd contracts/registry-v2
cargo fmt -- --check
make test
make check
```

```bash
cd reference/mlat/frontend
npm ci
npm run typecheck
npm run build
```

## Change Rules

- Use the vocabulary in `CONTEXT.md`.
- Keep Registry V2 free of MLAT simulation dependencies.
- Do not alter historical evidence to make it match current source paths.
- Do not present replay, fixtures, or local baselines as live evidence.
- Contract behavior changes require CKB-VM transaction tests and a new ADR.
- Schema or binary changes require a new deployment/evidence package; never
  overwrite the canonical 2026-07-30 package.
- Update `CHANGELOG.md`, project status, and affected operator docs with behavior.
- Keep private keys, feed credentials, `.env`, databases, and local deployment
  files out of Git.

## Contract Changes

Treat the current testnet binary and code hash as immutable. A behavioral change
to record validation or lifecycle rules is a new contract release, not an
in-place documentation correction.

A contract pull request must include:

- the security objective and threat being addressed
- positive and negative unit tests
- CKB-VM transaction tests
- cycle impact when material
- migration and compatibility notes
- an ADR for lifecycle/schema changes

## Python And MLAT Changes

The interface under test is the behavior exposed by `ckb_registry` or
`mlat_reference`, not internal helper count. Prefer changes with strong locality:
do not add pass-through modules or hypothetical adapters without a second real
implementation.

Live-ingest changes must preserve integer nanosecond timestamps and clock
qualification fields end to end.

## Documentation

Authoritative documents live at the repository root and under `docs/registry`
or `docs/reference/mlat`. Planning and grant copy do not belong in the source
tree. Git history is the archive for removed proposals.

Use relative links and run the repository link check before submission.

## Reporting Security Issues

Do not open a public issue for a vulnerability. Follow [SECURITY.md](SECURITY.md).

Release preparation follows [RELEASE.md](RELEASE.md). Contributors must not
create or push release tags without maintainer approval.
