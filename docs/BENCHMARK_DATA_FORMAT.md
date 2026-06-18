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
  "quality_score": 0.82
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
  --reference benchmark/reference.jsonl
```

This will output:

- matched record count
- coverage ratio
- median horizontal error
- p95 horizontal error
- median altitude error
- p95 altitude error

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

## OpenSky authentication

For proper historical benchmarking against OpenSky, use OAuth2 client credentials:

- `OPENSKY_CLIENT_ID`
- `OPENSKY_CLIENT_SECRET`

The fetch script also supports `--anonymous`, but anonymous mode is only appropriate for
recent-current snapshots and comes with OpenSky time/rate limitations.
