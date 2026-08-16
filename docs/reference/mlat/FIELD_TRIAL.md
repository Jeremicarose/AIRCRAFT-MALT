# Physical Four-Receiver Field Trial

This runbook defines the minimum evidence-capable MLAT trial. It does not treat
network arrival time, replay tracks, screenshots, or operator assertions as
proof of synchronized multilateration.

## Acceptance Gate

Do not start the evidence window until all of these are true:

- at least four physical receivers observe overlapping 1090 MHz coverage
- each receiver exports raw Beast frames with its native 48-bit counter
- each counter is measured against a common qualified timebase
- each clock uncertainty is no greater than `MAX_CLOCK_UNCERTAINTY_NS`
- all four immutable identities are active Registry V2 cells on CKB testnet
- registry coordinates match the measured receiver survey
- the repository is on a clean, published commit
- a time-aligned independent aircraft-position reference is available

Four receivers are the mathematical minimum, not a geometry recommendation.
Five or six well-spaced receivers provide a materially stronger trial and make
outlier detection possible.

## 1. Clock Qualification

Create one non-empty calibration artifact per receiver. It should state:

- receiver immutable identity and hardware serial number
- timing source and oscillator/GPSDO model
- qualification method and equipment
- measurement start/end in UTC
- measured offset, drift, jitter, and uncertainty
- operator and raw log references

Hash each artifact:

```bash
shasum -a 256 clock-evidence/*.json
```

The receiver config `clock.evidence.sha256` must match the corresponding file.
The config validity interval must be bounded by the measurement, oscillator
holdover, and observed drift. It must not be extended simply to pass preflight.

## 2. Registry And Geometry

Create or update one active Registry V2 identity for every physical receiver.
Use surveyed latitude, longitude, and antenna altitude. Record the accepted
transaction hash and confirm discovery through the application API:

```bash
curl http://127.0.0.1:5057/api/receivers
```

The `identity_id` values returned by discovery must exactly match the four or
more `receiver_id` values in `receiver-clocks.local.json`. Human receiver labels
are not identities.

## 3. Run-Scoped Paths

Choose a unique run ID and new paths. Do not append a new trial to old raw data:

```bash
export RUN_ID=YYYYMMDDTHHMMSSZ
export MLAT_RECEIVER_CONFIG=receiver-clocks.local.json
export MLAT_RAW_OBSERVATION_LOG="logs/${RUN_ID}-raw-observations.jsonl"
export LIVE_PREFLIGHT_REPORT="logs/${RUN_ID}-preflight.json"
export DATABASE_PATH="data/${RUN_ID}.db"
export FOURDSKY_TRANSPORT=command-jsonl
export FOURDSKY_BRIDGE_COMMAND="python3 tools/mlat/multi_receiver_beast_bridge.py --config ${MLAT_RECEIVER_CONFIG} --audit-log ${MLAT_RAW_OBSERVATION_LOG}"
export FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED=true
export STRICT_PRODUCTION_MODE=true
export SIMULATE_IF_UNAVAILABLE=false
export REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
```

The command transport uses argument parsing, not a shell. Expand variables in
the exported command as shown; do not put literal `${...}` values in `.env`.

## 4. Preflight

Run the same strict gate used by `run-live.sh`:

```bash
python3 tools/mlat/check_live_ingest_readiness.py \
  --receiver-config "$MLAT_RECEIVER_CONFIG" \
  --require-ready \
  --output "$LIVE_PREFLIGHT_REPORT"
```

`ready_for_evidence_run` must be `true`. The report checks:

- strict runtime flags
- the deployed Registry V2 code hash format
- the exact bridge/config/raw-log path relationship
- four unique non-placeholder identities, sensors, and endpoints
- current clock validity and qualification artifact hashes
- reachability of every Beast endpoint
- live CKB discovery of every configured immutable identity
- a new or empty raw observation log

This validates launch inputs. It cannot independently verify that a timing
instrument or receiver is truthful.

## 5. Start And Observe

Start the runtime:

```bash
./run-live.sh
```

In another terminal, require all runtime gates to remain healthy:

```bash
curl http://127.0.0.1:5057/api/system/mode
curl http://127.0.0.1:5057/api/pipeline
curl http://127.0.0.1:5057/api/readiness
curl http://127.0.0.1:5057/api/receivers
```

Stop the run if receiver count drops below four, clock-qualified receiver count
drops below four, registry discovery is not live, or simulation mode appears.
The multi-receiver bridge reconnects failed endpoints and logs connection state
to stderr, but a reconnecting receiver does not make a three-receiver interval
valid evidence.

## 6. Independent Reference

Collect a trusted position reference covering the same region and UTC window.
Preserve provider identity, query/export method, timestamps, and raw response.
Normalize the result to JSONL only after retaining the source artifact.

Do not use aircraft positions decoded from the same replay source as both MLAT
output and reference. ADS-B position broadcasts may be used as an identified
comparison source, but they must not enter the MLAT solver path.

## 7. Capture

After a statistically useful window, create an immutable bundle:

```bash
python3 tools/mlat/capture_grant_evidence.py \
  --api-base http://127.0.0.1:5057 \
  --db "$DATABASE_PATH" \
  --receiver-config "$MLAT_RECEIVER_CONFIG" \
  --preflight-report "$LIVE_PREFLIGHT_REPORT" \
  --raw-observations "$MLAT_RAW_OBSERVATION_LOG" \
  --reference /path/to/aligned-reference.jsonl \
  --reference-source "provider and dataset" \
  --region "declared coverage area" \
  --seconds 3600 \
  --reliability-seconds 1800 \
  --reliability-interval 5 \
  --output-dir "evidence/mlat-reference/live/captures/${RUN_ID}"
```

Without `--allow-non-live`, capture fails and removes the incomplete bundle when
any live, raw-input, clock, registry, or position-linkage gate fails.

## 8. Offline Verification

Run from a clean checkout of the manifest commit:

```bash
python3 tools/mlat/verify_live_evidence.py \
  --bundle "evidence/mlat-reference/live/captures/${RUN_ID}" \
  --require-publishable \
  --output "evidence/mlat-reference/live/captures/${RUN_ID}/verification-report.json"
```

The verifier checks every artifact hash, raw observation qualification,
four-receiver correlation, clock artifact mapping, clean source provenance, and
position-to-input linkage. It then runs the solver again using only bundled raw
arrival timestamps and bundled registry geometry, comparing every result with
the stored position.

## 9. Publish

Publish together:

- repository commit and CI run
- complete evidence bundle and checksum-bearing manifest
- verification report
- CKB type hash and active receiver transaction/out-point references
- hardware layout and coverage map
- clock qualification method and limitations
- benchmark sample count, time window, match rate, median, and p95 error
- unedited setup/run video showing hardware and clocks

Screenshots and video improve reviewer comprehension. The hashed raw bundle and
offline re-solve are the technical evidence.
