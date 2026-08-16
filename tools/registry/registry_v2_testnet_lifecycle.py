#!/usr/bin/env python3
"""Execute and capture a signed Registry V2 lifecycle on CKB testnet."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery
from ckb_registry.record import ReceiverRegistryRecord, calculate_type_id

SIGHASH_CODE_HASH = "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8"
HEX_32_RE = re.compile(r"0x[0-9a-f]{64}")
LOCK_ARG_RE = re.compile(r'"lock_arg"\s*:\s*"(0x[0-9a-f]{40})"')
TESTNET_ADDRESS_RE = re.compile(r'"testnet"\s*:\s*"(ckt1[0-9a-z]+)"')
FEE_SHANNONS = 1_000_000
REGISTRY_CAPACITY = 1000 * 100_000_000
TOMBSTONE_CAPACITY = 500 * 100_000_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run signed Registry V2 lifecycle and rejected attacks on CKB testnet"
    )
    parser.add_argument(
        "--deployment-info",
        default="deploy/registry-v2-testnet-2026-07-30-canonical/deployment-info.json",
    )
    parser.add_argument(
        "--contract-binary",
        default="evidence/registry-v2-testnet-2026-07-30-final/contract/receiver-registry",
    )
    parser.add_argument("--owner-a-key", default="/private/tmp/registry-v2-owner-a.key")
    parser.add_argument("--owner-b-key", default="/private/tmp/registry-v2-owner-b.key")
    parser.add_argument(
        "--evidence-dir",
        default="evidence/registry-v2-testnet-2026-07-30-final",
    )
    parser.add_argument("--rpc-url", default="https://testnet.ckb.dev/rpc")
    parser.add_argument("--indexer-url", default="https://testnet.ckb.dev/indexer")
    parser.add_argument("--receiver-label", default="RECV_REGISTRY_V2_EVIDENCE")
    parser.add_argument("--confirmation-timeout", type=int, default=300)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def rpc(url: str, method: str, params: list[Any]) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps({"id": 1, "jsonrpc": "2.0", "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "mlat-registry-v2-evidence/1"},
        method="POST",
    )
    ssl_context = None
    if url.startswith("https://"):
        try:
            import certifi

            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
        body = json.loads(response.read().decode())
    if body.get("error") is not None:
        raise RuntimeError(json.dumps(body["error"], sort_keys=True))
    return body["result"]


def wait_committed(rpc_url: str, tx_hash: str, timeout: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        result = rpc(rpc_url, "get_transaction", [tx_hash])
        if result is not None:
            last = result
            status = result.get("tx_status", {}).get("status")
            if status == "committed":
                return result
            if status == "rejected":
                raise RuntimeError(f"transaction {tx_hash} was rejected: {result}")
        time.sleep(3)
    raise TimeoutError(f"transaction {tx_hash} did not commit in {timeout}s; last={last}")


def ensure_private_key(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing isolated testnet private key: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f"Private key permissions must be 0600: {path} is {mode:04o}")


def key_public_info(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            "ckb-cli",
            "util",
            "key-info",
            "--privkey-path",
            str(path),
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lock_match = LOCK_ARG_RE.search(result.stdout)
    address_match = TESTNET_ADDRESS_RE.search(result.stdout)
    if lock_match is None or address_match is None:
        raise RuntimeError("Unable to parse public key information from ckb-cli")
    return {"lock_arg": lock_match.group(1), "testnet_address": address_match.group(1)}


def ckb_hash(data: bytes) -> str:
    return "0x" + hashlib.blake2b(data, digest_size=32, person=b"ckb-default-hash").hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_script(lock_arg: str) -> dict[str, str]:
    return {"code_hash": SIGHASH_CODE_HASH, "hash_type": "type", "args": lock_arg}


def type_script(contract_code_hash: str, identity_id: str) -> dict[str, str]:
    return {"code_hash": contract_code_hash, "hash_type": "type", "args": identity_id}


def output(
    capacity: int,
    lock_arg: str,
    registry_type: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "capacity": hex(capacity),
        "lock": lock_script(lock_arg),
        "type": registry_type,
    }


def write_tx(
    path: Path,
    *,
    input_tx_hash: str,
    input_index: int,
    outputs: list[dict[str, Any]],
    outputs_data: list[str],
    sighash_dep: dict[str, Any],
    contract_tx_hash: str,
    contract_index: int,
) -> None:
    if len(outputs) != len(outputs_data):
        raise ValueError("outputs and outputs_data must have equal lengths")
    atomic_json(
        path,
        {
            "transaction": {
                "version": "0x0",
                "cell_deps": [
                    sighash_dep,
                    {
                        "out_point": {
                            "tx_hash": contract_tx_hash,
                            "index": hex(contract_index),
                        },
                        "dep_type": "code",
                    },
                ],
                "header_deps": [],
                "inputs": [
                    {
                        "since": "0x0",
                        "previous_output": {
                            "tx_hash": input_tx_hash,
                            "index": hex(input_index),
                        },
                    }
                ],
                "outputs": outputs,
                "outputs_data": outputs_data,
                "witnesses": [],
            },
            "multisig_configs": {},
            "signatures": {},
        },
    )


def signed_submission(
    *,
    tx_path: Path,
    key_path: Path,
    rpc_url: str,
    response_path: Path,
    expect_accept: bool,
) -> str | None:
    sign = subprocess.run(
        [
            "ckb-cli",
            "--url",
            rpc_url,
            "tx",
            "sign-inputs",
            "--privkey-path",
            str(key_path),
            "--tx-file",
            str(tx_path),
            "--add-signatures",
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if sign.returncode != 0:
        raise RuntimeError(f"signing failed for {tx_path.name}: {sign.stderr or sign.stdout}")

    send = subprocess.run(
        [
            "ckb-cli",
            "--url",
            rpc_url,
            "tx",
            "send",
            "--tx-file",
            str(tx_path),
            "--max-tx-fee",
            "1",
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    response = {
        "attempted_at": utc_now(),
        "expected": "accepted" if expect_accept else "rejected",
        "returncode": send.returncode,
        "stdout": send.stdout.strip(),
        "stderr": send.stderr.strip(),
        "signed_tx_file": tx_path.name,
        "signed_tx_file_sha256": sha256(tx_path),
    }
    atomic_json(response_path, response)

    if expect_accept:
        if send.returncode != 0:
            raise RuntimeError(f"transaction {tx_path.name} was rejected: {response}")
        hashes = HEX_32_RE.findall(send.stdout.lower())
        if len(hashes) != 1:
            raise RuntimeError(f"unable to identify transaction hash in: {send.stdout}")
        return hashes[0]
    if send.returncode == 0:
        raise RuntimeError(f"attack transaction {tx_path.name} was unexpectedly accepted")
    return None


def record(
    label: str,
    sequence: int,
    updated_at: int,
    *,
    status: str = "online",
) -> ReceiverRegistryRecord:
    stream = status != "revoked"
    return ReceiverRegistryRecord(
        receiver_id=label,
        latitude=-1.286389,
        longitude=36.817223,
        altitude=1795.0,
        status=status,
        capabilities=["mode-s", "mlat"],
        sequence=sequence,
        updated_at=updated_at,
        stream_endpoint="wss://registry-v2-evidence.invalid/feed" if stream else None,
        stream_protocol="websocket-json" if stream else None,
        stream_format="json" if stream else None,
    )


async def discovery_snapshot(
    *,
    rpc_url: str,
    indexer_url: str,
    contract_code_hash: str,
) -> list[dict[str, Any]]:
    discovery = CKBPeerDiscovery(
        CKBConfig(
            ckb_rpc_url=rpc_url,
            ckb_indexer_url=indexer_url,
            receiver_registry_type_hash=contract_code_hash,
            simulate_if_unavailable=False,
            strict_production_mode=True,
        )
    )
    await discovery.initialize()
    try:
        return [asdict(peer) for peer in await discovery.discover_peers()]
    finally:
        await discovery.shutdown()


def capture_api_response(
    *,
    name: str,
    peers: list[dict[str, Any]],
    evidence_dir: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="registry-v2-api-") as directory:
        database_path = Path(directory) / "registry.db"
        previous_database_path = os.environ.get("DATABASE_PATH")
        previous_broadcaster = os.environ.get("ENABLE_BACKGROUND_BROADCASTER")
        os.environ["DATABASE_PATH"] = str(database_path)
        os.environ["ENABLE_BACKGROUND_BROADCASTER"] = "false"
        try:
            from mlat_reference.api.rest_api import create_app
            from mlat_reference.database.database import MLATDatabase
        finally:
            if previous_database_path is None:
                os.environ.pop("DATABASE_PATH", None)
            else:
                os.environ["DATABASE_PATH"] = previous_database_path
            if previous_broadcaster is None:
                os.environ.pop("ENABLE_BACKGROUND_BROADCASTER", None)
            else:
                os.environ["ENABLE_BACKGROUND_BROADCASTER"] = previous_broadcaster

        database = MLATDatabase(str(database_path))
        database.connect()
        try:
            for peer in peers:
                metadata = peer.get("metadata") or {}
                database.store_receiver(
                    receiver_id=peer["identity_id"],
                    receiver_label=peer["receiver_id"],
                    latitude=peer["latitude"],
                    longitude=peer["longitude"],
                    altitude=peer["altitude"],
                    status=peer["status"],
                    last_seen=peer["last_seen"],
                    capabilities=peer["capabilities"],
                    registry_sequence=int(metadata.get("sequence", 0)),
                    owner_lock_args=(metadata.get("owner_lock") or {}).get("args", ""),
                    registry_out_point=json.dumps(metadata.get("out_point") or {}, sort_keys=True),
                    metadata_hash=metadata.get("metadata_hash") or "",
                )
        finally:
            database.close()

        app = create_app(
            {
                "DATABASE_PATH": str(database_path),
                "ENABLE_BACKGROUND_BROADCASTER": False,
                "TESTING": True,
            }
        )
        response = app.test_client().get("/api/receivers")
        atomic_json(
            evidence_dir / "api" / f"{name}-receivers.json",
            {
                "captured_at": utc_now(),
                "method": "GET",
                "path": "/api/receivers",
                "status_code": response.status_code,
                "body": response.get_json(),
            },
        )


def capture_state(
    *,
    name: str,
    evidence_dir: Path,
    rpc_url: str,
    indexer_url: str,
    contract_code_hash: str,
    expected_out_point: dict[str, Any],
    timeout: int,
) -> None:
    search_key = {
        "script": {
            "code_hash": contract_code_hash,
            "hash_type": "type",
            "args": "0x",
        },
        "script_type": "type",
        "script_search_mode": "prefix",
        "with_data": True,
    }
    deadline = time.monotonic() + timeout
    cells: dict[str, Any] = {"objects": []}
    while time.monotonic() < deadline:
        cells = rpc(indexer_url, "get_cells", [search_key, "asc", "0x64"])
        if any(item.get("out_point") == expected_out_point for item in cells.get("objects", [])):
            break
        time.sleep(3)
    else:
        raise TimeoutError(f"indexer did not expose {expected_out_point} within {timeout}s")

    atomic_json(evidence_dir / "discovery" / f"{name}-indexer.json", cells)
    peers = asyncio.run(
        discovery_snapshot(
            rpc_url=rpc_url,
            indexer_url=indexer_url,
            contract_code_hash=contract_code_hash,
        )
    )
    atomic_json(evidence_dir / "discovery" / f"{name}-adapter.json", peers)
    capture_api_response(name=name, peers=peers, evidence_dir=evidence_dir)


def lifecycle_transition(
    *,
    name: str,
    input_tx_hash: str,
    input_capacity: int,
    next_record: ReceiverRegistryRecord,
    next_lock_arg: str,
    identity_id: str,
    contract_code_hash: str,
    contract_tx_hash: str,
    contract_index: int,
    sighash_dep: dict[str, Any],
    key_path: Path,
    rpc_url: str,
    evidence_dir: Path,
    timeout: int,
) -> tuple[str, int]:
    next_capacity = input_capacity - FEE_SHANNONS
    tx_path = evidence_dir / "transactions" / f"{name}.json"
    write_tx(
        tx_path,
        input_tx_hash=input_tx_hash,
        input_index=0,
        outputs=[
            output(
                next_capacity,
                next_lock_arg,
                type_script(contract_code_hash, identity_id),
            )
        ],
        outputs_data=[next_record.to_cell_data_hex()],
        sighash_dep=sighash_dep,
        contract_tx_hash=contract_tx_hash,
        contract_index=contract_index,
    )
    tx_hash = signed_submission(
        tx_path=tx_path,
        key_path=key_path,
        rpc_url=rpc_url,
        response_path=evidence_dir / "responses" / f"{name}-submission.json",
        expect_accept=True,
    )
    assert tx_hash is not None
    committed = wait_committed(rpc_url, tx_hash, timeout)
    atomic_json(evidence_dir / "rpc" / f"{name}-transaction.json", committed)
    return tx_hash, next_capacity


def main() -> None:
    args = parse_args()
    deployment_info_path = (ROOT / args.deployment_info).resolve()
    contract_binary_path = (ROOT / args.contract_binary).resolve()
    evidence_dir = (ROOT / args.evidence_dir).resolve()
    owner_a_key = Path(args.owner_a_key).resolve()
    owner_b_key = Path(args.owner_b_key).resolve()
    ensure_private_key(owner_a_key)
    ensure_private_key(owner_b_key)
    owner_a = key_public_info(owner_a_key)
    owner_b = key_public_info(owner_b_key)

    deployment_info = json.loads(deployment_info_path.read_text())
    recipes = {item["name"]: item for item in deployment_info["new_recipe"]["cell_recipes"]}
    contract = recipes["receiver_registry"]
    funding = recipes["lifecycle_funding"]
    deployment_tx_hash = contract["tx_hash"]
    if funding["tx_hash"] != deployment_tx_hash:
        raise SystemExit("Contract and lifecycle funding must share one deployment transaction")
    if contract["data_hash"] != ckb_hash(contract_binary_path.read_bytes()):
        raise SystemExit("Deployment recipe data hash does not match the local contract binary")
    deployment_lock_arg = deployment_info["deployment"]["lock"]["args"]
    if owner_a["lock_arg"] != deployment_lock_arg:
        raise SystemExit("Owner A key does not match the deployment lifecycle lock")

    deployment_evidence_dir = evidence_dir / "deployment"
    deployment_evidence_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(deployment_info_path, deployment_evidence_dir / "deployment-info.json")
    for artifact_name in ("deployment.toml", "lifecycle-funding.bin"):
        source = deployment_info_path.parent / artifact_name
        if source.is_file():
            shutil.copy2(source, deployment_evidence_dir / artifact_name)

    committed_deployment = wait_committed(
        args.rpc_url, deployment_tx_hash, args.confirmation_timeout
    )
    atomic_json(evidence_dir / "rpc" / "deployment-transaction.json", committed_deployment)

    contract_code_hash = contract["type_id"]
    contract_index = int(contract["index"])
    funding_index = int(funding["index"])
    funding_capacity = int(funding["occupied_capacity"])
    sighash_dep = deployment_info["cell_tx"]["cell_deps"][0]
    base_timestamp = int(time.time())
    identity_id = calculate_type_id(
        first_input_tx_hash=deployment_tx_hash,
        first_input_index=funding_index,
        output_index=0,
    )

    creation = record(args.receiver_label, 0, base_timestamp)
    creation_type = type_script(contract_code_hash, identity_id)
    change_capacity = funding_capacity - REGISTRY_CAPACITY - FEE_SHANNONS
    if change_capacity < 61 * 100_000_000:
        raise SystemExit("Lifecycle funding cell cannot support registry output and change")

    forged_path = evidence_dir / "transactions" / "attack-forged-identity.json"
    write_tx(
        forged_path,
        input_tx_hash=deployment_tx_hash,
        input_index=funding_index,
        outputs=[
            output(
                REGISTRY_CAPACITY,
                owner_a["lock_arg"],
                type_script(contract_code_hash, "0x" + "ff" * 32),
            ),
            output(change_capacity, owner_a["lock_arg"]),
        ],
        outputs_data=[creation.to_cell_data_hex(), "0x"],
        sighash_dep=sighash_dep,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
    )
    signed_submission(
        tx_path=forged_path,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        response_path=evidence_dir / "responses" / "attack-forged-identity.json",
        expect_accept=False,
    )

    create_path = evidence_dir / "transactions" / "create.json"
    write_tx(
        create_path,
        input_tx_hash=deployment_tx_hash,
        input_index=funding_index,
        outputs=[
            output(REGISTRY_CAPACITY, owner_a["lock_arg"], creation_type),
            output(change_capacity, owner_a["lock_arg"]),
        ],
        outputs_data=[creation.to_cell_data_hex(), "0x"],
        sighash_dep=sighash_dep,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
    )
    create_hash = signed_submission(
        tx_path=create_path,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        response_path=evidence_dir / "responses" / "create-submission.json",
        expect_accept=True,
    )
    assert create_hash is not None
    atomic_json(
        evidence_dir / "rpc" / "create-transaction.json",
        wait_committed(args.rpc_url, create_hash, args.confirmation_timeout),
    )
    capture_state(
        name="create",
        evidence_dir=evidence_dir,
        rpc_url=args.rpc_url,
        indexer_url=args.indexer_url,
        contract_code_hash=contract_code_hash,
        expected_out_point={"tx_hash": create_hash, "index": "0x0"},
        timeout=args.confirmation_timeout,
    )

    attack_records = {
        "sequence-jump": record(args.receiver_label, 2, base_timestamp + 1),
        "label-mutation": record("RECV_ATTACKER", 1, base_timestamp + 1),
    }
    for attack_name, attack_record in attack_records.items():
        path = evidence_dir / "transactions" / f"attack-{attack_name}.json"
        write_tx(
            path,
            input_tx_hash=create_hash,
            input_index=0,
            outputs=[
                output(
                    REGISTRY_CAPACITY - FEE_SHANNONS,
                    owner_a["lock_arg"],
                    creation_type,
                )
            ],
            outputs_data=[attack_record.to_cell_data_hex()],
            sighash_dep=sighash_dep,
            contract_tx_hash=deployment_tx_hash,
            contract_index=contract_index,
        )
        signed_submission(
            tx_path=path,
            key_path=owner_a_key,
            rpc_url=args.rpc_url,
            response_path=evidence_dir / "responses" / f"attack-{attack_name}.json",
            expect_accept=False,
        )

    next_record = record(args.receiver_label, 1, base_timestamp + 1)
    duplicate_capacity = (REGISTRY_CAPACITY - FEE_SHANNONS) // 2
    duplicate_path = evidence_dir / "transactions" / "attack-duplicate-output.json"
    duplicate_output = output(duplicate_capacity, owner_a["lock_arg"], creation_type)
    write_tx(
        duplicate_path,
        input_tx_hash=create_hash,
        input_index=0,
        outputs=[duplicate_output, duplicate_output],
        outputs_data=[next_record.to_cell_data_hex(), next_record.to_cell_data_hex()],
        sighash_dep=sighash_dep,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
    )
    signed_submission(
        tx_path=duplicate_path,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        response_path=evidence_dir / "responses" / "attack-duplicate-output.json",
        expect_accept=False,
    )

    burn_path = evidence_dir / "transactions" / "attack-burn.json"
    write_tx(
        burn_path,
        input_tx_hash=create_hash,
        input_index=0,
        outputs=[output(REGISTRY_CAPACITY - FEE_SHANNONS, owner_a["lock_arg"])],
        outputs_data=["0x"],
        sighash_dep=sighash_dep,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
    )
    signed_submission(
        tx_path=burn_path,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        response_path=evidence_dir / "responses" / "attack-burn.json",
        expect_accept=False,
    )

    update_hash, update_capacity = lifecycle_transition(
        name="update",
        input_tx_hash=create_hash,
        input_capacity=REGISTRY_CAPACITY,
        next_record=next_record,
        next_lock_arg=owner_a["lock_arg"],
        identity_id=identity_id,
        contract_code_hash=contract_code_hash,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
        sighash_dep=sighash_dep,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        evidence_dir=evidence_dir,
        timeout=args.confirmation_timeout,
    )
    capture_state(
        name="update",
        evidence_dir=evidence_dir,
        rpc_url=args.rpc_url,
        indexer_url=args.indexer_url,
        contract_code_hash=contract_code_hash,
        expected_out_point={"tx_hash": update_hash, "index": "0x0"},
        timeout=args.confirmation_timeout,
    )

    transfer_hash, transfer_capacity = lifecycle_transition(
        name="transfer",
        input_tx_hash=update_hash,
        input_capacity=update_capacity,
        next_record=record(args.receiver_label, 2, base_timestamp + 2),
        next_lock_arg=owner_b["lock_arg"],
        identity_id=identity_id,
        contract_code_hash=contract_code_hash,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
        sighash_dep=sighash_dep,
        key_path=owner_a_key,
        rpc_url=args.rpc_url,
        evidence_dir=evidence_dir,
        timeout=args.confirmation_timeout,
    )
    capture_state(
        name="transfer",
        evidence_dir=evidence_dir,
        rpc_url=args.rpc_url,
        indexer_url=args.indexer_url,
        contract_code_hash=contract_code_hash,
        expected_out_point={"tx_hash": transfer_hash, "index": "0x0"},
        timeout=args.confirmation_timeout,
    )

    revoke_record = record(args.receiver_label, 3, base_timestamp + 3, status="revoked")
    revoke_change = transfer_capacity - TOMBSTONE_CAPACITY - FEE_SHANNONS
    revoke_path = evidence_dir / "transactions" / "revoke.json"
    write_tx(
        revoke_path,
        input_tx_hash=transfer_hash,
        input_index=0,
        outputs=[
            output(TOMBSTONE_CAPACITY, owner_b["lock_arg"], creation_type),
            output(revoke_change, owner_b["lock_arg"]),
        ],
        outputs_data=[revoke_record.to_cell_data_hex(), "0x"],
        sighash_dep=sighash_dep,
        contract_tx_hash=deployment_tx_hash,
        contract_index=contract_index,
    )
    revoke_hash = signed_submission(
        tx_path=revoke_path,
        key_path=owner_b_key,
        rpc_url=args.rpc_url,
        response_path=evidence_dir / "responses" / "revoke-submission.json",
        expect_accept=True,
    )
    assert revoke_hash is not None
    atomic_json(
        evidence_dir / "rpc" / "revoke-transaction.json",
        wait_committed(args.rpc_url, revoke_hash, args.confirmation_timeout),
    )
    capture_state(
        name="revoke",
        evidence_dir=evidence_dir,
        rpc_url=args.rpc_url,
        indexer_url=args.indexer_url,
        contract_code_hash=contract_code_hash,
        expected_out_point={"tx_hash": revoke_hash, "index": "0x0"},
        timeout=args.confirmation_timeout,
    )

    for attack_name, outputs, data in (
        (
            "resurrection",
            [output(TOMBSTONE_CAPACITY - FEE_SHANNONS, owner_b["lock_arg"], creation_type)],
            [record(args.receiver_label, 4, base_timestamp + 4).to_cell_data_hex()],
        ),
        (
            "tombstone-burn",
            [output(TOMBSTONE_CAPACITY - FEE_SHANNONS, owner_b["lock_arg"])],
            ["0x"],
        ),
    ):
        path = evidence_dir / "transactions" / f"attack-{attack_name}.json"
        write_tx(
            path,
            input_tx_hash=revoke_hash,
            input_index=0,
            outputs=outputs,
            outputs_data=data,
            sighash_dep=sighash_dep,
            contract_tx_hash=deployment_tx_hash,
            contract_index=contract_index,
        )
        signed_submission(
            tx_path=path,
            key_path=owner_b_key,
            rpc_url=args.rpc_url,
            response_path=evidence_dir / "responses" / f"attack-{attack_name}.json",
            expect_accept=False,
        )

    tooling_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    github_ci_path = evidence_dir / "ci" / "github.json"
    github_ci = json.loads(github_ci_path.read_text()) if github_ci_path.is_file() else None
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "generated_at": utc_now(),
        "network": "CKB testnet",
        "rpc_url": args.rpc_url,
        "indexer_url": args.indexer_url,
        "source": {
            "repository": "https://github.com/Jeremicarose/AIRCRAFT-MALT",
            "branch": "registry-v2-testnet-evidence",
            "contract_source_commit": "61ab011de58397cb8d6ca3cecb5c659c69e2fc8c",
            "lifecycle_tooling_commit": tooling_commit,
        },
        "contract": {
            "deployment_tx_hash": deployment_tx_hash,
            "out_point": {"tx_hash": deployment_tx_hash, "index": hex(contract_index)},
            "binary_bytes": contract_binary_path.stat().st_size,
            "binary_sha256": sha256(contract_binary_path),
            "binary_ckb_data_hash": contract["data_hash"],
            "type_script_hash_for_registry_code_hash": contract_code_hash,
        },
        "lifecycle_funding": {
            "out_point": {"tx_hash": deployment_tx_hash, "index": hex(funding_index)},
            "capacity_shannons": funding_capacity,
            "data_hash": funding["data_hash"],
        },
        "receiver": {
            "identity_id": identity_id,
            "label": args.receiver_label,
            "owner_a": owner_a,
            "owner_b": owner_b,
        },
        "accepted_transactions": {
            "deployment": deployment_tx_hash,
            "create": create_hash,
            "update": update_hash,
            "transfer": transfer_hash,
            "revoke": revoke_hash,
        },
        "rejected_attacks": [
            "forged-identity",
            "sequence-jump",
            "label-mutation",
            "duplicate-output",
            "burn",
            "resurrection",
            "tombstone-burn",
        ],
        "github_ci": github_ci,
        "private_keys_included": False,
    }
    atomic_json(evidence_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
