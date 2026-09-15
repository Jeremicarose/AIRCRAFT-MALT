# Phase 1 Report

Audit date: 2026-09-14

## Objective

Freeze and explain the current MLAT baseline without changing production MLAT
behavior. The main goals were to identify the exact 300 held-out LocaRDS
transmissions, explain the successful and failed numerical solves, and find out
whether the large error tail is associated with identifiable conditions.

This remains a solver-only diagnostic. It does not validate production ingest,
raw-message correlation, CKB Receiver Registry identity, clock qualification,
storage, API output, or the frontend.

## What I Inspected

- [`docs/mlat/baseline.md`](baseline.md), which freezes the existing headline
  result.
- [`docs/mlat/locards-suitability-audit.md`](locards-suitability-audit.md),
  including its dataset schema, production-contract audit, calibration split,
  and diagnostic metrics.
- `src/mlat_reference/correlation/correlator.py`, including exact-frame
  grouping, integer-nanosecond ordering, the four-receiver rule, and the 5 ms
  production correlation window.
- `src/mlat_reference/ingest/feed_transports.py`, including message,
  timestamp, receiver-identity, and clock-field normalization.
- `src/mlat_reference/base.py` and `src/mlat_reference/runtime.py`, including
  Registry eligibility, observation construction, the clock gate, solving,
  persistence, and receiver attribution.
- `src/mlat_reference/solver/robust.py`, including timestamp validation,
  initialization, Levenberg-Marquardt optimization, result bounds, residuals,
  uncertainty, and quality scoring.
- All MLAT tests, with particular attention to solver precision, correlation,
  production clock rejection, lifecycle propagation, and evidence checks.
- The local LocaRDS v1.0 `subset_1` archive and actual CSV records at
  `/private/tmp/locards-subset-1/subset_1`.
- All repository-tracked files and temporary files matching LocaRDS,
  diagnostic, or baseline names. No original case-level diagnostic output or
  clock-offset artifact was present.

## What I Changed

- Added this report.
- Added `tools/mlat/locards_baseline_analysis.py`. This is a diagnostic-only
  command. It reads LocaRDS, uses a fixed calibration rule, calls the unchanged
  numerical solver, and emits case-level JSON. Production code does not import
  it.
- Added two focused tests in
  `tests/mlat/test_locards_baseline_analysis.py`. They verify that source
  timestamp precision is preserved and that clock fitting estimates only
  relative offsets.

I did not change the correlator, observation model, ingest adapters, runtime,
solver, Registry integration, database, API, or frontend. I did not add a
LocaRDS production adapter.

## Evidence

### Dataset And Experiment

The source is LocaRDS v1.0 `subset_1` from DOI
`10.5281/zenodo.4739276`. The inspected archive MD5 is
`ca2e163f437ff8b9dfaef64bed871ff3`, matching the suitability audit.

The original audit documented this split:

```text
0 <= timeAtServer < 120 seconds   calibration
120 <= timeAtServer < 180 seconds gap
timeAtServer >= 180 seconds       held-out validation
```

Calibration used trusted aircraft and receivers marked `good` by LocaRDS. It
contained 14,006 transmissions and 45,048 good-receiver observations. One
good-receiver timestamp was written as the coarse token `8.7e+10`; the locked
reconstruction records it in the source count but excludes it from clock
fitting. Pair links needed at least ten calibration samples. This left 229
receiver-pair links across 38 receivers.

The diagnostic fits one relative offset per receiver. For each receiver pair,
it takes the median observed-minus-geometric time difference, then weights the
pair equation by the square root of its calibration sample count. This rule is
fixed before validation. It must not be interpreted as a hardware clock-source
attestation or a per-receiver uncertainty bound.

The reconstruction command is:

```bash
PYTHONPATH=src .venv/bin/python tools/mlat/locards_baseline_analysis.py \
  --dataset-dir /private/tmp/locards-subset-1/subset_1 \
  --archive /private/tmp/locards-subset_1.zip \
  --output /private/tmp/locards-baseline-analysis.json
```

The calibration graph has two disconnected components. All 300 validation
cases use 28 receivers from the larger component, so no validation event mixes
receivers whose relative component offset is unknowable.

Validation selects the first 300 dataset rows, in source order, that meet all
of these conditions:

- `timeAtServer >= 180` seconds;
- aircraft is marked `trusted` by LocaRDS;
- at least four observations come from `good` receivers with fitted offsets;
- no selected receiver timestamp uses scientific notation.

The first selected transmission is ID `328455` at server time
`180.009999990463`. The last is ID `342610` at
`187.730999946594`. The ordered ID list has SHA-256
`7e4ef1d017ca80a924da2a716b0bce50c138b5753a8021e2ca36dc3336b08df2`.

The exact 300 transmission IDs are:

```text
328455, 328463, 328658, 328659, 328664, 328670, 328793, 328802,
328827, 328878, 328903, 329018, 329040, 329426, 329518, 329571,
329631, 329650, 329670, 329703, 329734, 329735, 329753, 329836,
329974, 330133, 330172, 330257, 330333, 330374, 330399, 330400,
330485, 330498, 330556, 330586, 330693, 330696, 330706, 330789,
330796, 330803, 330922, 330986, 330987, 331077, 331105, 331182,
331194, 331300, 331330, 331407, 331445, 331461, 331523, 331524,
331528, 331531, 331554, 331565, 331602, 331647, 331707, 331708,
331849, 331875, 331921, 331951, 332146, 332174, 332249, 332299,
332347, 332386, 332390, 332392, 332398, 332400, 332483, 332497,
332558, 332562, 332568, 332605, 332652, 332689, 332708, 333144,
333229, 333241, 333242, 333268, 333274, 333315, 333357, 333358,
333381, 333404, 333471, 333501, 333595, 333601, 333776, 333821,
333841, 333929, 333942, 334044, 334117, 334183, 334214, 334239,
334242, 334245, 334253, 334257, 334304, 334364, 334372, 334406,
334408, 334446, 334449, 334511, 334561, 334764, 334778, 334935,
335150, 335152, 335207, 335278, 335323, 335349, 335357, 335419,
335429, 335514, 335554, 335555, 335612, 335665, 335741, 335873,
335900, 335919, 336014, 336015, 336021, 336032, 336033, 336039,
336123, 336144, 336156, 336164, 336167, 336265, 336282, 336287,
336291, 336318, 336324, 336366, 336432, 336585, 336600, 336757,
336805, 336934, 337081, 337082, 337084, 337097, 337114, 337131,
337156, 337176, 337178, 337179, 337209, 337268, 337287, 337288,
337374, 337531, 337584, 337605, 337675, 337778, 337890, 337900,
337910, 337934, 337946, 337980, 338017, 338046, 338084, 338090,
338115, 338124, 338188, 338190, 338222, 338267, 338386, 338416,
338475, 338516, 338536, 338569, 338581, 338582, 338598, 338599,
338738, 338751, 338760, 338783, 338988, 339026, 339068, 339139,
339151, 339325, 339335, 339466, 339541, 339543, 339652, 339675,
339728, 339738, 339748, 339777, 339788, 339791, 339807, 339858,
339870, 339902, 339944, 339986, 339989, 340008, 340053, 340077,
340109, 340178, 340212, 340296, 340385, 340400, 340433, 340510,
340615, 340675, 340741, 340817, 340841, 340852, 340892, 341142,
341156, 341201, 341237, 341241, 341427, 341434, 341495, 341508,
341526, 341588, 341595, 341643, 341644, 341700, 341701, 341709,
341722, 341735, 341766, 341903, 341960, 342110, 342119, 342150,
342157, 342222, 342248, 342252, 342301, 342315, 342354, 342419,
342450, 342451, 342535, 342610
```

### Frozen Baseline Metrics

These are the previously recorded numbers. They remain the historical frozen
baseline and have not been changed.

| Metric | Uncalibrated | Calibrated frozen baseline |
|---|---:|---:|
| Held-out transmissions | 300 | 300 |
| Receiver observations | 1,483 | 1,483 |
| Successful positions | 78 | 236 |
| Success rate | 26.00% | 78.67% |
| Median horizontal error | 97.452 m | 34.574 m |
| 95th-percentile horizontal error | 38,501.359 m | 572.340 m |
| Median altitude error | 887.311 m | 226.875 m |
| Median 3D error | 1,064.781 m | 234.339 m |
| 95th-percentile 3D error | 40,007.606 m | 3,279.254 m |
| Worst 3D error | 89,889.692 m | 52,792.150 m |

The uncalibrated rejections were 142 optimizer failures, 73 altitude-bound
failures, and seven residual-bound failures. After calibration, all 64
rejections were altitude-bound failures. None were caused by insufficient
receiver count because the selection already required at least four.

### Reproducibility Check

The exact frozen aggregate result cannot be recreated from the repository.
The earlier run did not save:

- its fitted receiver-offset table;
- a complete description of pair weighting;
- its 300 case-level results;
- the exact diagnostic command or environment manifest.

The locked reconstruction uses only the documented calibration period and the
fixed square-root sample weighting described above. It reproduces the same
300 IDs, observation count, receiver-count distribution, uncalibrated median
timing error, and geometry statistics. Its solver result is close but not
identical:

| Metric | Frozen baseline | Locked reconstruction |
|---|---:|---:|
| Successful positions | 236 | 238 |
| Altitude-bound failures | 64 | 62 |
| Median horizontal error | 34.574 m | 32.934 m |
| 95th-percentile horizontal error | 572.340 m | 558.999 m |
| Median 3D error | 234.339 m | 225.466 m |
| 95th-percentile 3D error | 3,279.254 m | 3,256.634 m |
| Worst 3D error | 52,792.150 m | 53,491.955 m |

Reasonable calibration weighting variants produced between 227 and 238
successful positions. Fifty-one failed transmission IDs were common to every
checked variant, while 31 changed between accepted and rejected. The variants
were used only to measure sensitivity; no variant was selected by looking for
the best validation score.

This means the old headline numbers are valid as a recorded historical result,
but they are not a sufficiently complete artifact for exact case-by-case
reproduction. The reconstruction must not silently replace them.

### Timestamp And Clock Findings

All 1,483 selected timestamps are written as integer nanosecond-unit tokens in
the source CSV. None of these 300 cases contains a selected scientific-notation
timestamp. Applying the reconstructed offsets and rounding to the solver's
integer `timestamp_ns` model introduced at most 0.432 ns of representation
rounding.

This does not mean the measurements have sub-nanosecond accuracy. In the frozen
run, known-position TDOA disagreement had these equivalent range errors:

| State | Median | 95th percentile | Maximum |
|---|---:|---:|---:|
| Before calibration | 28,027.876 m | Not recorded | Not recorded |
| After calibration | 27.027 m | 60.271 m | 112.981 m |

The calibrated values correspond to about 90 ns, 201 ns, and 377 ns. The tail
therefore exceeds the production `100 ns` clock-uncertainty threshold. These
are group-level empirical residuals, not per-receiver hardware uncertainty
bounds.

### Receiver Count And Solver Outcome

The exact sample contains 28 unique receivers. Its receiver-count distribution
is 132 four-receiver events, 86 five-receiver events, 57 six-receiver events,
20 seven-receiver events, three eight-receiver events, one nine-receiver event,
and one ten-receiver event.

The following case-level breakdown comes from the locked reconstruction, not
the missing original case artifact:

| Receivers | Cases | Successful | Failed | Success rate | Median horizontal error | Median 3D error |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 132 | 95 | 37 | 72.0% | 77.1 m | 410.8 m |
| 5 | 86 | 66 | 20 | 76.7% | 34.5 m | 201.6 m |
| 6 | 57 | 53 | 4 | 93.0% | 24.5 m | 117.6 m |
| 7 | 20 | 19 | 1 | 95.0% | 21.2 m | 157.5 m |
| 8 | 3 | 3 | 0 | 100.0% | 20.1 m | 171.4 m |
| 9 | 1 | 1 | 0 | 100.0% | 17.3 m | 331.3 m |
| 10 | 1 | 1 | 0 | 100.0% | 13.1 m | 245.4 m |

The small 8–10 receiver groups are too few for a general performance claim.
The larger 4–7 receiver groups do show a clear practical pattern: six or more
receivers are substantially more reliable than the mathematical minimum of
four in this sample.

### Geometry And Error Tail

The geometry condition number is calculated at the ADS-B ground-truth
position. A large number means small timing errors can cause much larger
position errors. This is a diagnostic measure because the true aircraft
position is not available to a live solver before solving.

The condition-number distribution for the exact 300 cases is:

| Statistic | Condition number |
|---|---:|
| Median | 37.307 |
| 95th percentile | 10,230.781 |
| Maximum | 23,114.557 |

Using diagnostic bins in the reconstruction:

- 20 of 30 cases with condition number at least 1,000 were rejected, a 66.7%
  rejection rate.
- 33 of 220 cases below 100 were rejected, a 15.0% rejection rate.
- 13 accepted positions had at least 3 km of 3D error. Eleven used only four
  receivers, 12 had condition number above 100, and 11 were dominated by
  vertical error.
- Only three of those 13 high-error positions had known-position timing
  disagreement of at least 60 m. Timing error contributes, but it does not
  explain the whole tail.

For successful reconstructed positions, the correlation between log geometry
condition and log 3D error is `0.639`. The equivalent value for timing-fit error
is `0.199`. These are associations within this selected sample, not proof of
causation.

### Failure Breakdown

Every reconstructed case reached the numerical optimizer. The 62 rejected
cases all produced a candidate position and were then rejected by the existing
altitude gate:

- 45 candidate altitudes were below `-500 m`;
- 17 were above `15,000 m`;
- 37 failures used four receivers;
- 20 failures had geometry condition number at least 1,000;
- 16 failures recorded their best result at iteration 99 or 100;
- 20 failures nevertheless had solver residual below the nominal `0.01 m`
  convergence threshold.

That last point is important. A small solver residual means the calculated
position fits the supplied TDOA equations. It does not mean the position is
close to the aircraft. With four receivers there are exactly three independent
TDOA equations for three spatial coordinates, so a wrong or vertically
ambiguous solution can still have an almost zero residual.

Likely failure categories are:

| Category | Evidence | Conclusion | Confidence |
|---|---|---|---|
| Insufficient receiver count | Every selected case has 4–10 receivers. | Not a cause in this benchmark. | High |
| Poor geometry | Rejection rises from 15.0% below condition 100 to 66.7% at or above 1,000; the two extreme horizontal errors use condition numbers above 4,500. | A major contributor to failure and the large tail. | High for association; medium for individual causation |
| Altitude or vertical ambiguity | Every frozen rejection and every reconstructed rejection fails the altitude bound; 11 of 13 accepted 3D tail cases are vertically dominated. | The dominant visible failure mode. | High for the symptom; medium for the numerical root cause |
| Solver convergence | Sixteen reconstructed failures reach iteration 99 or 100, but 20 invalid-altitude cases also have residual below 0.01 m. | Slow convergence explains some cases; convergence to the wrong branch explains others. | Medium |
| Timing or clock error | Frozen held-out timing fit reaches 60.271 m at p95 and 112.981 m maximum, while results change under defensible calibration weighting choices. | Material contributor and source of benchmark sensitivity. | High for sensitivity; medium for individual failures |
| Outliers | The published groups contain no raw frame and four-receiver cases have no redundant equation for identifying one bad observation. | Possible, but not separately proven by this diagnostic. | Low |
| Other | Initialization chooses either a linearized estimate for 5+ receivers or a 9 km centroid-based prior for four receivers. The current solver has no explicit alternate-branch search or pre-solve geometry rejection. | Plausible contributor to vertical branch selection. | Medium |

### Representative Cases

These examples come from the locked reconstruction. Errors use LocaRDS
ADS-B ground truth and are not certified radar errors.

| Dataset ID | Outcome | Receivers | Geometry condition | Truth TDOA fit | Iterations | Solver residual | Horizontal error | Vertical error | 3D error |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 333501 | Low-error success | 6 | 27.8 | 7.6 m | 9 | 5.601 m | 3.8 m | 1.9 m | 4.2 m |
| 340212 | Low-horizontal-error success | 5 | 3.9 | 22.6 m | 5 | 1.742 m | 1.5 m | 59.9 m | 59.9 m |
| 339139 | Extreme horizontal tail | 4 | 4,545.3 | 16.8 m | 99 | 5.515 m | 53,305.0 m | 4,468.7 m | 53,492.0 m |
| 330789 | Extreme horizontal tail | 4 | 4,515.3 | 10.9 m | 100 | 0.432 m | 50,606.1 m | 749.7 m | 50,611.6 m |
| 339870 | Vertical tail | 4 | 159.2 | 27.6 m | 29 | 1.341 m | 317.4 m | 10,929.9 m | 10,934.6 m |
| 338124 | Rejected below ground | 5 | 4.3 | 78.2 m | 5 | 23.949 m | Not returned | Not returned | Not returned |

IDs `339139` and `330789` use the same aircraft and the same receiver quartet:
`10`, `147`, `474`, and `632`. Their combination of repeatable receiver
geometry, very large horizontal error, and near-maximum iteration count is
strong evidence that the extreme horizontal tail is concentrated rather than
randomly spread through the sample.

## Tests

The complete MLAT test directory passes:

```text
119 passed
```

This consists of the 117 pre-existing MLAT tests plus two diagnostic-tool
tests. The pre-existing baseline therefore still passes unchanged.

## Findings

1. The exact 300 held-out LocaRDS transmission IDs are now identified.
2. The frozen `236/300` aggregate remains useful as historical evidence, but
   its exact per-case result is not reproducible because the original clock
   offsets and diagnostic output were not preserved.
3. The large error tail is concentrated mainly in four-receiver cases with
   weak 3D geometry. Two extreme horizontal errors repeat the same aircraft
   and receiver quartet.
4. Vertical ambiguity is the dominant visible problem. It appears both as
   altitude-bound rejection and as accepted positions with multi-kilometre
   altitude error.
5. More receivers materially improve this sample. Six-receiver cases have a
   93.0% reconstructed success rate and 24.5 m median horizontal error, compared
   with 72.0% and 77.1 m for four receivers.
6. Solver residual is not a reliable accuracy estimate for minimally
   determined four-receiver cases.
7. Calibration matters enough that its exact algorithm and fitted offsets must
   be versioned before any solver before/after claim is defensible.

## Recommendations

1. Keep `docs/mlat/baseline.md` unchanged as the historical headline baseline.
2. Use the locked diagnostic tool for further case inspection, but label its
   `238/300` output as a reconstruction rather than silently replacing the
   frozen `236/300` result.
3. Before Phase 5 solver work, create an immutable benchmark evidence bundle
   containing the source checksum, tool revision, dependency versions, fitted
   offsets, ordered case IDs, complete case results, and stable checksums.
4. Do not add a LocaRDS production adapter. Its missing raw Mode-S frame and
   production clock attestations remain blocking issues.
5. Do not change the solver yet. Phase 2 should first determine whether a
   source-complete historical extract or legitimate operator feed can exercise
   the real production contract.

## Remaining Risks

- The original frozen diagnostic cannot be reconstructed exactly from saved
  artifacts. This limits precise regression comparison until a complete
  benchmark artifact is approved and frozen.
- LocaRDS ground truth is aircraft-reported ADS-B position, not independent
  certified radar truth.
- LocaRDS `good` and `trusted` flags were produced using the dataset authors'
  wider quality process. The time split prevents direct coordinate tuning on
  the validation interval, but those source labels are not fully blind.
- The geometry condition number in this report uses ground truth. A live
  quality gate would need a geometry measure calculated from a candidate
  solution or another method that does not know truth in advance.
- Calibration residuals do not provide the production clock-source evidence
  or per-receiver `clock_uncertainty_ns <= 100` attestation.
- Case sensitivity to calibration means individual root-cause labels remain
  probabilistic unless the original offset artifact is recovered.
- No result here validates raw-message correlation, CKB identity, lifecycle
  state, a live receiver feed, or end-to-end production MLAT.

## Decision

**CONDITIONAL GO**

Phase 1 is complete enough to proceed to data-source validation. The condition
is that the frozen aggregate and the reproducible reconstruction remain
separately labeled. Neither may be presented as full production-pipeline
validation, and solver improvement claims must wait for a newly frozen,
complete case-level artifact.

## Recommended Next Phase

After approval, begin **Phase 2 - Data Source Validation**. The first action
should be to determine whether LocaRDS/OpenSky maintainers can legitimately
provide the original Mode-S frames and defensible receiver clock metadata for
the published observation groups.

STOP HERE AND WAIT FOR USER APPROVAL.
