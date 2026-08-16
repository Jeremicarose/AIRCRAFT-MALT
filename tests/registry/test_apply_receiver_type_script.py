import json
import subprocess
import sys


def test_apply_receiver_type_script(tmp_path):
    tx_file = tmp_path / "tx.json"
    template_file = tmp_path / "template.json"

    tx_file.write_text(
        json.dumps(
            {
                "transaction": {
                    "inputs": [
                        {
                            "since": "0x0",
                            "previous_output": {
                                "tx_hash": "0x" + "11" * 32,
                                "index": "0x1",
                            },
                        }
                    ],
                    "outputs": [
                        {
                            "lock": {"args": "0xabc"},
                            "type": None,
                        }
                    ],
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
                            "code_hash": "0x" + "dd" * 32,
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
            "tools/registry/apply_receiver_type_script.py",
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
    assert tx["transaction"]["outputs"][0]["type"]["code_hash"] == "0x" + "dd" * 32
    assert tx["transaction"]["outputs"][0]["type"]["args"] == (
        "0x45d0ccb8d96da425ce73e1f2daa91d46e8d9dabc11293897eabad9f31a513cbd"
    )
    assert tx["transaction"]["cell_deps"][0]["out_point"]["tx_hash"] == "0xcontract"
    assert tx["transaction"]["cell_deps"][0]["out_point"]["index"] == "0x0"


def test_apply_receiver_type_script_preserves_existing_identity_for_update(tmp_path):
    tx_file = tmp_path / "tx.json"
    template_file = tmp_path / "template.json"
    identity_id = "0x" + "aa" * 32
    tx_file.write_text(json.dumps({"transaction": {"outputs": [{"type": None}]}}))
    template_file.write_text(
        json.dumps(
            {
                "outputs": [
                    {"type": {"code_hash": "0x" + "dd" * 32, "hash_type": "type", "args": "0x"}}
                ]
            }
        )
    )

    subprocess.run(
        [
            sys.executable,
            "tools/registry/apply_receiver_type_script.py",
            "--tx-file",
            str(tx_file),
            "--template-file",
            str(template_file),
            "--contract-tx-hash",
            "0xcontract",
            "--identity-id",
            identity_id,
        ],
        check=True,
    )

    tx = json.loads(tx_file.read_text())
    assert tx["transaction"]["outputs"][0]["type"]["args"] == identity_id
