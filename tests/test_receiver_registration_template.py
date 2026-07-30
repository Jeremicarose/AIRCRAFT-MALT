import json
from pathlib import Path
import subprocess
import sys


def test_generate_receiver_registration_tx_template(tmp_path):
    data_hex_path = tmp_path / "record.hex"
    data_hex_path.write_text("0x1234\n")
    output_path = tmp_path / "tx.json"

    subprocess.run(
        [
            sys.executable,
            "scripts/generate_receiver_registration_tx_template.py",
            "--lock-arg",
            "0xabc123",
            "--type-hash",
            "0x" + "dd" * 32,
            "--data-hex-file",
            str(data_hex_path),
            "--output",
            str(output_path),
        ],
        check=True,
    )

    tx = json.loads(output_path.read_text())
    assert tx["outputs"][0]["lock"]["args"] == "0xabc123"
    assert tx["outputs"][0]["type"]["code_hash"] == "0x" + "dd" * 32
    assert tx["registry_v2"]["type_args_pending"] is True
    assert tx["outputs_data"][0] == "0x1234"
