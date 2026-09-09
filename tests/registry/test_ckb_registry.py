import asyncio
import json
from pathlib import Path
import time

import pytest

from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery, ReceiverInfo
from ckb_registry.record import (
    U64_MAX,
    ReceiverRegistryRecord,
    calculate_type_id,
    decode_registry_v2_record,
    normalize_receiver_identity,
)

IDENTITY_A = "0x" + "11" * 32
IDENTITY_B = "0x" + "22" * 32
CONFORMANCE_CORPUS = Path(__file__).parent / "fixtures" / "registry_v2_conformance.json"


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


def receiver_cell(record, receiver_identity, *, lock_arg="0xowner", tx_hash=None):
    output_data = (
        "0x" + record.encode("utf-8").hex()
        if isinstance(record, str)
        else record.to_cell_data_hex()
    )
    return {
        "output_data": output_data,
        "output": {
            "lock": {
                "code_hash": "0x" + "33" * 32,
                "hash_type": "type",
                "args": lock_arg,
            },
            "type": {
                "code_hash": "0x" + "44" * 32,
                "hash_type": "type",
                "args": receiver_identity,
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


@pytest.mark.parametrize("field", ["sequence", "updated_at"])
def test_receiver_registry_record_rejects_values_above_u64(field):
    record = receiver_record(**{field: U64_MAX + 1})

    with pytest.raises(ValueError, match="u64"):
        record.validate()


@pytest.mark.parametrize("field", ["sequence", "updated_at", "schema_version"])
def test_receiver_registry_record_rejects_boolean_integers(field):
    record = receiver_record(**{field: True})

    with pytest.raises(ValueError):
        record.validate()


def test_registry_v2_decoder_rejects_duplicate_json_fields():
    payload = receiver_record().to_payload_dict()
    encoded = json.dumps(payload, separators=(",", ":"))
    duplicated = encoded[:-1] + ',"sequence":1}'

    with pytest.raises(ValueError, match="duplicate field"):
        decode_registry_v2_record(duplicated)


def test_registry_v2_decoder_rejects_oversized_payload_before_parsing():
    with pytest.raises(ValueError, match="byte limit"):
        decode_registry_v2_record(b"{}" + b" " * 32, max_bytes=16)


def test_registry_v2_record_conformance_corpus():
    corpus = json.loads(CONFORMANCE_CORPUS.read_text())
    assert corpus["schema_version"] == 2

    for case in corpus["record_cases"]:
        try:
            record = decode_registry_v2_record(case["payload"])
        except (KeyError, TypeError, ValueError):
            record = None
        assert (record is not None) is case["valid"], case["name"]
        if record is not None:
            try:
                record.validate_creation()
            except ValueError:
                creation_valid = False
            else:
                creation_valid = True
            assert creation_valid is case["creation_valid"], case["name"]

    for case in corpus["identity_cases"]:
        try:
            normalize_receiver_identity(case["value"])
        except ValueError:
            valid = False
        else:
            valid = True
        assert valid is case["valid"], case["name"]

    for vector in corpus["type_id_vectors"]:
        observed = calculate_type_id(
            first_input_tx_hash=vector["first_input_tx_hash"],
            first_input_index=vector["first_input_index"],
            first_input_since=vector["first_input_since"],
            output_index=vector["output_index"],
        )
        assert observed == vector["expected"], vector["name"]

    record_cases = {case["name"]: case for case in corpus["record_cases"]}
    registry_script = corpus["registry_script"]
    for case in corpus["creation_cases"]:
        try:
            record = decode_registry_v2_record(record_cases[case["record_case"]]["payload"])
            record.validate_creation()
            valid = (
                normalize_receiver_identity(case["code_hash"])
                == normalize_receiver_identity(registry_script["code_hash"])
                and case["hash_type"] == registry_script["hash_type"]
                and normalize_receiver_identity(case["args"])
                == calculate_type_id(
                    first_input_tx_hash=case["first_input_tx_hash"],
                    first_input_index=case["first_input_index"],
                    first_input_since=case["first_input_since"],
                    output_index=case["output_index"],
                )
            )
        except (KeyError, TypeError, ValueError):
            valid = False
        assert valid is case["valid"], case["name"]

    for case in corpus["transition_cases"]:
        previous = decode_registry_v2_record(case["previous"])
        successor = decode_registry_v2_record(case["next"])
        try:
            previous_identity = normalize_receiver_identity(
                case.get("previous_identity", IDENTITY_A)
            )
            next_identity = normalize_receiver_identity(case.get("next_identity", IDENTITY_A))
            if previous_identity != next_identity:
                raise ValueError("receiver_identity is immutable")
            successor.validate_successor(previous)
        except ValueError:
            valid = False
        else:
            valid = True
        assert valid is case["valid"], case["name"]
        if valid and "action" in case:
            action = (
                "revoke"
                if successor.status == "revoked"
                else (
                    "transfer" if case.get("previous_lock") != case.get("next_lock") else "update"
                )
            )
            assert action == case["action"], case["name"]

    for index, case in enumerate(corpus["script_cases"]):
        record = decode_registry_v2_record(record_cases["valid_creation_with_stream"]["payload"])
        cell = receiver_cell(
            record,
            case["args"],
            tx_hash="0x" + f"{index + 1:064x}",
        )
        cell["output"]["type"].update(
            code_hash=case["code_hash"],
            hash_type=case["hash_type"],
        )
        discovery = CKBPeerDiscovery(CKBConfig(receiver_registry_type_hash="0x" + "44" * 32))
        parsed = asyncio.run(discovery._parse_receiver_cell(cell))
        assert (parsed is not None) is case["valid"], case["name"]

    for case in corpus["discovery_cases"]:
        cells = []
        for index, definition in enumerate(case["cells"]):
            record = record_cases[definition["record_case"]]["payload"]
            cells.append(
                receiver_cell(
                    record,
                    definition["receiver_identity"],
                    tx_hash="0x" + f"{index + 1:064x}",
                )
            )

        async def fake_search():
            return cells

        active_discovery = CKBPeerDiscovery(CKBConfig())
        active_discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
        active = asyncio.run(active_discovery.discover_peers())
        assert [item.receiver_identity for item in active] == case["expected_active_identities"]
        assert active_discovery.quarantined_identities == case["quarantined_identities"]

        historical_discovery = CKBPeerDiscovery(CKBConfig())
        historical_discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
        historical = asyncio.run(
            historical_discovery.discover_peers(include_inactive=True, include_revoked=True)
        )
        assert [item.receiver_identity for item in historical] == case[
            "expected_including_revoked_identities"
        ]


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
    discovery = CKBPeerDiscovery(CKBConfig())
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
    receivers = asyncio.run(discovery.discover_peers())

    assert len(receivers) == 2
    assert {receiver.receiver_identity for receiver in receivers} == {IDENTITY_A, IDENTITY_B}
    assert {receiver.receiver_id for receiver in receivers} == {"RECV_NYC_001"}


def test_ckb_peer_discovery_quarantines_duplicate_live_identity():
    discovery = CKBPeerDiscovery(CKBConfig())
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
    assert asyncio.run(discovery.discover_peers()) == []


def test_ckb_peer_discovery_quarantines_identity_even_when_duplicate_is_revoked():
    discovery = CKBPeerDiscovery(CKBConfig())
    now = int(time.time())
    cells = [
        receiver_cell(receiver_record(updated_at=now), IDENTITY_A),
        receiver_cell(
            receiver_record(status="revoked", updated_at=now, sequence=1),
            IDENTITY_A,
            tx_hash="0x" + "66" * 32,
        ),
    ]

    async def fake_search():
        return cells

    discovery._search_receiver_cells = fake_search  # type: ignore[method-assign]
    assert asyncio.run(discovery.discover_peers()) == []
    assert discovery.cached_peers == {}


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
        if len(calls) == 2:
            return {"objects": [{"id": 3}], "last_cursor": "0xcursor2"}
        return {"objects": [], "last_cursor": "0xcursor2"}

    discovery._rpc_call = fake_rpc  # type: ignore[method-assign]

    cells = asyncio.run(discovery._search_receiver_cells())

    assert [cell["id"] for cell in cells] == [1, 2, 3]
    assert len(calls) == 3
    assert calls[1][-1] == "0xcursor"


def test_indexer_search_does_not_treat_a_short_page_as_exhausted():
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash="0x" + "44" * 32,
            registry_page_size=3,
        )
    )
    responses = [
        {"objects": [{"id": 1}], "last_cursor": "0x1"},
        {"objects": [{"id": 2}], "last_cursor": "0x2"},
        {"objects": [], "last_cursor": "0x2"},
    ]

    async def fake_rpc(method, params, url=None):
        return responses.pop(0)

    discovery._rpc_call = fake_rpc  # type: ignore[method-assign]

    cells = asyncio.run(discovery._search_receiver_cells())

    assert [cell["id"] for cell in cells] == [1, 2]
    assert responses == []


def test_receiver_info_never_uses_human_label_as_canonical_identity():
    receiver = ReceiverInfo(
        receiver_id="RECV_DEMO",
        latitude=0.0,
        longitude=0.0,
        altitude=0.0,
        status="online",
        last_seen=time.time(),
        capabilities=["mode-s"],
        ckb_address="demo",
        lock_hash="",
        data_source="simulation",
    )

    assert receiver.receiver_identity is None
    assert receiver.runtime_id == "simulation:RECV_DEMO"


def test_registry_receiver_requires_canonical_identity():
    with pytest.raises(ValueError, match="receiver_identity"):
        ReceiverInfo(
            receiver_id="RECV_CHAIN",
            latitude=0.0,
            longitude=0.0,
            altitude=0.0,
            status="online",
            last_seen=time.time(),
            capabilities=["mode-s"],
            ckb_address="0xowner",
            lock_hash="0xlock",
            data_source="ckb_registry",
        )


def test_registry_rejects_invalid_contract_code_hash_configuration():
    discovery = CKBPeerDiscovery(CKBConfig(receiver_registry_type_hash="0x1234"))

    with pytest.raises(RuntimeError, match="32-byte"):
        asyncio.run(discovery.initialize())


def test_registry_requires_explicit_opt_in_for_mutable_type_hash_code():
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash="0x" + "44" * 32,
            receiver_registry_hash_type="type",
        )
    )

    with pytest.raises(RuntimeError, match="mutable contract code"):
        asyncio.run(discovery.initialize())


def test_discovery_exposes_no_write_or_private_key_api():
    discovery = CKBPeerDiscovery(CKBConfig())

    assert not hasattr(discovery, "register_receiver")
