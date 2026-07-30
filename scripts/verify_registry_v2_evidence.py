#!/usr/bin/env python3
"""Verify a published Registry V2 testnet evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
import urllib.request


ACCEPTED_STAGES = ("deployment", "create", "update", "transfer", "revoke")
LIFECYCLE_STAGES = ("create", "update", "transfer", "revoke")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Registry V2 evidence")
    parser.add_argument(
        "--bundle",
        default="evidence/registry-v2-testnet-2026-07-30-final",
        help="Evidence bundle directory",
    )
    parser.add_argument("--live", action="store_true", help="Re-query the public CKB RPC")
    parser.add_argument("--output", help="Optional JSON verification report")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ckb_hash(path: Path) -> str:
    return "0x" + hashlib.blake2b(
        path.read_bytes(), digest_size=32, person=b"ckb-default-hash"
    ).hexdigest()


def rpc(url: str, method: str, params: list[Any]) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps(
            {"id": 1, "jsonrpc": "2.0", "method": method, "params": params}
        ).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "mlat-registry-v2-verifier/1"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode())
    if body.get("error") is not None:
        raise RuntimeError(json.dumps(body["error"], sort_keys=True))
    return body["result"]


class Verification:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks.append({"name": name, "pass": bool(condition), "detail": detail})

    @property
    def passed(self) -> bool:
        return all(check["pass"] for check in self.checks)


def transaction_view(response: dict[str, Any]) -> dict[str, Any]:
    transaction = response.get("transaction")
    if not isinstance(transaction, dict):
        return {}
    inner = transaction.get("inner")
    return inner if isinstance(inner, dict) else transaction


def record_from_transaction(response: dict[str, Any]) -> dict[str, Any]:
    transaction = transaction_view(response)
    data_hex = transaction["outputs_data"][0]
    return json.loads(bytes.fromhex(data_hex[2:]).decode())


def first_output(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["outputs"][0]


def first_input_out_point(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["inputs"][0]["previous_output"]


def verify_bundle(bundle: Path, *, live: bool = False) -> dict[str, Any]:
    verification = Verification()
    manifest_path = bundle / "manifest.json"
    verification.require("manifest exists", manifest_path.is_file(), str(manifest_path))
    if not manifest_path.is_file():
        return {"pass": False, "checks": verification.checks}
    manifest = load_json(manifest_path)

    binary_path = bundle / "contract" / "receiver-registry"
    verification.require("contract binary exists", binary_path.is_file(), str(binary_path))
    if binary_path.is_file():
        verification.require(
            "contract SHA-256",
            sha256(binary_path) == manifest["contract"]["binary_sha256"],
            manifest["contract"]["binary_sha256"],
        )
        verification.require(
            "contract CKB data hash",
            ckb_hash(binary_path) == manifest["contract"]["binary_ckb_data_hash"],
            manifest["contract"]["binary_ckb_data_hash"],
        )

    accepted = manifest["accepted_transactions"]
    saved: dict[str, dict[str, Any]] = {}
    for stage in ACCEPTED_STAGES:
        path = bundle / "rpc" / f"{stage}-transaction.json"
        verification.require(f"{stage} RPC response exists", path.is_file(), str(path))
        if not path.is_file():
            continue
        response = load_json(path)
        saved[stage] = response
        status = response.get("tx_status", {}).get("status")
        verification.require(f"{stage} committed", status == "committed", str(status))
        observed_hash = transaction_view(response).get("hash")
        verification.require(
            f"{stage} transaction hash",
            observed_hash == accepted[stage],
            f"expected={accepted[stage]} observed={observed_hash}",
        )

    if all(stage in saved for stage in LIFECYCLE_STAGES):
        expected_parents = {
            "update": accepted["create"],
            "transfer": accepted["update"],
            "revoke": accepted["transfer"],
        }
        for stage, expected_parent in expected_parents.items():
            parent = first_input_out_point(saved[stage])
            verification.require(
                f"{stage} spends previous registry cell",
                parent.get("tx_hash") == expected_parent and int(parent.get("index", "0x0"), 0) == 0,
                str(parent),
            )

        records = {stage: record_from_transaction(saved[stage]) for stage in LIFECYCLE_STAGES}
        labels = {record["receiver_id"] for record in records.values()}
        sequences = [records[stage]["sequence"] for stage in LIFECYCLE_STAGES]
        statuses = [records[stage]["status"] for stage in LIFECYCLE_STAGES]
        verification.require("receiver label immutable", len(labels) == 1, str(sorted(labels)))
        verification.require("sequence is 0,1,2,3", sequences == [0, 1, 2, 3], str(sequences))
        verification.require("revocation is final accepted state", statuses[-1] == "revoked", str(statuses))

        outputs = {stage: first_output(saved[stage]) for stage in LIFECYCLE_STAGES}
        identities = {output["type"]["args"] for output in outputs.values()}
        code_hashes = {output["type"]["code_hash"] for output in outputs.values()}
        verification.require(
            "immutable Receiver Identity",
            identities == {manifest["receiver"]["identity_id"]},
            str(sorted(identities)),
        )
        verification.require(
            "registry code hash",
            code_hashes == {manifest["contract"]["type_script_hash_for_registry_code_hash"]},
            str(sorted(code_hashes)),
        )
        locks = [outputs[stage]["lock"]["args"] for stage in LIFECYCLE_STAGES]
        expected_locks = [
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
        ]
        verification.require("ownership transfer lock lineage", locks == expected_locks, str(locks))

    for attack in manifest.get("rejected_attacks", []):
        response_path = bundle / "responses" / f"attack-{attack}.json"
        tx_path = bundle / "transactions" / f"attack-{attack}.json"
        verification.require(f"{attack} response exists", response_path.is_file(), str(response_path))
        verification.require(f"{attack} signed tx exists", tx_path.is_file(), str(tx_path))
        if response_path.is_file() and tx_path.is_file():
            response = load_json(response_path)
            tx_file = load_json(tx_path)
            signatures = tx_file.get("signatures", {})
            verification.require(
                f"{attack} was signed",
                any(values for values in signatures.values()),
                f"signature groups={len(signatures)}",
            )
            verification.require(
                f"{attack} rejected",
                response.get("expected") == "rejected" and response.get("returncode") != 0,
                response.get("stderr") or response.get("stdout") or "no rejection output",
            )
            verification.require(
                f"{attack} transaction file hash",
                response.get("signed_tx_file_sha256") == sha256(tx_path),
                response.get("signed_tx_file_sha256", "missing"),
            )

    discovery_files = list((bundle / "discovery").glob("*-indexer.json"))
    adapter_files = list((bundle / "discovery").glob("*-adapter.json"))
    verification.require("indexer discovery snapshots", len(discovery_files) >= 4, str(len(discovery_files)))
    verification.require("adapter discovery snapshots", len(adapter_files) >= 4, str(len(adapter_files)))

    api_files = list((bundle / "api").glob("*.json"))
    verification.require("API responses captured", len(api_files) >= 4, str(len(api_files)))

    if live:
        for stage, tx_hash in accepted.items():
            response = rpc(manifest["rpc_url"], "get_transaction", [tx_hash])
            status = None if response is None else response.get("tx_status", {}).get("status")
            verification.require(f"live {stage} committed", status == "committed", str(status))

    return {
        "pass": verification.passed,
        "bundle": str(bundle),
        "live_rpc_checked": live,
        "checks": verification.checks,
    }


def main() -> None:
    args = parse_args()
    report = verify_bundle(Path(args.bundle).resolve(), live=args.live)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    print(rendered, end="")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
