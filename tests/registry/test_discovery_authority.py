"""An indexer candidate is not authoritative until the node confirms it."""

import asyncio
import copy

import pytest

from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery
from test_ckb_registry import IDENTITY_A, receiver_cell, receiver_record


def discovery_with_responses(monkeypatch, node_result):
    candidate = receiver_cell(receiver_record(), IDENTITY_A)
    discovery = CKBPeerDiscovery(CKBConfig())
    calls = []

    async def rpc(method, params, url=None):
        calls.append((method, params))
        if method == "get_cells":
            return {"objects": [candidate] if len(params) == 3 else [], "last_cursor": "0x1"}
        assert method == "get_live_cell"
        assert params == [candidate["out_point"], True]
        if isinstance(node_result, Exception):
            raise node_result
        return node_result

    monkeypatch.setattr(discovery, "_rpc_call", rpc)
    return discovery, candidate, calls


@pytest.mark.parametrize("status", ["dead", "unknown"])
def test_spent_or_unknown_indexer_cell_is_not_discovered(monkeypatch, status):
    discovery, _, calls = discovery_with_responses(monkeypatch, {"status": status, "cell": None})
    assert asyncio.run(discovery.discover_peers()) == []
    assert discovery.cached_peers == {}
    assert any(method == "get_live_cell" for method, _ in calls)


@pytest.mark.parametrize("field", ["output_data", "owner_lock", "type_script"])
def test_indexer_cannot_override_node_data_or_ownership(monkeypatch, field):
    candidate = receiver_cell(receiver_record(), IDENTITY_A)
    node_cell = copy.deepcopy(candidate)
    if field == "output_data":
        node_cell["output_data"] = receiver_record(status="revoked", sequence=1).to_cell_data_hex()
    elif field == "owner_lock":
        node_cell["output"]["lock"]["args"] = "0x1234"
    else:
        node_cell["output"]["type"]["code_hash"] = "0x" + "aa" * 32
    response = {
        "status": "live",
        "cell": {"output": node_cell["output"], "data": {"content": node_cell["output_data"]}},
    }
    discovery, _, _ = discovery_with_responses(monkeypatch, response)
    with pytest.raises(RuntimeError, match="node|RPC"):
        asyncio.run(discovery.discover_peers())
    assert discovery.cached_peers == {}


def test_node_outage_invalidates_discovery_instead_of_falling_back(monkeypatch):
    discovery, _, _ = discovery_with_responses(monkeypatch, OSError("node unavailable"))
    with pytest.raises(OSError, match="unavailable"):
        asyncio.run(discovery.discover_peers())
    assert discovery.cached_peers == {}


def test_complete_discovery_has_a_deadline(monkeypatch):
    discovery = CKBPeerDiscovery(CKBConfig())
    discovery.config.discovery_timeout_seconds = 0.01

    async def slow_search():
        await asyncio.sleep(0.1)
        return []

    monkeypatch.setattr(discovery, "_search_receiver_cells", slow_search)
    with pytest.raises(TimeoutError):
        asyncio.run(discovery.discover_peers())
    assert discovery.cached_peers == {}


def test_stale_indexer_revocation_removes_pending_runtime_observations(monkeypatch, tmp_path):
    import time
    from mlat_reference.ingest.client import NetworkConfig
    from mlat_reference.runtime import ProductionMLATSystem

    system = ProductionMLATSystem(
        NetworkConfig(
            receiver_registry_type_hash="0x" + "44" * 32, fourdsky_transport="command-jsonl"
        ),
        str(tmp_path / "revocation.db"),
    )
    candidate = receiver_cell(receiver_record(), IDENTITY_A)
    spent = False

    async def rpc(method, params, url=None):
        if method == "get_tip_block_number":
            return "0x10"
        if method == "get_cells":
            return {"objects": [candidate] if len(params) == 3 else [], "last_cursor": "0x1"}
        assert method == "get_live_cell"
        return (
            {"status": "dead", "cell": None}
            if spent
            else {
                "status": "live",
                "cell": {
                    "output": candidate["output"],
                    "data": {"content": candidate["output_data"]},
                },
            }
        )

    monkeypatch.setattr(system.network_client.peer_discovery, "_rpc_call", rpc)
    system.database.connect()

    async def run():
        nonlocal spent
        await system.initialize_network()
        timestamp_ns = time.time_ns()

        async def receive(offset):
            await system.handle_incoming_signal(
                IDENTITY_A,
                (timestamp_ns + offset) / 1e9,
                "8D4840D6202CC371C32CE0576098",
                timestamp_ns=timestamp_ns + offset,
                clock_synchronized=True,
                clock_source="gps",
                clock_uncertainty_ns=50,
            )

        await receive(0)
        assert len(system.correlator.signal_buffer) == 1
        spent = True
        await system.network_client.refresh_registry_receivers()
        system._cache_receiver_positions()
        assert system.receiver_positions == {}
        assert system.correlator.signal_buffer == []
        assert system.database.get_receivers() == []
        await receive(1)
        assert system.correlator.signal_buffer == []
        assert system.observation_counts["rejected"] == 1

    try:
        asyncio.run(run())
    finally:
        system.database.close()
