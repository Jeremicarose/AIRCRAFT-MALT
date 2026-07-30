#!/usr/bin/env python3
"""
Generate a receiver-registry cell transaction template for manual completion
or integration with ckb-cli / custom tooling.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from network.receiver_registry import normalize_identity_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a receiver registration transaction template")
    parser.add_argument("--lock-arg", required=True, help="Owner lock arg for the receiver cell")
    parser.add_argument("--type-hash", required=True, help="Deployed receiver-registry type hash")
    parser.add_argument("--data-hex-file", default="deploy/receiver-registry-record.hex")
    parser.add_argument("--capacity", default="1000", help="Cell capacity in CKB")
    parser.add_argument("--output", default="deploy/receiver-registration-tx-template.json")
    return parser.parse_args()


def ckb_to_shannons(value: str) -> int:
    try:
        capacity = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("capacity must be a decimal CKB amount") from exc
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    shannons = capacity * 100_000_000
    if shannons != shannons.to_integral_value():
        raise ValueError("capacity supports at most 8 decimal places")
    return int(shannons)


def main() -> None:
    args = parse_args()
    contract_code_hash = normalize_identity_id(args.type_hash)
    data_hex = Path(args.data_hex_file).read_text().strip()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tx_template = {
        "version": "0x0",
        "cell_deps": [],
        "header_deps": [],
        "inputs": [],
        "outputs": [
            {
                "capacity": hex(ckb_to_shannons(args.capacity)),
                "lock": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": args.lock_arg,
                },
                "type": {
                    "code_hash": contract_code_hash,
                    "hash_type": "type",
                    "args": "0x",
                },
            }
        ],
        "outputs_data": [data_hex],
        "witnesses": [],
        "registry_v2": {
            "identity_rule": "blake2b(first_input_molecule || output_index_le_u64)",
            "type_args_pending": True,
            "next_step": "run scripts/apply_receiver_type_script.py after adding the funding input",
        },
    }

    output_path.write_text(json.dumps(tx_template, indent=2) + "\n")
    print(f"Wrote transaction template to {output_path}")


if __name__ == "__main__":
    main()
