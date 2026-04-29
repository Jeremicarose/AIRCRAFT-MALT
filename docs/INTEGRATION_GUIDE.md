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

## 🔧 Step 3: Replace the Simulated 4DSky Feed

The network client currently simulates a shared 4DSky feed so the MLAT pipeline can run locally. To connect the real SDK, replace the simulated stream path in `src/network/ckb_client.py`.

Your real implementation should:

1. Authenticate with 4DSky
2. Subscribe to the selected receivers
3. Forward `receiver_id`, `timestamp`, and `message` to the callback used by the processor
4. Preserve precise timestamps so TDOA remains valid

Required environment variables:

```bash
FOURDSKYAPIKEY=your_api_key_here
FOURDSKYENDPOINT=wss://api.4dsky.com/stream
```

## 🚀 Step 4: Run the System

Local run:

```bash
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src python src/api/rest_api.py
PYTHONPATH=src python src/production_main.py
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
