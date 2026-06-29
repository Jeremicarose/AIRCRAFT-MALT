#!/usr/bin/env python3
"""
Minimal command-jsonl bridge helper.

Usage:
  python3 scripts/sample_live_bridge.py --once
  cat feed.jsonl | python3 scripts/sample_live_bridge.py

This does not create real aircraft data on its own. It exists to make the
`command-jsonl` transport path concrete and testable in the repo so it can be
replaced with a real bridge or decoder command.
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample command-jsonl feed bridge")
    parser.add_argument("--once", action="store_true", help="Emit one sample line and exit")
    parser.add_argument("--receiver-id", default="RECV_NYC_001")
    parser.add_argument("--message", default="8D4840D6202CC371C32CE0576098")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.once:
        print(
            json.dumps(
                {
                    "receiver_id": args.receiver_id,
                    "timestamp": time.time(),
                    "message": args.message,
                }
            ),
            flush=True,
        )
        return 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        print(line, flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
