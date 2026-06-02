#!/usr/bin/env python3
"""
Fetch live cells for a deployer address and print the exact ckb-cli tx command
sequence to assemble, sign, and send a receiver-registration transaction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print ckb-cli tx commands for receiver registration")
    parser.add_argument("--address", required=True, help="Funding/deployer address")
    parser.add_argument("--rpc-url", default="https://testnet.ckb.dev/rpc")
    parser.add_argument("--tx-file", default="deploy/receiver-registration-tx.json")
    parser.add_argument(
        "--template-file",
        default="deploy/receiver-registration-tx-template.json",
    )
    parser.add_argument(
        "--record-json-file",
        default="deploy/receiver-registry-record.json",
    )
    parser.add_argument(
        "--capacity",
        default="1000",
        help="Receiver registry output capacity in CKB",
    )
    parser.add_argument("--limit", default="5")
    return parser.parse_args()


def fetch_live_cells(address: str, rpc_url: str, limit: str) -> dict:
    result = subprocess.run(
        [
            "ckb-cli",
            "--url",
            rpc_url,
            "wallet",
            "get-live-cells",
            "--address",
            address,
            "--limit",
            limit,
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def choose_funding_cell(live_cells: dict) -> dict:
    cells = live_cells.get("live_cells", [])
    if not cells:
        raise SystemExit("No live cells found for funding address")

    # Prefer a plain change cell without type scripts.
    plain_cells = [cell for cell in cells if not cell.get("type_hashes")]
    selected = plain_cells[0] if plain_cells else cells[0]
    return selected


def main() -> None:
    args = parse_args()
    template_path = Path(args.template_file)
    if not template_path.exists():
        raise SystemExit(f"Missing transaction template: {template_path}")

    live_cells = fetch_live_cells(args.address, args.rpc_url, args.limit)
    funding_cell = choose_funding_cell(live_cells)
    tx_hash = funding_cell["tx_hash"]
    output_index = funding_cell["output_index"]

    print("Receiver registration command sequence")
    print("=" * 48)
    print(f"Selected funding cell: {tx_hash}#{output_index}")
    print()
    print("1. Initialize a ckb-cli tx file:")
    print(f"   ckb-cli tx init --tx-file {args.tx_file}")
    print()
    print("2. Add the funding input:")
    print(
        "   ckb-cli tx add-input "
        f"--tx-hash {tx_hash} --index {output_index} --tx-file {args.tx_file}"
    )
    print()
    print("3. Add the receiver registry output:")
    print(
        "   ckb-cli --url {rpc} tx add-output "
        f"--to-sighash-address \"{args.address}\" "
        f"--capacity {args.capacity} "
        f"--to-data-path {args.record_json_file} "
        f"--tx-file {args.tx_file}".format(rpc=args.rpc_url)
    )
    print()
    print("4. Apply the receiver-registry type script to the tx file:")
    print(
        "   python3 scripts/apply_receiver_type_script.py "
        f"--tx-file {args.tx_file} --template-file {template_path}"
    )
    print()
    print("5. Inspect the transaction and calculate a change output:")
    print(f"   ckb-cli --url {args.rpc_url} tx info --tx-file {args.tx_file}")
    print()
    print("6. Add a change output back to your address using the remaining capacity.")
    print("   Suggested formula: input_total - receiver_output - small_fee_buffer")
    print()
    print("7. Re-run tx info and verify the fee is small.")
    print()
    print("8. Sign the transaction:")
    print(
        f"   ckb-cli --url {args.rpc_url} tx sign-inputs "
        f"--from-account \"{args.address}\" "
        f"--tx-file {args.tx_file} --add-signatures"
    )
    print()
    print("9. Send the transaction:")
    print(f"   ckb-cli --url {args.rpc_url} tx send --tx-file {args.tx_file}")


if __name__ == "__main__":
    main()
