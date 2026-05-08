#![cfg_attr(not(test), no_std)]

use serde::{Deserialize, Serialize};

#[derive(Debug, PartialEq)]
pub enum ValidationError {
    MissingReceiverId,
    InvalidLatitude,
    InvalidLongitude,
    InvalidAltitude,
    InvalidStatus,
    MissingCapabilities,
    MissingModeS,
    InvalidTimestamp,
    InvalidStreamProtocol,
    InvalidStreamFormat,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct ReceiverRegistryRecord<'a> {
    pub receiver_id: &'a str,
    pub latitude: f64,
    pub longitude: f64,
    pub altitude: f64,
    pub status: &'a str,
    pub capabilities: heapless::Vec<&'a str, 8>,
    pub timestamp: f64,
    pub stream_endpoint: Option<&'a str>,
    pub stream_protocol: Option<&'a str>,
    pub stream_format: Option<&'a str>,
}

impl<'a> ReceiverRegistryRecord<'a> {
    pub fn validate(&self) -> Result<(), ValidationError> {
        if self.receiver_id.is_empty() {
            return Err(ValidationError::MissingReceiverId);
        }
        if !(self.latitude >= -90.0 && self.latitude <= 90.0) {
            return Err(ValidationError::InvalidLatitude);
        }
        if !(self.longitude >= -180.0 && self.longitude <= 180.0) {
            return Err(ValidationError::InvalidLongitude);
        }
        if !(self.altitude >= -500.0 && self.altitude <= 20_000.0) {
            return Err(ValidationError::InvalidAltitude);
        }
        if !matches!(self.status, "online" | "offline" | "degraded") {
            return Err(ValidationError::InvalidStatus);
        }
        if self.capabilities.is_empty() {
            return Err(ValidationError::MissingCapabilities);
        }
        if !self.capabilities.iter().any(|capability| *capability == "mode-s") {
            return Err(ValidationError::MissingModeS);
        }
        if self.timestamp <= 0.0 {
            return Err(ValidationError::InvalidTimestamp);
        }
        if let Some(protocol) = self.stream_protocol {
            if !matches!(protocol, "simulation" | "websocket-json" | "command-jsonl") {
                return Err(ValidationError::InvalidStreamProtocol);
            }
        }
        if let Some(format) = self.stream_format {
            if !matches!(format, "json" | "jsonl") {
                return Err(ValidationError::InvalidStreamFormat);
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn capabilities(values: &[&str]) -> heapless::Vec<&str, 8> {
        let mut caps = heapless::Vec::new();
        for value in values {
            caps.push(*value).unwrap();
        }
        caps
    }

    #[test]
    fn validates_canonical_receiver_record() {
        let record = ReceiverRegistryRecord {
            receiver_id: "RECV_NYC_001",
            latitude: 40.7128,
            longitude: -74.0060,
            altitude: 10.0,
            status: "online",
            capabilities: capabilities(&["mode-s", "adsb", "mlat"]),
            timestamp: 1_700_000_000.0,
            stream_endpoint: Some("wss://feed.example/ws"),
            stream_protocol: Some("websocket-json"),
            stream_format: Some("json"),
        };

        assert_eq!(record.validate(), Ok(()));
    }

    #[test]
    fn rejects_record_without_mode_s() {
        let record = ReceiverRegistryRecord {
            receiver_id: "RECV_BAD",
            latitude: 40.7128,
            longitude: -74.0060,
            altitude: 10.0,
            status: "online",
            capabilities: capabilities(&["mlat"]),
            timestamp: 1_700_000_000.0,
            stream_endpoint: None,
            stream_protocol: None,
            stream_format: None,
        };

        assert_eq!(record.validate(), Err(ValidationError::MissingModeS));
    }
}
