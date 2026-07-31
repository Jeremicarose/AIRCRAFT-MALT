# Reproducibility

## Dependency locks

Python `3.12.11` is the project evidence runtime. Production dependencies are
fully resolved in `requirements.lock`; development and test dependencies are in
`requirements-dev.lock`. Both files include distribution SHA-256 hashes.

Install the development environment with hash verification:

```bash
python -m pip install --require-hashes -r requirements-dev.lock
```

The lockfiles are generated from `pyproject.toml` and
`requirements-build.in` with an explicit resolution cutoff. The exact command
is recorded in each lockfile header. Regenerating a lock is an intentional
dependency update and must be reviewed like source code.

Rust uses `contracts/receiver-registry/Cargo.lock` and the pinned toolchain in
`contracts/receiver-registry/rust-toolchain.toml`.

## Deterministic benchmark

Generate the committed benchmark evidence package:

```bash
python scripts/run_reproducible_benchmark.py
```

Verify it without changing files:

```bash
python scripts/run_reproducible_benchmark.py --verify-only
```

The runner packages its fixture inputs, implementation sources, workflow,
Dockerfile, Python version, project metadata, and dependency locks.
`manifest.json` records byte counts and hashes; `checksums.sha256` covers every
other file. Running the generator twice must produce byte-identical directories.

This benchmark tests deterministic reference matching and evidence generation.
Its inputs are synthetic, so both the report and manifest explicitly reject any
claim that it proves live receiver operation or real-world MLAT accuracy.

## Performance and live evidence

Operational latency and throughput are inherently environment-dependent. Their
reports must record runtime, platform, commit, sample counts, and provenance;
they are repeatable measurements rather than byte-reproducible outputs.

Real accuracy evidence requires the synchronized hardware procedure in
`docs/GRANT_EVIDENCE_RUNBOOK.md`. That evidence remains incomplete until an
actual multi-receiver capture is published.

## CI contract

`.github/workflows/reproducibility.yml`:

- installs the hash-locked development environment on Python `3.12.11`
- runs the complete Python test suite
- generates the benchmark twice and compares every byte
- compares regenerated evidence with the committed package
- builds and smoke-tests the digest-pinned application container
- uploads the benchmark package, lockfiles, and CI environment provenance

The workflow has read-only repository permissions and pins third-party actions
to immutable commit SHAs.
