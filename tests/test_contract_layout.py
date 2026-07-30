from pathlib import Path


def test_contract_skeleton_exists():
    root = Path("contracts/receiver-registry")
    assert (root / "Cargo.toml").exists()
    assert (root / ".cargo" / "config.toml").exists()
    assert (root / "rust-toolchain.toml").exists()
    assert (root / "Makefile").exists()
    assert (root / "README.md").exists()
    assert (root / "src" / "error.rs").exists()
    assert (root / "src" / "record.rs").exists()
    assert (root / "src" / "entry.rs").exists()
    assert (root / "src" / "main.rs").exists()


def test_contract_mentions_canonical_schema_fields():
    record_rs = Path("contracts/receiver-registry/src/record.rs").read_text()
    for field in [
        "receiver_id",
        "latitude",
        "longitude",
        "altitude",
        "status",
        "capabilities",
        "schema_version",
        "sequence",
        "updated_at",
        "stream_endpoint",
        "stream_protocol",
        "stream_format",
        "metadata_hash",
    ]:
        assert field in record_rs


def test_contract_has_transaction_level_lifecycle_tests():
    lifecycle_test = Path("contracts/receiver-registry/tests/lifecycle.rs").read_text()
    for behavior in [
        "valid_creation_uses_type_id_identity",
        "creation_rejects_forged_identity",
        "valid_update_and_owner_transfer_pass",
        "sequence_jump_fails",
        "receiver_label_change_fails",
        "burn_fails_and_tombstone_revocation_passes",
        "revoked_identity_cannot_be_resurrected",
        "duplicate_registry_outputs_fail",
    ]:
        assert behavior in lifecycle_test
