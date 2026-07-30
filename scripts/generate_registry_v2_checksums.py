#!/usr/bin/env python3
"""Generate a deterministic SHA-256 inventory for a Registry V2 bundle."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hash every public Registry V2 evidence file")
    parser.add_argument(
        "--bundle",
        default="evidence/registry-v2-testnet-2026-07-30-final",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = Path(args.bundle).resolve()
    if not bundle.is_dir():
        raise SystemExit(f"Evidence bundle does not exist: {bundle}")
    output = bundle / "checksums.sha256"
    files = sorted(
        path
        for path in bundle.rglob("*")
        if path.is_file()
        and path != output
        and path.name != ".DS_Store"
        and not (
            len(path.relative_to(bundle).parts) >= 2
            and path.relative_to(bundle).parts[0] == "ci"
            and (
                path.relative_to(bundle).parts[1] == "github-artifacts"
                or path.relative_to(bundle).parts[1].startswith("github-run-")
            )
        )
    )
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(bundle).as_posix()}"
        for path in files
    ]
    output.write_text("\n".join(lines) + "\n")
    print(f"Hashed {len(files)} files into {output}")


if __name__ == "__main__":
    main()
