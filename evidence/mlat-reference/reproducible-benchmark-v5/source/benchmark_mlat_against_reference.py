#!/usr/bin/env python3
"""Compare MLAT output against a trusted reference dataset."""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

NON_LIVE_SOLVER_METHODS = {"", "unknown", "simulation", "simulated_replay"}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected a JSON object in {path} at line {line_number}")
            rows.append(row)
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _timestamp_range(rows: list[dict]) -> dict[str, float | None]:
    timestamps = [float(row["timestamp"]) for row in rows if row.get("timestamp") is not None]
    return {
        "start": min(timestamps) if timestamps else None,
        "end": max(timestamps) if timestamps else None,
    }


def _created_at_timestamp(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp()


def _normalize_runtime_snapshot(snapshot: dict | None) -> dict | None:
    if not isinstance(snapshot, dict):
        return None
    dimensions = snapshot.get("dimensions")
    if not isinstance(dimensions, dict):
        return None
    freshness = dimensions.get("freshness")
    reliability = dimensions.get("reliability")
    if not isinstance(freshness, dict) or not isinstance(reliability, dict):
        return None
    return {
        "captured_at": snapshot.get("generated_at"),
        "ready": bool(snapshot.get("ready")),
        "freshness": freshness,
        "reliability": reliability,
    }


def match_records(
    mlat_rows: list[dict],
    reference_rows: list[dict],
    time_tolerance_seconds: float,
) -> list[tuple[dict, dict, float]]:
    """Return globally-nearest one-to-one matches within each aircraft track."""
    reference_by_aircraft: dict[str, list[tuple[float, int, dict]]] = {}
    for reference_index, row in enumerate(reference_rows):
        reference_by_aircraft.setdefault(str(row["aircraft_id"]), []).append(
            (float(row["timestamp"]), reference_index, row)
        )

    for rows in reference_by_aircraft.values():
        rows.sort(key=lambda item: item[0])
    reference_timestamps_by_aircraft = {
        aircraft_id: [item[0] for item in rows]
        for aircraft_id, rows in reference_by_aircraft.items()
    }

    candidates: list[tuple[float, int, int, dict, dict]] = []
    for mlat_index, row in enumerate(mlat_rows):
        references = reference_by_aircraft.get(str(row["aircraft_id"]), [])
        if not references:
            continue
        timestamp = float(row["timestamp"])
        reference_timestamps = reference_timestamps_by_aircraft[str(row["aircraft_id"])]
        start = bisect_left(reference_timestamps, timestamp - time_tolerance_seconds)
        end = bisect_right(reference_timestamps, timestamp + time_tolerance_seconds)
        for reference_timestamp, reference_index, reference in references[start:end]:
            candidates.append(
                (
                    abs(reference_timestamp - timestamp),
                    mlat_index,
                    reference_index,
                    row,
                    reference,
                )
            )

    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    used_mlat: set[int] = set()
    used_reference: set[int] = set()
    matches: list[tuple[dict, dict, float]] = []
    for delta, mlat_index, reference_index, mlat_row, reference_row in candidates:
        if mlat_index in used_mlat or reference_index in used_reference:
            continue
        used_mlat.add(mlat_index)
        used_reference.add(reference_index)
        matches.append((mlat_row, reference_row, delta))
    return matches


def build_report(
    mlat_rows: list[dict],
    reference_rows: list[dict],
    *,
    mlat_path: Path,
    reference_path: Path,
    time_tolerance_seconds: float,
    reference_source: str,
    region: str,
    data_provenance: str,
    runtime_snapshot: dict | None = None,
    runtime_snapshot_path: Path | None = None,
) -> dict[str, Any]:
    matches = match_records(mlat_rows, reference_rows, time_tolerance_seconds)
    horizontal_errors = [
        haversine_m(
            float(mlat["latitude"]),
            float(mlat["longitude"]),
            float(reference["latitude"]),
            float(reference["longitude"]),
        )
        for mlat, reference, _delta in matches
    ]
    altitude_errors = [
        abs(float(mlat.get("altitude", 0.0)) - float(reference.get("altitude", 0.0)))
        for mlat, reference, _delta in matches
    ]
    match_deltas_ms = [delta * 1000 for _mlat, _reference, delta in matches]

    end_to_store_ages_ms = []
    for row in mlat_rows:
        created_at = _created_at_timestamp(row.get("created_at"))
        if created_at is None or row.get("timestamp") is None:
            continue
        end_to_store_ages_ms.append(max(0.0, (created_at - float(row["timestamp"])) * 1000))

    solver_methods = sorted({str(row.get("solver_method", "unknown")) for row in mlat_rows})
    normalized_runtime_snapshot = _normalize_runtime_snapshot(runtime_snapshot)
    limitations = []
    if data_provenance != "live":
        limitations.append("The dataset was not explicitly attested as live receiver data.")
    if not mlat_rows:
        limitations.append("The MLAT dataset is empty.")
    if not matches:
        limitations.append("No MLAT records matched the reference dataset.")
    if any(method.strip().lower() in NON_LIVE_SOLVER_METHODS for method in solver_methods):
        limitations.append(
            "The MLAT dataset contains simulated, unknown, or unlabelled solver provenance."
        )
    if reference_source.strip().lower() == "unspecified":
        limitations.append("The reference source was not identified.")
    if region.strip().lower() == "unspecified":
        limitations.append("The benchmark region was not identified.")
    if normalized_runtime_snapshot is None:
        limitations.append("No valid runtime freshness and reliability snapshot was attached.")

    benchmarkable = not limitations
    matched_aircraft = {str(mlat["aircraft_id"]) for mlat, _reference, _delta in matches}
    quality_scores = [float(row.get("quality_score", 0.0)) for row in mlat_rows]
    receiver_counts = [float(row.get("receiver_count", 0.0)) for row in mlat_rows]

    accuracy = {
        "horizontal_error_median_m": (
            statistics.median(horizontal_errors) if horizontal_errors else 0.0
        ),
        "horizontal_error_p95_m": percentile(horizontal_errors, 95),
        "altitude_error_median_m": statistics.median(altitude_errors) if altitude_errors else 0.0,
        "altitude_error_p95_m": percentile(altitude_errors, 95),
        "match_delta_median_ms": statistics.median(match_deltas_ms) if match_deltas_ms else 0.0,
        "match_delta_p95_ms": percentile(match_deltas_ms, 95),
    }
    freshness = {
        "measured_records": len(end_to_store_ages_ms),
        "end_to_store_age_median_ms": (
            statistics.median(end_to_store_ages_ms) if end_to_store_ages_ms else None
        ),
        "end_to_store_age_p95_ms": (
            percentile(end_to_store_ages_ms, 95) if end_to_store_ages_ms else None
        ),
    }
    matched = len(matches)
    total_mlat = len(mlat_rows)
    total_reference = len(reference_rows)

    inputs = {
        "mlat": {"filename": mlat_path.name, "sha256": file_sha256(mlat_path)},
        "reference": {"filename": reference_path.name, "sha256": file_sha256(reference_path)},
    }
    if runtime_snapshot_path is not None:
        inputs["runtime_snapshot"] = {
            "filename": runtime_snapshot_path.name,
            "sha256": file_sha256(runtime_snapshot_path),
        }

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "publishable" if benchmarkable else "pipeline_only",
        "provenance": {
            "benchmarkable": benchmarkable,
            "data_provenance": data_provenance,
            "solver_methods": solver_methods,
            "reference_source": reference_source,
            "region": region,
            "limitations": limitations,
        },
        "inputs": inputs,
        "window": {
            "mlat": _timestamp_range(mlat_rows),
            "reference": _timestamp_range(reference_rows),
        },
        "matching": {
            "strategy": "nearest_timestamp_one_to_one",
            "time_tolerance_seconds": time_tolerance_seconds,
        },
        "sample": {
            "total_mlat_records": total_mlat,
            "total_reference_records": total_reference,
            "matched_records": matched,
            "matched_aircraft": len(matched_aircraft),
            "coverage_ratio_vs_reference": (matched / total_reference) if total_reference else 0.0,
            "match_ratio_vs_mlat": (matched / total_mlat) if total_mlat else 0.0,
        },
        "accuracy": accuracy,
        "freshness": freshness,
        "runtime_snapshot": normalized_runtime_snapshot,
        "quality": {
            "avg_quality_score": average(quality_scores),
            "avg_receiver_count": average(receiver_counts),
        },
        # Preserve the original flat fields for existing automation.
        "total_mlat_records": total_mlat,
        "total_reference_records": total_reference,
        "matched_records": matched,
        "coverage_ratio_vs_reference": (matched / total_reference) if total_reference else 0.0,
        **{key: value for key, value in accuracy.items() if "error_" in key},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlat", required=True, help="Path to MLAT JSONL export")
    parser.add_argument("--reference", required=True, help="Path to reference JSONL export")
    parser.add_argument("--output", help="Optional path for the versioned JSON evidence report")
    parser.add_argument("--reference-source", default="unspecified", help="Reference provider name")
    parser.add_argument("--region", default="unspecified", help="Human-readable benchmark region")
    parser.add_argument(
        "--runtime-snapshot",
        help="Path to a timestamped /api/readiness JSON response captured during the run",
    )
    parser.add_argument(
        "--data-provenance",
        choices=("live", "replay", "synthetic", "unknown"),
        default="unknown",
        help="Explicit provenance attestation for the MLAT input",
    )
    parser.add_argument(
        "--time-tolerance-seconds",
        type=float,
        default=2.0,
        help="Maximum allowed timestamp delta when matching records",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.time_tolerance_seconds < 0:
        raise SystemExit("--time-tolerance-seconds must be non-negative")

    mlat_path = Path(args.mlat)
    reference_path = Path(args.reference)
    runtime_snapshot_path = Path(args.runtime_snapshot) if args.runtime_snapshot else None
    runtime_snapshot = None
    if runtime_snapshot_path is not None:
        try:
            runtime_snapshot = json.loads(runtime_snapshot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Unable to load --runtime-snapshot: {exc}") from exc
    report = build_report(
        load_jsonl(mlat_path),
        load_jsonl(reference_path),
        mlat_path=mlat_path,
        reference_path=reference_path,
        time_tolerance_seconds=args.time_tolerance_seconds,
        reference_source=args.reference_source,
        region=args.region,
        data_provenance=args.data_provenance,
        runtime_snapshot=runtime_snapshot,
        runtime_snapshot_path=runtime_snapshot_path,
    )

    encoded_report = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded_report + "\n", encoding="utf-8")
    print(encoded_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
