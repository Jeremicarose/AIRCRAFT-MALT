#!/usr/bin/env python3
"""
Compare MLAT output against a trusted reference dataset.

Input files are newline-delimited JSON (JSONL) with records containing:

MLAT record:
{
  "aircraft_id": "A1B2C3",
  "timestamp": 1710000000.0,
  "latitude": 40.75,
  "longitude": -73.85,
  "altitude": 9000.0,
  "uncertainty": 120.5,
  "quality_score": 0.82
}

Reference record:
{
  "aircraft_id": "A1B2C3",
  "timestamp": 1710000000.0,
  "latitude": 40.751,
  "longitude": -73.849,
  "altitude": 9050.0
}
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((q / 100.0) * len(ordered)) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mlat", required=True, help="Path to MLAT JSONL export")
    parser.add_argument("--reference", required=True, help="Path to reference JSONL export")
    parser.add_argument(
        "--time-tolerance-seconds",
        type=float,
        default=2.0,
        help="Maximum allowed timestamp delta when matching records",
    )
    args = parser.parse_args()

    mlat_rows = load_jsonl(Path(args.mlat))
    reference_rows = load_jsonl(Path(args.reference))

    reference_by_aircraft: dict[str, list[dict]] = {}
    for row in reference_rows:
        reference_by_aircraft.setdefault(row["aircraft_id"], []).append(row)

    for rows in reference_by_aircraft.values():
        rows.sort(key=lambda item: item["timestamp"])

    horizontal_errors = []
    altitude_errors = []
    matched = 0

    for row in mlat_rows:
        candidates = reference_by_aircraft.get(row["aircraft_id"], [])
        best = None
        best_dt = None
        for candidate in candidates:
            dt = abs(candidate["timestamp"] - row["timestamp"])
            if dt > args.time_tolerance_seconds:
                continue
            if best is None or dt < best_dt:
                best = candidate
                best_dt = dt

        if best is None:
            continue

        matched += 1
        horizontal_errors.append(
            haversine_m(
                row["latitude"],
                row["longitude"],
                best["latitude"],
                best["longitude"],
            )
        )
        altitude_errors.append(abs(float(row.get("altitude", 0.0)) - float(best.get("altitude", 0.0))))

    total_mlat = len(mlat_rows)
    total_reference = len(reference_rows)
    coverage_ratio = (matched / total_reference) if total_reference else 0.0

    summary = {
        "total_mlat_records": total_mlat,
        "total_reference_records": total_reference,
        "matched_records": matched,
        "coverage_ratio_vs_reference": coverage_ratio,
        "horizontal_error_median_m": statistics.median(horizontal_errors) if horizontal_errors else 0.0,
        "horizontal_error_p95_m": percentile(horizontal_errors, 95),
        "altitude_error_median_m": statistics.median(altitude_errors) if altitude_errors else 0.0,
        "altitude_error_p95_m": percentile(altitude_errors, 95),
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
