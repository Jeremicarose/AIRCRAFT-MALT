#!/usr/bin/env python3
"""Generate the compact historical MLAT solver benchmark report."""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlat_reference.benchmarks.compact_solver import (  # noqa: E402
    SourceIntegrityError,
    build_compact_benchmark_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a solver-only benchmark against pinned historical observations. "
            "This command does not validate live operation or CKB Registry identity."
        )
    )
    fixtures = ROOT / "reference/mlat/benchmarks/fixtures/compact-public"
    parser.add_argument("--sensors", type=Path, default=fixtures / "sensors.csv")
    parser.add_argument("--measurements", type=Path, default=fixtures / "set_1.csv")
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=ROOT
        / "reference"
        / "mlat"
        / "benchmarks"
        / "fixtures"
        / "mpyc-gps-five-source.json",
    )
    parser.add_argument(
        "--event-fixture",
        type=Path,
        default=ROOT
        / "reference"
        / "mlat"
        / "benchmarks"
        / "fixtures"
        / "mpyc-gps-five-event.json",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/compact-public-solver-v2/report.json"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_compact_benchmark_report(
            args.sensors,
            args.measurements,
            source_manifest_path=args.source_manifest,
            event_fixture_path=args.event_fixture,
        )
    except (OSError, KeyError, ValueError, SourceIntegrityError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".sha256").write_text(
        f"{checksum}  {args.output.name}\n", encoding="utf-8"
    )
    counts = report["compact_dataset"]["event_counts"]
    print(
        f"Solved {counts['solved']} of {counts['total']} events "
        f"({report['compact_dataset']['solve_rate']:.1%})."
    )
    print("Scope: historical solver-only evidence; not live or Registry validation.")
    print(f"Report: {args.output}")
    return 0 if report["synthetic_control"]["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
