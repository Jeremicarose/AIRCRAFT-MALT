#!/usr/bin/env python3
"""Compare Registry indexer discovery with direct CKB RPC for a known cell."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import ssl
import urllib.request
from typing import Any

HEX32 = re.compile(r"^0x[0-9a-fA-F]{64}$")
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 1_000
DEFAULT_MAX_CELLS = 10_000


def normalize_hash(value: str, name: str) -> str:
    if not HEX32.fullmatch(value):
        raise ValueError(f"{name} must be a 0x-prefixed 32-byte hex value")
    return value.lower()


def outpoint_matches(objects: list[dict[str, Any]], tx_hash: str, index: int) -> bool:
    expected_hash = tx_hash.lower()
    expected_index = {hex(index), str(index)}
    return any(
        isinstance(item, dict)
        and isinstance(item.get("out_point"), dict)
        and str(item["out_point"].get("tx_hash", "")).lower() == expected_hash
        and str(item["out_point"].get("index", "")) in expected_index
        for item in objects
    )


def identity_matches(objects: list[dict[str, Any]], identity: str) -> list[dict[str, Any]]:
    """Return well-shaped indexer cells whose type-script args match identity."""
    matches: list[dict[str, Any]] = []
    for item in objects:
        output = item.get("output") if isinstance(item, dict) else None
        type_script = output.get("type") if isinstance(output, dict) else None
        args = type_script.get("args") if isinstance(type_script, dict) else None
        if isinstance(args, str) and args.lower() == identity:
            matches.append(item)
    return matches


def fetch_all_indexer_cells(
    *,
    indexer_url: str,
    search_key: dict[str, Any],
    ca_bundle: str | None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_cells: int = DEFAULT_MAX_CELLS,
) -> tuple[list[dict[str, Any]], int]:
    if page_size < 1 or page_size > 1_000:
        raise ValueError("page_size must be between 1 and 1000")
    if max_pages < 1 or max_cells < 1:
        raise ValueError("pagination safety limits must be positive")

    objects: list[dict[str, Any]] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    for page_number in range(1, max_pages + 1):
        params: list[Any] = [search_key, "asc", hex(page_size)]
        if cursor is not None:
            params.append(cursor)
        page = rpc_call(indexer_url, "get_cells", params, ca_bundle)
        if not isinstance(page, dict):
            raise RuntimeError("indexer returned a non-object get_cells result")
        page_objects = page.get("objects")
        if not isinstance(page_objects, list):
            raise RuntimeError("indexer get_cells response has no objects array")
        if any(not isinstance(item, dict) for item in page_objects):
            raise RuntimeError("indexer get_cells objects must contain only objects")
        objects.extend(page_objects)
        if len(objects) > max_cells:
            raise RuntimeError("indexer lookup exceeded the Registry cell safety limit")
        if not page_objects:
            return objects, page_number

        next_cursor = page.get("last_cursor")
        if (
            not isinstance(next_cursor, str)
            or not next_cursor
            or next_cursor == cursor
            or next_cursor in seen_cursors
        ):
            raise RuntimeError("indexer returned an invalid cursor after a non-empty page")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    raise RuntimeError("indexer lookup exceeded the Registry page safety limit")


def classify_consistency(
    *,
    indexed_match: bool,
    direct_status: str,
    expected_outpoint: bool,
) -> str:
    if direct_status in {"rpc_error", "unavailable"}:
        return "rpc_unavailable"
    if not expected_outpoint:
        return "ok" if indexed_match else "empty_registry_or_indexer_lag"
    if direct_status == "live" and indexed_match:
        return "ok"
    if direct_status == "live" and not indexed_match:
        return "indexer_lag"
    if direct_status != "live" and indexed_match:
        return "stale_indexer"
    return "not_live"


def rpc_call(url: str, method: str, params: list[Any], ca_bundle: str | None) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps({"id": 1, "jsonrpc": "2.0", "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "registry-v2-indexer-health/1"},
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
    parser.add_argument("--contract-code-hash", required=True)
    parser.add_argument("--hash-type", choices=("data1", "type"), default="data1")
    parser.add_argument("--receiver-identity")
    parser.add_argument("--expected-tx-hash")
    parser.add_argument("--expected-index", type=int, default=0)
    parser.add_argument("--rpc-url", default="https://testnet.ckb.dev/rpc")
    parser.add_argument("--indexer-url", default="https://testnet.ckb.dev/indexer")
    parser.add_argument("--ca-bundle")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--max-cells", type=int, default=DEFAULT_MAX_CELLS)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    code_hash = normalize_hash(args.contract_code_hash, "contract code hash")
    identity = (
        normalize_hash(args.receiver_identity, "receiver identity")
        if args.receiver_identity
        else None
    )
    expected_tx = (
        normalize_hash(args.expected_tx_hash, "expected transaction hash")
        if args.expected_tx_hash
        else None
    )
    if expected_tx is not None and args.expected_index < 0:
        raise SystemExit("--expected-index must be non-negative")
    search_key = {
        "script": {
            "code_hash": code_hash,
            "hash_type": args.hash_type,
            "args": identity or "0x",
        },
        "script_type": "type",
        "script_search_mode": "exact" if identity else "prefix",
        "filter": {"script_len_range": ["0x0", "0xffffffff"]},
    }
    try:
        objects, pages_scanned = fetch_all_indexer_cells(
            indexer_url=args.indexer_url,
            search_key=search_key,
            ca_bundle=args.ca_bundle,
            page_size=args.page_size,
            max_pages=args.max_pages,
            max_cells=args.max_cells,
        )
    except Exception as exc:  # noqa: BLE001 - turn infrastructure failures into evidence
        report = {
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "indexer_unavailable_or_malformed",
            "pass": False,
            "deployment": {"code_hash": code_hash, "hash_type": args.hash_type},
            "receiver_identity": identity,
            "indexer": {
                "url": args.indexer_url,
                "pages_scanned": 0,
                "error": str(exc),
            },
            "direct_rpc": {"url": args.rpc_url, "status": "not_checked"},
            "expected_outpoint": (
                {"tx_hash": expected_tx, "index": args.expected_index} if expected_tx else None
            ),
        }
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        raise SystemExit(1)
    if identity:
        objects = identity_matches(objects, identity)
    indexed_match = bool(objects)
    if expected_tx:
        indexed_match = outpoint_matches(objects, expected_tx, args.expected_index)

    direct_status = "not_checked"
    direct_cell: Any = None
    if expected_tx:
        try:
            direct = rpc_call(
                args.rpc_url,
                "get_live_cell",
                [{"tx_hash": expected_tx, "index": hex(args.expected_index)}, True],
                args.ca_bundle,
            )
            direct_status = (
                direct.get("status", "unavailable") if isinstance(direct, dict) else "unavailable"
            )
            direct_cell = direct.get("cell") if isinstance(direct, dict) else None
        except Exception as exc:  # noqa: BLE001 - report the operational failure
            direct_status = "rpc_error"
            direct_cell = {"error": str(exc)}
    status = classify_consistency(
        indexed_match=indexed_match,
        direct_status=direct_status,
        expected_outpoint=expected_tx is not None,
    )
    if identity and len(objects) > 1:
        status = "duplicate_identity"
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "pass": status == "ok",
        "deployment": {"code_hash": code_hash, "hash_type": args.hash_type},
        "receiver_identity": identity,
        "indexer": {
            "url": args.indexer_url,
            "object_count": len(objects),
            "pages_scanned": pages_scanned,
            "objects": objects,
        },
        "direct_rpc": {"url": args.rpc_url, "status": direct_status, "cell": direct_cell},
        "expected_outpoint": (
            {"tx_hash": expected_tx, "index": args.expected_index} if expected_tx else None
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if status != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
