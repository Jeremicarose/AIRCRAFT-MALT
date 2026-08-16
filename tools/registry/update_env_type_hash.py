#!/usr/bin/env python3
"""
Update RECEIVER_REGISTRY_TYPE_HASH inside a .env file.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import normalize_identity_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write deployed CKB type hash into .env")
    parser.add_argument("--type-hash", required=True, help="Deployed receiver-registry type hash")
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
    type_hash = normalize_identity_id(args.type_hash)
    env_path = Path(args.env_file)
    if not env_path.exists():
        raise SystemExit(f"Env file not found: {env_path}")

    text = env_path.read_text()
    text = replace_line(text, "RECEIVER_REGISTRY_TYPE_HASH", type_hash)
    if args.disable_simulation:
        text = replace_line(text, "SIMULATE_IF_UNAVAILABLE", "false")
    env_path.write_text(text)
    print(f"Updated {env_path}")


if __name__ == "__main__":
    main()
