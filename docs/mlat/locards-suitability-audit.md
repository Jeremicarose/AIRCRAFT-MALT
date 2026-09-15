# LocaRDS Suitability Audit

Audit date: 2026-09-14

Scope: AIRCRAFT-MALT production MLAT input, correlation, clock qualification,
numerical solving, persistence, and display. The inspected dataset is official
LocaRDS version 1.0 `subset_1.zip` from Zenodo DOI
[`10.5281/zenodo.4739276`](https://doi.org/10.5281/zenodo.4739276).

## 1. Executive Finding

**LocaRDS is a NO-GO for validating the complete, unchanged production MLAT
pipeline.** It cannot supply several fields that the production path requires:

- The raw Mode-S frame used by the correlator as message identity is absent.
- Its pseudonymous sensor serials are not CKB Receiver Identities.
- It has no production receiver lifecycle status or capability declarations.
- It has no per-observation `clock_source` or numeric
  `clock_uncertainty_ns` value.
- The `good` sensor flag must not be translated into
  `clock_synchronized=true` or `clock_uncertainty_ns <= 100`.

LocaRDS does contain legitimate **decoded, pre-grouped receiver observations**.
Those observations can support a narrower, scientifically useful study of the
existing numerical solver after documented clock-offset calibration. That is
not equivalent to validating the current correlator, runtime clock gate,
Registry discovery, or complete production pipeline.

No adapter was implemented. Doing so now would require either bypassing the
correlator or putting a non-frame value into its `message` field.

## 2. Current MLAT Input Contract

The implemented production path is:

```text
JSON/JSONL or Beast bridge
  -> RawSignal
  -> exact-message correlation
  -> runtime receiver and clock qualification
  -> SignalObservation
  -> RobustMLATSolver
  -> database/API/frontend
```

The contract below comes from the code, not from a proposed dataset format.

| Field | Required? | Meaning | Where enforced | Precision/constraints |
|---|---|---|---|---|
| `receiver_id` | Yes throughout | Stable routing identity for one receiver | `base.py:99`, `correlator.py:232`, `robust.py:201`; live Beast config requires a Registry V2 identity | Unique within a solve; live identity is normalized `0x` plus 64 hex characters |
| `timestamp` | Yes in the data models | Wall/display time and buffer/freshness time | `RawSignal`, `SignalObservation`, `base.py:110-121`, `robust.py:205` | Float seconds; group span must be at most 100 ms in the solver |
| `timestamp_ns` | Yes for production; optional only for isolated solver tests | Arrival time on a comparable receiver timebase | `feed_transports.py:137`, `robust.py:162-190`, `runtime.py:351` | Positive integer at ingest; every observation must have it; integer subtraction occurs before conversion to seconds |
| `message` | Yes for production correlation | Complete Mode-S frame represented as hex | Normalizer drops records without it at `feed_transports.py:134`; correlator groups on it at `correlator.py:145-147` | Must be identical across receivers; effective production window is 5 ms; code does not currently validate length, CRC, or hex syntax |
| `clock_synchronized` | Yes in production | Assertion that the arrival timestamp is on a qualified common timebase | `runtime.py:348-355` | Must be exactly `true`; the JSON normalizer also requires `timestamp_ns` |
| `clock_source` | Yes in production | Name of the measured synchronization/calibration source | `runtime.py:352`; strict Beast validation in `receiver_config.py:82-85` | Cannot be empty, `unknown`, `network-arrival`, or a configured placeholder |
| `clock_uncertainty_ns` | Yes in production | Declared error bound for receiver timing | `feed_transports.py:159-161`, `runtime.py:353-354`, `receiver_config.py:98-104` | Finite, non-negative, and at most 100 ns by default |
| Receiver latitude | Yes for solver | Antenna latitude used to build ECEF position | Registry record validation and `runtime.py:275-281` | Finite and between -90 and 90 degrees |
| Receiver longitude | Yes for solver | Antenna longitude used to build ECEF position | Registry record validation and `runtime.py:275-281` | Finite and between -180 and 180 degrees |
| Receiver altitude | Yes for solver | Antenna height used in ECEF conversion | Registry record validation and `robust.py:24-35` | Registry accepts -500 to 20,000 metres |
| Receiver status | Yes for production discovery | Registry lifecycle state | `record.py:205-211`, `discovery.py:391-403`, `client.py:134` | Runtime MLAT selection requires `online` |
| Receiver capabilities | Yes for production discovery | Declared receiver functions | `record.py:212-222`, `discovery.py:405-411`, `client.py:134` | Registry requires `mode-s`; runtime selection additionally requires `mlat` |
| Signal strength | No | Optional correlation-quality input | `correlator.py:19`, `correlator.py:246-264` | The current base runtime sets it to `0.0`, so live RSSI is discarded |

Component-specific requirements:

- **Correlator:** `receiver_id`, `timestamp` or `timestamp_ns`, and identical
  `message`; at least four unique receivers within the configured 5 ms window.
- **Numerical solver:** four unique receiver IDs, receiver latitude/longitude/
  altitude, comparable arrival times, and a required but unused `signal_data`
  string. It does not decode or inspect the frame.
- **Runtime:** an active discovered receiver, at least four observations, and
  all three clock-qualification fields. It hard-codes four receivers for both
  correlation and solving.
- **UI/display:** consumes solved position, float result timestamp, quality,
  residual, receiver count, and contributor IDs. It does not consume raw
  frames or receiver arrival timestamps.

The numerical solver accepts small relative float times for mathematical
tests, but it rejects Unix-epoch floats without integer `timestamp_ns` because
epoch floats cannot reliably preserve MLAT-scale differences. Production uses
integer nanoseconds and subtracts them before conversion to seconds.

## 3. LocaRDS Dataset Structure

The archive is not checked into this repository. It was inspected at
`/tmp/locards-subset_1.zip`. Its MD5 was
`ca2e163f437ff8b9dfaef64bed871ff3`, which matches the official Zenodo record.

| File | Actual format and schema | Actual rows including header |
|---|---|---:|
| `set_1.csv` | CSV: `id,timeAtServer,aircraft,latitude,longitude,baroAltitude,geoAltitude,numMeasurements,measurements` | 6,457,543 |
| `set_1_sensors.csv` | CSV: `serial,latitude,longitude,height,type,good` | 717 |
| `set_1_aircraft.csv` | CSV: `aircraft,trusted` | 2,930 |
| `LICENSE.txt` | Creative Commons Attribution-ShareAlike 4.0 text | 427 lines |

The main file has 6,457,542 transmission rows containing 28,234,130 receiver
observations. The sensor file lists 716 sensors; 318 appear in the main file.
It marks 45 sensors as `good`. The aircraft file lists 2,929 pseudonymous
aircraft, of which 206 are marked `trusted`.

An actual main-file record is:

```text
id=272
timeAtServer=0.0820000171661377
aircraft=1424
latitude=50.4795684814453
longitude=7.03681544253701
baroAltitude=11582.4
geoAltitude=11452.86
numMeasurements=10
```

Five of its measurement triples refer to `good` sensors:

```text
[247,1045452484,50]
[398,1045352062,102]
[550,1045042557,49]
[414,1045398378,31]
[134,1045243734,83]
```

Each triple is `[sensor serial, receiver timestamp, RSSI]`. For example, sensor
247 is directly described as latitude `51.486576`, longitude `7.597741`, height
`146.599701`, type `Radarcape`, and `good=TRUE`. Aircraft 1424 is directly
marked `trusted=TRUE`.

This is category **B: decoded, pre-grouped receiver observations**. It is not:

- category A, because the published CSV does not contain the raw Mode-S frame;
- category C, because the measurement triples are receiver-level inputs rather
  than already-solved MLAT positions; or
- only category D, although each row also contains an ADS-B aircraft-reported
  position that can be used as ground truth.

The row relationship is legitimate and direct. The LocaRDS authors state that
they grouped receptions belonging to the same transmission using the original
continuous timestamps and signal payload during dataset preparation. The
published dataset retains that group as `id` plus `measurements`, but removes
the payload itself.

## 4. Field-by-Field Mapping

| Our field | LocaRDS field | Classification | Exact transformation | Confidence |
|---|---|---|---|---|
| Production `receiver_id` | `measurements[][0]` -> `sensors.serial` | **INCOMPATIBLE** for production; **DIRECT** for solver-only work | Preserve the serial as a dataset-local string for solver attribution. It cannot be transformed into a CKB Receiver Identity. | High |
| `timestamp` | `timeAtServer` or receiver timestamp | **INCOMPATIBLE** for live freshness; **DERIVABLE** for offline relative time | For solver-only work, derive a small relative float from the receiver timestamps. `timeAtServer` is relative server time and includes network delay, so it is not TDOA input or Unix wall time. | High |
| `timestamp_ns` | `measurements[][1]` | **CONDITIONALLY DERIVABLE** | Parse the published decimal exactly, reject visibly coarse values, apply a separately fitted clock offset, then round to the nearest integer ns because the current model cannot store fractional ns. The rounding loses at most 0.5 ns and does not improve source accuracy. | High for unit; conditional for comparability |
| `message` | None | **MISSING** | No legitimate transformation. `id` is a dataset transmission-group ID, not a Mode-S frame. | High |
| `clock_synchronized` | No matching field; `sensors.good` is related quality metadata | **MISSING** for production | Do not map `good=TRUE` to this field. A benchmark may describe observations as offset-calibrated, but that is not the production attestation. | High |
| `clock_source` | `sensors.type` | **MISSING** | Hardware type is not a clock source or calibration method. | High |
| `clock_uncertainty_ns` | None | **MISSING** | Calibration residuals can be reported as empirical benchmark statistics, but they are not a supplied per-receiver hardware uncertainty and cannot be declared as `<=100`. | High |
| Receiver latitude | `sensors.latitude` | **DIRECT** | Parse as a finite decimal degree value. | High |
| Receiver longitude | `sensors.longitude` | **DIRECT** | Parse as a finite decimal degree value. | High |
| Receiver altitude | `sensors.height` | **DIRECT** | Parse as metres. | High |
| Receiver status | None | **MISSING** | Historical participation in a row is not a Registry lifecycle status. | High |
| Receiver capabilities | None | **MISSING** | Receiving a historical ADS-B report must not be converted into the Registry declarations `mode-s` and `mlat`. | High |
| Signal strength | `measurements[][2]` | **DIRECT**, optional | Preserve the numeric RSSI with its dataset-defined unknown reference. Current runtime does not pass it through. | High |
| Observation relationship | One `set_1.csv` row and its `measurements` array | **DIRECT** | Preserve the published group. Do not re-infer or merge groups. | High |
| Ground truth | Main-row `latitude`, `longitude`, `geoAltitude`; `aircraft.trusted` | **DIRECT** for scoring | Use only as calibration input in the training interval or as scoring truth in the held-out interval, never both for one event. | High with documented quality limitation |

## 5. Timestamp Analysis

The LocaRDS paper describes each receiver timestamp as a continuous timestamp
in nanoseconds since the beginning of the recording. It also warns that sensor
clocks have different resolutions, offsets, drift, and failure modes. The unit
is nanoseconds; the accuracy is not automatically one nanosecond.

Actual subset 1 values confirm this:

- 15,428,677 timestamps are serialized as integers.
- 12,805,453 are serialized with fractional nanoseconds, commonly repeating
  fractions produced by counter-frequency conversion.
- 2,053 timestamps in 2,051 events use scientific notation such as
  `7.1702e+10`. Those tokens do not retain enough decimal digits to claim
  nanosecond precision.
- 83 of those scientific-notation observations belong to `good` sensors.
- Nine otherwise eligible `4+ good receiver + trusted aircraft` events contain
  one of those values and must be rejected rather than expanded into invented
  nanosecond digits.

The current integer observation model can represent ordinary decimal LocaRDS
timestamps by exact decimal parsing followed by disclosed nearest-nanosecond
rounding. This is a representation conversion only. It must not be described
as improving the underlying receiver clock.

The receiver timestamps are not directly comparable, even among `good`
receivers. In the held-out diagnostic described below, the known aircraft
positions disagreed with uncalibrated TDOA by a median equivalent range of
28,027.876 m. This corresponds to receiver-specific timing offsets on the
order of tens of microseconds, far above the production 100 ns limit.

The `good` flag is narrower than the production contract. The authors define
it as true only when the receiver timestamps did not drift over the one-hour
recording and the sensor location could be jointly verified from those
timestamps. It does not supply a zero clock offset, clock-source name, or
numeric per-receiver uncertainty.

## 6. Clock Synchronization and Calibration Analysis

Clock-offset calibration is legitimate for a solver-only LocaRDS experiment.
It is also the method described by the dataset authors. For receivers `i` and
`j` observing a trusted ADS-B position `p`, the pair bias can be estimated from:

```text
bias(i) - bias(j)
  = observed_time(i) - observed_time(j)
  - (distance(p, receiver_i) - distance(p, receiver_j)) / speed_of_light
```

The audit used this separation:

- Calibration: trusted ADS-B rows in server-time interval `[0, 120)` seconds.
- Gap: `[120, 180)` seconds.
- Validation: 300 eligible transmissions beginning at 180 seconds.
- Validation aircraft positions were used only after solving to calculate
  error. They were not used to fit receiver offsets or calculate positions.
- Only `good` sensors were considered, and visibly coarse scientific-notation
  timestamps were excluded.

Calibration used 14,006 transmissions, 45,048 receiver observations, 38
receivers, and 229 observed receiver-pair links. The clock-difference matrix
had rank 36 for 38 receivers, indicating two connected timing components. A
common additive time offset inside each component is unobservable but cancels
from TDOA.

The fitted pair model had absolute consistency residuals of:

| Statistic | Residual |
|---|---:|
| Median | 30.889 ns |
| 95th percentile | 148.833 ns |
| Maximum | 254.137 ns |

On the held-out events, known-position TDOA fit improved from a median
28,027.876 m before calibration to 27.027 m after calibration. The calibrated
95th percentile was 60.271 m and the maximum was 112.981 m. In equivalent
time, these are approximately 90 ns, 201 ns, and 377 ns.

This calibration is scientifically defensible when reported as empirical,
dataset-specific preprocessing. It is **not** enough to populate the live
runtime's `clock_uncertainty_ns` field:

- The statistics are pair/group residuals, not a measured bound for each
  physical receiver clock.
- The 95th percentile exceeds the production 100 ns threshold.
- Hardware, cable, decoder, and synchronization-source evidence is absent.
- The dataset's `good` and `trusted` flags were created by the dataset authors'
  own whole-dataset quality process. They are useful source metadata, but this
  is not a fully blind hardware qualification.

## 7. Receiver Geometry Analysis

The 45 `good` receivers cover:

- Latitude: 37.171374 to 53.469921 degrees.
- Longitude: -9.354864 to 16.371110 degrees.
- Height: 10.984 to 1,577.347 m.

This wide network provides many overlapping observations, but individual
aircraft events often see receivers on one side of the aircraft or nearly in
one plane. For the 300-event held-out sample, the condition number of the
TDOA geometry matrix was:

| Statistic | Condition number |
|---|---:|
| Median | 37.307 |
| 95th percentile | 10,230.781 |
| Maximum | 23,114.557 |

Larger values mean timing errors are amplified more strongly. The current
solver calculates a geometry-related uncertainty after solving, but it does
not reject poor geometry before accepting a position. This contributes to
unstable altitude and large tail errors in the diagnostic.

## 8. Multi-Receiver Coverage

Full-file streaming validation produced:

| Measure | Count |
|---|---:|
| Receiver observations | 28,234,130 |
| Grouped transmissions | 6,457,542 |
| Events with exactly 2 receivers | 1,970,472 |
| Events with exactly 3 receivers | 1,356,043 |
| Events with 4 or more receivers | 3,131,027 |
| Events with 4 or more `good` receivers | 396,426 |
| Events with 4 or more `good` receivers and trusted aircraft | 128,248 |
| Same after excluding the 9 affected coarse-timestamp events | 128,239 |
| Maximum receivers on any event | 30 |
| Maximum `good` receivers on any event | 12 |

Every declared `numMeasurements` value matched the parsed array. No event had
a duplicate receiver serial, and every observation referenced an existing
sensor metadata record.

These counts prove that four-receiver numerical experiments are available.
They do not establish production eligibility. In particular, a correlator
success rate cannot be measured because the original raw messages have been
removed and the events are already grouped.

## 9. Licensing and Terms

The archive contains the full Creative Commons Attribution-ShareAlike 4.0
International licence. The accompanying paper also states that LocaRDS is
released under CC BY-SA.

Under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/):

- Research and commercial use are permitted.
- Sharing and adaptation are permitted.
- Attribution, a licence link, and an indication of changes are required.
- Adapted material that is shared must use the same licence.
- Additional restrictions cannot be imposed on recipients' licensed rights.

There is no dataset-specific non-commercial restriction in the inspected
licence. A publication should cite the creators, title, version 1.0, DOI
`10.5281/zenodo.4739276`, and the accompanying
[LocaRDS paper](https://arxiv.org/abs/2012.00116). If transformed rows,
calibration data, or benchmark fixtures are redistributed, the attribution and
ShareAlike obligations must travel with them.

The official archive was downloaded through Zenodo's public dataset page. No
authentication, access control, rate limit, or download restriction was
bypassed.

## 10. GO / CONDITIONAL GO / NO-GO Decision

### Decision: NO-GO for the current production pipeline

The decision follows directly from the production contract:

| Blocking issue | Why preprocessing cannot legitimately fill it |
|---|---|
| Raw `message` missing | The dataset row ID proves a grouping relationship but is not the Mode-S frame required by the correlator and aircraft-ID extraction. |
| CKB Receiver Identity missing | Sensor serials are intentionally pseudonymous dataset identifiers. Creating CKB-looking IDs would manufacture identity. |
| `clock_source` missing | Sensor hardware type is not a synchronization source or calibration record. |
| `clock_uncertainty_ns` missing | Empirical pair residuals do not provide the required per-receiver uncertainty bound, and observed tails exceed 100 ns. |
| `clock_synchronized` missing | The `good` flag establishes no drift plus jointly verified location, not the runtime's common-clock assertion. |
| Status and capabilities missing | Historical observation presence cannot be substituted for Registry lifecycle state or declared capabilities. |
| Live wall timestamp missing | `timeAtServer` is relative recording time with network delay, not a current Unix timestamp suitable for runtime freshness checks. |

LocaRDS is conditionally useful for the numerical solver alone, but that
narrower statement does not change the overall decision. It cannot exercise
the actual production ingress, correlator, clock gate, Registry path, or
aircraft-ID output without fabricating or changing required semantics.

Because the decision is NO-GO, this audit does not design or implement the
requested `LocaRDS -> adapter -> existing correlator -> existing solver`
benchmark. That exact path is not legitimate with the published files.

## 11. Evidence Supporting the Decision

The production JSON normalizer was given an actual LocaRDS receiver serial and
timestamp without adding a message. It returned no records, as required by
`feed_transports.py:134`. Supplying `id=272` as `message` would make the record
pass syntactically but would falsely label a dataset row ID as a Mode-S frame.

A separate diagnostic exercised only `RobustMLATSolver`. It used:

- Actual LocaRDS sensor serials as dataset-local solver IDs.
- Actual receiver latitude, longitude, and height.
- Actual published receiver timestamps, with disclosed nearest-nanosecond
  rounding after calibration.
- An empty `signal_data` string because the solver never reads it.
- No correlator, production clock gate, Registry identities, database, API, or
  frontend.

The unchanged solver produced this limited baseline:

| Metric | Uncalibrated | Calibrated |
|---|---:|---:|
| Validation transmissions | 300 | 300 |
| Receiver observations | 1,483 | 1,483 |
| Successful solver returns | 78 | 236 |
| Solver success rate | 26.00% | 78.67% |
| Median horizontal error | 97.452 m | 34.574 m |
| 95th percentile horizontal error | 38,501.359 m | 572.340 m |
| Median altitude error | 887.311 m | 226.875 m |
| Median 3D error | 1,064.781 m | 234.339 m |
| 95th percentile 3D error | 40,007.606 m | 3,279.254 m |
| Maximum 3D error | 89,889.692 m | 52,792.150 m |
| Median solve runtime | 19.351 ms | 3.652 ms |

Uncalibrated failures were 142 optimizer failures, 73 altitude-bound failures,
and 7 residual-bound failures. After calibration, all 64 rejected events
failed the altitude bound. The calibrated receiver-count distribution was 132
events with four receivers, 86 with five, 57 with six, 20 with seven, and five
with eight to ten receivers.

This is evidence that LocaRDS can reveal real solver weaknesses. It is not
evidence that the complete MLAT pipeline works, and the large tail errors do
not support a production-accuracy claim.

After the audit, the unchanged repository MLAT suite completed with 117 tests
passing. No production implementation or validation rule was changed.

## 12. Recommended Next Step

Request a source-complete research extract from the LocaRDS/OpenSky maintainers
before writing an adapter. The request should require, for the same observation
groups:

1. The original complete Mode-S frame for every transmission.
2. The existing pseudonymous receiver serial and antenna coordinates.
3. The original per-receiver arrival timestamp and documented counter unit.
4. Receiver clock source, calibration method, offset/drift model, validity
   window, and a defensible per-receiver uncertainty estimate.
5. Written confirmation that the extract may be used and that derived benchmark
   evidence may be published under specified terms.

CKB identities, online status, and `mode-s`/`mlat` capabilities would still need
to come from actual participating operators. They cannot be reconstructed from
the historical LocaRDS serials.

If that complete extract is unavailable, the legitimate alternative is a
recorded multi-receiver Beast capture from at least four cooperating operators,
with receiver-specific clock calibration evidence and coordinates.

## 13. Risks and Limitations

- The ground truth is an aircraft-reported ADS-B position, not independent
  certified radar truth. The `trusted` flag improves confidence but does not
  change its source.
- The dataset authors' `good` and `trusted` flags rely on their own validation
  process, so selecting them is a documented quality filter rather than a blind
  external test.
- Opportunistic clock calibration assumes receiver location accuracy, trusted
  aircraft position, stable offsets, line-of-sight propagation, and stable
  hardware delay between calibration and validation.
- Pairwise empirical timing residuals cannot be re-labelled as hardware clock
  uncertainty.
- Poor receiver geometry creates severe altitude instability and large error
  tails in the current solver.
- Using only `good` sensors selects a higher-quality subset and must not be
  presented as performance across all crowdsourced receivers.
- Pseudonymous LocaRDS sensor IDs cannot demonstrate CKB ownership or lifecycle.
- The temporary inspected archive is outside version control. Any future audit
  must verify its DOI, version, checksum, and licence again.
- No dataset-specific parsing tests were added because implementation is not
  justified under the NO-GO decision. Existing production validation remains
  unchanged.

DECISION:
**NO-GO**

NEXT ACTION:
**Ask the LocaRDS/OpenSky maintainers for a source-complete extract containing
the original raw Mode-S frame and defensible per-receiver clock calibration and
uncertainty metadata for the published observation groups.**
