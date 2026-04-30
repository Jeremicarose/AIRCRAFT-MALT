# CKB Blockchain Integration Guide

Complete guide for using Nervos Network (CKB) blockchain with the MLAT system.

## 🎯 Why CKB for MLAT?

CKB (Common Knowledge Base) is perfect for decentralized peer discovery because:

✅ **Truly Decentralized** - No central authority
✅ **Flexible Cell Model** - Store any data structure
✅ **Low Transaction Costs** - Affordable for frequent updates
✅ **Permanent Storage** - Data persists on-chain
✅ **Programmable** - Custom validation logic
✅ **Open Ecosystem** - No permission needed

## 📋 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              CKB Blockchain                          │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Receiver Cell│  │ Receiver Cell│  │ Receiver  │ │
│  │  NYC Data    │  │  BOS Data    │  │ Cell...   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
                       │ RPC Query
                       │
        ┌──────────────▼──────────────┐
        │   CKB Peer Discovery        │
        │   (ckb_discovery.py)        │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   MLAT System receives        │
        │   receiver metadata          │
        └──────────────────────────────┘
```

### Data Flow

1. **Receiver Registration**
   - Receiver creates CKB cell with metadata
   - Cell contains: location, capabilities, status
   - Uses type script for identification

2. **Peer Discovery**
   - MLAT system queries CKB for receiver cells
   - Filters for active, MLAT-capable receivers
   - Caches receiver information

3. **Data Streaming**
   - Connects to receivers via 4DSky
   - Streams Mode-S data
   - Performs MLAT calculations

## 🚀 Quick Start

### 1. Install CKB SDK

```bash
# Install CKB Python SDK
pip install ckb-py

# Or add to requirements.txt
echo "ckb-py>=0.1.0" >> requirements.txt
pip install -r requirements.txt
```

### 2. Setup CKB Account

```bash
# Install CKB CLI
# Mac
brew install nervosnetwork/tap/ckb

# Linux
wget https://github.com/nervosnetwork/ckb/releases/download/v0.109.0/ckb_v0.109.0_x86_64-unknown-linux-gnu.tar.gz
tar -xzf ckb_v0.109.0_x86_64-unknown-linux-gnu.tar.gz

# Initialize account
ckb init --chain testnet
ckb run --indexer

# Create wallet
ckb-cli account new
# Save your private key securely!
```

### 3. Get Testnet CKB

```bash
# Get testnet CKB from faucet
# Visit: https://faucet.nervos.org/

# Check balance
ckb-cli wallet get-capacity --address <your-address>
```

### 4. Deploy Receiver Registry Contract

```bash
# Clone the receiver registry contract
git clone https://github.com/your-org/ckb-receiver-registry

cd ckb-receiver-registry

# Build contract
capsule build

# Deploy to testnet
capsule deploy --address <your-address>

# Save the type script hash!
# e.g., 0x1234567890abcdef...
```

### 5. Configure MLAT System

Edit `.env`:

```bash
# CKB Configuration
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0x1234567890abcdef...

# Optional: Your CKB private key (for registering receivers)
CKB_PRIVATE_KEY=0x...

# 4DSky Configuration (still needed for data streaming)
FOURDSKYAPIKEY=your_api_key
FOURDSKYENDPOINT=wss://your-feed-endpoint
FOURDSKY_TRANSPORT=auto
```

### 6. Run MLAT System with CKB

```bash
# Start the system
mlat-processor
```

## 📝 Receiver Registration

### Manual Registration

```python
from network.ckb_discovery import CKBPeerDiscovery, CKBConfig

# Configure
config = CKBConfig(
    network="testnet",
    ckb_rpc_url="https://testnet.ckb.dev/rpc",
    receiver_registry_type_hash="0x..."
)

# Create discovery client
discovery = CKBPeerDiscovery(config)
await discovery.initialize()

# Register your receiver
await discovery.register_receiver(
    receiver_id="RECV_NYC_001",
    latitude=40.7128,
    longitude=-74.0060,
    altitude=10.0,
    capabilities=["mode-s", "adsb", "mlat"],
    private_key="0x...",  # Your CKB private key
    stream_endpoint="wss://your-4dsky-feed",
    stream_protocol="websocket-json",
    stream_format="json"
)
```

### Automated Registration Script

```python
#!/usr/bin/env python3
"""Register receiver on CKB blockchain"""

import asyncio
import sys
from network.ckb_discovery import CKBPeerDiscovery, CKBConfig

async def register():
    # Get parameters
    receiver_id = input("Receiver ID: ")
    latitude = float(input("Latitude: "))
    longitude = float(input("Longitude: "))
    altitude = float(input("Altitude (m): "))
    private_key = input("CKB Private Key: ")
    
    # Configure
    config = CKBConfig(
        network="testnet",
        ckb_rpc_url="https://testnet.ckb.dev/rpc",
        receiver_registry_type_hash="0x..."
    )
    
    # Register
    discovery = CKBPeerDiscovery(config)
    await discovery.initialize()
    
    success = await discovery.register_receiver(
        receiver_id=receiver_id,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        capabilities=["mode-s", "adsb", "mlat"],
        private_key=private_key
    )
    
    if success:
        print("✅ Receiver registered successfully!")
    else:
        print("❌ Registration failed")
    
    await discovery.shutdown()

if __name__ == "__main__":
    asyncio.run(register())
```

## 🔧 CKB Cell Structure

### Receiver Registry Cell

```javascript
{
  // Cell capacity (minimum 61 CKB)
  capacity: "0x174876e800",  // 100 CKB in hex
  
  // Lock script (controls ownership)
  lock: {
    code_hash: "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    hash_type: "type",
    args: "0x..." // Your address
  },
  
  // Type script (identifies as receiver registry)
  type: {
    code_hash: "0x...", // Receiver registry type hash
    hash_type: "type",
    args: "0x"
  },
  
  // Cell data (receiver metadata as JSON)
  data: {
    receiver_id: "RECV_NYC_001",
    latitude: 40.7128,
    longitude: -74.0060,
    altitude: 10.0,
    status: "online",
    capabilities: ["mode-s", "adsb", "mlat"],
    timestamp: 1704067200,
    signature: "0x..."  // Signature for verification
  }
}
```

### Querying Receivers

```python
async def query_receivers():
    """Query all receivers from CKB"""
    
    from ckb import rpc
    
    client = rpc.RPC("https://testnet.ckb.dev/rpc")
    
    # Search for receiver cells
    search_key = {
        "script": {
            "code_hash": "0x...",  # Registry type hash
            "hash_type": "type",
            "args": "0x"
        },
        "script_type": "type"
    }
    
    cells = client.get_cells(search_key, "asc", "0x64")
    
    receivers = []
    for cell in cells.get("objects", []):
        # Parse cell data
        data_hex = cell["output_data"]
        data_bytes = bytes.fromhex(data_hex[2:])
        receiver_data = json.loads(data_bytes.decode('utf-8'))
        
        receivers.append(receiver_data)
    
    return receivers
```

## 🏗️ Receiver Registry Smart Contract

### Contract Structure

```rust
// Simplified Receiver Registry Contract

use ckb_std::high_level::{load_cell_data, load_script};

pub fn main() -> Result<(), Error> {
    // Load receiver data
    let data = load_cell_data(0, Source::GroupInput)?;
    
    // Parse JSON
    let receiver: ReceiverData = serde_json::from_slice(&data)?;
    
    // Validate receiver data
    assert!(receiver.latitude >= -90.0 && receiver.latitude <= 90.0);
    assert!(receiver.longitude >= -180.0 && receiver.longitude <= 180.0);
    assert!(receiver.altitude >= 0.0 && receiver.altitude <= 10000.0);
    assert!(!receiver.capabilities.is_empty());
    
    // Verify signature
    verify_signature(&receiver)?;
    
    Ok(())
}
```

### Building and Deploying

```bash
# Initialize Capsule project
capsule new receiver-registry
cd receiver-registry

# Add code to contracts/receiver-registry/src/entry.rs

# Build
capsule build

# Test
capsule test

# Deploy to testnet
capsule deploy --address <your-address>

# Output will show:
# Type script hash: 0x1234...
# Save this for configuration!
```

## 📊 Monitoring CKB Integration

### Check Receiver Status

```bash
# Query receivers via RPC
curl -X POST https://testnet.ckb.dev/rpc \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_cells",
    "params": [{
      "script": {
        "code_hash": "0x...",
        "hash_type": "type",
        "args": "0x"
      },
      "script_type": "type"
    }, "asc", "0x64"],
    "id": 1
  }'
```

### Update Receiver Status

```python
async def update_receiver_status(receiver_id: str, new_status: str):
    """Update receiver status on CKB"""
    
    # 1. Find existing cell
    # 2. Create transaction consuming old cell
    # 3. Create new cell with updated status
    # 4. Sign and send transaction
    
    pass  # Implementation details
```

## 💰 Cost Estimation

### CKB Costs (Testnet/Mainnet)

- **Cell Creation**: ~100 CKB per receiver (~$10-20 on mainnet)
- **Storage**: Permanent, included in cell capacity
- **Updates**: ~1 CKB per transaction (~$0.10-0.20)

### Optimization

- **Batch Updates**: Update multiple receivers in one transaction
- **Cell Recycling**: Consume old cell when updating
- **Minimal Data**: Store only essential metadata on-chain

## 🔒 Security Considerations

### Private Key Management

```bash
# NEVER commit private keys!
# Use environment variables
export CKB_PRIVATE_KEY="0x..."

# Or use hardware wallet
# Or use CKB key management service
```

### Signature Verification

```python
def verify_receiver_signature(receiver_data: dict) -> bool:
    """Verify receiver data is signed by owner"""
    
    # Extract signature
    signature = receiver_data.pop('signature')
    
    # Compute message hash
    message = json.dumps(receiver_data, sort_keys=True)
    message_hash = hashlib.sha256(message.encode()).digest()
    
    # Verify signature
    # ... verification logic
    
    return is_valid
```

## 🎯 Production Checklist

- [ ] CKB node/RPC access configured
- [ ] Receiver registry contract deployed
- [ ] Type script hash saved in configuration
- [ ] Receivers registered on-chain
- [ ] Query system tested
- [ ] Backup private keys securely
- [ ] Monitor CKB node health
- [ ] Plan for cell capacity management
- [ ] Setup automated status updates
- [ ] Test failover scenarios

## 📚 Additional Resources

- **CKB Documentation**: https://docs.nervos.org/
- **CKB Explorer**: https://explorer.nervos.org/
- **CKB Faucet**: https://faucet.nervos.org/
- **Capsule (Smart Contract Dev)**: https://github.com/nervosnetwork/capsule
- **CKB.py SDK**: https://github.com/nervosnetwork/ckb-py

## 🆚 CKB vs Hedera Comparison

| Feature | CKB | Hedera |
|---------|-----|--------|
| Decentralization | Fully decentralized | Permissioned council |
| Transaction Cost | Low (~$0.10) | Very low (~$0.0001) |
| Data Storage | Permanent on-chain | Consensus service |
| Smart Contracts | Full Turing-complete | Limited |
| Ecosystem | Growing | Enterprise-focused |
| Developer Tools | Mature | Very mature |

**For MLAT**: CKB provides true decentralization with flexible data storage!

---

## ✅ You're Ready!

Your MLAT system now uses **CKB blockchain** for decentralized peer discovery!

**Benefits**:
✅ No central authority
✅ Permanent receiver registry
✅ Trustless verification
✅ Open participation
✅ Community-owned infrastructure

Start by deploying the receiver registry contract and registering your receivers! 🚀
