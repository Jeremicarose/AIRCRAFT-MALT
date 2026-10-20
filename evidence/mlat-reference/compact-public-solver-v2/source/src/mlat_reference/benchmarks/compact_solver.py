"""Run the unchanged MLAT solver against compact, attributed fixtures."""

from __future__ import annotations

import csv
import json
import hashlib
import math
import platform
import subprocess
from collections import Counter
from pathlib import Path
from statistics import fmean, median
from typing import Any, Literal

import numpy as np

from mlat_reference.solver.robust import ReceiverPosition, RobustMLATSolver, SignalObservation
from mlat_reference.benchmarks.diagnostics import (
    DiagnosticSolver,
    receiver_geometry,
    summarize as metric_summary,
)

TimingMode = Literal["synthetic", "published"]
_EARTH_RADIUS_M = 6_371_000.0
BENCHMARK_ID = "compact-public-solver-v2"


def solver_revision() -> dict:
    root = Path(__file__).resolve().parents[3]
    relative = "src/mlat_reference/solver/robust.py"
    try:
        commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", relative],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        committed = subprocess.check_output(
            ["git", "show", f"{commit}:{relative}"], cwd=root, stderr=subprocess.DEVNULL
        )
        return {
            "solver_commit": commit,
            "solver_worktree_modified": committed != (root / relative).read_bytes(),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"solver_commit": None, "solver_worktree_modified": None}


class SourceIntegrityError(ValueError):
    """Raised when benchmark input does not match its pinned source manifest."""


def _verify_source_file(path: Path, expected: dict[str, Any]) -> None:
    if path.stat().st_size > 5_242_880:
        raise SourceIntegrityError("Compact benchmark input exceeds 5 MiB")
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha256 != expected["sha256"]:
        raise SourceIntegrityError(
            f"{expected['name']} SHA-256 mismatch: "
            f"expected {expected['sha256']}, got {actual_sha256}"
        )


def _sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_compact_source(sensors_path, measurements_path, source_manifest_path):
    """Shared verified input for the numerical benchmark and historical adapter."""
    manifest = json.loads(Path(source_manifest_path).read_text(encoding="utf-8"))
    _verify_source_file(Path(sensors_path), manifest["files"]["sensors"])
    _verify_source_file(Path(measurements_path), manifest["files"]["measurements"])
    sensors = {}
    with Path(sensors_path).open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["serial"] in sensors:
                raise SourceIntegrityError("Duplicate dataset receiver serial")
            position = ReceiverPosition(
                float(row["latitude"]),
                float(row["longitude"]),
                float(row["height"]),
                f"locards:{row['serial']}",
            )
            if (
                not all(
                    math.isfinite(value)
                    for value in (position.latitude, position.longitude, position.altitude)
                )
                or not -90 <= position.latitude <= 90
                or not -180 <= position.longitude <= 180
            ):
                raise SourceIntegrityError("Invalid dataset receiver geometry")
            sensors[row["serial"]] = position
    with Path(measurements_path).open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != int(manifest["expected_event_count"]) or len(
        {row["id"] for row in rows}
    ) != len(rows):
        raise SourceIntegrityError(
            "Dataset event count or unique event IDs do not match the manifest"
        )
    return sensors, rows, manifest


def build_compact_benchmark_report(
    sensors_path: str | Path,
    measurements_path: str | Path,
    *,
    source_manifest_path: str | Path,
    event_fixture_path: str | Path,
) -> dict[str, Any]:
    """Build one deterministic report for the control, example, and full sample."""
    synthetic_control = evaluate_fixture_event(event_fixture_path, timing_mode="synthetic")
    published_event = evaluate_fixture_event(event_fixture_path, timing_mode="published")
    dataset = evaluate_compact_dataset(
        sensors_path,
        measurements_path,
        source_manifest_path=source_manifest_path,
    )
    synthetic_error = (
        synthetic_control["errors_m"]["three_dimensional"] if synthetic_control["solved"] else None
    )
    synthetic_control["acceptance"] = {
        "criterion": "Exact-propagation 3D error is below 1 metre.",
        "maximum_3d_error_m": 1.0,
        "passed": synthetic_error is not None and synthetic_error < 1.0,
    }
    return {
        "schema_version": 1,
        "benchmark_id": BENCHMARK_ID,
        "benchmark_version": 2,
        "is_live": False,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "implementation": platform.python_implementation(),
        },
        "claim_scope": "solver_only",
        "implementation": {
            **solver_revision(),
            "diagnostics_module_sha256": _sha256(Path(__file__).with_name("diagnostics.py")),
            "benchmark_module_sha256": _sha256(Path(__file__)),
            "solver_module_sha256": _sha256(
                Path(__file__).resolve().parents[1] / "solver" / "robust.py"
            ),
        },
        "inputs": {
            "source_manifest_sha256": _sha256(source_manifest_path),
            "event_fixture_sha256": _sha256(event_fixture_path),
            "sensors_sha256": _sha256(sensors_path),
            "measurements_sha256": _sha256(measurements_path),
        },
        "synthetic_control": synthetic_control,
        "published_event": published_event,
        "compact_dataset": dataset,
        "interpretation": {
            "solver_numeric_behavior_measured": True,
            "production_pipeline_validated": False,
            "registry_identity_validated": False,
            "live_operation_validated": False,
            "clock_attestation_validated": False,
            "physical_receiver_claims_validated": False,
        },
    }


def evaluate_compact_dataset(
    sensors_path: str | Path,
    measurements_path: str | Path,
    *,
    source_manifest_path: str | Path,
) -> dict[str, Any]:
    """Verify and evaluate the complete compact historical dataset."""
    sensors_path = Path(sensors_path)
    measurements_path = Path(measurements_path)
    sensors, rows, manifest = load_compact_source(
        sensors_path, measurements_path, source_manifest_path
    )

    solver = DiagnosticSolver()
    events: list[dict[str, Any]] = []
    for row in rows:
        event_measurements = json.loads(row["measurements"])
        missing_sensors = [
            str(measurement[0])
            for measurement in event_measurements
            if str(measurement[0]) not in sensors
        ]
        event: dict[str, Any] = {
            "event_id": row["id"],
            "aircraft_dataset_id": row["aircraft"],
            "receiver_count": len(event_measurements),
            "solved": False,
            "data_provenance": "HISTORICAL_REPLAY",
            "source_time_seconds": float(row["timeAtServer"]),
            "timestamp_context": "dataset-relative; UTC epoch not supplied",
        }
        if missing_sensors:
            event["failure_reason"] = "missing_sensor_metadata"
            event["missing_sensor_ids"] = missing_sensors
            events.append(event)
            continue

        observations = []
        for serial, timestamp_ns, _signal_strength in event_measurements:
            position = sensors[str(serial)]
            timestamp_ns = int(timestamp_ns)
            observations.append(
                SignalObservation(
                    receiver_id=position.receiver_id,
                    timestamp=timestamp_ns / 1_000_000_000.0,
                    timestamp_ns=timestamp_ns,
                    signal_data=f"benchmark:{row['id']}",
                    receiver_position=position,
                )
            )

        expected_latitude = float(row["latitude"])
        expected_longitude = float(row["longitude"])
        expected_altitude = float(row["geoAltitude"])
        truth = ReceiverPosition(
            expected_latitude, expected_longitude, expected_altitude, "reference"
        )
        event["geometry"] = receiver_geometry(observations, truth)
        event["receiver_ids"] = [observation.receiver_id for observation in observations]
        solution = solver.solve_position(observations)
        event["diagnostics"] = dict(solver.diagnostics)
        if solution is None:
            event["failure_reason"] = solver.diagnostics["failure_category"]
            events.append(event)
            continue

        horizontal_error = _horizontal_error_m(
            expected_latitude,
            expected_longitude,
            solution.latitude,
            solution.longitude,
        )
        vertical_error = abs(solution.altitude - expected_altitude)
        event.update(
            {
                "solved": True,
                "errors_m": {
                    "horizontal": horizontal_error,
                    "vertical": vertical_error,
                    "three_dimensional": math.hypot(horizontal_error, vertical_error),
                },
                "solution": {
                    "latitude": solution.latitude,
                    "longitude": solution.longitude,
                    "altitude_m": solution.altitude,
                    "residual_m": solution.residual,
                    "uncertainty_m": solution.uncertainty,
                    "iterations": solution.iterations,
                },
            }
        )
        events.append(event)

    if len(events) != int(manifest["expected_event_count"]):
        raise SourceIntegrityError(
            "event count mismatch: "
            f"expected {manifest['expected_event_count']}, got {len(events)}"
        )

    solved_events = [event for event in events if event["solved"]]

    def summarize(metric: str) -> dict[str, float] | None:
        values = [event["errors_m"][metric] for event in solved_events]
        if not values:
            return None
        return {
            "median": median(values),
            "p95": float(np.percentile(values, 95)),
            "mean": fmean(values),
            "maximum": max(values),
        }

    solved_count = len(solved_events)
    total_count = len(events)
    return {
        "schema_version": 1,
        "benchmark_id": BENCHMARK_ID,
        "data_provenance": "HISTORICAL_REPLAY",
        "data_source": manifest["data_source"],
        "claim_scope": manifest["claim_scope"],
        "is_live": False,
        "source": {
            "source_id": manifest["source_id"],
            "license": manifest["license"],
            "upstream_repository": manifest.get("upstream_repository"),
            "upstream_version": manifest.get("upstream_version"),
            "original_dataset": manifest.get("original_dataset"),
            "files": manifest["files"],
            "limitations": manifest["limitations"],
        },
        "solver": "RobustMLATSolver",
        "event_counts": {
            "total": total_count,
            "solved": solved_count,
            "unsolved": total_count - solved_count,
        },
        "solve_rate": solved_count / total_count if total_count else 0.0,
        "residual_m": metric_summary(event["solution"]["residual_m"] for event in solved_events),
        "iterations": {
            "definition": "Iteration at the best returned candidate, as reported by the unchanged solver; not necessarily total optimizer steps.",
            "successful": metric_summary(
                event["solution"]["iterations"] for event in solved_events
            ),
            "failed_with_candidate": metric_summary(
                event.get("diagnostics", {}).get("iterations")
                for event in events
                if not event["solved"]
            ),
        },
        "failure_categories": dict(
            sorted(
                Counter(event["failure_reason"] for event in events if not event["solved"]).items()
            )
        ),
        "receiver_geometry": {
            "unique_receivers": len(
                {receiver_id for event in events for receiver_id in event.get("receiver_ids", [])}
            ),
            "receiver_count": metric_summary(event["receiver_count"] for event in events),
            "successful": {
                name: metric_summary(event["geometry"][name] for event in solved_events)
                for name in (
                    "minimum_baseline_m",
                    "maximum_baseline_m",
                    "vertical_aperture_m",
                    "tdoa_condition_number_at_reference",
                )
            },
            "failed": {
                name: metric_summary(
                    event["geometry"][name]
                    for event in events
                    if not event["solved"] and "geometry" in event
                )
                for name in (
                    "minimum_baseline_m",
                    "maximum_baseline_m",
                    "vertical_aperture_m",
                    "tdoa_condition_number_at_reference",
                )
            },
        },
        "accuracy_m": {
            "horizontal": summarize("horizontal"),
            "vertical": summarize("vertical"),
            "three_dimensional": summarize("three_dimensional"),
        },
        "events": events,
    }


def _horizontal_error_m(
    expected_latitude: float,
    expected_longitude: float,
    actual_latitude: float,
    actual_longitude: float,
) -> float:
    """Return great-circle distance between two latitude/longitude pairs."""
    expected_latitude_rad = math.radians(expected_latitude)
    actual_latitude_rad = math.radians(actual_latitude)
    latitude_delta = actual_latitude_rad - expected_latitude_rad
    longitude_delta = math.radians(actual_longitude - expected_longitude)
    haversine = (
        math.sin(latitude_delta / 2.0) ** 2
        + math.cos(expected_latitude_rad)
        * math.cos(actual_latitude_rad)
        * math.sin(longitude_delta / 2.0) ** 2
    )
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(haversine))


def evaluate_fixture_event(
    fixture_path: str | Path,
    *,
    timing_mode: TimingMode,
) -> dict[str, Any]:
    """Evaluate one historical event or its exact-propagation synthetic control."""
    if timing_mode not in {"synthetic", "published"}:
        raise ValueError("timing_mode must be 'synthetic' or 'published'")

    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    timestamp_field = f"{timing_mode}_timestamp_ns"
    observations: list[SignalObservation] = []

    for receiver in fixture["receivers"]:
        timestamp_ns = int(receiver[timestamp_field])
        position = ReceiverPosition(
            latitude=float(receiver["latitude"]),
            longitude=float(receiver["longitude"]),
            altitude=float(receiver["altitude_m"]),
            receiver_id=str(receiver["receiver_id"]),
        )
        observations.append(
            SignalObservation(
                receiver_id=position.receiver_id,
                timestamp=timestamp_ns / 1_000_000_000.0,
                timestamp_ns=timestamp_ns,
                signal_data=f"benchmark:{fixture['event_id']}",
                receiver_position=position,
            )
        )

    solution = RobustMLATSolver().solve_position(observations)
    source = "SIMULATION" if timing_mode == "synthetic" else "HISTORICAL_RECORDING"
    result: dict[str, Any] = {
        "benchmark_id": fixture["benchmark_id"],
        "event_id": fixture["event_id"],
        "timing_mode": timing_mode,
        "data_source": source,
        "data_provenance": "SYNTHETIC" if timing_mode == "synthetic" else "HISTORICAL_REPLAY",
        "source": fixture["source"],
        "claim_scope": fixture["claim_scope"],
        "is_live": False,
        "receiver_count": len(observations),
        "ground_truth": fixture["ground_truth"],
        "receiver_geometry": [
            {
                "receiver_id": receiver["receiver_id"],
                "latitude": receiver["latitude"],
                "longitude": receiver["longitude"],
                "altitude_m": receiver["altitude_m"],
            }
            for receiver in fixture["receivers"]
        ],
        "solved": solution is not None,
    }
    if solution is None:
        result["errors_m"] = None
        return result

    truth = fixture["ground_truth"]
    horizontal_error = _horizontal_error_m(
        float(truth["latitude"]),
        float(truth["longitude"]),
        solution.latitude,
        solution.longitude,
    )
    vertical_error = abs(solution.altitude - float(truth["altitude_m"]))
    result.update(
        {
            "solution": {
                "latitude": solution.latitude,
                "longitude": solution.longitude,
                "altitude_m": solution.altitude,
                "residual_m": solution.residual,
                "uncertainty_m": solution.uncertainty,
                "iterations": solution.iterations,
                "quality_score": solution.quality_score,
                "quality_bucket": solution.quality_bucket,
            },
            "errors_m": {
                "horizontal": horizontal_error,
                "vertical": vertical_error,
                "three_dimensional": math.hypot(horizontal_error, vertical_error),
            },
        }
    )
    return result
