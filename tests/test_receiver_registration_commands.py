import json
from pathlib import Path
import subprocess
import sys


def test_print_receiver_registration_commands_selects_plain_funding_cell(tmp_path):
    template = tmp_path / "template.json"
    template.write_text(
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

    wrapper = tmp_path / "ckb-cli"
    wrapper.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--url\" ]; then shift 2; fi\n"
        "printf '%s' '{\"live_cells\":["
        "{\"tx_hash\":\"0xtypecell\",\"output_index\":0,\"type_hashes\":[\"0x1\"]},"
        "{\"tx_hash\":\"0xplaincell\",\"output_index\":1,\"type_hashes\":null}"
        "]}'\n"
    )
    wrapper.chmod(0o755)

    env = {"PATH": f"{tmp_path}:{Path('/usr/bin')}:{Path('/bin')}"}
    result = subprocess.run(
        [
            sys.executable,
            "scripts/print_receiver_registration_commands.py",
            "--address",
            "ckt1testaddress",
            "--template-file",
            str(template),
            "--contract-tx-hash",
            "0x" + "cc" * 32,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "0xplaincell#1" in result.stdout
    assert "ckb-cli --url https://testnet.ckb.dev/rpc tx send" in result.stdout
