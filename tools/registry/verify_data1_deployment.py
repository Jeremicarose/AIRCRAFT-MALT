#!/usr/bin/env python3
"""Verify an immutable Registry V2 data1 code cell without signing anything."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import urllib.request
from typing import Any

HEX32 = re.compile(r"^0x[0-9a-fA-F]{64}$")


def normalize_hash(value: str, name: str) -> str:
    if not HEX32.fullmatch(value):
        raise ValueError(f"{name} must be a 0x-prefixed 32-byte hex value")
    return value.lower()


def ckb_data_hash(data_hex: str) -> str:
    if not isinstance(data_hex, str) or not data_hex.startswith("0x"):
        raise ValueError("cell data must be a 0x-prefixed hex string")
    raw = bytes.fromhex(data_hex[2:])
    digest = hashlib.blake2b(raw, digest_size=32, person=b"ckb-default-hash")
    return "0x" + digest.hexdigest()


def verify_live_cell(
    result: dict[str, Any],
    *,
    expected_code_hash: str,
    expected_tx_hash: str,
    expected_index: int,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    normalized_code_hash = normalize_hash(expected_code_hash, "code hash")
    normalized_tx_hash = normalize_hash(expected_tx_hash, "transaction hash")
    status = result.get("status") if isinstance(result, dict) else None
    cell = result.get("cell") if isinstance(result, dict) else None
    output = cell.get("output") if isinstance(cell, dict) else None
    data = cell.get("data") if isinstance(cell, dict) else None
    observed_data_hash = None
    if isinstance(data, dict) and isinstance(data.get("content"), str):
        observed_data_hash = ckb_data_hash(data["content"])

    checks.append({"name": "cell is live", "pass": status == "live", "observed": status})
    checks.append(
        {
            "name": "data1 code hash matches",
            "pass": observed_data_hash == normalized_code_hash,
            "expected": normalized_code_hash,
            "observed": observed_data_hash,
        }
    )
    return {
        "pass": all(check["pass"] for check in checks),
        "script_hash_type": "data1",
        "queried_out_point": {"tx_hash": normalized_tx_hash, "index": hex(expected_index)},
        "expected_code_hash": normalized_code_hash,
        "checks": checks,
        "observed_cell": output,
        "observed_data_hash": observed_data_hash,
    }


def rpc_call(url: str, method: str, params: list[Any], ca_bundle: str | None) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps({"id": 1, "jsonrpc": "2.0", "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "registry-v2-data1-verifier/1"},
        method="POST",
    )
    context = None
    if url.startswith("https://"):
        if ca_bundle:
            context = ssl.create_default_context(cafile=ca_bundle)
        else:
            try:
                import certifi

                context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        body = json.loads(response.read().decode())
    if body.get("error") is not None:
        raise RuntimeError(json.dumps(body["error"], sort_keys=True))
    return body.get("result")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-tx-hash", required=True)
    parser.add_argument("--contract-index", type=int, default=0)
    parser.add_argument("--code-hash", required=True, help="Expected CKB data1 hash of the binary")
    parser.add_argument("--binary", type=Path, help="Optional local binary to hash and compare")
    parser.add_argument("--rpc-url", default="https://testnet.ckb.dev/rpc")
    parser.add_argument(
        "--ca-bundle", help="CA bundle path when the platform trust store is unavailable"
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.contract_index < 0:
        raise SystemExit("--contract-index must be non-negative")
    code_hash = normalize_hash(args.code_hash, "code hash")
    tx_hash = normalize_hash(args.contract_tx_hash, "transaction hash")
    try:
        result = rpc_call(
            args.rpc_url,
            "get_live_cell",
            [{"tx_hash": tx_hash, "index": hex(args.contract_index)}, True],
            args.ca_bundle,
        )
    except Exception as exc:  # noqa: BLE001 - preserve failure as machine-readable evidence
        report = {
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "pass": False,
            "status": "rpc_unavailable_or_malformed",
            "script_hash_type": "data1",
            "queried_out_point": {"tx_hash": tx_hash, "index": hex(args.contract_index)},
            "expected_code_hash": code_hash,
            "error": str(exc),
        }
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        raise SystemExit(1)
    report = verify_live_cell(
        result,
        expected_code_hash=code_hash,
        expected_tx_hash=tx_hash,
        expected_index=args.contract_index,
    )
    if args.binary:
        binary_bytes = args.binary.read_bytes()
        report["binary"] = {
            "path": str(args.binary),
            "sha256": hashlib.sha256(binary_bytes).hexdigest(),
            "ckb_data_hash": ckb_data_hash("0x" + binary_bytes.hex()),
            "matches_deployment": ckb_data_hash("0x" + binary_bytes.hex()) == code_hash,
        }
        report["pass"] = report["pass"] and report["binary"]["matches_deployment"]
    report["checked_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
