use ckb_system_scripts::BUNDLED_CELL;
use ckb_testtool::{
    ckb_crypto::secp::Privkey,
    ckb_hash::{blake2b_256, new_blake2b},
    ckb_types::{
        bytes::Bytes,
        core::{ScriptHashType, TransactionBuilder, TransactionView},
        packed::{self, CellDep, CellInput, CellOutput, OutPoint, Script, WitnessArgs},
        prelude::*,
        H256,
    },
    context::Context,
};
use std::{fs, path::PathBuf};

const MAX_CYCLES: u64 = 20_000_000;

struct Scripts {
    context: Context,
    contract_out_point: OutPoint,
    lock_out_point: OutPoint,
    secp256k1_data_dep: CellDep,
}

fn setup() -> Scripts {
    let mut context = Context::default();
    let contract_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("target/riscv64imac-unknown-none-elf/release/receiver-registry");
    let contract_bin: Bytes = fs::read(contract_path)
        .expect("build contract first")
        .into();
    let contract_out_point = context.deploy_cell(contract_bin);
    let secp256k1_data = BUNDLED_CELL
        .get("specs/cells/secp256k1_data")
        .expect("bundled secp256k1 data");
    let secp256k1_sighash_all = BUNDLED_CELL
        .get("specs/cells/secp256k1_blake160_sighash_all")
        .expect("bundled secp256k1 sighash lock");
    let secp256k1_data_out_point = context.deploy_cell(secp256k1_data.to_vec().into());
    let lock_out_point = context.deploy_cell(secp256k1_sighash_all.to_vec().into());
    Scripts {
        context,
        contract_out_point,
        lock_out_point,
        secp256k1_data_dep: CellDep::new_builder()
            .out_point(secp256k1_data_out_point)
            .build(),
    }
}

fn owner_key(owner: u8) -> Privkey {
    Privkey::from_slice(&[owner; 32])
}

fn blake160(data: &[u8]) -> [u8; 20] {
    let hash = blake2b_256(data);
    let mut result = [0u8; 20];
    result.copy_from_slice(&hash[..20]);
    result
}

fn lock_script(scripts: &mut Scripts, owner: u8) -> Script {
    let public_key = owner_key(owner).pubkey().expect("owner public key");
    let lock_args = blake160(&public_key.serialize());
    scripts
        .context
        .build_script_with_hash_type(
            &scripts.lock_out_point,
            ScriptHashType::Type,
            Bytes::from(lock_args.to_vec()),
        )
        .expect("secp256k1 sighash lock")
}

fn registry_script(scripts: &mut Scripts, identity: [u8; 32]) -> Script {
    scripts
        .context
        .build_script(&scripts.contract_out_point, Bytes::from(identity.to_vec()))
        .expect("registry script")
}

fn type_id(input: &CellInput, output_index: u64) -> [u8; 32] {
    let mut blake2b = new_blake2b();
    blake2b.update(input.as_slice());
    blake2b.update(&output_index.to_le_bytes());
    let mut identity = [0u8; 32];
    blake2b.finalize(&mut identity);
    identity
}

fn sign_tx(tx: TransactionView, key: &Privkey) -> TransactionView {
    const SIGNATURE_SIZE: usize = 65;

    let unsigned_witness = WitnessArgs::default();
    let zero_signature = Bytes::from(vec![0u8; SIGNATURE_SIZE]);
    let witness_for_digest = unsigned_witness
        .clone()
        .as_builder()
        .lock(Some(zero_signature).pack())
        .build();

    let mut hasher = new_blake2b();
    hasher.update(&tx.hash().raw_data());
    hasher.update(&(witness_for_digest.as_bytes().len() as u64).to_le_bytes());
    hasher.update(&witness_for_digest.as_bytes());
    for witness in tx.witnesses().into_iter().skip(1) {
        hasher.update(&(witness.raw_data().len() as u64).to_le_bytes());
        hasher.update(&witness.raw_data());
    }

    let mut message = [0u8; 32];
    hasher.finalize(&mut message);
    let signature = key
        .sign_recoverable(&H256::from(message))
        .expect("sign transaction")
        .serialize();
    let signed_witness = unsigned_witness
        .as_builder()
        .lock(Some(Bytes::from(signature)).pack())
        .build()
        .as_bytes()
        .pack();
    let mut witnesses: Vec<packed::Bytes> = tx.witnesses().into_iter().collect();
    if witnesses.is_empty() {
        witnesses.push(signed_witness);
    } else {
        witnesses[0] = signed_witness;
    }
    tx.as_advanced_builder().set_witnesses(witnesses).build()
}

#[test]
fn type_id_matches_off_chain_tooling_vector() {
    let input = CellInput::new_builder()
        .previous_output(
            OutPoint::new_builder()
                .tx_hash([0x11u8; 32].pack())
                .index(1u32)
                .build(),
        )
        .build();
    let expected =
        hex::decode("45d0ccb8d96da425ce73e1f2daa91d46e8d9dabc11293897eabad9f31a513cbd").unwrap();

    assert_eq!(type_id(&input, 0).as_slice(), expected.as_slice());
}

fn record(sequence: u64, updated_at: u64, status: &str) -> Bytes {
    let stream = if status == "revoked" {
        String::new()
    } else {
        r#","stream_endpoint":"wss://feed.example/ws","stream_protocol":"websocket-json","stream_format":"json""#.to_owned()
    };
    Bytes::from(
        format!(
            r#"{{"schema_version":2,"receiver_id":"RECV_NYC_001","latitude":40.7128,"longitude":-74.006,"altitude":10.0,"status":"{status}","capabilities":["mode-s","mlat"],"sequence":{sequence},"updated_at":{updated_at}{stream}}}"#,
        )
        .into_bytes(),
    )
}

fn create_registry_cell(
    scripts: &mut Scripts,
    type_script: Script,
    owner: u8,
    data: Bytes,
) -> OutPoint {
    let lock = lock_script(scripts, owner);
    scripts.context.create_cell(
        CellOutput::new_builder()
            .capacity(1_000u64)
            .lock(lock)
            .type_(Some(type_script).pack())
            .build(),
        data,
    )
}

fn verify_creation(identity_override: Option<[u8; 32]>) -> Result<u64, String> {
    let mut scripts = setup();
    let lock = lock_script(&mut scripts, 1);
    let funding_out_point = scripts.context.create_cell(
        CellOutput::new_builder()
            .capacity(2_000u64)
            .lock(lock.clone())
            .build(),
        Bytes::new(),
    );
    let input = CellInput::new_builder()
        .previous_output(funding_out_point)
        .build();
    let identity = identity_override.unwrap_or_else(|| type_id(&input, 0));
    let type_script = registry_script(&mut scripts, identity);
    let output = CellOutput::new_builder()
        .capacity(1_000u64)
        .lock(lock)
        .type_(Some(type_script).pack())
        .build();
    let tx = TransactionBuilder::default()
        .input(input)
        .output(output)
        .output_data(record(0, 1_700_000_000, "online").pack())
        .cell_dep(scripts.secp256k1_data_dep.clone())
        .build();
    let tx = scripts.context.complete_tx(tx);
    let tx = sign_tx(tx, &owner_key(1));
    scripts
        .context
        .verify_tx(&tx, MAX_CYCLES)
        .map_err(|error| error.to_string())
}

fn verify_transition(
    previous: Bytes,
    next: Option<Bytes>,
    previous_owner: u8,
    next_owner: u8,
    duplicate_output: bool,
) -> Result<u64, String> {
    verify_transition_as(
        previous,
        next,
        previous_owner,
        next_owner,
        previous_owner,
        duplicate_output,
    )
}

fn verify_transition_as(
    previous: Bytes,
    next: Option<Bytes>,
    previous_owner: u8,
    next_owner: u8,
    signer: u8,
    duplicate_output: bool,
) -> Result<u64, String> {
    let mut scripts = setup();
    let type_script = registry_script(&mut scripts, [7u8; 32]);
    let previous_out_point =
        create_registry_cell(&mut scripts, type_script.clone(), previous_owner, previous);
    let input = CellInput::new_builder()
        .previous_output(previous_out_point)
        .build();
    let mut builder = TransactionBuilder::default().input(input);

    if let Some(next_data) = next {
        let next_lock = lock_script(&mut scripts, next_owner);
        let output = CellOutput::new_builder()
            .capacity(1_000u64)
            .lock(next_lock)
            .type_(Some(type_script.clone()).pack())
            .build();
        builder = builder
            .output(output.clone())
            .output_data(next_data.clone().pack());
        if duplicate_output {
            builder = builder.output(output).output_data(next_data.pack());
        }
    }

    let tx = builder.cell_dep(scripts.secp256k1_data_dep.clone()).build();
    let tx = scripts.context.complete_tx(tx);
    let tx = sign_tx(tx, &owner_key(signer));
    scripts
        .context
        .verify_tx(&tx, MAX_CYCLES)
        .map_err(|error| error.to_string())
}

#[test]
fn valid_creation_uses_type_id_identity() {
    assert!(verify_creation(None).is_ok());
}

#[test]
fn creation_rejects_forged_identity() {
    assert!(verify_creation(Some([9u8; 32])).is_err());
}

#[test]
fn valid_update_and_owner_transfer_pass() {
    assert!(verify_transition(
        record(0, 1_700_000_000, "online"),
        Some(record(1, 1_700_000_001, "degraded")),
        1,
        2,
        false,
    )
    .is_ok());
}

#[test]
fn wrong_owner_signature_cannot_update() {
    assert!(verify_transition_as(
        record(0, 1_700_000_000, "online"),
        Some(record(1, 1_700_000_001, "online")),
        1,
        1,
        2,
        false,
    )
    .is_err());
}

#[test]
fn sequence_jump_fails() {
    assert!(verify_transition(
        record(0, 1_700_000_000, "online"),
        Some(record(2, 1_700_000_001, "online")),
        1,
        1,
        false,
    )
    .is_err());
}

#[test]
fn receiver_label_change_fails() {
    let changed_label = Bytes::from(
        String::from_utf8(record(1, 1_700_000_001, "online").to_vec())
            .unwrap()
            .replace("RECV_NYC_001", "RECV_ATTACKER")
            .into_bytes(),
    );
    assert!(verify_transition(
        record(0, 1_700_000_000, "online"),
        Some(changed_label),
        1,
        1,
        false,
    )
    .is_err());
}

#[test]
fn burn_fails_and_tombstone_revocation_passes() {
    assert!(verify_transition(record(0, 1_700_000_000, "online"), None, 1, 1, false,).is_err());
    assert!(verify_transition(
        record(0, 1_700_000_000, "online"),
        Some(record(1, 1_700_000_001, "revoked")),
        1,
        1,
        false,
    )
    .is_ok());
}

#[test]
fn revoked_identity_cannot_be_resurrected() {
    assert!(verify_transition(
        record(1, 1_700_000_001, "revoked"),
        Some(record(2, 1_700_000_002, "online")),
        1,
        1,
        false,
    )
    .is_err());
}

#[test]
fn duplicate_registry_outputs_fail() {
    assert!(verify_transition(
        record(0, 1_700_000_000, "online"),
        Some(record(1, 1_700_000_001, "online")),
        1,
        1,
        true,
    )
    .is_err());
}
