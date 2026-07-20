# Grant Evidence Runbook

This runbook produces the evidence needed to describe the project as a
decentralized receiver registry and aviation data control plane with measured
MLAT output. It does not treat replay or synthetic output as live proof.

## Evidence produced

A complete run establishes this sequence:

```text
CKB receiver cell
  -> type-hash discovery
  -> live receiver observations
  -> correlation and robust MLAT solve
  -> SQLite position with receiver and solver provenance
  -> public API and dashboard
  -> hashed external benchmark report
```

The final report includes one-to-one reference matches, accuracy, end-to-store
freshness, a timestamped runtime reliability snapshot, provenance labels, and
SHA-256 hashes for every input.

## Physical prerequisites

- four or more receivers observing the same Mode-S transmissions
- synchronized receiver timestamps suitable for TDOA/MLAT
- each receiver registered under its canonical ID on CKB testnet
- one Beast TCP endpoint per receiver, or an equivalent JSONL bridge
- a trusted reference feed such as OpenSky

Four unsynchronized TCP arrival times do not constitute valid MLAT timing data.

## 1. Register and discover receivers

Generate a canonical record for each receiver:

```bash
python3 scripts/generate_receiver_registry_record.py \
  --receiver-id RECV_NYC_001 \
  --latitude 40.7128 \
  --longitude -74.0060 \
  --altitude 10 \
  --capability mode-s \
  --capability mlat \
  --stream-protocol beast-tcp \
  --stream-format beast
```

Generate the transaction template and funded command sequence:

```bash
python3 scripts/generate_receiver_registration_tx_template.py \
  --lock-arg 0xYOUR_LOCK_ARG \
  --type-hash 0xYOUR_DEPLOYED_TYPE_HASH

python3 scripts/print_receiver_registration_commands.py \
  --address ckt1YOUR_DEPLOYER_ADDRESS
```

After sending the transactions, configure `.env`:

```env
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_DEPLOYED_TYPE_HASH
SIMULATE_IF_UNAVAILABLE=false
```

## 2. Connect live observations

Create `beast_receivers.local.json` from the example and set one canonical CKB
receiver ID per endpoint:

```bash
cp docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json beast_receivers.local.json
```

Set the runtime to fail closed instead of falling back to simulation:

```env
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND=python3 scripts/multi_receiver_beast_bridge.py --config beast_receivers.local.json
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
DATABASE_PATH=data/mlat_data.db
BENCHMARK_REPORT_PATH=benchmark/latest.json
```

Check the machine before starting:

```bash
STRICT_PRODUCTION_MODE=true \
SIMULATE_IF_UNAVAILABLE=false \
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true \
python3 scripts/check_live_ingest_readiness.py --require-ready
```

Both `ready_for_real_live_ingest` and `ready_for_evidence_run` must be `true`.
For a verified remote source that cannot be probed locally, explicitly set
`FOURDSKY_EXTERNAL_SOURCE_ATTESTED=true`.

## 3. Run the vertical slice

Start the processor and API as one fail-closed service:

```bash
./run-live.sh
```

Verify all public surfaces:

```bash
curl http://localhost:5000/api/system/mode
curl http://localhost:5000/api/receivers
curl http://localhost:5000/api/positions/recent?seconds=300\&limit=20
curl http://localhost:5000/api/readiness
curl http://localhost:5000/api/pipeline
```

Do not continue unless:

- the registry type hash is present
- at least four canonical receivers are visible
- `synthetic_feed_mode` is `false`
- recent positions use a real ICAO aircraft ID and `robust_mlat`
- `benchmarkable_output` is `true`

## 4. Capture the benchmark window

Capture readiness while the receiver network and processor are running:

```bash
curl http://localhost:5000/api/readiness -o benchmark/readiness.json
```

Export a short matching position window:

```bash
python3 scripts/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output benchmark/mlat-live.jsonl \
  --seconds 300
```

Fetch a current OpenSky reference snapshot for the same bounds immediately:

```bash
python3 scripts/fetch_opensky_reference.py \
  --anonymous \
  --output benchmark/reference-opensky.jsonl \
  --lamin 38.55 \
  --lomin -79.2 \
  --lamax 43.25 \
  --lomax -70.6
```

For a publication-quality repeated-window run, use authenticated historical
OpenSky access and capture multiple aligned windows.

## 5. Generate and publish evidence

The preferred path captures the complete bundle and publishes the stable API
artifacts in one command:

```bash
python3 scripts/capture_grant_evidence.py \
  --api-base http://127.0.0.1:5000 \
  --db data/mlat_live.db \
  --reference benchmark/reference-opensky.jsonl \
  --reference-source OpenSky \
  --region "Northeast corridor" \
  --reliability-seconds 300
```

This command fails before capture unless every CKB registration, discovery,
ingest, correlation, solve, storage, API, and dashboard stage reports `pass`.
It writes a timestamped directory under `benchmark/captures/` and hashes every
artifact in `manifest.json`.

The manual accuracy-only command remains useful for debugging:

Only use `--data-provenance live` after the live gates in step 3 pass:

```bash
python3 scripts/benchmark_mlat_against_reference.py \
  --mlat benchmark/mlat-live.jsonl \
  --reference benchmark/reference-opensky.jsonl \
  --runtime-snapshot benchmark/readiness.json \
  --reference-source OpenSky \
  --region "Northeast corridor" \
  --data-provenance live \
  --output benchmark/latest.json
```

Confirm the report says `evidence_status: publishable`. If it says
`pipeline_only`, read `provenance.limitations` and fix those conditions rather
than relabeling the data.

The report is then public at:

```text
GET /api/benchmark/latest
```

It is also rendered on:

```text
/app/analytics.html
```

The complete pipeline is rendered at `/app/pipeline.html` and exposed at
`/api/pipeline`.

## 6. Grant-ready evidence bundle

Archive these together for each published run:

- transaction hashes for the receiver cells
- receiver registry type hash
- `benchmark/mlat-live.jsonl`
- `benchmark/reference-opensky.jsonl`
- `benchmark/readiness.json`
- `benchmark/latest.json`
- `benchmark/performance-latest.json`
- `benchmark/reliability-latest.json`
- `benchmark/captures/<timestamp>/manifest.json`
- the software commit hash
- the exact receiver clock/synchronization method

The JSON report hashes its three data inputs, making later changes detectable.

## Record the evidence demo

Use [GRANT_DEMO_SCRIPT.md](GRANT_DEMO_SCRIPT.md). The five-minute recording is
ordered around proof: CKB identity, live observation movement, MLAT output,
storage/API delivery, then measured evidence. Never splice replay footage into
a recording labeled live.

## Current machine status

As of 2026-07-17, the repository is configured for `command-jsonl`, `readsb` is
installed, and live output is required. No RTL-SDR was detected and no local
Beast endpoint was reachable. A receiver or remote Beast source is still needed
before this runbook can produce honest live evidence.
