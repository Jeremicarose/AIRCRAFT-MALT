use crate::error::Error;
use heapless::{String, Vec};
use serde::{Deserialize, Serialize};

pub const REGISTRY_SCHEMA_VERSION: u8 = 2;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ReceiverRegistryRecord {
    pub schema_version: u8,
    pub receiver_id: String<64>,
    pub latitude: f64,
    pub longitude: f64,
    pub altitude: f64,
    pub status: String<16>,
    pub capabilities: Vec<String<32>, 8>,
    pub sequence: u64,
    pub updated_at: u64,
    pub stream_endpoint: Option<String<256>>,
    pub stream_protocol: Option<String<32>>,
    pub stream_format: Option<String<16>>,
    pub metadata_hash: Option<String<66>>,
}

impl ReceiverRegistryRecord {
    pub fn validate(&self) -> Result<(), Error> {
        if self.schema_version != REGISTRY_SCHEMA_VERSION {
            return Err(Error::InvalidSchemaVersion);
        }
        if !valid_receiver_id(self.receiver_id.as_str()) {
            return Err(Error::InvalidReceiverId);
        }
        if !self.latitude.is_finite() || !(-90.0..=90.0).contains(&self.latitude) {
            return Err(Error::InvalidLatitude);
        }
        if !self.longitude.is_finite() || !(-180.0..=180.0).contains(&self.longitude) {
            return Err(Error::InvalidLongitude);
        }
        if !self.altitude.is_finite() || !(-500.0..=20_000.0).contains(&self.altitude) {
            return Err(Error::InvalidAltitude);
        }
        if !matches!(
            self.status.as_str(),
            "online" | "offline" | "degraded" | "revoked"
        ) {
            return Err(Error::InvalidStatus);
        }
        if self.capabilities.is_empty() {
            return Err(Error::MissingCapabilities);
        }
        if !self
            .capabilities
            .iter()
            .all(|capability| valid_capability(capability.as_str()))
        {
            return Err(Error::InvalidCapability);
        }
        for (index, capability) in self.capabilities.iter().enumerate() {
            if self.capabilities[index + 1..]
                .iter()
                .any(|other| other == capability)
            {
                return Err(Error::DuplicateCapabilities);
            }
        }
        if !self
            .capabilities
            .iter()
            .any(|capability| capability.as_str() == "mode-s")
        {
            return Err(Error::MissingModeS);
        }
        if self.updated_at == 0 {
            return Err(Error::InvalidUpdatedAt);
        }
        if let Some(protocol) = &self.stream_protocol {
            if !matches!(protocol.as_str(), "websocket-json" | "command-jsonl") {
                return Err(Error::InvalidStreamProtocol);
            }
        }
        if let Some(format) = &self.stream_format {
            if !matches!(format.as_str(), "json" | "jsonl") {
                return Err(Error::InvalidStreamFormat);
            }
        }
        if self.stream_endpoint.is_some() && self.stream_protocol.is_none() {
            return Err(Error::StreamProtocolRequired);
        }
        if let Some(metadata_hash) = &self.metadata_hash {
            if !valid_hash(metadata_hash.as_str()) {
                return Err(Error::InvalidMetadataHash);
            }
        }
        if self.status.as_str() == "revoked"
            && (self.stream_endpoint.is_some()
                || self.stream_protocol.is_some()
                || self.stream_format.is_some())
        {
            return Err(Error::RevokedStream);
        }
        Ok(())
    }

    pub fn validate_creation(&self) -> Result<(), Error> {
        self.validate()?;
        if self.sequence != 0 {
            return Err(Error::InvalidSequence);
        }
        if self.status.as_str() == "revoked" {
            return Err(Error::InvalidTransition);
        }
        Ok(())
    }

    pub fn validate_successor(&self, previous: &Self) -> Result<(), Error> {
        previous.validate()?;
        self.validate()?;
        if previous.status.as_str() == "revoked" {
            return Err(Error::RevokedTerminal);
        }
        if self.receiver_id != previous.receiver_id {
            return Err(Error::ImmutableReceiverId);
        }
        if previous.sequence.checked_add(1) != Some(self.sequence) {
            return Err(Error::InvalidSequence);
        }
        if self.updated_at < previous.updated_at {
            return Err(Error::InvalidUpdatedAt);
        }
        Ok(())
    }
}

fn valid_receiver_id(value: &str) -> bool {
    let bytes = value.as_bytes();
    !bytes.is_empty()
        && bytes[0].is_ascii_uppercase_or_digit()
        && bytes
            .iter()
            .all(|byte| byte.is_ascii_uppercase_or_digit() || matches!(byte, b'_' | b'-'))
}

fn valid_capability(value: &str) -> bool {
    let bytes = value.as_bytes();
    !bytes.is_empty()
        && bytes[0].is_ascii_lowercase_or_digit()
        && bytes
            .iter()
            .all(|byte| byte.is_ascii_lowercase_or_digit() || matches!(byte, b'_' | b'-'))
}

fn valid_hash(value: &str) -> bool {
    let bytes = value.as_bytes();
    bytes.len() == 66
        && bytes.starts_with(b"0x")
        && bytes[2..].iter().all(|byte| byte.is_ascii_hexdigit())
}

trait AsciiIdentifierByte {
    fn is_ascii_uppercase_or_digit(&self) -> bool;
    fn is_ascii_lowercase_or_digit(&self) -> bool;
}

impl AsciiIdentifierByte for u8 {
    fn is_ascii_uppercase_or_digit(&self) -> bool {
        self.is_ascii_uppercase() || self.is_ascii_digit()
    }

    fn is_ascii_lowercase_or_digit(&self) -> bool {
        self.is_ascii_lowercase() || self.is_ascii_digit()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn text<const N: usize>(value: &str) -> String<N> {
        let mut item = String::new();
        item.push_str(value).unwrap();
        item
    }

    fn capabilities(values: &[&str]) -> Vec<String<32>, 8> {
        let mut caps = Vec::new();
        for value in values {
            caps.push(text(value)).unwrap();
        }
        caps
    }

    fn record() -> ReceiverRegistryRecord {
        ReceiverRegistryRecord {
            schema_version: REGISTRY_SCHEMA_VERSION,
            receiver_id: text("RECV_NYC_001"),
            latitude: 40.7128,
            longitude: -74.0060,
            altitude: 10.0,
            status: text("online"),
            capabilities: capabilities(&["mode-s", "adsb", "mlat"]),
            sequence: 0,
            updated_at: 1_700_000_000,
            stream_endpoint: Some(text("wss://feed.example/ws")),
            stream_protocol: Some(text("websocket-json")),
            stream_format: Some(text("json")),
            metadata_hash: None,
        }
    }

    #[test]
    fn validates_creation_and_successor() {
        let initial = record();
        assert_eq!(initial.validate_creation(), Ok(()));

        let mut update = initial.clone();
        update.sequence = 1;
        update.updated_at += 1;
        assert_eq!(update.validate_successor(&initial), Ok(()));
    }

    #[test]
    fn rejects_identity_label_change_and_sequence_jump() {
        let initial = record();
        let mut update = initial.clone();
        update.receiver_id = text("RECV_ATTACKER");
        update.sequence = 1;
        assert_eq!(
            update.validate_successor(&initial),
            Err(Error::ImmutableReceiverId)
        );

        let mut skipped = initial.clone();
        skipped.sequence = 2;
        assert_eq!(
            skipped.validate_successor(&initial),
            Err(Error::InvalidSequence)
        );
    }

    #[test]
    fn revocation_is_terminal() {
        let initial = record();
        let mut revoked = initial.clone();
        revoked.status = text("revoked");
        revoked.sequence = 1;
        revoked.stream_endpoint = None;
        revoked.stream_protocol = None;
        revoked.stream_format = None;
        assert_eq!(revoked.validate_successor(&initial), Ok(()));

        let mut resurrection = revoked.clone();
        resurrection.status = text("online");
        resurrection.sequence = 2;
        assert_eq!(
            resurrection.validate_successor(&revoked),
            Err(Error::RevokedTerminal)
        );
    }

    #[test]
    fn rejects_duplicate_capabilities() {
        let mut invalid = record();
        invalid.capabilities = capabilities(&["mode-s", "mode-s"]);
        assert_eq!(invalid.validate(), Err(Error::DuplicateCapabilities));
    }
}
