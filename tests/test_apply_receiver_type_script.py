import json
from pathlib import Path
import subprocess
import sys


def test_apply_receiver_type_script(tmp_path):
    tx_file = tmp_path / "tx.json"
    template_file = tmp_path / "template.json"

    tx_file.write_text(
        json.dumps(
            {
                "transaction": {
                    "outputs": [
                        {
                            "lock": {"args": "0xabc"},
                            "type": None,
                        }
                    ]
                }
            }
        )
    )
    template_file.write_text(
        json.dumps(
            {
                "outputs": [
                    {
                        "type": {
                            "code_hash": "0xdeadbeef",
                            "hash_type": "type",
                            "args": "0x",
                        }
                    }
                ]
            }
        )
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/apply_receiver_type_script.py",
            "--tx-file",
            str(tx_file),
            "--template-file",
            str(template_file),
            "--contract-tx-hash",
            "0xcontract",
            "--contract-index",
            "0",
        ],
        check=True,
    )

    tx = json.loads(tx_file.read_text())
    assert tx["transaction"]["outputs"][0]["type"]["code_hash"] == "0xdeadbeef"
    assert tx["transaction"]["cell_deps"][0]["out_point"]["tx_hash"] == "0xcontract"
    assert tx["transaction"]["cell_deps"][0]["out_point"]["index"] == "0x0"
