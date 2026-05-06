import asyncio
import json
import time

from network.ckb_discovery import CKBConfig, CKBPeerDiscovery, ReceiverRegistryRecord


def test_receiver_registry_record_roundtrip_and_validation():
    record = ReceiverRegistryRecord(
        receiver_id="RECV_NYC_001",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        capabilities=["mode-s", "adsb", "mlat"],
        timestamp=1_700_000_000.0,
        stream_endpoint="wss://feed.example/ws",
        stream_protocol="websocket-json",
        stream_format="json",
        metadata={"region": "nyc"},
    )

    payload_hex = record.to_cell_data_hex()
    decoded = json.loads(bytes.fromhex(payload_hex[2:]).decode("utf-8"))
    restored = ReceiverRegistryRecord.from_dict(decoded)

    assert restored.receiver_id == "RECV_NYC_001"
    assert restored.stream_protocol == "websocket-json"
    assert restored.metadata == {"region": "nyc"}


def test_receiver_registry_record_rejects_missing_mode_s():
    record = ReceiverRegistryRecord(
        receiver_id="RECV_BAD_001",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        capabilities=["mlat"],
        timestamp=1_700_000_000.0,
    )

    try:
        record.validate()
    except ValueError as exc:
        assert "mode-s" in str(exc)
    else:
        raise AssertionError("Expected validation to fail")


def test_ckb_peer_discovery_prefers_latest_receiver_cell():
    discovery = CKBPeerDiscovery(CKBConfig(simulate_if_unavailable=True))
    now = time.time()

    older = ReceiverRegistryRecord(
        receiver_id="RECV_NYC_001",
        latitude=40.7,
        longitude=-74.0,
        altitude=10.0,
        status="online",
        capabilities=["mode-s", "mlat"],
        timestamp=now - 10,
    ).to_cell_data_hex()

    newer = ReceiverRegistryRecord(
        receiver_id="RECV_NYC_001",
        latitude=40.8,
        longitude=-73.9,
        altitude=20.0,
        status="online",
        capabilities=["mode-s", "mlat"],
        timestamp=now,
    ).to_cell_data_hex()

    cells = [
        {
            "output_data": older,
            "output": {"lock": {"args": "0xolder", "hash": "0xlock1"}},
        },
        {
            "output_data": newer,
            "output": {"lock": {"args": "0xnewer", "hash": "0xlock2"}},
        },
    ]

    async def fake_search():
        return cells

    discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
    discovery.simulation_mode = False

    receivers = asyncio.run(discovery.discover_peers())

    assert len(receivers) == 1
    assert receivers[0].latitude == 40.8
    assert receivers[0].altitude == 20.0
    assert receivers[0].ckb_address == "0xnewer"
