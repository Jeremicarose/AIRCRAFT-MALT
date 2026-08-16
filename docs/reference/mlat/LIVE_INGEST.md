# Multi-Receiver Beast Runtime

This file gives the exact runtime config and commands for running
`mlat-processor` against multiple real Beast-format receiver feeds.

For an evidence-capable physical deployment, follow
[Physical Four-Receiver Field Trial](./FIELD_TRIAL.md) end to end.

Use this when you have:

- multiple `readsb` / `dump1090-fa` instances
- Beast TCP output available per receiver
- canonical receiver IDs already chosen

---

## 1. Receiver config

Use:

- [`reference/mlat/config/beast-receivers.example.json`](../../../reference/mlat/config/beast-receivers.example.json)

Copy it to a local runtime file and edit host/port values:

```bash
cp reference/mlat/config/beast-receivers.example.json receiver-clocks.local.json
```

Example:

```json
{
  "receivers": [
    {
      "receiver_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
      "sensor_id": "raw-nyc",
      "host": "127.0.0.1",
      "port": 30005,
      "clock": {
        "enabled": true,
        "source": "gpsdo-nyc",
        "frequency_hz": 12000000,
        "anchor_tick": 123456,
        "anchor_time_ns": 1714400000123456789,
        "uncertainty_ns": 50,
        "valid_from_ns": 1714400000000000000,
        "valid_until_ns": 1714403600000000000,
        "evidence": {
          "method": "gpsdo-1pps-calibration",
          "file": "clock-evidence/raw-nyc.json",
          "sha256": "replace-with-the-file-sha256"
        }
      }
    }
  ]
}
```

The abbreviated object above shows the required fields for one receiver. The
actual file must contain at least four receivers with unique identities, sensor
IDs, and host/port pairs. The repository example contains four deliberately
disabled placeholders and therefore cannot pass the strict preflight.

Every receiver needs its own qualified `clock` block. The anchor maps one
48-bit Beast counter value to common UTC nanoseconds. Generate the anchor from
the receiver's GPS-disciplined clock or another measured synchronization
system, refresh it often enough to bound drift, and set `uncertainty_ns` from
measurement rather than guesswork. Leaving `enabled` false is safe for packet
inspection, but those observations cannot enter an MLAT solve.

`valid_from_ns` and `valid_until_ns` bound the interval for which the measured
calibration is defensible. Strict startup rejects a stale or future window. Do
not extend the interval merely to pass preflight; derive it from oscillator
holdover and drift measurements. The bridge can inspect an unqualified feed
with `--diagnostic`, but that mode is not evidence-capable.

Every strict clock entry must also identify its qualification method and a
non-empty calibration log or report. `sha256` must match that file. Relative
paths are resolved from the receiver config directory. This pins the operator's
timing evidence; it does not independently validate the measurement method.

For live Registry V2 operation, `receiver_id` is the immutable 32-byte CKB type
argument, not the human Receiver Label. Replace every example identity with the
actual value discovered from its registered cell.

---

## 2. Required env settings

Set the runtime away from simulation:

```bash
export FOURDSKY_TRANSPORT=command-jsonl
export FOURDSKY_BRIDGE_COMMAND="python3 tools/mlat/multi_receiver_beast_bridge.py --config receiver-clocks.local.json --audit-log logs/field-trial-raw.jsonl"
export MLAT_RECEIVER_CONFIG=receiver-clocks.local.json
export MLAT_RAW_OBSERVATION_LOG=logs/field-trial-raw.jsonl
export SIMULATE_IF_UNAVAILABLE=false
export REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
export FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED=true
export MAX_CLOCK_UNCERTAINTY_NS=100
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
FOURDSKY_BRIDGE_COMMAND="python3 tools/mlat/multi_receiver_beast_bridge.py --config receiver-clocks.local.json --audit-log logs/field-trial-raw.jsonl" \
MLAT_RECEIVER_CONFIG=receiver-clocks.local.json \
MLAT_RAW_OBSERVATION_LOG=logs/field-trial-raw.jsonl \
SIMULATE_IF_UNAVAILABLE=false \
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true \
mlat-processor
```

If you want to keep using values from `.env`, update only:

```env
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND=python3 tools/mlat/multi_receiver_beast_bridge.py --config receiver-clocks.local.json --audit-log logs/field-trial-raw.jsonl
MLAT_RECEIVER_CONFIG=receiver-clocks.local.json
MLAT_RAW_OBSERVATION_LOG=logs/field-trial-raw.jsonl
SIMULATE_IF_UNAVAILABLE=false
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED=true
MAX_CLOCK_UNCERTAINTY_NS=100
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
- at least four clock-qualified receivers
- no continuing increase in `clock_rejected_groups`

---

## 5. Runtime checks

After starting the processor, check:

```bash
curl http://localhost:5057/api/health
curl http://localhost:5057/api/readiness
curl 'http://localhost:5057/api/positions/recent?seconds=300&limit=20'
```

What you want to see:

- `signal_fresh: true`
- `synthetic_feed_mode: false`
- `benchmarkable_output: true`
- `dimensions.clock.ready: true`

If `synthetic_feed_mode` is still `true`, you are not on the live path yet.

---

## 6. Benchmark readiness check

Once real aircraft positions are appearing in the DB, export them:

```bash
python3 tools/mlat/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output /tmp/mlat-live.jsonl \
  --seconds 3600
```

Then inspect the file:

```bash
head /tmp/mlat-live.jsonl
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
- fewer than four receivers with qualified common-clock timestamps

### Benchmarkability stays false

Possible causes:

- still using simulation transport
- still ingesting replay output
- bridge command not switched
- observations marked `clock_synchronized: false`

### Real feed but weak solves

Possible causes:

- timestamp quality not good enough
- poor receiver geometry
- insufficient synchronized receivers

Network or adapter arrival time is not a synchronization mechanism. The bridge
emits such records for diagnostics with `clock_synchronized: false`, and the
runtime deliberately rejects their correlated groups.

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
