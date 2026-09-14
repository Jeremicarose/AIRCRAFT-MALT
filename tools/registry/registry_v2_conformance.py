"""Evaluate the shared Registry V2 corpus with the Python implementation."""

from __future__ import annotations

import asyncio
import struct
from typing import Any, Dict

from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery
from ckb_registry.record import (
    ReceiverRegistryRecord,
    calculate_type_id,
    decode_registry_v2_record,
    normalize_receiver_identity,
)

DEFAULT_IDENTITY = "0x" + "11" * 32


def _canonical_record(record: ReceiverRegistryRecord) -> Dict[str, Any]:
    def f64_bits(value: float) -> str:
        return "0x" + struct.pack(">d", float(value)).hex()

    return {
        "schema_version": record.schema_version,
        "receiver_id": record.receiver_id,
        "latitude_f64_bits": f64_bits(record.latitude),
        "longitude_f64_bits": f64_bits(record.longitude),
        "altitude_f64_bits": f64_bits(record.altitude),
        "status": record.status,
        "capabilities": record.capabilities,
        "sequence": str(record.sequence),
        "updated_at": str(record.updated_at),
        "stream_endpoint": record.stream_endpoint,
        "stream_protocol": record.stream_protocol,
        "stream_format": record.stream_format,
        "metadata_hash": record.metadata_hash,
    }


def _cell(
    payload: str,
    receiver_identity: str,
    *,
    code_hash: str,
    hash_type: str = "type",
    index: int = 0,
) -> Dict[str, Any]:
    return {
        "output_data": "0x" + payload.encode("utf-8").hex(),
        "output": {
            "lock": {
                "code_hash": "0x" + "33" * 32,
                "hash_type": "type",
                "args": "0x1234",
            },
            "type": {
                "code_hash": code_hash,
                "hash_type": hash_type,
                "args": receiver_identity,
            },
        },
        "out_point": {
            "tx_hash": "0x" + f"{index + 1:064x}",
            "index": hex(index),
        },
    }


def _record_outcome(case: Dict[str, Any]) -> Dict[str, Any]:
    try:
        record = decode_registry_v2_record(case["payload"])
    except Exception:
        return {"accepted": False, "creation_accepted": False, "record": None}

    try:
        record.validate_creation()
    except ValueError:
        creation_accepted = False
    else:
        creation_accepted = True
    return {
        "accepted": True,
        "creation_accepted": creation_accepted,
        "record": _canonical_record(record),
    }


def _identity_outcome(case: Dict[str, Any]) -> Dict[str, Any]:
    try:
        normalized = normalize_receiver_identity(case["value"])
    except Exception:
        return {"accepted": False, "normalized": None}
    return {"accepted": True, "normalized": normalized}


def _type_id_outcome(case: Dict[str, Any]) -> Dict[str, Any]:
    try:
        value = calculate_type_id(
            first_input_tx_hash=case["first_input_tx_hash"],
            first_input_index=case["first_input_index"],
            first_input_since=case["first_input_since"],
            output_index=case["output_index"],
        )
    except Exception:
        return {"accepted": False, "value": None}
    return {"accepted": True, "value": value}


def _creation_outcome(
    case: Dict[str, Any],
    record_cases: Dict[str, Dict[str, Any]],
    registry_script: Dict[str, str],
) -> Dict[str, Any]:
    try:
        record = decode_registry_v2_record(record_cases[case["record_case"]]["payload"])
        record.validate_creation()
        code_hash = normalize_receiver_identity(case["code_hash"])
        expected_code_hash = normalize_receiver_identity(registry_script["code_hash"])
        receiver_identity = normalize_receiver_identity(case["args"])
        expected_identity = calculate_type_id(
            first_input_tx_hash=case["first_input_tx_hash"],
            first_input_index=case["first_input_index"],
            first_input_since=case["first_input_since"],
            output_index=case["output_index"],
        )
        if (
            code_hash != expected_code_hash
            or case["hash_type"] != registry_script["hash_type"]
            or receiver_identity != expected_identity
        ):
            raise ValueError("creation script does not satisfy Registry V2 Type ID rules")
    except Exception:
        return {"accepted": False, "receiver_identity": None}
    return {"accepted": True, "receiver_identity": receiver_identity}


def _transition_outcome(case: Dict[str, Any]) -> Dict[str, Any]:
    try:
        previous = decode_registry_v2_record(case["previous"])
        successor = decode_registry_v2_record(case["next"])
        previous_identity = normalize_receiver_identity(
            case.get("previous_identity", DEFAULT_IDENTITY)
        )
        next_identity = normalize_receiver_identity(case.get("next_identity", DEFAULT_IDENTITY))
        if previous_identity != next_identity:
            raise ValueError("receiver_identity is immutable")
        successor.validate_successor(previous)
    except Exception:
        return {"accepted": False, "action": None}

    action = (
        "revoke"
        if successor.status == "revoked"
        else ("transfer" if case.get("previous_lock") != case.get("next_lock") else "update")
    )
    return {"accepted": True, "action": action}


async def _script_outcome(
    case: Dict[str, Any],
    record_cases: Dict[str, Dict[str, Any]],
    registry_script: Dict[str, str],
) -> Dict[str, Any]:
    cell = _cell(
        record_cases["valid_creation_with_stream"]["payload"],
        case["args"],
        code_hash=case["code_hash"],
        hash_type=case["hash_type"],
    )
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash=registry_script["code_hash"],
            receiver_registry_hash_type=registry_script["hash_type"],
            allow_mutable_registry_code=registry_script["hash_type"] == "type",
        )
    )
    receiver = await discovery._parse_receiver_cell(cell)
    if receiver is None:
        return {"accepted": False, "receiver_identity": None}
    return {"accepted": True, "receiver_identity": receiver.receiver_identity}


async def _discovery_outcome(
    case: Dict[str, Any],
    record_cases: Dict[str, Dict[str, Any]],
    registry_script: Dict[str, str],
    discovery_policy: Dict[str, int],
) -> Dict[str, Any]:
    cells = [
        _cell(
            record_cases[definition["record_case"]]["payload"],
            definition["receiver_identity"],
            code_hash=registry_script["code_hash"],
            hash_type=registry_script["hash_type"],
            index=index,
        )
        for index, definition in enumerate(case["cells"])
    ]

    async def search() -> list[Dict[str, Any]]:
        return cells

    active_discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash=registry_script["code_hash"],
            receiver_registry_hash_type=registry_script["hash_type"],
            allow_mutable_registry_code=registry_script["hash_type"] == "type",
            max_future_record_skew_seconds=discovery_policy["max_future_skew_seconds"],
            time_provider=lambda: float(discovery_policy["observed_at"]),
        )
    )
    active_discovery._search_receiver_cells = search  # type: ignore[method-assign]
    active = await active_discovery.discover_peers()

    historical_discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash=registry_script["code_hash"],
            receiver_registry_hash_type=registry_script["hash_type"],
            allow_mutable_registry_code=registry_script["hash_type"] == "type",
            max_future_record_skew_seconds=discovery_policy["max_future_skew_seconds"],
            time_provider=lambda: float(discovery_policy["observed_at"]),
        )
    )
    historical_discovery._search_receiver_cells = search  # type: ignore[method-assign]
    historical = await historical_discovery.discover_peers(
        include_inactive=True,
        include_revoked=True,
    )
    return {
        "active_identities": [receiver.receiver_identity for receiver in active],
        "including_revoked_identities": [receiver.receiver_identity for receiver in historical],
        "quarantined_identities": active_discovery.quarantined_identities,
    }


async def _evaluate_async(corpus: Dict[str, Any]) -> list[Dict[str, Any]]:
    record_cases = {case["name"]: case for case in corpus["record_cases"]}
    registry_script = corpus["registry_script"]
    discovery_policy = corpus["discovery_policy"]
    results: list[Dict[str, Any]] = []

    def add(category: str, name: str, outcome: Dict[str, Any]) -> None:
        results.append({"id": f"{category}/{name}", "outcome": outcome})

    for case in corpus["record_cases"]:
        add("record", case["name"], _record_outcome(case))
    for case in corpus["identity_cases"]:
        add("identity", case["name"], _identity_outcome(case))
    for case in corpus["type_id_vectors"]:
        add("type_id", case["name"], _type_id_outcome(case))
    for case in corpus["creation_cases"]:
        add("creation", case["name"], _creation_outcome(case, record_cases, registry_script))
    for case in corpus["transition_cases"]:
        add("transition", case["name"], _transition_outcome(case))
    for case in corpus["script_cases"]:
        add("script", case["name"], await _script_outcome(case, record_cases, registry_script))
    for case in corpus["discovery_cases"]:
        add(
            "discovery",
            case["name"],
            await _discovery_outcome(case, record_cases, registry_script, discovery_policy),
        )
    return results


def evaluate_python(corpus: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "implementation": "python",
        "corpus_schema_version": corpus["schema_version"],
        "results": asyncio.run(_evaluate_async(corpus)),
    }
