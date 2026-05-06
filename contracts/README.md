# Receiver Registry Smart Contract for CKB

This project standardizes the receiver registry around a **canonical JSON cell-data schema**.

## Design

The intended separation is:

- **State**: receiver registry records live in CKB cell data
- **Logic**: the receiver-registry type script validates record contents
- **Ownership**: the cell lock script controls who may update the record
- **Application**: the Python MLAT system reads validated records off-chain

## Canonical Receiver Registry Schema

Each receiver cell stores UTF-8 JSON with this shape:

```json
{
  "receiver_id": "RECV_NYC_001",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "altitude": 10.0,
  "status": "online",
  "capabilities": ["mode-s", "adsb", "mlat"],
  "timestamp": 1704067200.0,
  "stream_endpoint": "wss://feed.example/ws",
  "stream_protocol": "websocket-json",
  "stream_format": "json",
  "metadata": {
    "region": "nyc"
  }
}
```

Required fields:

- `receiver_id`
- `latitude`
- `longitude`
- `altitude`
- `status`
- `capabilities`
- `timestamp`

Optional fields:

- `stream_endpoint`
- `stream_protocol`
- `stream_format`
- `metadata`

## Validation Rules

The off-chain implementation currently enforces:

- `receiver_id` must be non-empty
- `latitude` must be between `-90` and `90`
- `longitude` must be between `-180` and `180`
- `altitude` must be between `-500` and `20000`
- `status` must be one of:
  - `online`
  - `offline`
  - `degraded`
- `capabilities` must be a non-empty list
- `capabilities` must include `mode-s`
- `timestamp` must be positive
- `stream_protocol`, if present, must be one of:
  - `simulation`
  - `websocket-json`
  - `command-jsonl`
- `stream_format`, if present, must be one of:
  - `json`
  - `jsonl`

That schema is implemented in:

- [src/network/ckb_discovery.py](/Users/jeremicarose/Downloads/mlat-system%202/src/network/ckb_discovery.py:23)

## Ownership Model

Ownership is intentionally **not** represented inside the JSON payload.

Ownership is controlled by the **lock script** on the cell:

- the lock script decides who can spend/update the cell
- the type script validates that the replacement cell data is structurally valid

That is the proper CKB separation:

- lock script = authorization
- type script = validation

## Canonical Record Selection

If multiple cells exist for the same `receiver_id`, the off-chain client currently selects the **latest valid record by timestamp**.

That rule is implemented in:

- [src/network/ckb_discovery.py](/Users/jeremicarose/Downloads/mlat-system%202/src/network/ckb_discovery.py:112)

## Example Cell Layout

```javascript
{
  capacity: "0x174876e800",
  lock: {
    code_hash: "0x...",
    hash_type: "type",
    args: "0x..."
  },
  type: {
    code_hash: "0x...",  // receiver registry type hash
    hash_type: "type",
    args: "0x"
  },
  data: {
    receiver_id: "RECV_NYC_001",
    latitude: 40.7128,
    longitude: -74.0060,
    altitude: 10.0,
    status: "online",
    capabilities: ["mode-s", "adsb", "mlat"],
    timestamp: 1704067200.0,
    stream_endpoint: "wss://feed.example/ws",
    stream_protocol: "websocket-json",
    stream_format: "json",
    metadata: {
      region: "nyc"
    }
  }
}
```

## Off-Chain Registration Payload

The Python registration path now builds the same canonical JSON schema before encoding it into cell data:

- [src/network/ckb_discovery.py](/Users/jeremicarose/Downloads/mlat-system%202/src/network/ckb_discovery.py:359)

## Contract Guidance

The type script should validate the same JSON schema the Python code expects.

Practical contract expectations:

1. Decode JSON cell data
2. Validate required fields and ranges
3. Reject malformed capability lists
4. Reject unsupported `stream_protocol` / `stream_format`
5. Let the lock script control ownership and updates

## Recommendation

Do **not** maintain both:

- a compact binary on-chain format in docs
- a JSON format in code

This project should use the canonical JSON schema everywhere until a deliberate migration to a compact binary format is actually implemented across:

- contract
- discovery client
- registration path
- tests
- docs

## Next Steps

1. Implement the on-chain type script against the canonical JSON schema
2. Deploy the registry contract
3. Save the deployed type hash as `RECEIVER_REGISTRY_TYPE_HASH`
4. Register real receivers
5. Switch discovery out of simulation mode
