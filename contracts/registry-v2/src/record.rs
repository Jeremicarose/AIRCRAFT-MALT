use crate::error::Error;
use heapless::{String, Vec};
use serde::{Deserialize, Serialize};

pub const REGISTRY_SCHEMA_VERSION: u8 = 2;
pub const MAX_RECORD_BYTES: usize = 16 * 1024;

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
        if let Some(endpoint) = &self.stream_endpoint {
            if !valid_wire_text(endpoint.as_str()) {
                return Err(Error::InvalidStreamEndpoint);
            }
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

pub fn decode_registry_v2_record(payload: &[u8]) -> Result<ReceiverRegistryRecord, Error> {
    if payload.len() > MAX_RECORD_BYTES || !has_strict_json_lexemes(payload) {
        return Err(Error::Encoding);
    }
    let (record, consumed): (ReceiverRegistryRecord, usize) =
        serde_json_core::from_slice(payload).map_err(|_| Error::Encoding)?;
    if consumed != payload.len() {
        return Err(Error::Encoding);
    }
    record.validate()?;
    Ok(record)
}

fn has_strict_json_lexemes(payload: &[u8]) -> bool {
    let mut index = 0;
    let mut in_string = false;

    while index < payload.len() {
        let byte = payload[index];
        if in_string {
            match byte {
                b'"' => in_string = false,
                b'\\' | 0..=0x1f => return false,
                _ => {}
            }
            index += 1;
            continue;
        }

        match byte {
            b'"' => {
                in_string = true;
                index += 1;
            }
            b'+' => return false,
            b'-' | b'0'..=b'9' => match consume_json_number(payload, index) {
                Some(next) => index = next,
                None => return false,
            },
            _ => index += 1,
        }
    }

    !in_string
}

fn consume_json_number(payload: &[u8], mut index: usize) -> Option<usize> {
    if payload.get(index) == Some(&b'-') {
        index += 1;
    }

    match payload.get(index)? {
        b'0' => {
            index += 1;
            if payload.get(index).is_some_and(u8::is_ascii_digit) {
                return None;
            }
        }
        b'1'..=b'9' => {
            index += 1;
            while payload.get(index).is_some_and(u8::is_ascii_digit) {
                index += 1;
            }
        }
        _ => return None,
    }

    if payload.get(index) == Some(&b'.') {
        index += 1;
        let fraction_start = index;
        while payload.get(index).is_some_and(u8::is_ascii_digit) {
            index += 1;
        }
        if index == fraction_start {
            return None;
        }
    }

    if matches!(payload.get(index), Some(b'e' | b'E')) {
        index += 1;
        if matches!(payload.get(index), Some(b'+' | b'-')) {
            index += 1;
        }
        let exponent_start = index;
        while payload.get(index).is_some_and(u8::is_ascii_digit) {
            index += 1;
        }
        if index == exponent_start {
            return None;
        }
    }

    match payload.get(index) {
        None | Some(b' ' | b'\t' | b'\n' | b'\r' | b',' | b']' | b'}') => Some(index),
        _ => None,
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

fn valid_wire_text(value: &str) -> bool {
    !value.is_empty()
        && value
            .bytes()
            .all(|byte| byte >= 0x20 && !matches!(byte, b'"' | b'\\'))
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
    use serde::Deserialize;
    use std::{string::String as StdString, vec::Vec as StdVec};

    #[derive(Deserialize)]
    struct ConformanceCorpus {
        schema_version: u8,
        record_cases: StdVec<RecordCase>,
        identity_cases: StdVec<IdentityCase>,
        transition_cases: StdVec<TransitionCase>,
    }

    #[derive(Deserialize)]
    struct RecordCase {
        name: StdString,
        payload: StdString,
        valid: bool,
        creation_valid: bool,
    }

    #[derive(Deserialize)]
    struct TransitionCase {
        name: StdString,
        previous: StdString,
        next: StdString,
        previous_identity: Option<StdString>,
        next_identity: Option<StdString>,
        valid: bool,
    }

    #[derive(Deserialize)]
    struct IdentityCase {
        name: StdString,
        value: StdString,
        valid: bool,
    }

    fn parse_record(payload: &str) -> Result<ReceiverRegistryRecord, Error> {
        decode_registry_v2_record(payload.as_bytes())
    }

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

    #[test]
    fn matches_shared_registry_v2_conformance_corpus() {
        let corpus: ConformanceCorpus = serde_json::from_str(include_str!(
            "../../../tests/registry/fixtures/registry_v2_conformance.json"
        ))
        .expect("valid conformance corpus");
        assert_eq!(corpus.schema_version, 2);

        for case in corpus.record_cases {
            let parsed = parse_record(&case.payload);
            assert_eq!(parsed.is_ok(), case.valid, "{}", case.name);
            if let Ok(record) = parsed {
                assert_eq!(
                    record.validate_creation().is_ok(),
                    case.creation_valid,
                    "{}",
                    case.name
                );
            }
        }

        for case in corpus.identity_cases {
            let decoded = case
                .value
                .strip_prefix("0x")
                .and_then(|value| hex::decode(value).ok());
            let valid = decoded.is_some_and(|value| value.len() == 32);
            assert_eq!(valid, case.valid, "{}", case.name);
        }

        for case in corpus.transition_cases {
            let previous = parse_record(&case.previous).expect("valid previous record");
            let next = parse_record(&case.next).expect("valid successor record encoding");
            let identity_unchanged = case.previous_identity == case.next_identity;
            assert_eq!(
                identity_unchanged && next.validate_successor(&previous).is_ok(),
                case.valid,
                "{}",
                case.name
            );
        }
    }
}
