#![cfg_attr(not(test), no_std)]

extern crate alloc;

use receiver_registry::ReceiverRegistryRecord;
use serde_json_core::de::from_slice;

#[cfg(not(test))]
fn main() {
    // Placeholder for the real Capsule/ckb-std entrypoint.
    //
    // Intended flow:
    // 1. Load cell data from the input group.
    // 2. Decode canonical JSON receiver registry record.
    // 3. Validate with ReceiverRegistryRecord::validate().
    // 4. Return success/failure to the VM.
}

#[allow(dead_code)]
fn validate_receiver_cell_data(data: &[u8]) -> bool {
    match from_slice::<ReceiverRegistryRecord>(data) {
        Ok((record, _consumed)) => record.validate().is_ok(),
        Err(_) => false,
    }
}
