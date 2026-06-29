# Integration Guide

This guide explains how to connect external infrastructure to MLAT Airspace Console after you understand the product surfaces and output model.

Read this guide after:

- [README.md](../README.md) for product framing
- [GETTING_STARTED.md](GETTING_STARTED.md) for local setup
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture and runtime flow

If you need contract and registry details, also read [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md).

## Integration goal

The integration goal is not just to ingest data. It is to produce usable, explainable aircraft outputs with:

- receiver-backed positioning
- normalized quality metadata
- operational freshness visibility
- API and stream delivery surfaces

## Integration layers

1. **Receiver identity and discovery**
   - CKB-backed registry workflows can provide receiver metadata and ownership context.
2. **Observation ingress**
   - 4DSky or another compatible bridge can feed receiver observations into the runtime.
3. **MLAT processing**
   - the runtime correlates signals and solves aircraft positions.
4. **Delivery**
   - the API, dashboard, and WebSocket surfaces expose the resulting product.

## Current behavior

For local development, the code can use simulated receivers and simulated feed traffic when `SIMULATE_IF_UNAVAILABLE=true`.

That allows you to validate:

- API behavior
- dashboard behavior
- quality metadata
- health and statistics endpoints
- commercial controls

before wiring live infrastructure.

## Step 1: Configure receiver discovery

Set the CKB-related environment variables when using registry-backed discovery:

```bash
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_HASH
SIMULATE_IF_UNAVAILABLE=false
```

Relevant code lives in:

- `src/network/ckb_discovery.py`
- `src/network/ckb_client.py`
- `src/production_main.py`

### What CKB is doing here

In this system, CKB is intended to support:

- receiver identity
- receiver metadata discovery
- registry-style ownership workflows

It is **not** the main store for aircraft telemetry or the primary product surface.

## Step 2: Provide receiver metadata

The runtime needs enough receiver metadata to localize aircraft reliably.

At minimum that means:

- receiver identifier
- latitude
- longitude
- altitude
- MLAT-relevant capability metadata

The intended flow is:

1. deploy or identify the receiver registry contract
2. register receiver metadata
3. query registry cells through RPC or indexer access
4. parse receiver coordinates and capabilities
5. hand the resulting receiver set to the MLAT runtime

## Step 3: Connect a feed source

The client supports multiple feed modes in `src/network/ckb_client.py`:

- `simulation`
- `websocket-json`
- `command-jsonl`
- `auto`

### Option A: WebSocket JSON feed

```bash
FOURDSKY_TRANSPORT=websocket-json
FOURDSKYENDPOINT=wss://your-feed-endpoint
FOURDSKYAPIKEY=your_api_key_here
FOURDSKY_AUTH_HEADER=X-API-Key
FOURDSKY_AUTH_SCHEME=
FOURDSKY_SUBSCRIBE_MESSAGE=
```

Accepted records include shapes like:

```json
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123,"message":"8D4840D6202CC371C32CE0576098"}
```

### Option B: Local bridge process

```bash
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND='python3 scripts/bridge_adapter.py --source stdin'
```

Each line should look like:

```json
{"receiver_id":"RECV_NYC_001","timestamp":"2026-04-29T12:00:00Z","message":"8D4840D6202CC371C32CE0576098"}
```

You can validate the bridge interface immediately with:

```bash
python3 scripts/sample_live_bridge.py --once
```

That proves the transport path and payload shape. Replace it with a real
decoder, 4DSky bridge, or local ingest adapter when you are ready for actual
live aircraft output.

### Stronger local bridge adapter

For a reusable bridge process, use:

```bash
python3 scripts/bridge_adapter.py --source stdin
python3 scripts/bridge_adapter.py --source tcp --tcp-host 127.0.0.1 --tcp-port 5001
python3 scripts/bridge_adapter.py --source unix --unix-path /tmp/aircraft.sock
python3 scripts/bridge_adapter.py --source subprocess --command 'python3 your_source.py'
```

Optional receiver-id mapping:

```bash
python3 scripts/bridge_adapter.py \
  --source stdin \
  --receiver-map receiver_map.json \
  --default-receiver-id RECV_NYC_001
```

### Multi-receiver Beast bridge

If you have several local Beast endpoints, use:

```bash
python3 scripts/multi_receiver_beast_bridge.py \
  --config docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json
```

## Step 4: Validate derived outputs

After integration, validate the product rather than only the transport.

Check:

- `/api/positions/recent` returns recent positions
- payloads include `quality`, `solver`, and `correlation` objects
- `/api/health` reports runtime and freshness details
- `/api/statistics` behaves according to plan access
- dashboard selection flows explain estimates clearly

## Step 5: Validate access tiers

If you are enabling commercial behavior, also validate:

- public/demo API keys remain limited
- premium keys can access deeper history or premium metrics
- live-stream entitlements are required where expected
- usage events are recorded for billable or tracked resources

## Local run

```bash
pip install -r requirements.txt
cp .env.example .env
mlat-api
mlat-processor
```

## Validation checklist

- registry endpoint is reachable if using CKB-backed discovery
- at least 4 MLAT-capable receivers are discoverable
- timestamps are synchronized enough for useful MLAT solves
- API returns recent positions and health data
- dashboard shows aircraft, receivers, and quality-oriented context
- access-tier behavior matches plan expectations

## Security notes

- do not commit private keys
- store secrets in environment variables or a secret manager
- restrict admin access and secret-bearing endpoints
- treat registry credentials and feed credentials as separate concerns

## Related docs

- [README.md](../README.md)
- [GETTING_STARTED.md](GETTING_STARTED.md)
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md)
