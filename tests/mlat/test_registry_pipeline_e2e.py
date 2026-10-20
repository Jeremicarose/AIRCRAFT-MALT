"""Offline chain-to-API control. All observations are explicitly SYNTHETIC."""

import asyncio
import json
import time

from ckb_registry.record import ReceiverRegistryRecord
from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.ingest.feed_transports import JsonFeedParsingMixin
from mlat_reference.runtime import ProductionMLATSystem
from test_api import _load_api_module
from test_solver import build_known_position_observations


def test_verified_discovery_through_ingest_solver_storage_api_and_revocation(monkeypatch, tmp_path):
    target, observations = build_known_position_observations()
    database = tmp_path / "pipeline.db"
    code_hash = "0x" + "44" * 32
    system = ProductionMLATSystem(
        NetworkConfig(
            fourdsky_transport="simulation",
            receiver_registry_type_hash=code_hash,
            hybrid_simulation_min_receivers=1,
        ),
        str(database),
    )
    cells = []
    for index, observation in enumerate(observations):
        receiver = observation.receiver_position
        record = ReceiverRegistryRecord(
            receiver_id=receiver.receiver_id,
            latitude=receiver.latitude,
            longitude=receiver.longitude,
            altitude=receiver.altitude,
            status="online",
            capabilities=["mode-s", "mlat"],
            sequence=0,
            updated_at=1_700_000_000,
        )
        cells.append(
            {
                "output": {
                    "type": {
                        "code_hash": code_hash,
                        "hash_type": "data1",
                        "args": "0x" + f"{index+1:064x}",
                    },
                    "lock": {"code_hash": "0x" + "33" * 32, "hash_type": "type", "args": "0x1234"},
                },
                "output_data": record.to_cell_data_hex(),
                "out_point": {"tx_hash": "0x" + f"{index+10:064x}", "index": "0x0"},
            }
        )
    spent = set()

    async def rpc(method, params, url=None):
        if method == "get_cells":
            return {"objects": cells if len(params) == 3 else [], "last_cursor": "0x1"}
        assert method == "get_live_cell"
        candidate = next(item for item in cells if item["out_point"] == params[0])
        if candidate["output"]["type"]["args"] in spent:
            return {"status": "dead", "cell": None}
        return {
            "status": "live",
            "cell": {"output": candidate["output"], "data": {"content": candidate["output_data"]}},
        }

    monkeypatch.setattr(system.network_client.peer_discovery, "_rpc_call", rpc)
    system.database.connect()
    system.database.bind_runtime_provenance("SYNTHETIC", "offline-chain-to-api-control")
    parser = JsonFeedParsingMixin()

    async def run():
        discovered = await system.network_client.peer_discovery.discover_peers()
        system.network_client.active_receivers = {item.runtime_id: item for item in discovered}
        system._cache_receiver_positions()
        origin = time.time_ns()
        for index, observation in enumerate(observations):
            timestamp_ns = origin + observation.timestamp_ns - 1_700_000_000_000_000_000
            await parser.dispatch_feed_payload(
                json.dumps(
                    {
                        "receiver_id": cells[index]["output"]["type"]["args"],
                        "message": "8D4840D6202CC371C32CE0576098",
                        "timestamp_ns": str(timestamp_ns),
                        "clock_synchronized": True,
                        "clock_source": "synthetic-control",
                        "clock_uncertainty_ns": 1,
                    }
                ),
                system.handle_incoming_signal,
                allowed_receiver_ids=set(system.receiver_positions),
            )
        groups = system.correlator.correlate()
        assert len(groups) == 1
        await system._process_signal_group(groups[0])
        assert system.stats["successful_solves"] == 1
        assert system.database.get_latest_position().data_provenance == "SYNTHETIC"
        spent.update(item["output"]["type"]["args"] for item in cells[:3])
        # Indexer still advertises all six old records. Only three remain live.
        await system.network_client.refresh_registry_receivers()
        system._cache_receiver_positions()
        assert len(system.receiver_positions) == 3
        assert system.correlator.correlate() == []

    try:
        asyncio.run(run())
    finally:
        system.database.close()
    module = _load_api_module(monkeypatch, tmp_path, DATABASE_PATH=str(database))
    client = module.create_app().test_client()
    response = client.get("/api/positions/recent")
    assert response.status_code == 200
    position = response.get_json()["positions"][0]
    assert position["data_provenance"] == "SYNTHETIC"
    assert abs(position["position"]["latitude"] - target.latitude) < 0.0001
    assert len(client.get("/api/receivers").get_json()["receivers"]) == 3
