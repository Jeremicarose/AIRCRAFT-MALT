# Compact Public Solver Benchmark V1

`report.json` contains the synthetic control, one inspectable historical event,
and all 362 outcomes from the pinned compact public sample.

Headline result: 270 of 362 events solved. Median horizontal error among solved
events was 59.05 m. Median 3D error was 399.58 m, mainly because vertical error
was substantially larger than horizontal error.

This is historical **solver-only** evidence. It is not live evidence, Registry
evidence, clock-attestation evidence, or validation of the complete production
pipeline.

See [`docs/mlat/compact-public-solver-benchmark.md`](../../../docs/mlat/compact-public-solver-benchmark.md)
for source attribution, coordinates, reproduction steps, results, and limits.

Dataset-derived values in the report are provided under CC BY-SA 4.0. Original
benchmark code remains under the repository's MIT licence.
