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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply receiver-registry type script to a ckb-cli tx file")
    parser.add_argument("--tx-file", default="deploy/receiver-registration-tx.json")
    parser.add_argument("--template-file", default="deploy/receiver-registration-tx-template.json")
    parser.add_argument(
        "--contract-tx-hash",
        default="0x3c70291371806e0a49f4bfd198811583724de8ffec5b1dc9de93e2a58de2114c",
        help="Deployment transaction hash for the receiver-registry contract",
    )
    parser.add_argument(
        "--contract-index",
        type=int,
        default=0,
        help="Output index of the deployed receiver-registry contract cell",
    )
    parser.add_argument("--output-index", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tx_path = Path(args.tx_file)
    template_path = Path(args.template_file)

    tx = json.loads(tx_path.read_text())
    template = json.loads(template_path.read_text())

    outputs = tx.get("transaction", {}).get("outputs")
    if outputs is None:
        raise SystemExit("Unsupported tx file format: missing transaction.outputs")

    template_outputs = template.get("outputs")
    if not template_outputs:
        raise SystemExit("Template missing outputs")

    output = outputs[args.output_index]
    output["type"] = template_outputs[0]["type"]

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
    print(f"Updated type script and contract cell dep in {tx_path}")


if __name__ == "__main__":
    main()
