use ckb_hash::new_blake2b;
use receiver_registry::record::{decode_registry_v2_record, ReceiverRegistryRecord};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{HashMap, HashSet},
    env, fs,
};

const DEFAULT_IDENTITY: &str = "0x1111111111111111111111111111111111111111111111111111111111111111";

#[derive(Deserialize)]
struct Corpus {
    schema_version: u8,
    registry_script: RegistryScript,
    discovery_policy: DiscoveryPolicy,
    record_cases: Vec<RecordCase>,
    identity_cases: Vec<IdentityCase>,
    type_id_vectors: Vec<TypeIdVector>,
    creation_cases: Vec<CreationCase>,
    transition_cases: Vec<TransitionCase>,
    script_cases: Vec<ScriptCase>,
    discovery_cases: Vec<DiscoveryCase>,
}

#[derive(Deserialize)]
struct RegistryScript {
    code_hash: String,
    hash_type: String,
}

#[derive(Deserialize)]
struct DiscoveryPolicy {
    observed_at: u64,
    max_future_skew_seconds: u64,
}

#[derive(Deserialize)]
struct RecordCase {
    name: String,
    payload: String,
}

#[derive(Deserialize)]
struct IdentityCase {
    name: String,
    value: String,
}

#[derive(Deserialize)]
struct TypeIdVector {
    name: String,
    first_input_tx_hash: String,
    first_input_index: u32,
    first_input_since: u64,
    output_index: u64,
}

#[derive(Deserialize)]
struct CreationCase {
    name: String,
    record_case: String,
    first_input_tx_hash: String,
    first_input_index: u32,
    first_input_since: u64,
    output_index: u64,
    code_hash: String,
    hash_type: String,
    args: String,
}

#[derive(Deserialize)]
struct TransitionCase {
    name: String,
    previous: String,
    next: String,
    previous_identity: Option<String>,
    next_identity: Option<String>,
    previous_lock: Option<String>,
    next_lock: Option<String>,
}

#[derive(Deserialize)]
struct ScriptCase {
    name: String,
    code_hash: String,
    hash_type: String,
    args: String,
}

#[derive(Deserialize)]
struct DiscoveryCell {
    receiver_identity: String,
    record_case: String,
}

#[derive(Deserialize)]
struct DiscoveryCase {
    name: String,
    cells: Vec<DiscoveryCell>,
}

#[derive(Serialize)]
struct CaseResult {
    id: String,
    outcome: Value,
}

#[derive(Serialize)]
struct RunnerOutput {
    implementation: &'static str,
    corpus_schema_version: u8,
    results: Vec<CaseResult>,
}

fn canonical_record(record: &ReceiverRegistryRecord) -> Value {
    json!({
        "schema_version": record.schema_version,
        "receiver_id": record.receiver_id.as_str(),
        "latitude_f64_bits": format!("0x{:016x}", record.latitude.to_bits()),
        "longitude_f64_bits": format!("0x{:016x}", record.longitude.to_bits()),
        "altitude_f64_bits": format!("0x{:016x}", record.altitude.to_bits()),
        "status": record.status.as_str(),
        "capabilities": record.capabilities.iter().map(|item| item.as_str()).collect::<Vec<_>>(),
        "sequence": record.sequence.to_string(),
        "updated_at": record.updated_at.to_string(),
        "stream_endpoint": record.stream_endpoint.as_ref().map(|item| item.as_str()),
        "stream_protocol": record.stream_protocol.as_ref().map(|item| item.as_str()),
        "stream_format": record.stream_format.as_ref().map(|item| item.as_str()),
        "metadata_hash": record.metadata_hash.as_ref().map(|item| item.as_str()),
    })
}

fn normalize_identity(value: &str) -> Option<String> {
    let bytes = hex::decode(value.strip_prefix("0x")?).ok()?;
    (bytes.len() == 32).then(|| format!("0x{}", hex::encode(bytes)))
}

fn calculate_type_id(
    first_input_tx_hash: &str,
    first_input_index: u32,
    first_input_since: u64,
    output_index: u64,
) -> Option<String> {
    let tx_hash: [u8; 32] = hex::decode(first_input_tx_hash.strip_prefix("0x")?)
        .ok()?
        .try_into()
        .ok()?;
    let mut input = Vec::with_capacity(44);
    input.extend_from_slice(&first_input_since.to_le_bytes());
    input.extend_from_slice(&tx_hash);
    input.extend_from_slice(&first_input_index.to_le_bytes());
    let mut hasher = new_blake2b();
    hasher.update(&input);
    hasher.update(&output_index.to_le_bytes());
    let mut identity = [0u8; 32];
    hasher.finalize(&mut identity);
    Some(format!("0x{}", hex::encode(identity)))
}

fn record_outcome(case: &RecordCase) -> Value {
    match decode_registry_v2_record(case.payload.as_bytes()) {
        Ok(record) => json!({
            "accepted": true,
            "creation_accepted": record.validate_creation().is_ok(),
            "record": canonical_record(&record),
        }),
        Err(_) => json!({
            "accepted": false,
            "creation_accepted": false,
            "record": null,
        }),
    }
}

fn identity_outcome(case: &IdentityCase) -> Value {
    match normalize_identity(&case.value) {
        Some(normalized) => json!({"accepted": true, "normalized": normalized}),
        None => json!({"accepted": false, "normalized": null}),
    }
}

fn type_id_outcome(case: &TypeIdVector) -> Value {
    match calculate_type_id(
        &case.first_input_tx_hash,
        case.first_input_index,
        case.first_input_since,
        case.output_index,
    ) {
        Some(value) => json!({"accepted": true, "value": value}),
        None => json!({"accepted": false, "value": null}),
    }
}

fn creation_outcome(
    case: &CreationCase,
    records: &HashMap<&str, &RecordCase>,
    registry_script: &RegistryScript,
) -> Value {
    let receiver_identity = normalize_identity(&case.args);
    let expected_identity = calculate_type_id(
        &case.first_input_tx_hash,
        case.first_input_index,
        case.first_input_since,
        case.output_index,
    );
    let accepted = records
        .get(case.record_case.as_str())
        .and_then(|record_case| decode_registry_v2_record(record_case.payload.as_bytes()).ok())
        .is_some_and(|record| record.validate_creation().is_ok())
        && normalize_identity(&case.code_hash) == normalize_identity(&registry_script.code_hash)
        && case.hash_type == registry_script.hash_type
        && receiver_identity.is_some()
        && receiver_identity == expected_identity;
    json!({
        "accepted": accepted,
        "receiver_identity": if accepted { receiver_identity } else { None },
    })
}

fn transition_outcome(case: &TransitionCase) -> Value {
    let previous_identity = case
        .previous_identity
        .as_deref()
        .unwrap_or(DEFAULT_IDENTITY);
    let next_identity = case.next_identity.as_deref().unwrap_or(DEFAULT_IDENTITY);
    let identity_unchanged = matches!(
        (
            normalize_identity(previous_identity),
            normalize_identity(next_identity),
        ),
        (Some(previous), Some(next)) if previous == next
    );
    let validated = decode_registry_v2_record(case.previous.as_bytes()).and_then(|previous| {
        decode_registry_v2_record(case.next.as_bytes()).and_then(|next| {
            if !identity_unchanged {
                return Err(receiver_registry::error::Error::InvalidIdentityRule);
            }
            next.validate_successor(&previous)?;
            Ok(next)
        })
    });
    match validated {
        Ok(next) => {
            let action = if next.status.as_str() == "revoked" {
                "revoke"
            } else if case.previous_lock != case.next_lock {
                "transfer"
            } else {
                "update"
            };
            json!({"accepted": true, "action": action})
        }
        Err(_) => json!({"accepted": false, "action": null}),
    }
}

fn script_outcome(case: &ScriptCase, registry_script: &RegistryScript) -> Value {
    let receiver_identity = normalize_identity(&case.args);
    let accepted = normalize_identity(&case.code_hash)
        == normalize_identity(&registry_script.code_hash)
        && case.hash_type == registry_script.hash_type
        && receiver_identity.is_some();
    json!({
        "accepted": accepted,
        "receiver_identity": if accepted { receiver_identity } else { None },
    })
}

fn discovery_outcome(
    case: &DiscoveryCase,
    records: &HashMap<&str, &RecordCase>,
    policy: &DiscoveryPolicy,
) -> Value {
    let mut seen = HashSet::new();
    let mut duplicates = HashSet::new();
    let mut by_identity: HashMap<String, ReceiverRegistryRecord> = HashMap::new();

    for cell in &case.cells {
        let Some(identity) = normalize_identity(&cell.receiver_identity) else {
            continue;
        };
        if duplicates.contains(&identity) {
            continue;
        }
        if !seen.insert(identity.clone()) {
            duplicates.insert(identity.clone());
            by_identity.remove(&identity);
            continue;
        }
        let Some(record_case) = records.get(cell.record_case.as_str()) else {
            continue;
        };
        if let Ok(record) = decode_registry_v2_record(record_case.payload.as_bytes()) {
            by_identity.insert(identity, record);
        }
    }

    let mut active = by_identity
        .iter()
        .filter(|(_, record)| {
            record.status.as_str() == "online"
                && record.updated_at
                    <= policy
                        .observed_at
                        .saturating_add(policy.max_future_skew_seconds)
        })
        .map(|(identity, _)| identity.clone())
        .collect::<Vec<_>>();
    let mut including_revoked = by_identity
        .iter()
        .filter(|(_, record)| {
            record.updated_at
                <= policy
                    .observed_at
                    .saturating_add(policy.max_future_skew_seconds)
        })
        .map(|(identity, _)| identity.clone())
        .collect::<Vec<_>>();
    let mut quarantined = duplicates.into_iter().collect::<Vec<_>>();
    active.sort();
    including_revoked.sort();
    quarantined.sort();
    json!({
        "active_identities": active,
        "including_revoked_identities": including_revoked,
        "quarantined_identities": quarantined,
    })
}

fn main() {
    let corpus_path = env::args()
        .nth(1)
        .expect("usage: cargo run --example conformance -- CORPUS");
    let corpus: Corpus =
        serde_json::from_str(&fs::read_to_string(corpus_path).expect("read corpus"))
            .expect("parse corpus");
    let records = corpus
        .record_cases
        .iter()
        .map(|case| (case.name.as_str(), case))
        .collect::<HashMap<_, _>>();
    let mut results = Vec::new();
    let mut add = |category: &str, name: &str, outcome: Value| {
        results.push(CaseResult {
            id: format!("{category}/{name}"),
            outcome,
        });
    };

    for case in &corpus.record_cases {
        add("record", &case.name, record_outcome(case));
    }
    for case in &corpus.identity_cases {
        add("identity", &case.name, identity_outcome(case));
    }
    for case in &corpus.type_id_vectors {
        add("type_id", &case.name, type_id_outcome(case));
    }
    for case in &corpus.creation_cases {
        add(
            "creation",
            &case.name,
            creation_outcome(case, &records, &corpus.registry_script),
        );
    }
    for case in &corpus.transition_cases {
        add("transition", &case.name, transition_outcome(case));
    }
    for case in &corpus.script_cases {
        add(
            "script",
            &case.name,
            script_outcome(case, &corpus.registry_script),
        );
    }
    for case in &corpus.discovery_cases {
        add(
            "discovery",
            &case.name,
            discovery_outcome(case, &records, &corpus.discovery_policy),
        );
    }

    println!(
        "{}",
        serde_json::to_string(&RunnerOutput {
            implementation: "rust",
            corpus_schema_version: corpus.schema_version,
            results,
        })
        .expect("serialize conformance results")
    );
}
