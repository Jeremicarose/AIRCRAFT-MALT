# Benchmark Data Format

Use newline-delimited JSON files when comparing MLAT output against a trusted
reference source.

## MLAT export format

Each line should contain:

```json
{
  "aircraft_id": "A1B2C3",
  "timestamp": 1710000000.0,
  "latitude": 40.75,
  "longitude": -73.85,
  "altitude": 9000.0,
  "uncertainty": 120.5,
  "quality_score": 0.82,
  "solver_method": "robust_mlat",
  "receiver_count": 4,
  "receiver_ids": ["RECV_NYC_001", "RECV_BOS_001", "RECV_PHL_001", "RECV_DC_001"],
  "created_at": "2026-07-16T12:00:00.125000"
}
```

## Reference export format

Each line should contain:

```json
{
  "aircraft_id": "A1B2C3",
  "timestamp": 1710000000.0,
  "latitude": 40.751,
  "longitude": -73.849,
  "altitude": 9050.0
}
```

## Comparison script

Use:

```bash
python3 scripts/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output benchmark/mlat.jsonl \
  --seconds 86400

python3 scripts/fetch_opensky_reference.py \
  --output benchmark/reference.jsonl \
  --time 1710000000 \
  --lamin 40.0 \
  --lomin -75.0 \
  --lamax 41.5 \
  --lomax -73.0

python3 scripts/benchmark_mlat_against_reference.py \
  --mlat benchmark/mlat.jsonl \
  --reference benchmark/reference.jsonl \
  --runtime-snapshot benchmark/readiness.json \
  --reference-source OpenSky \
  --region "Northeast corridor" \
  --data-provenance live \
  --output benchmark/latest.json
```

This will output:

- matched record count
- coverage ratio
- median horizontal error
- p95 horizontal error
- median altitude error
- p95 altitude error
- median and p95 end-to-store freshness
- timestamped runtime freshness/reliability snapshot
- input SHA-256 hashes and explicit provenance limitations

Matching is one-to-one: a reference point cannot be reused for several MLAT
points. This prevents inflated coverage ratios.

## Export fields included from the MLAT DB

The benchmark exporter writes:

- `aircraft_id`
- `timestamp`
- `latitude`
- `longitude`
- `altitude`
- `uncertainty`
- `quality_score`
- `quality_bucket`
- `solver_residual_m`
- `receiver_count`
- `receiver_ids`
- `solver_method`
- `correlation_time_span_s`
- `created_at`

## OpenSky authentication

For proper historical benchmarking against OpenSky, use OAuth2 client credentials:

- `OPENSKY_CLIENT_ID`
- `OPENSKY_CLIENT_SECRET`

The fetch script also supports `--anonymous`, but anonymous mode is only appropriate for
recent-current snapshots and comes with OpenSky time/rate limitations.
