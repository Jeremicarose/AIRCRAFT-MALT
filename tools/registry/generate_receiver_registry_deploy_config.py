#!/usr/bin/env python3
"""
Generate a ckb-cli deployment config for the receiver-registry contract.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATE = """[[cells]]
name = "receiver_registry"
enable_type_id = true
location = {{ file = "{contract_path}" }}

[lock]
code_hash = "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8"
args = "{lock_arg}"
hash_type = "type"
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ckb-cli deploy config for receiver registry"
    )
    parser.add_argument(
        "--contract-path",
        default="contracts/registry-v2/target/riscv64imac-unknown-none-elf/release/receiver-registry",
        help="Path to the built receiver-registry contract binary",
    )
    parser.add_argument(
        "--lock-arg",
        required=True,
        help="Lock arg for the deployer account (from ckb-cli account list)",
    )
    parser.add_argument(
        "--output",
        default="deploy/receiver-registry.toml",
        help="Output deployment config path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contract_path = Path(args.contract_path).resolve()
    if not contract_path.exists():
        raise SystemExit(f"Contract binary not found: {contract_path}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        TEMPLATE.format(
            contract_path=contract_path.as_posix(),
            lock_arg=args.lock_arg,
        )
    )
    print(f"Wrote deployment config to {output_path}")


if __name__ == "__main__":
    main()
