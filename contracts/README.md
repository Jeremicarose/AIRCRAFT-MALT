# Receiver Registry Smart Contract for CKB

This directory contains a simplified CKB smart contract for the MLAT receiver registry.

## Overview

The receiver registry contract validates receiver metadata stored in CKB cells.

## Contract Logic

```rust
// File: contracts/receiver-registry/src/entry.rs

#![no_std]
#![cfg_attr(not(test), no_main)]

use ckb_std::{
    debug,
    high_level::{load_script, load_cell_data},
    ckb_constants::Source,
};

use core::result::Result;

// Import error handling
#[derive(Debug, PartialEq)]
pub enum Error {
    InvalidLatitude,
    InvalidLongitude,
    InvalidAltitude,
    InvalidCapabilities,
    InvalidTimestamp,
}

// Receiver data structure
pub struct ReceiverData {
    pub receiver_id: [u8; 32],
    pub latitude: i32,   // Fixed point: value * 1000000
    pub longitude: i32,  // Fixed point: value * 1000000
    pub altitude: u32,   // Meters
    pub capabilities: u8, // Bit flags
    pub timestamp: u64,
}

impl ReceiverData {
    pub fn from_bytes(data: &[u8]) -> Result<Self, Error> {
        if data.len() < 77 {
            return Err(Error::InvalidData);
        }
        
        // Parse fixed-size structure
        let mut receiver_id = [0u8; 32];
        receiver_id.copy_from_slice(&data[0..32]);
        
        let latitude = i32::from_le_bytes([
            data[32], data[33], data[34], data[35]
        ]);
        
        let longitude = i32::from_le_bytes([
            data[36], data[37], data[38], data[39]
        ]);
        
        let altitude = u32::from_le_bytes([
            data[40], data[41], data[42], data[43]
        ]);
        
        let capabilities = data[44];
        
        let timestamp = u64::from_le_bytes([
            data[45], data[46], data[47], data[48],
            data[49], data[50], data[51], data[52]
        ]);
        
        Ok(ReceiverData {
            receiver_id,
            latitude,
            longitude,
            altitude,
            capabilities,
            timestamp,
        })
    }
    
    pub fn validate(&self) -> Result<(), Error> {
        // Validate latitude: -90 to 90 degrees
        if self.latitude < -90_000_000 || self.latitude > 90_000_000 {
            return Err(Error::InvalidLatitude);
        }
        
        // Validate longitude: -180 to 180 degrees
        if self.longitude < -180_000_000 || self.longitude > 180_000_000 {
            return Err(Error::InvalidLongitude);
        }
        
        // Validate altitude: 0 to 10000 meters
        if self.altitude > 10000 {
            return Err(Error::InvalidAltitude);
        }
        
        // Validate capabilities (at least one bit set)
        if self.capabilities == 0 {
            return Err(Error::InvalidCapabilities);
        }
        
        // Validate timestamp (not in far future)
        let current_time = 1704067200; // Placeholder
        if self.timestamp > current_time + 86400 {
            return Err(Error::InvalidTimestamp);
        }
        
        Ok(())
    }
}

#[no_mangle]
pub fn main() -> i8 {
    // Load cell data
    let data = match load_cell_data(0, Source::GroupInput) {
        Ok(d) => d,
        Err(_) => return -1,
    };
    
    // Parse receiver data
    let receiver = match ReceiverData::from_bytes(&data) {
        Ok(r) => r,
        Err(_) => return -2,
    };
    
    // Validate receiver data
    match receiver.validate() {
        Ok(_) => 0,  // Success
        Err(Error::InvalidLatitude) => -10,
        Err(Error::InvalidLongitude) => -11,
        Err(Error::InvalidAltitude) => -12,
        Err(Error::InvalidCapabilities) => -13,
        Err(Error::InvalidTimestamp) => -14,
        Err(_) => -99,
    }
}
```

## Building the Contract

### Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install CKB development tools
cargo install ckb-capsule

# Install RISC-V target
rustup target add riscv64imac-unknown-none-elf
```

### Build Steps

```bash
# Initialize project
capsule new receiver-registry
cd receiver-registry

# Add the contract code above to:
# contracts/receiver-registry/src/entry.rs

# Build
capsule build

# Test
capsule test

# The built contract will be in:
# build/release/receiver-registry
```

## Deploying the Contract

```bash
# Deploy to testnet
capsule deploy --address <your-ckb-address>

# This will output:
# - Transaction hash
# - Type script hash (save this!)
# - Code hash

# Example output:
# Type Script:
# {
#   "code_hash": "0x00000000000000000000000000000000000000000000000000545950455f4944",
#   "hash_type": "type",
#   "args": "0x1234567890abcdef..."
# }
```

## Using the Contract

### Creating a Receiver Cell

```python
from ckb import transaction

# Receiver data (77 bytes fixed structure)
receiver_data = {
    'receiver_id': b'RECV_NYC_001' + b'\x00' * 19,  # 32 bytes
    'latitude': int(40.7128 * 1_000_000),  # 4 bytes
    'longitude': int(-74.0060 * 1_000_000),  # 4 bytes
    'altitude': 10,  # 4 bytes
    'capabilities': 0b00000111,  # 1 byte (mode-s, adsb, mlat)
    'timestamp': int(time.time()),  # 8 bytes
}

# Convert to bytes
data_bytes = (
    receiver_data['receiver_id'] +
    receiver_data['latitude'].to_bytes(4, 'little', signed=True) +
    receiver_data['longitude'].to_bytes(4, 'little', signed=True) +
    receiver_data['altitude'].to_bytes(4, 'little') +
    bytes([receiver_data['capabilities']]) +
    receiver_data['timestamp'].to_bytes(8, 'little')
)

# Create cell
output = {
    'capacity': '0x174876e800',  # 100 CKB
    'lock': your_lock_script,
    'type': {
        'code_hash': '0x...',  # Deployed contract code hash
        'hash_type': 'type',
        'args': '0x'
    }
}

outputs_data = ['0x' + data_bytes.hex()]

# Build and send transaction
# tx = build_transaction(inputs, outputs, outputs_data)
# send_transaction(tx)
```

## Capability Flags

```python
# Bit flags for capabilities
MODE_S = 0b00000001
ADSB   = 0b00000010
MLAT   = 0b00000100

# Example: receiver with all capabilities
capabilities = MODE_S | ADSB | MLAT  # 0b00000111 = 7
```

## Data Format

### Fixed Binary Structure (77 bytes)

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| receiver_id | 0 | 32 | bytes | Unique receiver identifier |
| latitude | 32 | 4 | i32 | Latitude * 1,000,000 |
| longitude | 36 | 4 | i32 | Longitude * 1,000,000 |
| altitude | 40 | 4 | u32 | Altitude in meters |
| capabilities | 44 | 1 | u8 | Capability bit flags |
| timestamp | 45 | 8 | u64 | Unix timestamp |

### Example

```
Receiver: RECV_NYC_001
Location: 40.7128°N, -74.0060°W, 10m
Capabilities: Mode-S, ADS-B, MLAT
Timestamp: 1704067200

Binary (hex):
52 45 43 56 5f 4e 59 43 5f 30 30 31 00 00 00 00  # receiver_id
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  # padding
C0 D4 6D 02                                      # latitude (40712800)
A0 90 8F FC                                      # longitude (-7400600)
0A 00 00 00                                      # altitude (10)
07                                               # capabilities (111)
00 36 9A 65 00 00 00 00                          # timestamp
```

## Testing

```bash
# Run contract tests
cd receiver-registry
capsule test

# Test with specific data
capsule test -- --test-name test_valid_receiver
capsule test -- --test-name test_invalid_latitude
```

## Security Notes

1. **Validation**: Contract validates all receiver data
2. **Immutability**: Once deployed, contract code cannot change
3. **Transparency**: All receiver data is publicly readable
4. **Ownership**: Lock script controls who can update cells

## Alternative: JSON Format

For easier development, you can use JSON format instead:

```rust
// Use serde_json for JSON parsing
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Serialize, Deserialize)]
struct ReceiverDataJSON {
    receiver_id: String,
    latitude: f64,
    longitude: f64,
    altitude: f64,
    capabilities: Vec<String>,
    timestamp: u64,
}

// Parse from cell data
let receiver: ReceiverDataJSON = serde_json::from_slice(&data)?;
```

Note: JSON format uses more space (~200 bytes vs 77 bytes) but is more flexible.

## Next Steps

1. Build and deploy the contract
2. Save the type script hash
3. Update MLAT system configuration
4. Register receivers on-chain
5. Test peer discovery

---

**This contract enables decentralized, trustless receiver registry on CKB!** 🚀
