# Compact public MLAT solver benchmark

**VALIDATED: numerical regression only.** The benchmark consumes all 362
checksum-pinned MPyC v0.11/LocaRDS historical events. It does not prove live
transport, raw-frame correlation, CKB ownership, receiver location or clock
accuracy. The complete source is bundled, with upstream CC BY-SA 4.0 attribution,
so reproduction needs no dataset download.

## Reproduce

Use Python 3.12.11 and the hash-locked dependencies, then run:

```bash
python tools/mlat/run_compact_solver_benchmark.py --output /tmp/compact-a/report.json
python tools/mlat/run_compact_solver_benchmark.py --output /tmp/compact-b/report.json
diff -ru /tmp/compact-a /tmp/compact-b
```

The command verifies source hashes, processes every event, writes strict JSON and
a SHA-256 sidecar, and exits unsuccessfully if the synthetic control exceeds one
metre. Repeat output is byte-identical in the same tested numerical environment.
Different Python/NumPy/BLAS environments may produce small floating-point changes;
compare their metrics and provenance rather than pretending they are identical.

[Complete report](../../evidence/mlat-reference/compact-public-solver-v2/report.json)
· [report checksum](../../evidence/mlat-reference/compact-public-solver-v2/report.sha256)
· [source manifest](../../reference/mlat/benchmarks/fixtures/mpyc-gps-five-source.json)

## Control and published example

| Test | Horizontal error | Vertical error | 3D error | Residual | Best iteration |
|---|---:|---:|---:|---:|---:|
| Synthetic, same five receivers | 0.067 m | 0.447 m | 0.452 m | 0.004605 m | 3 |
| Historical event 5711382 | 31.459 m | 21.542 m | 38.127 m | 3.166 m | 6 |

The synthetic control passes below one metre. The approximately 31.5 m horizontal
and 38.1 m 3D historical values are regression references, not rigid acceptance
requirements. Reference positions are aircraft-reported ADS-B values, not surveyed
truth. The example's geometry remains in the report and the attributed event fixture.

## All events

270 solved; 92 rejected;
**74.586% success**. Error statistics below use solved events only;
all 362 events remain in the solve-rate denominator and per-event report.

| Error, metres | Median | P95 | Maximum |
|---|---:|---:|---:|
| Horizontal | 59.052 | 295.921 | 961.568 |
| Vertical (absolute) | 382.416 | 2961.128 | 9612.893 |
| 3D | 399.580 | 2963.702 | 9612.981 |

Residual: median 5.791 m, P95 20.725 m,
maximum 128.409 m.
Iterations: median 11, P95 28.1,
maximum 74. The existing solver reports the iteration of
its best returned candidate, not necessarily the total number of optimizer steps.
Failed candidates: median 11,
P95 25.7, maximum 86.

## Failures and geometry

All 92 rejections are `altitude_out_of_bounds`: candidate altitude falls outside
-500..15,000 m. The solver's decision is observed through a diagnostic subclass;
its calculations and rejection thresholds are unchanged. Type annotations were
added to the solver; stripping annotations/casts gives the same executable AST.

There are 26 distinct receivers across
the sample and exactly five per event. Receiver geometry is not the same for every
event. Solved events' median maximum baseline is 279.09 km;
failed events' is 296.24 km. Median minimum
spacing is 19803.03 m for solved events and
22.46 m for failed events. 56/92 failed
and 134/270 solved events include a receiver pair less than 100 m apart.

This association is a useful investigation lead, not proof that close spacing is
the sole cause. The TDOA Jacobian condition-number median is
50.02 for solved events and
36.45 for failed events, so a
single geometry statistic does not explain the failures. Vertical errors dominate
the large-error tail. Small residuals do not establish accurate altitude.

## Frozen provenance

- Benchmark version: `compact-public-solver-v2`.
- Runtime: Python 3.12.11, NumPy 2.5.1.
- Solver base commit: `b73f2efa92ddcfc41c448491402532b373cc2fa3`.
- Solver worktree modified: `True` (typing-only edits).
- Current solver SHA-256: `b725e7fdad9518369cef4b36dc439d41712c2c539d093be24e7c34160eacdf7b`.
- Dataset SHA-256: `7167988f67af8314a2d9f44378f748f3a897de783c85271a154cbd81d49d20f5`.
- Receiver metadata SHA-256: `998a63f5fc89fa41fd1a37468431da96f355812054e7bca8b2a4f4db0ba47d1b`.
- Event fixture SHA-256: `98d54df0f4cabd37a6585da8088cc373a5aa17737acfabbf806f4eda1a055435`.
- Output SHA-256: `c90fd799273deaf27266b758cedd533654f5981a24bf46b467fafc25507c1bc4`.

The output also records implementation and manifest hashes. Preserve this package
when changing the numerical solver; create a new version. The earlier v1 report
remains historical evidence. See [historical replay](HISTORICAL_REPLAY.md) to inspect
these events through the real storage/API/frontend path with the missing-input
limitations kept visible.
