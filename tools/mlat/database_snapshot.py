#!/usr/bin/env python3
"""Back up or restore an MLAT SQLite database into a new file, including WAL state."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mlat_reference.database.backup import copy_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = copy_database(args.source, args.destination)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"status": "FAIL", "operation": args.operation, "reason": str(exc)}))
        return 1
    print(json.dumps({**report, "operation": args.operation}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
