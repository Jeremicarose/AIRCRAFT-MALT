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
        "timestamp",
        "stream_endpoint",
        "stream_protocol",
        "stream_format",
    ]:
        assert field in record_rs
