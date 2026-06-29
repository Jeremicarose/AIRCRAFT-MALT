# Multi-Receiver Beast Runtime

This file gives the exact runtime config and commands for running
`mlat-processor` against multiple real Beast-format receiver feeds.

Use this when you have:

- multiple `readsb` / `dump1090-fa` instances
- Beast TCP output available per receiver
- canonical receiver IDs already chosen

---

## 1. Receiver config

Use:

- [docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json](./MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json)

Copy it to a local runtime file and edit host/port values:

```bash
cp docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json beast_receivers.local.json
```

Example:

```json
{
  "receivers": [
    {
      "receiver_id": "RECV_NYC_001",
      "sensor_id": "raw-nyc",
      "host": "127.0.0.1",
      "port": 30005
    },
    {
      "receiver_id": "RECV_BOS_001",
      "sensor_id": "raw-bos",
      "host": "127.0.0.1",
      "port": 30006
    },
    {
      "receiver_id": "RECV_PHL_001",
      "sensor_id": "raw-phl",
      "host": "127.0.0.1",
      "port": 30007
    },
    {
      "receiver_id": "RECV_DC_001",
      "sensor_id": "raw-dc",
      "host": "127.0.0.1",
      "port": 30008
    }
  ]
}
```

---

## 2. Required env settings

Set the runtime away from simulation:

```bash
export FOURDSKY_TRANSPORT=command-jsonl
export FOURDSKY_BRIDGE_COMMAND="python3 scripts/multi_receiver_beast_bridge.py --config beast_receivers.local.json"
export SIMULATE_IF_UNAVAILABLE=false
export REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
```

Keep your CKB registry settings too:

```bash
export CKB_NETWORK=testnet
export CKB_RPC_URL=https://testnet.ckb.dev/rpc
export CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
export RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_DEPLOYED_TYPE_HASH
```

---

## 3. Exact processor command

Run:

```bash
FOURDSKY_TRANSPORT=command-jsonl \
FOURDSKY_BRIDGE_COMMAND="python3 scripts/multi_receiver_beast_bridge.py --config beast_receivers.local.json" \
SIMULATE_IF_UNAVAILABLE=false \
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true \
mlat-processor
```

If you want to keep using values from `.env`, update only:

```env
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND=python3 scripts/multi_receiver_beast_bridge.py --config beast_receivers.local.json
SIMULATE_IF_UNAVAILABLE=false
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
```

Then run:

```bash
mlat-processor
```

---

## 4. What success looks like

In the logs, you should stop seeing:

- `Simulated aircraft A1B2C3`
- `Simulated aircraft D4E5F6`

And instead start seeing real aircraft hex-derived identifiers from real observations.

The system should also report:

- real signal ingest continuing
- active receivers discovered
- no simulation warning

---

## 5. Runtime checks

After starting the processor, check:

```bash
curl http://localhost:5051/api/health
curl http://localhost:5051/api/readiness
curl http://localhost:5051/api/positions/recent?seconds=300&limit=20
```

What you want to see:

- `signal_fresh: true`
- `synthetic_feed_mode: false`
- `benchmarkable_output: true`

If `synthetic_feed_mode` is still `true`, you are not on the live path yet.

---

## 6. Benchmark readiness check

Once real aircraft positions are appearing in the DB, export them:

```bash
python3 scripts/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output benchmark/mlat.jsonl \
  --seconds 3600
```

Then inspect the file:

```bash
head benchmark/mlat.jsonl
```

If you still see:

- `A1B2C3`
- `D4E5F6`

then you are still benchmarking replay output, not real traffic.

If you see real aircraft identifiers, the benchmark path is now meaningful.

---

## 7. Common failure cases

### No positions appear

Possible causes:

- Beast ports not reachable
- too few live receivers
- incorrect receiver IDs/config
- source adapters not producing valid frames

### Benchmarkability stays false

Possible causes:

- still using simulation transport
- still ingesting replay output
- bridge command not switched

### Real feed but weak solves

Possible causes:

- timestamp quality not good enough
- poor receiver geometry
- insufficient synchronized receivers

---

## 8. Recommended next check after startup

Run:

```bash
sqlite3 data/mlat_data.db "select aircraft_id, timestamp, latitude, longitude from positions order by timestamp desc limit 10;"
```

That is the fastest way to confirm whether the DB is now receiving:

- real live aircraft output

instead of:

- replay aircraft output
