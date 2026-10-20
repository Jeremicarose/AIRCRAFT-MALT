#!/usr/bin/env python3
"""Replay the compact historical source into an isolated, provenance-bound DB."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mlat_reference.replay import replay_compact_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    fixtures = ROOT / "reference/mlat/benchmarks/fixtures"
    try:
        result = replay_compact_dataset(
            args.database,
            fixtures / "compact-public/sensors.csv",
            fixtures / "compact-public/set_1.csv",
            fixtures / "mpyc-gps-five-source.json",
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Historical replay failed: {exc}\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "replay_status",
                    "event_count",
                    "successful_solves",
                    "failed_solves",
                    "failure_categories",
                    "timestamp_context",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
