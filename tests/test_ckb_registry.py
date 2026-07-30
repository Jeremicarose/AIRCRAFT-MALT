import asyncio
import json
import time

import pytest

from network.ckb_discovery import CKBConfig, CKBPeerDiscovery
from network.receiver_registry import ReceiverRegistryRecord


IDENTITY_A = "0x" + "11" * 32
IDENTITY_B = "0x" + "22" * 32


def receiver_record(**overrides):
    values = {
        "receiver_id": "RECV_NYC_001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 10.0,
        "status": "online",
        "capabilities": ["mode-s", "mlat"],
        "sequence": 0,
        "updated_at": 1_700_000_000,
    }
    values.update(overrides)
    return ReceiverRegistryRecord(**values)


def receiver_cell(record, identity_id, *, lock_arg="0xowner", tx_hash=None):
    return {
        "output_data": record.to_cell_data_hex(),
        "output": {
            "lock": {
                "code_hash": "0x" + "33" * 32,
                "hash_type": "type",
                "args": lock_arg,
            },
            "type": {
                "code_hash": "0x" + "44" * 32,
                "hash_type": "type",
                "args": identity_id,
            },
        },
        "out_point": {
            "tx_hash": tx_hash or "0x" + "55" * 32,
            "index": "0x0",
        },
        "block_number": "0x10",
    }


def test_receiver_registry_record_roundtrip_and_validation():
    record = receiver_record(
        capabilities=["mode-s", "adsb", "mlat"],
        stream_endpoint="wss://feed.example/ws",
        stream_protocol="websocket-json",
        stream_format="json",
        metadata_hash="0x" + "ab" * 32,
    )

    payload_hex = record.to_cell_data_hex()
    decoded = json.loads(bytes.fromhex(payload_hex[2:]).decode("utf-8"))
    restored = ReceiverRegistryRecord.from_dict(decoded)

    assert restored.receiver_id == "RECV_NYC_001"
    assert restored.stream_protocol == "websocket-json"
    assert restored.schema_version == 2
    assert restored.sequence == 0
    assert restored.metadata_hash == "0x" + "ab" * 32


def test_receiver_registry_record_omits_optional_null_fields_from_payload():
    record = receiver_record(
        stream_protocol="websocket-json",
        stream_format="json",
    )

    payload = record.to_payload_dict()

    assert "metadata_hash" not in payload
    assert "stream_endpoint" not in payload


def test_receiver_registry_record_rejects_missing_mode_s():
    record = receiver_record(receiver_id="RECV_BAD_001", capabilities=["mlat"])

    with pytest.raises(ValueError, match="mode-s"):
        record.validate()


def test_registry_transition_requires_immutable_label_and_next_sequence():
    previous = receiver_record(sequence=7, updated_at=1_700_000_000)

    receiver_record(sequence=8, updated_at=1_700_000_001).validate_successor(previous)

    with pytest.raises(ValueError, match="receiver_id"):
        receiver_record(
            receiver_id="RECV_OTHER",
            sequence=8,
            updated_at=1_700_000_001,
        ).validate_successor(previous)
    with pytest.raises(ValueError, match="sequence"):
        receiver_record(sequence=9, updated_at=1_700_000_001).validate_successor(previous)


def test_revocation_is_terminal():
    active = receiver_record(sequence=2)
    revoked = receiver_record(
        status="revoked",
        sequence=3,
        updated_at=1_700_000_001,
    )
    revoked.validate_successor(active)

    with pytest.raises(ValueError, match="revoked"):
        receiver_record(sequence=4, updated_at=1_700_000_002).validate_successor(revoked)


def test_ckb_peer_discovery_keeps_duplicate_labels_as_distinct_identities():
    discovery = CKBPeerDiscovery(CKBConfig(simulate_if_unavailable=True))
    now = time.time()
    cells = [
        receiver_cell(
            receiver_record(updated_at=int(now), latitude=40.7),
            IDENTITY_A,
            lock_arg="0xowner-a",
        ),
        receiver_cell(
            receiver_record(updated_at=int(now), latitude=40.8),
            IDENTITY_B,
            lock_arg="0xowner-b",
        ),
    ]

    async def fake_search():
        return cells

    discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
    discovery.simulation_mode = False

    receivers = asyncio.run(discovery.discover_peers())

    assert len(receivers) == 2
    assert {receiver.identity_id for receiver in receivers} == {IDENTITY_A, IDENTITY_B}
    assert {receiver.receiver_id for receiver in receivers} == {"RECV_NYC_001"}


def test_ckb_peer_discovery_quarantines_duplicate_live_identity():
    discovery = CKBPeerDiscovery(CKBConfig(simulate_if_unavailable=True))
    now = int(time.time())
    cells = [
        receiver_cell(receiver_record(updated_at=now), IDENTITY_A),
        receiver_cell(
            receiver_record(updated_at=now, sequence=1),
            IDENTITY_A,
            tx_hash="0x" + "66" * 32,
        ),
    ]

    async def fake_search():
        return cells

    discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
    discovery.simulation_mode = False

    assert asyncio.run(discovery.discover_peers()) == []


def test_indexer_search_paginates_until_cursor_is_exhausted():
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash="0x" + "44" * 32,
            registry_page_size=2,
        )
    )
    calls = []

    async def fake_rpc(method, params, url=None):
        calls.append(params)
        if len(calls) == 1:
            return {"objects": [{"id": 1}, {"id": 2}], "last_cursor": "0xcursor"}
        return {"objects": [{"id": 3}], "last_cursor": "0xcursor2"}

    discovery._rpc_call = fake_rpc  # type: ignore[method-assign]

    cells = asyncio.run(discovery._search_receiver_cells())

    assert [cell["id"] for cell in cells] == [1, 2, 3]
    assert len(calls) == 2
    assert calls[1][-1] == "0xcursor"


def test_registry_rejects_invalid_contract_code_hash_configuration():
    discovery = CKBPeerDiscovery(
        CKBConfig(receiver_registry_type_hash="0x1234", simulate_if_unavailable=False)
    )

    with pytest.raises(RuntimeError, match="32-byte"):
        asyncio.run(discovery.initialize())


def test_discovery_write_adapter_never_claims_unbroadcast_registration():
    discovery = CKBPeerDiscovery(CKBConfig())

    with pytest.raises(NotImplementedError, match="does not sign or broadcast"):
        asyncio.run(discovery.register_receiver(
            receiver_id="RECV_NYC_001",
            latitude=40.7,
            longitude=-74.0,
            altitude=10.0,
            capabilities=["mode-s", "mlat"],
            private_key="must-not-be-consumed",
        ))
