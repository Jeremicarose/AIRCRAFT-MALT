# Readsb / Dump1090 Beast To JSONL Mapping

## Recommended first real source

The **best first real source** to connect to this project is:

- **readsb** or **dump1090-fa**
- using the **Beast TCP output**
- one receiver adapter per physical receiver

This is the best first source because it preserves the thing MLAT actually needs:

- **per-message timing**

It is better than using already-decoded aircraft state feeds because those feeds are too late in the pipeline and do not preserve the raw observation semantics you need for multilateration.

---

## Why Beast output is the right first source

For MLAT, the system needs:

- one observation per receiver
- one timestamp per observation
- one raw Mode-S frame per observation

Beast-format receiver output is a much better fit than:

- aggregated aircraft JSON
- SBS/BaseStation aircraft state feeds
- map-level tracking feeds

Those formats are useful for display, but they are not the right first source for MLAT solving.

---

## Exact JSONL contract for this project

The MLAT runtime expects newline-delimited JSON records that normalize to:

```json
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123456,"message":"8D4840D6202CC371C32CE0576098"}
```

This is the **minimum valid contract**.

### Required fields

- `receiver_id`
  - canonical receiver identifier
  - should match the receiver identity used in your CKB registry

- `timestamp`
  - floating-point Unix epoch seconds
  - UTC
  - must be as close as possible to the true receive time

- `message`
  - uppercase hex Mode-S frame
  - no spaces
  - no separators
  - one observation = one frame

---

## Preferred richer JSONL contract

The runtime currently only requires `receiver_id`, `timestamp`, and `message`, but for future debugging and quality analysis, the adapter should emit a richer shape like this:

```json
{
  "receiver_id": "RECV_NYC_001",
  "timestamp": 1714400000.123456,
  "message": "8D4840D6202CC371C32CE0576098",
  "signal_strength": -21.4,
  "source": "readsb-beast",
  "observed_at": "2026-06-18T12:00:00.123456Z",
  "metadata": {
    "beast_host": "127.0.0.1",
    "beast_port": 30005,
    "receiver_clock": "system-ntp",
    "adapter_version": "v1"
  }
}
```

### Why emit extra fields?

Because later you will likely want:

- timestamp quality analysis
- per-receiver debugging
- source provenance
- signal-quality comparisons

The current bridge adapter ignores extra fields safely, so you do not pay a compatibility penalty for including them now.

---

## Mapping from Beast decoder output

Your source-specific Beast decoder/adapter should transform each decoded Beast frame into one JSONL line.

### Beast-side input conceptually contains

- raw Mode-S frame bytes
- receive timestamp / tick value
- optional signal level

### Bridge-side output must contain

- `message` = decoded raw frame hex
- `timestamp` = normalized wall-clock Unix epoch seconds
- `receiver_id` = canonical receiver id for that physical station

---

## Canonical field mapping

### 1. `receiver_id`

#### Rule

This must identify the physical receiver that observed the message.

#### Best practice

Assign one adapter process per receiver and inject:

```text
RECV_NYC_001
RECV_BOS_001
RECV_PHL_001
RECV_DC_001
```

If the upstream source does not provide a receiver id, use:

```bash
python3 scripts/bridge_adapter.py --source ... --default-receiver-id RECV_NYC_001
```

If the upstream source uses local aliases, use:

```json
{
  "readsb-local-nyc": "RECV_NYC_001",
  "readsb-local-bos": "RECV_BOS_001"
}
```

with:

```bash
python3 scripts/bridge_adapter.py --receiver-map receiver_map.json ...
```

### 2. `timestamp`

#### Rule

This must represent **receive time**, not processing time.

#### Required semantics

- float Unix epoch seconds
- UTC
- ideally derived from the Beast timing source plus local clock correlation

#### Acceptable fallback

If the adapter cannot yet reconstruct high-quality receive time from Beast timing, it may temporarily use:

- adapter receipt time

but this should be treated as a quality limitation, not final production behavior.

#### Good example

```json
"timestamp": 1714400000.123456
```

### 3. `message`

#### Rule

Use the full Mode-S / ADS-B frame as uppercase hex.

#### Good example

```json
"message": "8D4840D6202CC371C32CE0576098"
```

#### Bad examples

- lowercase hex
- whitespace
- decoded aircraft state instead of the original frame
- partial frame

---

## What NOT to send

Do **not** send:

- already-solved aircraft positions
- SBS/BaseStation aircraft-state rows
- map-oriented aggregated track objects
- one record containing multiple aircraft observations
- one record containing multiple frames

The runtime wants:

> one receiver, one timestamp, one raw frame, one JSON line

---

## Recommended adapter architecture

### Per receiver

Run one source adapter per receiver:

```text
readsb/dump1090 Beast output
  -> source-specific Beast decoder
  -> JSONL line emitter
  -> bridge_adapter.py (optional normalization)
  -> mlat-processor command-jsonl input
```

### Why per receiver?

Because it keeps:

- receiver identity clear
- timing provenance clearer
- debugging easier
- mapping simpler

---

## Two implementation modes

### Mode A: source adapter emits canonical JSONL directly

Best long-term approach:

```json
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123456,"message":"8D4840D6202CC371C32CE0576098"}
```

In this mode, `bridge_adapter.py` is optional.

### Mode B: source adapter emits near-canonical JSON and bridge_adapter normalizes it

Example source adapter output:

```json
{"sensor_id":"readsb-local-nyc","time":"2026-06-18T12:00:00.123456Z","hex":"8D4840D6202CC371C32CE0576098"}
```

Then run:

```bash
python3 scripts/bridge_adapter.py \
  --source subprocess \
  --command 'python3 your_beast_decoder.py' \
  --receiver-map receiver_map.json
```

This is the easiest first real integration pattern.

---

## Best first practical implementation

The best first real integration to build next is:

### A Beast decoder subprocess that emits:

```json
{"sensor_id":"readsb-local-nyc","time":"2026-06-18T12:00:00.123456Z","hex":"8D4840D6202CC371C32CE0576098"}
```

Then normalize through:

```bash
python3 scripts/bridge_adapter.py \
  --source subprocess \
  --command 'python3 your_beast_decoder.py' \
  --receiver-map receiver_map.json
```

That is the most practical first non-simulation live path for this project.

## Repo-native skeleton now available

The repo now includes:

- [scripts/beast_tcp_adapter.py](../scripts/beast_tcp_adapter.py)
- [scripts/multi_receiver_beast_bridge.py](../scripts/multi_receiver_beast_bridge.py)

Example usage:

```bash
python3 scripts/beast_tcp_adapter.py \
  --host 127.0.0.1 \
  --port 30005 \
  --receiver-id RECV_NYC_001
```

Or with mapping:

```bash
python3 scripts/beast_tcp_adapter.py \
  --host 127.0.0.1 \
  --port 30005 \
  --sensor-id raw-nyc \
  --receiver-map receiver_map.json
```

## Multi-receiver launch path

If you have multiple local Beast feeds, use the bundled multiplexing wrapper:

```bash
python3 scripts/multi_receiver_beast_bridge.py \
  --config docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json
```

Then point the runtime at:

```bash
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND='python3 scripts/multi_receiver_beast_bridge.py --config docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json'
```

This is the shortest path to feeding multiple real receivers into the current runtime.

---

## Benchmarking implication

Once you use Beast-derived real observations instead of replay output:

- the resulting positions become candidate real benchmark data
- `benchmarkable_output` can become meaningful
- OpenSky comparison becomes worth interpreting

Until then, replay/simulation output remains useful only for:

- UI validation
- storage validation
- workflow validation

not for real-world quality claims.
