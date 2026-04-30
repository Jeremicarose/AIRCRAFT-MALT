# Integration Guide: Connecting to CKB and 4DSky

This guide shows how the project is intended to integrate with its real external systems:

1. **CKB (Nervos Network)** for decentralized receiver discovery
2. **4DSky** for live Mode-S data streaming

If you need the contract and registry details, read [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md) alongside this file.

## 🎯 Overview

The active runtime now expects a CKB-backed receiver registry. The Python entrypoints load configuration from environment variables and then:

1. Initialize CKB discovery
2. Fetch receiver metadata from the on-chain registry
3. Select MLAT-capable receivers
4. Start the 4DSky data feed
5. Correlate and solve positions

For local development, the code can fall back to simulated receivers and a simulated 4DSky feed when `SIMULATE_IF_UNAVAILABLE=true`.

## 📋 Prerequisites

- CKB RPC endpoint
- Receiver registry type hash
- Optional CKB private key if you want to register receivers
- 4DSky API credentials when you replace the simulated feed

## 🔧 Step 1: Configure CKB Discovery

Set the CKB environment variables:

```bash
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_HASH
SIMULATE_IF_UNAVAILABLE=false
```

The active discovery code lives in:

- `src/network/ckb_discovery.py`
- `src/network/ckb_client.py`

The processor entrypoint loads this config in `src/production_main.py`.

## 🔧 Step 2: Register or Discover Receivers

The intended production flow is:

1. Deploy the receiver registry contract
2. Register receiver metadata on CKB
3. Query registry cells through the CKB RPC API
4. Parse receiver coordinates and capabilities
5. Hand the resulting receiver list to the MLAT pipeline

The current code already supports:

- Reading `RECEIVER_REGISTRY_TYPE_HASH`
- Querying a CKB node when the SDK and RPC are available
- Falling back to a deterministic local receiver set when not available

## 🔧 Step 3: Connect a Real 4DSky Feed

The network client now supports these feed modes in `src/network/ckb_client.py`:

- `simulation`: local generated feed
- `websocket-json`: connect to a websocket that emits JSON records
- `command-jsonl`: run a local bridge process that prints newline-delimited JSON
- `auto`: choose a real feed when configured, otherwise fall back to simulation

### Option A: Direct WebSocket JSON Feed

Use this when 4DSky or your bridge gives you a websocket endpoint:

```bash
FOURDSKY_TRANSPORT=websocket-json
FOURDSKYENDPOINT=wss://your-feed-endpoint
FOURDSKYAPIKEY=your_api_key_here
FOURDSKY_AUTH_HEADER=X-API-Key
FOURDSKY_AUTH_SCHEME=
FOURDSKY_SUBSCRIBE_MESSAGE=
```

Accepted inbound JSON shapes include records like:

```json
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123,"message":"8D4840D6202CC371C32CE0576098"}
```

### Option B: Local ADEX / Bridge Process

Use this when the 4DSky client or your own bridge can output JSON lines to stdout:

```bash
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND='python bridge.py'
```

Each output line should look like:

```json
{"receiver_id":"RECV_NYC_001","timestamp":"2026-04-29T12:00:00Z","message":"8D4840D6202CC371C32CE0576098"}
```

### Optional Receiver-Level Metadata

If you want the receiver registry to carry stream metadata too, `src/network/ckb_discovery.py` now supports these optional fields in the stored receiver JSON:

- `stream_endpoint`
- `stream_protocol`
- `stream_format`
- `metadata`

That lets you publish per-receiver stream connection details alongside location and capability data.

## 🚀 Step 4: Run the System

Local run:

```bash
pip install -r requirements.txt
cp .env.example .env
mlat-api
mlat-processor
```

Docker run:

```bash
cp .env.example .env
docker-compose up -d
```

## 📊 Validation Checklist

- `RECEIVER_REGISTRY_TYPE_HASH` points to the deployed registry contract
- CKB RPC endpoint is reachable
- At least 4 MLAT-capable receivers are discoverable
- 4DSky delivers synchronized timestamps
- Processor logs show correlated groups and solved positions
- API returns recent positions at `/api/positions/recent`

## 🔒 Security Notes

- Do not commit private keys
- Store secrets in environment variables or a secret manager
- Restrict access to the CKB RPC endpoint where possible
- Protect any admin API endpoints before public deployment

## 📚 Related Docs

- [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
