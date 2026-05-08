use crate::error::Error;
use heapless::Vec;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct ReceiverRegistryRecord<'a> {
    pub receiver_id: &'a str,
    pub latitude: f64,
    pub longitude: f64,
    pub altitude: f64,
    pub status: &'a str,
    pub capabilities: Vec<&'a str, 8>,
    pub timestamp: f64,
    pub stream_endpoint: Option<&'a str>,
    pub stream_protocol: Option<&'a str>,
    pub stream_format: Option<&'a str>,
}

impl<'a> ReceiverRegistryRecord<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        if self.receiver_id.is_empty() {
            return Err(Error::MissingReceiverId);
        }
        if !(self.latitude >= -90.0 && self.latitude <= 90.0) {
            return Err(Error::InvalidLatitude);
        }
        if !(self.longitude >= -180.0 && self.longitude <= 180.0) {
            return Err(Error::InvalidLongitude);
        }
        if !(self.altitude >= -500.0 && self.altitude <= 20_000.0) {
            return Err(Error::InvalidAltitude);
        }
        if !matches!(self.status, "online" | "offline" | "degraded") {
            return Err(Error::InvalidStatus);
        }
        if self.capabilities.is_empty() {
            return Err(Error::MissingCapabilities);
        }
        if !self.capabilities.iter().any(|capability| *capability == "mode-s") {
            return Err(Error::MissingModeS);
        }
        if self.timestamp <= 0.0 {
            return Err(Error::InvalidTimestamp);
        }
        if let Some(protocol) = self.stream_protocol {
            if !matches!(protocol, "simulation" | "websocket-json" | "command-jsonl") {
                return Err(Error::InvalidStreamProtocol);
            }
        }
        if let Some(format) = self.stream_format {
            if !matches!(format, "json" | "jsonl") {
                return Err(Error::InvalidStreamFormat);
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn capabilities(values: &[&str]) -> Vec<&str, 8> {
        let mut caps = Vec::new();
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

        assert_eq!(record.validate(), Err(Error::MissingModeS));
    }
}
