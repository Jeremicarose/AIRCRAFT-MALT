# MLAT Reference Benchmarking

## Deterministic Regression

Run:

```bash
python3 tools/mlat/run_reproducible_benchmark.py
python3 tools/mlat/run_reproducible_benchmark.py --verify-only
```

Inputs are under `reference/mlat/benchmarks/fixtures`; the generated package is
`evidence/mlat-reference/reproducible-benchmark-v2`.

This path validates benchmark code and artifact reproducibility. The fixture is
synthetic and the output must remain `evidence_status=pipeline_only` with
`benchmarkable=false`.

## Live Benchmark Input

MLAT JSONL requires:

```json
{
  "aircraft_id": "A1B2C3",
  "timestamp": 1710000000.25,
  "latitude": 40.75,
  "longitude": -73.85,
  "altitude": 9000.0,
  "quality_score": 0.82,
  "solver_method": "robust_mlat",
  "receiver_count": 4
}
```

Reference JSONL requires aircraft identity, timestamp, latitude, longitude, and
altitude from an identified trusted source.

Export and compare:

```bash
python3 tools/mlat/export_positions_for_benchmark.py \
  --db data/mlat_live.db \
  --output /tmp/mlat-live.jsonl

python3 tools/mlat/benchmark_mlat_against_reference.py \
  --mlat /tmp/mlat-live.jsonl \
  --reference /tmp/reference.jsonl \
  --runtime-snapshot /tmp/readiness.json \
  --reference-source OpenSky \
  --region "declared region" \
  --data-provenance live \
  --output /tmp/accuracy.json
```

The matcher uses nearest timestamps with one-to-one assignment inside the
configured tolerance. A report is publishable only when source, region, live
provenance, runtime readiness, and non-synthetic solver fields pass.

## Complete Capture

```bash
python3 tools/mlat/capture_grant_evidence.py \
  --db data/mlat_live.db \
  --receiver-config receiver-clocks.local.json \
  --preflight-report logs/live-preflight.json \
  --raw-observations logs/field-trial-raw.jsonl \
  --reference /tmp/reference.jsonl \
  --reference-source OpenSky \
  --region "declared region"
```

Despite the historical script name, this is an evidence capture tool, not proof
of grant readiness. It fails closed unless strict live gates pass, unless
`--allow-non-live` is explicitly used; non-live output is labeled validation
only.

The capture fails unless the saved launch preflight passed, the receiver config
still matches its clock-evidence hashes, and every exported position links to a
four-receiver raw transmission. A publishable bundle must also come from a
clean Git commit.

Verify the bundle offline and independently run the solver again from its raw
arrival timestamps and captured registry geometry:

```bash
python3 tools/mlat/verify_live_evidence.py \
  --bundle evidence/mlat-reference/live/captures/<RUN_ID> \
  --require-publishable
```

## Current Limitation

No live benchmark package exists in this repository. Experimental simulation
performance and reliability captures are not valid substitutes.
