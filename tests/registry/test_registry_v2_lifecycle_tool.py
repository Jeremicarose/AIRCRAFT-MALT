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
        "hash_type": "data1",
    }
    assert transaction["cell_deps"][0] == sighash_dep
    assert transaction["cell_deps"][1]["dep_type"] == "code"
    assert transaction_file["signatures"] == {}
    assert "private" not in tx_path.read_text().lower()


def test_type_script_requires_an_explicit_supported_code_binding():
    code_hash = "0x" + "44" * 32
    identity = "0x" + "55" * 32

    assert lifecycle.type_script(code_hash, identity)["hash_type"] == "data1"
    assert lifecycle.type_script(code_hash, identity, "type")["hash_type"] == "type"
    with pytest.raises(ValueError, match="data1 or type"):
        lifecycle.type_script(code_hash, identity, "data")


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


def test_capture_state_uses_exact_identity_and_collects_every_indexer_page(tmp_path, monkeypatch):
    identity = "0x" + "55" * 32
    expected = {"tx_hash": "0x" + "66" * 32, "index": "0x0"}
    conflicting = {"tx_hash": "0x" + "77" * 32, "index": "0x0"}
    responses = iter(
        [
            {"objects": [{"out_point": expected}], "last_cursor": "0x01"},
            {"objects": [{"out_point": conflicting}], "last_cursor": "0x02"},
            {"objects": [], "last_cursor": "0x02"},
        ]
    )
    calls = []

    def fake_rpc(url, method, params):
        calls.append((url, method, params))
        return next(responses)

    async def fake_discovery_snapshot(**kwargs):
        assert kwargs["registry_hash_type"] == "data1"
        return []

    monkeypatch.setattr(lifecycle, "rpc", fake_rpc)
    monkeypatch.setattr(lifecycle, "discovery_snapshot", fake_discovery_snapshot)
    monkeypatch.setattr(lifecycle, "capture_api_response", lambda **kwargs: None)

    lifecycle.capture_state(
        name="create",
        evidence_dir=tmp_path,
        rpc_url="https://testnet.invalid/rpc",
        indexer_url="https://testnet.invalid/indexer",
        contract_code_hash="0x" + "44" * 32,
        registry_hash_type="data1",
        receiver_identity=identity,
        expected_out_point=expected,
        timeout=1,
    )

    search_key = calls[0][2][0]
    assert search_key["script"] == {
        "code_hash": "0x" + "44" * 32,
        "hash_type": "data1",
        "args": identity,
    }
    assert search_key["script_search_mode"] == "exact"
    assert calls[1][2][-1] == "0x01"
    assert calls[2][2][-1] == "0x02"
    saved = json.loads((tmp_path / "discovery" / "create-indexer.json").read_text())
    assert [item["out_point"] for item in saved["objects"]] == [expected, conflicting]


def test_capture_state_fails_closed_on_non_advancing_indexer_cursor(tmp_path, monkeypatch):
    identity = "0x" + "55" * 32
    expected = {"tx_hash": "0x" + "66" * 32, "index": "0x0"}
    responses = iter(
        [
            {"objects": [{"out_point": expected}], "last_cursor": "0x01"},
            {"objects": [{"out_point": expected}], "last_cursor": "0x01"},
        ]
    )
    monkeypatch.setattr(lifecycle, "rpc", lambda *args, **kwargs: next(responses))

    with pytest.raises(RuntimeError, match="invalid cursor"):
        lifecycle.capture_state(
            name="create",
            evidence_dir=tmp_path,
            rpc_url="https://testnet.invalid/rpc",
            indexer_url="https://testnet.invalid/indexer",
            contract_code_hash="0x" + "44" * 32,
            registry_hash_type="data1",
            receiver_identity=identity,
            expected_out_point=expected,
            timeout=1,
        )


def test_capture_state_fails_closed_when_indexer_never_exhausts(tmp_path, monkeypatch):
    identity = "0x" + "55" * 32
    expected = {"tx_hash": "0x" + "66" * 32, "index": "0x0"}
    cursor = 0

    def endless_page(*args, **kwargs):
        nonlocal cursor
        cursor += 1
        return {
            "objects": [{"out_point": expected}],
            "last_cursor": hex(cursor),
        }

    monkeypatch.setattr(lifecycle, "INDEXER_MAX_PAGES", 2)
    monkeypatch.setattr(lifecycle, "rpc", endless_page)

    with pytest.raises(RuntimeError, match="page safety limit"):
        lifecycle.capture_state(
            name="create",
            evidence_dir=tmp_path,
            rpc_url="https://testnet.invalid/rpc",
            indexer_url="https://testnet.invalid/indexer",
            contract_code_hash="0x" + "44" * 32,
            registry_hash_type="data1",
            receiver_identity=identity,
            expected_out_point=expected,
            timeout=1,
        )
