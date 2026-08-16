import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.registry import registry_v2_testnet_lifecycle as lifecycle


def test_write_tx_builds_registry_transaction_without_secret_material(tmp_path):
    tx_path = tmp_path / "create.json"
    sighash_dep = {
        "out_point": {"tx_hash": "0x" + "11" * 32, "index": "0x0"},
        "dep_type": "dep_group",
    }

    lifecycle.write_tx(
        tx_path,
        input_tx_hash="0x" + "22" * 32,
        input_index=1,
        outputs=[
            lifecycle.output(
                100_000_000_000,
                "0x" + "33" * 20,
                lifecycle.type_script("0x" + "44" * 32, "0x" + "55" * 32),
            )
        ],
        outputs_data=["0x7b7d"],
        sighash_dep=sighash_dep,
        contract_tx_hash="0x" + "66" * 32,
        contract_index=0,
    )

    transaction_file = json.loads(tx_path.read_text())
    transaction = transaction_file["transaction"]
    assert transaction["inputs"][0]["previous_output"]["index"] == "0x1"
    assert transaction["outputs"][0]["type"] == {
        "args": "0x" + "55" * 32,
        "code_hash": "0x" + "44" * 32,
        "hash_type": "type",
    }
    assert transaction["cell_deps"][0] == sighash_dep
    assert transaction["cell_deps"][1]["dep_type"] == "code"
    assert transaction_file["signatures"] == {}
    assert "private" not in tx_path.read_text().lower()


def test_write_tx_rejects_mismatched_outputs_and_data(tmp_path):
    with pytest.raises(ValueError, match="equal lengths"):
        lifecycle.write_tx(
            tmp_path / "invalid.json",
            input_tx_hash="0x" + "22" * 32,
            input_index=0,
            outputs=[],
            outputs_data=["0x"],
            sighash_dep={},
            contract_tx_hash="0x" + "66" * 32,
            contract_index=0,
        )


def test_submission_records_public_result_without_private_key_path(tmp_path, monkeypatch):
    tx_path = tmp_path / "tx.json"
    tx_path.write_text("{}\n")
    key_path = Path("/private/tmp/secret-owner.key")
    tx_hash = "0x" + "77" * 32
    results = iter(
        [
            SimpleNamespace(returncode=0, stdout="[]\n", stderr=""),
            SimpleNamespace(returncode=0, stdout=json.dumps(tx_hash) + "\n", stderr=""),
        ]
    )
    monkeypatch.setattr(lifecycle.subprocess, "run", lambda *args, **kwargs: next(results))
    response_path = tmp_path / "response.json"

    assert (
        lifecycle.signed_submission(
            tx_path=tx_path,
            key_path=key_path,
            rpc_url="https://testnet.invalid/rpc",
            response_path=response_path,
            expect_accept=True,
        )
        == tx_hash
    )
    response_text = response_path.read_text()
    assert str(key_path) not in response_text
    assert json.loads(response_text)["expected"] == "accepted"


def test_attack_must_be_rejected(tmp_path, monkeypatch):
    tx_path = tmp_path / "attack.json"
    tx_path.write_text("{}\n")
    results = iter(
        [
            SimpleNamespace(returncode=0, stdout="[]\n", stderr=""),
            SimpleNamespace(returncode=0, stdout='"0x' + "88" * 32 + '"\n', stderr=""),
        ]
    )
    monkeypatch.setattr(lifecycle.subprocess, "run", lambda *args, **kwargs: next(results))

    with pytest.raises(RuntimeError, match="unexpectedly accepted"):
        lifecycle.signed_submission(
            tx_path=tx_path,
            key_path=Path("/private/tmp/test.key"),
            rpc_url="https://testnet.invalid/rpc",
            response_path=tmp_path / "response.json",
            expect_accept=False,
        )


def test_revocation_record_has_no_stream_fields():
    revoked = lifecycle.record("RECV_TEST", 3, 1_700_000_003, status="revoked")
    payload = revoked.to_payload_dict()
    assert payload["status"] == "revoked"
    assert "stream_endpoint" not in payload
    assert "stream_protocol" not in payload
    assert "stream_format" not in payload
