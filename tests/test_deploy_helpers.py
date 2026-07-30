from pathlib import Path
import subprocess
import sys


def test_generate_receiver_registry_deploy_config(tmp_path):
    contract = tmp_path / "receiver-registry"
    contract.write_bytes(b"binary")
    output = tmp_path / "deploy.toml"

    subprocess.run(
        [
            sys.executable,
            "scripts/generate_receiver_registry_deploy_config.py",
            "--contract-path",
            str(contract),
            "--lock-arg",
            "0xabc123",
            "--output",
            str(output),
        ],
        check=True,
    )

    text = output.read_text()
    assert "receiver_registry" in text
    assert "0xabc123" in text
    assert contract.resolve().as_posix() in text


def test_update_env_type_hash(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "RECEIVER_REGISTRY_TYPE_HASH=\nSIMULATE_IF_UNAVAILABLE=true\n"
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/update_env_type_hash.py",
            "--type-hash",
            "0x" + "dd" * 32,
            "--env-file",
            str(env_file),
            "--disable-simulation",
        ],
        check=True,
    )

    text = env_file.read_text()
    assert "RECEIVER_REGISTRY_TYPE_HASH=" + "0x" + "dd" * 32 in text
    assert "SIMULATE_IF_UNAVAILABLE=false" in text
