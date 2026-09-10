#!/usr/bin/env python3
"""
Update the Registry V2 code binding inside a .env file.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import normalize_receiver_identity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Registry V2 code binding into .env")
    parser.add_argument(
        "--code-hash",
        "--type-hash",
        dest="code_hash",
        required=True,
        help="Registry contract code hash (the binary data hash for data1)",
    )
    parser.add_argument(
        "--hash-type",
        choices=("data1", "type"),
        default="data1",
        help="Registry script hash type; new deployments must use data1",
    )
    parser.add_argument(
        "--allow-mutable-code",
        action="store_true",
        help="Required with --hash-type=type for historical read-only compatibility",
    )
    parser.add_argument("--env-file", default=".env", help="Path to env file")
    parser.add_argument(
        "--disable-simulation",
        action="store_true",
        help="Also set SIMULATE_IF_UNAVAILABLE=false",
    )
    return parser.parse_args()


def replace_line(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    updated = False
    for idx, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[idx] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    if args.hash_type == "type" and not args.allow_mutable_code:
        raise SystemExit(
            "hash_type=type permits mutable Registry code; pass --allow-mutable-code "
            "only for historical read-only compatibility"
        )
    code_hash = normalize_receiver_identity(args.code_hash)
    env_path = Path(args.env_file)
    if not env_path.exists():
        raise SystemExit(f"Env file not found: {env_path}")

    text = env_path.read_text()
    text = replace_line(text, "RECEIVER_REGISTRY_TYPE_HASH", code_hash)
    text = replace_line(text, "RECEIVER_REGISTRY_HASH_TYPE", args.hash_type)
    text = replace_line(
        text,
        "ALLOW_MUTABLE_REGISTRY_CODE",
        "true" if args.hash_type == "type" else "false",
    )
    if args.disable_simulation:
        text = replace_line(text, "SIMULATE_IF_UNAVAILABLE", "false")
    env_path.write_text(text)
    print(f"Updated {env_path}")


if __name__ == "__main__":
    main()
