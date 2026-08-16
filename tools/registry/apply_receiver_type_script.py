#!/usr/bin/env python3
"""
Inject the receiver-registry type script from the template file into a
ckb-cli-generated transaction JSON file, and add the required contract
cell dependency.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import calculate_type_id, normalize_identity_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply receiver-registry type script to a ckb-cli tx file"
    )
    parser.add_argument("--tx-file", default="deploy/receiver-registration-tx.json")
    parser.add_argument("--template-file", default="deploy/receiver-registration-tx-template.json")
    parser.add_argument(
        "--contract-tx-hash",
        required=True,
        help="Deployment transaction hash for the receiver-registry contract",
    )
    parser.add_argument(
        "--contract-index",
        type=int,
        default=0,
        help="Output index of the deployed receiver-registry contract cell",
    )
    parser.add_argument("--output-index", type=int, default=0)
    parser.add_argument(
        "--identity-id",
        help="Existing 32-byte identity for update/transfer/revocation; omit for creation",
    )
    return parser.parse_args()


def parse_hex_int(value, field: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid {field}: expected integer or 0x-prefixed integer") from exc


def creation_identity(transaction: dict, output_index: int) -> str:
    inputs = transaction.get("inputs")
    if not inputs:
        raise SystemExit(
            "Registry V2 creation requires a funding input before applying the type script"
        )
    first = inputs[0]
    previous_output = first.get("previous_output") or {}
    try:
        tx_hash = previous_output["tx_hash"]
        input_index = parse_hex_int(previous_output["index"], "first input index")
    except KeyError as exc:
        raise SystemExit("First input is missing previous_output tx_hash/index") from exc
    since = parse_hex_int(first.get("since", "0x0"), "first input since")
    return calculate_type_id(
        first_input_tx_hash=tx_hash,
        first_input_index=input_index,
        first_input_since=since,
        output_index=output_index,
    )


def main() -> None:
    args = parse_args()
    tx_path = Path(args.tx_file)
    template_path = Path(args.template_file)

    tx = json.loads(tx_path.read_text())
    template = json.loads(template_path.read_text())

    transaction = tx.get("transaction", {})
    outputs = transaction.get("outputs")
    if outputs is None:
        raise SystemExit("Unsupported tx file format: missing transaction.outputs")

    template_outputs = template.get("outputs")
    if not template_outputs:
        raise SystemExit("Template missing outputs")
    template_type = template_outputs[0].get("type") or {}
    try:
        contract_code_hash = normalize_identity_id(template_type.get("code_hash", ""))
    except ValueError as exc:
        raise SystemExit("Template Registry V2 code_hash must be 32-byte hex") from exc

    if not 0 <= args.output_index < len(outputs):
        raise SystemExit("output-index is outside transaction.outputs")
    identity_id = (
        normalize_identity_id(args.identity_id)
        if args.identity_id
        else creation_identity(transaction, args.output_index)
    )
    output = outputs[args.output_index]
    output["type"] = {
        **template_type,
        "code_hash": contract_code_hash,
        "args": identity_id,
    }

    cell_deps = tx.setdefault("transaction", {}).setdefault("cell_deps", [])
    contract_dep = {
        "out_point": {
            "tx_hash": args.contract_tx_hash,
            "index": hex(args.contract_index),
        },
        "dep_type": "code",
    }
    if contract_dep not in cell_deps:
        cell_deps.append(contract_dep)

    tx_path.write_text(json.dumps(tx, indent=2) + "\n")
    print(f"Updated Registry V2 identity {identity_id} and contract cell dep in {tx_path}")


if __name__ == "__main__":
    main()
