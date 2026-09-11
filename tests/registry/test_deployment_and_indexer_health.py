import pytest

from tools.registry import check_registry_indexer_health as indexer_health
from tools.registry.check_registry_indexer_health import (
    classify_consistency,
    fetch_all_indexer_cells,
    identity_matches,
    outpoint_matches,
)
from tools.registry.verify_data1_deployment import ckb_data_hash, verify_live_cell


def test_data1_hash_matches_ckb_blake2b_vector():
    assert (
        ckb_data_hash("0x") == "0x44f4c69744d5f8c55d642062949dcae49bc4e7ef43d388c5a12f42b5633d163e"
    )


def test_data1_verifier_rejects_dead_or_mismatched_code_cell():
    report = verify_live_cell(
        {
            "status": "live",
            "cell": {"output": {}, "data": {"content": "0x01"}},
        },
        expected_code_hash="0x" + "aa" * 32,
        expected_tx_hash="0x" + "bb" * 32,
        expected_index=0,
    )
    assert report["pass"] is False
    assert report["observed_data_hash"] != "0x" + "aa" * 32
    assert report["queried_out_point"] == {
        "tx_hash": "0x" + "bb" * 32,
        "index": "0x0",
    }


def test_indexer_health_distinguishes_live_cell_from_indexer_lag():
    assert (
        classify_consistency(indexed_match=False, direct_status="live", expected_outpoint=True)
        == "indexer_lag"
    )
    assert (
        classify_consistency(indexed_match=True, direct_status="live", expected_outpoint=True)
        == "ok"
    )
    assert (
        classify_consistency(indexed_match=True, direct_status="dead", expected_outpoint=True)
        == "stale_indexer"
    )
    assert (
        classify_consistency(indexed_match=False, direct_status="rpc_error", expected_outpoint=True)
        == "rpc_unavailable"
    )


def test_indexer_health_matches_expected_outpoint_without_timestamp_winner():
    objects = [{"out_point": {"tx_hash": "0x" + "ab" * 32, "index": "0x0"}}]
    assert outpoint_matches(objects, "0x" + "ab" * 32, 0) is True
    assert outpoint_matches(objects, "0x" + "cd" * 32, 0) is False


def test_indexer_health_follows_short_pages_until_empty(monkeypatch):
    responses = [
        {"objects": [{"id": 1}], "last_cursor": "0x01"},
        {"objects": [{"id": 2}], "last_cursor": "0x02"},
        {"objects": [], "last_cursor": "0x02"},
    ]
    calls = []

    def fake_rpc(url, method, params, ca_bundle):
        calls.append((url, method, params, ca_bundle))
        return responses.pop(0)

    monkeypatch.setattr(indexer_health, "rpc_call", fake_rpc)
    objects, pages = fetch_all_indexer_cells(
        indexer_url="https://indexer.example",
        search_key={"script": {}},
        ca_bundle=None,
        page_size=100,
    )

    assert objects == [{"id": 1}, {"id": 2}]
    assert pages == 3
    assert len(calls) == 3
    assert len(calls[0][2]) == 3
    assert calls[1][2][-1] == "0x01"
    assert calls[2][2][-1] == "0x02"


def test_indexer_health_rejects_repeated_cursor(monkeypatch):
    monkeypatch.setattr(
        indexer_health,
        "rpc_call",
        lambda *_args: {"objects": [{"id": 1}], "last_cursor": "0x01"},
    )

    with pytest.raises(RuntimeError, match="invalid cursor"):
        fetch_all_indexer_cells(
            indexer_url="https://indexer.example",
            search_key={"script": {}},
            ca_bundle=None,
        )


def test_indexer_health_enforces_cell_limit(monkeypatch):
    monkeypatch.setattr(
        indexer_health,
        "rpc_call",
        lambda *_args: {"objects": [{"id": 1}, {"id": 2}], "last_cursor": "0x01"},
    )

    with pytest.raises(RuntimeError, match="cell safety limit"):
        fetch_all_indexer_cells(
            indexer_url="https://indexer.example",
            search_key={"script": {}},
            ca_bundle=None,
            max_cells=1,
        )


def test_indexer_health_does_not_crash_on_malformed_identity_shape():
    identity = "0x" + "12" * 32
    objects = [{"output": None}, {"output": {"type": None}}]
    assert identity_matches(objects, identity) == []
