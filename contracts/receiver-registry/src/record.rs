use crate::error::Error;
use heapless::{String, Vec};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct ReceiverRegistryRecord {
    pub receiver_id: String<64>,
    pub latitude: f64,
    pub longitude: f64,
    pub altitude: f64,
    pub status: String<16>,
    pub capabilities: Vec<String<32>, 8>,
    pub timestamp: f64,
    pub stream_endpoint: Option<String<256>>,
    pub stream_protocol: Option<String<32>>,
    pub stream_format: Option<String<16>>,
}

impl ReceiverRegistryRecord {
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
        if !matches!(self.status.as_str(), "online" | "offline" | "degraded") {
            return Err(Error::InvalidStatus);
        }
        if self.capabilities.is_empty() {
            return Err(Error::MissingCapabilities);
        }
        if !self
            .capabilities
            .iter()
            .any(|capability| capability.as_str() == "mode-s")
        {
            return Err(Error::MissingModeS);
        }
        if self.timestamp <= 0.0 {
            return Err(Error::InvalidTimestamp);
        }
        if let Some(protocol) = &self.stream_protocol {
            if !matches!(
                protocol.as_str(),
                "simulation" | "websocket-json" | "command-jsonl"
            ) {
                return Err(Error::InvalidStreamProtocol);
            }
        }
        if let Some(format) = &self.stream_format {
            if !matches!(format.as_str(), "json" | "jsonl") {
                return Err(Error::InvalidStreamFormat);
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn capability(value: &str) -> String<32> {
        let mut item = String::new();
        item.push_str(value).unwrap();
        item
    }

    fn capabilities(values: &[&str]) -> Vec<String<32>, 8> {
        let mut caps = Vec::new();
        for value in values {
            caps.push(capability(value)).unwrap();
        }
        caps
    }

    fn short<const N: usize>(value: &str) -> String<N> {
        let mut item = String::new();
        item.push_str(value).unwrap();
        item
    }

    #[test]
    fn validates_canonical_receiver_record() {
        let record = ReceiverRegistryRecord {
            receiver_id: short("RECV_NYC_001"),
            latitude: 40.7128,
            longitude: -74.0060,
            altitude: 10.0,
            status: short("online"),
            capabilities: capabilities(&["mode-s", "adsb", "mlat"]),
            timestamp: 1_700_000_000.0,
            stream_endpoint: Some(short("wss://feed.example/ws")),
            stream_protocol: Some(short("websocket-json")),
            stream_format: Some(short("json")),
        };

        assert_eq!(record.validate(), Ok(()));
    }

    #[test]
    fn rejects_record_without_mode_s() {
        let record = ReceiverRegistryRecord {
            receiver_id: short("RECV_BAD"),
            latitude: 40.7128,
            longitude: -74.0060,
            altitude: 10.0,
            status: short("online"),
            capabilities: capabilities(&["mlat"]),
            timestamp: 1_700_000_000.0,
            stream_endpoint: None,
            stream_protocol: None,
            stream_format: None,
        };

        assert_eq!(record.validate(), Err(Error::MissingModeS));
    }
}
