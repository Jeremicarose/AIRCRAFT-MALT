from pathlib import Path


def test_contract_skeleton_exists():
    root = Path("contracts/receiver-registry")
    assert (root / "Cargo.toml").exists()
    assert (root / "src" / "lib.rs").exists()
    assert (root / "src" / "main.rs").exists()


def test_contract_mentions_canonical_schema_fields():
    lib_rs = Path("contracts/receiver-registry/src/lib.rs").read_text()
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
        assert field in lib_rs
