# Benchmark results — 19 October 2026

The numerical solver and benchmark input files were not changed in this audit.
The five-receiver MPyC fixture and full compact dataset remain permanent,
checksum-pinned fixtures with their existing attribution/licence.

## Historical and synthetic numerical controls

Executed twice, with fresh output paths, exit 0 each:

```bash
python tools/mlat/run_compact_solver_benchmark.py --output artifacts/readiness-2026-10-19/compact-a/report.json
python tools/mlat/run_compact_solver_benchmark.py --output artifacts/readiness-2026-10-19/compact-b/report.json
cmp artifacts/readiness-2026-10-19/compact-a/report.json artifacts/readiness-2026-10-19/compact-b/report.json
```

The two JSON reports match byte for byte. Environment: Python 3.12.11, locked
NumPy, local macOS host. Cross-platform floating-point bit identity is not claimed.

**362 historical events: 270 solved, 92 rejected (74.586% solved).** Every rejected
candidate violated the existing -500..15,000 m altitude bounds. Errors below are
for the 270 accepted events; excluding failures from the error distribution must
not be mistaken for a 100% success rate.

| Error in metres | Median | P95 | Maximum |
| --- | ---: | ---: | ---: |
| Horizontal | 59.052 | 295.921 | 961.568 |
| Vertical | 382.416 | 2961.128 | 9612.893 |
| 3D | 399.580 | 2963.702 | 9612.981 |

Residual median/P95/maximum: **5.791 / 20.725 / 128.409 m**. Best-candidate iteration
median/P95/maximum: **11 / 28.1 / 74** for accepted events. This reports the
iteration at the best returned candidate, not necessarily total optimizer work.
Reports include receiver counts, baseline lengths, vertical aperture and geometry
conditioning. Every historical group has five receivers; there are 26 unique
dataset receiver serials across the file.

The retained published event **5711382** has 31.459 m horizontal, 21.542 m vertical,
and 38.127 m 3D error. The explicitly synthetic propagation control has 0.067 m
horizontal, 0.447 m vertical, and 0.452 m 3D error and passes its existing bound.

The reference positions are aircraft-reported ADS-B positions from the dataset,
not an independent surveyed truth service. Original Mode-S frames, CKB identities
and per-observation clock uncertainty are absent. Published grouping and relative
arrival timestamps are preserved. No timestamps, frame bytes or qualifications
were invented for historical records. These results establish a reproducible
solver baseline, **not live deployment or validated aviation accuracy**. The large
vertical tail is a production blocker for any precision claim.

The separate synthetic artifact/matching benchmark also regenerated identically:

```bash
python tools/mlat/run_reproducible_benchmark.py --output-dir artifacts/readiness-2026-10-19/synthetic-a
python tools/mlat/run_reproducible_benchmark.py --output-dir artifacts/readiness-2026-10-19/synthetic-b
diff -ru artifacts/readiness-2026-10-19/synthetic-a artifacts/readiness-2026-10-19/synthetic-b
python tools/mlat/run_reproducible_benchmark.py --output-dir artifacts/readiness-2026-10-19/synthetic-a --verify-only
```

All four commands exited 0. This bundle checks deterministic artifact/matching
behavior; the numerical controls above exercise the retained robust solver.

## Measured local load

Executed, exit 0:

```bash
python tools/mlat/measure_pipeline_envelope.py --output artifacts/readiness-2026-10-19/load-envelope-report.json
```

Profile: 4, 5, or 10 synthetic receiver callbacks; three aircraft; 100 events per
scenario; target input rates 100/1,000/10,000 observations/s. Each event traverses
JSON normalization, observation checks, correlation, actual solve and SQLite.
All nine scenarios stored exactly 100 positions with zero solver/storage failures.
P99 was added to the existing measurement output, without changing solver behavior.

These are short in-process runs. They exclude network handshakes, HTTP clients,
normal per-signal logging and the production loop's 100 ms batching wait. Browser
and other audit work were running on the same host; these numbers are not a
controlled comparison to earlier measurements. No performance improvement is
claimed. P99 at 100 samples is effectively the worst observation under this
tool's order-statistic definition. RSS is cumulative process peak memory.

| Receivers | Target obs/s | Measured obs/s | Pipeline P50 ms | P95 ms | P99 ms | Peak RSS MB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 100 | 100.0 | 16.12 | 27.75 | 41.85 | 34.2 |
| 4 | 1000 | 186.7 | 18.50 | 41.27 | 76.31 | 34.4 |
| 4 | 10000 | 159.7 | 20.18 | 57.86 | 101.22 | 34.5 |
| 5 | 100 | 100.0 | 4.39 | 12.45 | 59.71 | 34.6 |
| 5 | 1000 | 806.2 | 5.17 | 13.23 | 17.19 | 34.7 |
| 5 | 10000 | 919.6 | 4.62 | 10.59 | 15.28 | 34.8 |
| 10 | 100 | 100.0 | 11.56 | 37.51 | 93.13 | 34.9 |
| 10 | 1000 | 864.0 | 10.48 | 19.47 | 67.97 | 34.9 |
| 10 | 10000 | 766.6 | 11.31 | 26.91 | 50.94 | 35.0 |

## Process restart observation

The 120-second process soak used real loopback HTTP, the synthetic processor,
SQLite and one intentional service restart. It passed its continuity checks:
startup **2.84 s**, restart **4.74 s**, first stored position ID preserved.
**112 of 113 samples succeeded** (99.115%); one request failed during the restart.
Polling-sequence latency median/P95/maximum: **20.07 / 51.47 / 86.31 ms**.
This latency is the sampler's sequence of API reads, not each endpoint separately.
The report preserves degraded startup/restart samples and unsuccessful solves.
It is a bounded recovery check, not a production availability SLO or a sustained
load campaign. The detailed report is under `artifacts/readiness-2026-10-19/process-soak/`.

Before production load claims, agree actual receiver count, transmissions/sec,
frame distribution, API/browser concurrency and retention with the operator.
Run at least an hour on the intended host, then a longer soak covering backups,
feed disconnects, RPC outages and disk pressure. Record attempted/accepted/rejected
observations, latency percentiles, event-loop lag, CPU/RSS, queue drops, stored
solutions and deliberate failures. Compare runs only on equivalent hardware,
configuration, logging and data.
