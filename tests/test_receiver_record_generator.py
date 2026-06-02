import json
from pathlib import Path
import subprocess
import sys


def test_generate_receiver_registry_record(tmp_path):
    json_path = tmp_path / "record.json"
    hex_path = tmp_path / "record.hex"

    subprocess.run(
        [
            sys.executable,
            "scripts/generate_receiver_registry_record.py",
            "--receiver-id",
            "RECV_NYC_001",
            "--latitude",
            "40.7128",
            "--longitude",
            "-74.0060",
            "--altitude",
            "10",
            "--capability",
            "mode-s",
            "--capability",
            "mlat",
            "--stream-protocol",
            "websocket-json",
            "--stream-format",
            "json",
            "--output-json",
            str(json_path),
            "--output-hex",
            str(hex_path),
        ],
        check=True,
    )

    record = json.loads(json_path.read_text())
    payload_hex = hex_path.read_text().strip()

    assert record["receiver_id"] == "RECV_NYC_001"
    assert "mode-s" in record["capabilities"]
    assert "metadata" not in record
    assert payload_hex.startswith("0x")
