#!/usr/bin/env python3
"""Reproduce and explain the frozen LocaRDS solver-only diagnostic.

This tool deliberately bypasses production ingest, correlation, Registry
discovery, and clock qualification. It must not be used as a production feed
adapter or as evidence that the complete production pipeline is validated.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Iterable

import numpy as np

from mlat_reference.solver.robust import (
    SPEED_OF_LIGHT,
    ReceiverPosition,
    RobustMLATSolver,
    SignalObservation,
)

CALIBRATION_START_S = Decimal("0")
CALIBRATION_END_S = Decimal("120")
VALIDATION_START_S = Decimal("180")
VALIDATION_CASES = 300
MIN_PAIR_SAMPLES = 10
PAIR_WEIGHT_EXPONENT = 0.5


def percentile(values: Iterable[float], percentile_value: float) -> float | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * percentile_value / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def parse_measurements(value: str) -> list[dict[str, Any]]:
    decoded = json.loads(value, parse_int=str, parse_float=str)
    measurements = []
    for serial_token, timestamp_token, rssi_token in decoded:
        timestamp_text = str(timestamp_token)
        measurements.append(
            {
                "receiver_id": int(serial_token),
                "timestamp_text": timestamp_text,
                "timestamp_decimal": Decimal(timestamp_text),
                "timestamp_coarse": "e" in timestamp_text.lower(),
                "rssi": float(rssi_token),
            }
        )
    return measurements


def round_decimal_ns(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def geodetic_ecef(latitude: float, longitude: float, altitude: float) -> np.ndarray:
    return ReceiverPosition(latitude, longitude, altitude, "point").to_ecef()


def distance_m(point: np.ndarray, receiver: dict[str, Any]) -> float:
    return float(np.linalg.norm(point - receiver["ecef"]))


def load_metadata(dataset_dir: Path) -> tuple[dict[int, dict[str, Any]], set[int]]:
    sensors: dict[int, dict[str, Any]] = {}
    with (dataset_dir / "set_1_sensors.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            serial = int(row["serial"])
            sensor = {
                "receiver_id": serial,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "altitude": float(row["height"]),
                "type": row["type"],
                "good": row["good"].upper() == "TRUE",
            }
            sensor["ecef"] = geodetic_ecef(
                sensor["latitude"], sensor["longitude"], sensor["altitude"]
            )
            sensors[serial] = sensor

    trusted_aircraft: set[int] = set()
    with (dataset_dir / "set_1_aircraft.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["trusted"].upper() == "TRUE":
                trusted_aircraft.add(int(row["aircraft"]))
    return sensors, trusted_aircraft


def ground_truth_ecef(row: dict[str, str]) -> np.ndarray:
    return geodetic_ecef(
        float(row["latitude"]),
        float(row["longitude"]),
        float(row["geoAltitude"]),
    )


def pair_bias_ns(
    first: dict[str, Any],
    second: dict[str, Any],
    point: np.ndarray,
    sensors: dict[int, dict[str, Any]],
) -> float:
    observed_difference_ns = float(first["timestamp_decimal"] - second["timestamp_decimal"])
    propagation_difference_ns = (
        (
            distance_m(point, sensors[first["receiver_id"]])
            - distance_m(point, sensors[second["receiver_id"]])
        )
        / SPEED_OF_LIGHT
        * 1_000_000_000.0
    )
    return observed_difference_ns - propagation_difference_ns


def collect_calibration(
    dataset_dir: Path,
    sensors: dict[int, dict[str, Any]],
    trusted_aircraft: set[int],
) -> tuple[dict[tuple[int, int], list[float]], dict[str, Any]]:
    pair_samples: dict[tuple[int, int], list[float]] = defaultdict(list)
    transmission_count = 0
    observation_count = 0
    coarse_good_count = 0

    with (dataset_dir / "set_1.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            server_time = Decimal(row["timeAtServer"])
            if server_time >= CALIBRATION_END_S:
                break
            if server_time < CALIBRATION_START_S or int(row["aircraft"]) not in trusted_aircraft:
                continue

            observations = [
                observation
                for observation in parse_measurements(row["measurements"])
                if sensors[observation["receiver_id"]]["good"]
            ]
            coarse_good_count += sum(obs["timestamp_coarse"] for obs in observations)
            if len(observations) < 2:
                continue

            transmission_count += 1
            observation_count += len(observations)
            observations = [obs for obs in observations if not obs["timestamp_coarse"]]
            if len(observations) < 2:
                continue
            point = ground_truth_ecef(row)
            observations.sort(key=lambda obs: obs["receiver_id"])
            for first_index, first in enumerate(observations[:-1]):
                for second in observations[first_index + 1 :]:
                    pair = (first["receiver_id"], second["receiver_id"])
                    pair_samples[pair].append(pair_bias_ns(first, second, point, sensors))

    return pair_samples, {
        "transmissions": transmission_count,
        "observations": observation_count,
        "coarse_good_observations_excluded": coarse_good_count,
    }


def fit_clock_offsets(
    pair_samples: dict[tuple[int, int], list[float]],
) -> tuple[dict[int, float], dict[str, Any]]:
    retained_pairs = {
        pair: values for pair, values in pair_samples.items() if len(values) >= MIN_PAIR_SAMPLES
    }
    receiver_ids = sorted({receiver_id for pair in retained_pairs for receiver_id in pair})
    receiver_index = {receiver_id: index for index, receiver_id in enumerate(receiver_ids)}

    matrix = np.zeros((len(retained_pairs), len(receiver_ids)), dtype=float)
    targets = np.zeros(len(retained_pairs), dtype=float)
    pair_rows = []
    for row_index, (pair, values) in enumerate(sorted(retained_pairs.items())):
        first, second = pair
        target = float(statistics.median(values))
        matrix[row_index, receiver_index[first]] = 1.0
        matrix[row_index, receiver_index[second]] = -1.0
        targets[row_index] = target
        pair_rows.append((pair, len(values), target))

    sample_weights = (
        np.asarray([sample_count for _pair, sample_count, _target in pair_rows], dtype=float)
        ** PAIR_WEIGHT_EXPONENT
    )
    offsets, _residuals, rank, singular_values = np.linalg.lstsq(
        matrix * sample_weights[:, np.newaxis],
        targets * sample_weights,
        rcond=None,
    )
    fitted = matrix @ offsets
    absolute_residuals = np.abs(fitted - targets)
    offset_map = {
        receiver_id: float(offsets[index]) for receiver_id, index in receiver_index.items()
    }
    return offset_map, {
        "receiver_count": len(receiver_ids),
        "pair_count": len(retained_pairs),
        "rank": int(rank),
        "component_count": len(receiver_ids) - int(rank),
        "pair_absolute_residual_ns": {
            "median": statistics.median(absolute_residuals),
            "p95": percentile(absolute_residuals, 95),
            "maximum": max(absolute_residuals),
        },
        "singular_values": singular_values.tolist(),
        "pairs": [
            {
                "first_receiver_id": pair[0],
                "second_receiver_id": pair[1],
                "sample_count": sample_count,
                "median_bias_difference_ns": target,
            }
            for pair, sample_count, target in pair_rows
        ],
    }


def haversine_distance_m(
    latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float
) -> float:
    earth_radius_m = 6_371_000.0
    latitude_1_rad = math.radians(latitude_1)
    latitude_2_rad = math.radians(latitude_2)
    delta_latitude = latitude_2_rad - latitude_1_rad
    delta_longitude = math.radians(longitude_2 - longitude_1)
    value = (
        math.sin(delta_latitude / 2.0) ** 2
        + math.cos(latitude_1_rad) * math.cos(latitude_2_rad) * math.sin(delta_longitude / 2.0) ** 2
    )
    return earth_radius_m * 2.0 * math.atan2(math.sqrt(value), math.sqrt(1.0 - value))


def geometry_metrics(
    receiver_ids: list[int], point: np.ndarray, sensors: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    receiver_positions = [sensors[receiver_id]["ecef"] for receiver_id in receiver_ids]
    reference = receiver_positions[0]
    reference_unit = (point - reference) / np.linalg.norm(point - reference)
    rows = []
    for receiver_position in receiver_positions[1:]:
        unit = (point - receiver_position) / np.linalg.norm(point - receiver_position)
        rows.append(unit - reference_unit)
    matrix = np.asarray(rows)
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    condition_number = (
        float(singular_values[0] / singular_values[-1]) if singular_values[-1] > 0 else math.inf
    )

    horizontal_baselines = []
    for first_index, first_id in enumerate(receiver_ids[:-1]):
        first = sensors[first_id]
        for second_id in receiver_ids[first_index + 1 :]:
            second = sensors[second_id]
            horizontal_baselines.append(
                haversine_distance_m(
                    first["latitude"],
                    first["longitude"],
                    second["latitude"],
                    second["longitude"],
                )
            )

    return {
        "condition_number_at_truth": condition_number,
        "singular_values_at_truth": singular_values.tolist(),
        "maximum_receiver_baseline_m": max(horizontal_baselines),
        "median_receiver_baseline_m": statistics.median(horizontal_baselines),
    }


def known_position_tdoa_error_m(
    observations: list[dict[str, Any]],
    point: np.ndarray,
    sensors: dict[int, dict[str, Any]],
    offsets: dict[int, float] | None,
) -> float:
    corrected = []
    for observation in observations:
        offset = Decimal(str(offsets[observation["receiver_id"]])) if offsets else Decimal(0)
        corrected.append((observation, observation["timestamp_decimal"] - offset))
    corrected.sort(key=lambda item: item[1])
    reference_observation, reference_time = corrected[0]
    reference_distance = distance_m(point, sensors[reference_observation["receiver_id"]])
    residuals = []
    for observation, timestamp_value in corrected[1:]:
        observed_range_difference = float(timestamp_value - reference_time) / 1e9 * SPEED_OF_LIGHT
        expected_range_difference = (
            distance_m(point, sensors[observation["receiver_id"]]) - reference_distance
        )
        residuals.append(observed_range_difference - expected_range_difference)
    return float(math.sqrt(sum(value * value for value in residuals) / len(residuals)))


def trace_solver(solver: RobustMLATSolver, observations: list[SignalObservation]) -> dict[str, Any]:
    if len(observations) < solver.min_receivers:
        return {"stage": "insufficient_receiver_count"}
    if not solver._validate_observations(observations):
        return {"stage": "observation_validation"}
    timing = solver._relative_arrival_times(observations)
    if timing is None:
        return {"stage": "timestamp_validation"}
    ordered, time_differences, time_span = timing
    reference_position = ordered[0].receiver_position.to_ecef()
    positions = np.array([obs.receiver_position.to_ecef() for obs in ordered[1:]])
    initial = solver._get_smart_initial_guess(reference_position, positions, time_differences)
    if initial is None:
        return {"stage": "initial_guess"}
    optimized = solver._levenberg_marquardt(
        reference_position, positions, time_differences, initial
    )
    if optimized is None:
        return {"stage": "optimizer"}
    ecef, residual, iterations = optimized
    latitude, longitude, altitude = solver._ecef_to_lla(ecef)
    if latitude < -90 or latitude > 90:
        reason = "latitude_bound"
    elif longitude < -180 or longitude > 180:
        reason = "longitude_bound"
    elif altitude < -500 or altitude > 15000:
        reason = "altitude_bound"
    elif residual > 5000:
        reason = "residual_bound"
    else:
        reason = "success"
    return {
        "stage": reason,
        "latitude": latitude,
        "longitude": longitude,
        "altitude_m": altitude,
        "residual_m": float(residual),
        "iterations": int(iterations),
        "correlation_time_span_s": float(time_span),
    }


def classify_case(case: dict[str, Any]) -> tuple[str, str]:
    if case["solver_stage"] != "success":
        if case["solver_stage"] == "altitude_bound":
            if case["geometry_condition_number"] >= 1000:
                return "poor_geometry", "medium"
            if case["known_position_tdoa_error_m"] >= 60:
                return "timing_or_clock", "medium"
            return "altitude_or_vertical_ambiguity", "low"
        return case["solver_stage"], "high"

    if case["error_3d_m"] >= 3000:
        if case["geometry_condition_number"] >= 1000:
            return "poor_geometry", "medium"
        if case["known_position_tdoa_error_m"] >= 60:
            return "timing_or_clock", "medium"
        if case["vertical_error_m"] >= case["horizontal_error_m"] * 2:
            return "altitude_or_vertical_ambiguity", "medium"
        return "other_large_error", "low"
    return "accepted_baseline", "high"


def collect_validation(
    dataset_dir: Path,
    sensors: dict[int, dict[str, Any]],
    trusted_aircraft: set[int],
    offsets: dict[int, float],
) -> list[dict[str, Any]]:
    solver = RobustMLATSolver(min_receivers=4)
    cases = []
    with (dataset_dir / "set_1.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            server_time = Decimal(row["timeAtServer"])
            if server_time < VALIDATION_START_S:
                continue
            if int(row["aircraft"]) not in trusted_aircraft:
                continue

            all_good_observations = [
                observation
                for observation in parse_measurements(row["measurements"])
                if sensors[observation["receiver_id"]]["good"]
            ]
            eligible_observations = [
                observation
                for observation in all_good_observations
                if not observation["timestamp_coarse"] and observation["receiver_id"] in offsets
            ]
            if len(eligible_observations) < 4:
                continue

            point = ground_truth_ecef(row)
            geometry = geometry_metrics(
                [obs["receiver_id"] for obs in eligible_observations], point, sensors
            )
            corrected_timestamps = {
                obs["receiver_id"]: obs["timestamp_decimal"]
                - Decimal(str(offsets[obs["receiver_id"]]))
                for obs in eligible_observations
            }
            rounded_timestamp_ns = {
                receiver_id: round_decimal_ns(value)
                for receiver_id, value in corrected_timestamps.items()
            }
            observations = [
                SignalObservation(
                    receiver_id=str(obs["receiver_id"]),
                    timestamp=float(rounded_timestamp_ns[obs["receiver_id"]]) / 1e9,
                    signal_data="",
                    receiver_position=ReceiverPosition(
                        sensors[obs["receiver_id"]]["latitude"],
                        sensors[obs["receiver_id"]]["longitude"],
                        sensors[obs["receiver_id"]]["altitude"],
                        str(obs["receiver_id"]),
                    ),
                    timestamp_ns=rounded_timestamp_ns[obs["receiver_id"]],
                )
                for obs in eligible_observations
            ]
            started = time.perf_counter()
            position = solver.solve_position(observations)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            trace = trace_solver(solver, observations)
            truth_latitude = float(row["latitude"])
            truth_longitude = float(row["longitude"])
            truth_altitude = float(row["geoAltitude"])
            result = {
                "dataset_id": int(row["id"]),
                "server_time_s": float(server_time),
                "aircraft_id": int(row["aircraft"]),
                "receiver_count": len(observations),
                "receiver_ids": [int(obs.receiver_id) for obs in observations],
                "raw_timestamp_tokens": [obs["timestamp_text"] for obs in eligible_observations],
                "raw_fractional_timestamp_count": sum(
                    "." in obs["timestamp_text"] for obs in eligible_observations
                ),
                "raw_coarse_timestamp_count": sum(
                    obs["timestamp_coarse"] for obs in all_good_observations
                ),
                "clock_offsets_ns": {
                    str(obs["receiver_id"]): offsets[obs["receiver_id"]]
                    for obs in eligible_observations
                },
                "corrected_timestamp_ns": rounded_timestamp_ns,
                "rounding_error_ns_max": max(
                    abs(float(Decimal(rounded_timestamp_ns[receiver_id]) - value))
                    for receiver_id, value in corrected_timestamps.items()
                ),
                "known_position_tdoa_error_uncalibrated_m": known_position_tdoa_error_m(
                    eligible_observations, point, sensors, None
                ),
                "known_position_tdoa_error_m": known_position_tdoa_error_m(
                    eligible_observations, point, sensors, offsets
                ),
                "geometry_condition_number": geometry["condition_number_at_truth"],
                "geometry_singular_values": geometry["singular_values_at_truth"],
                "maximum_receiver_baseline_m": geometry["maximum_receiver_baseline_m"],
                "median_receiver_baseline_m": geometry["median_receiver_baseline_m"],
                "solver_stage": trace["stage"],
                "solver_candidate_latitude": trace.get("latitude"),
                "solver_candidate_longitude": trace.get("longitude"),
                "solver_candidate_altitude_m": trace.get("altitude_m"),
                "solver_residual_m": trace.get("residual_m"),
                "solver_iterations": trace.get("iterations"),
                "solver_runtime_ms": runtime_ms,
                "truth_latitude": truth_latitude,
                "truth_longitude": truth_longitude,
                "truth_altitude_m": truth_altitude,
            }
            if position is not None:
                horizontal_error = haversine_distance_m(
                    truth_latitude,
                    truth_longitude,
                    position.latitude,
                    position.longitude,
                )
                vertical_error = abs(position.altitude - truth_altitude)
                result.update(
                    {
                        "result_latitude": position.latitude,
                        "result_longitude": position.longitude,
                        "result_altitude_m": position.altitude,
                        "horizontal_error_m": horizontal_error,
                        "vertical_error_m": vertical_error,
                        "error_3d_m": math.hypot(horizontal_error, vertical_error),
                    }
                )
            else:
                result.update(
                    {
                        "result_latitude": None,
                        "result_longitude": None,
                        "result_altitude_m": None,
                        "horizontal_error_m": None,
                        "vertical_error_m": None,
                        "error_3d_m": None,
                    }
                )
            category, confidence = classify_case(result)
            result["likely_category"] = category
            result["category_confidence"] = confidence
            cases.append(result)
            if len(cases) == VALIDATION_CASES:
                break
    return cases


def summarize(
    dataset_path: Path,
    calibration_counts: dict[str, Any],
    calibration_fit: dict[str, Any],
    offsets: dict[int, float],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    successes = [case for case in cases if case["solver_stage"] == "success"]
    failures = [case for case in cases if case["solver_stage"] != "success"]

    def metric_summary(field: str, selected: list[dict[str, Any]]) -> dict[str, float | None]:
        values = [case[field] for case in selected if case[field] is not None]
        return {
            "minimum": min(values) if values else None,
            "median": statistics.median(values) if values else None,
            "p95": percentile(values, 95),
            "maximum": max(values) if values else None,
        }

    archive_hash = (
        hashlib.md5(dataset_path.read_bytes()).hexdigest() if dataset_path.is_file() else None
    )
    return {
        "experiment": {
            "scope": "solver-only diagnostic; not production-pipeline validation",
            "source": "LocaRDS v1.0 subset_1, DOI 10.5281/zenodo.4739276",
            "source_license": "CC BY-SA 4.0",
            "archive_path": str(dataset_path),
            "archive_md5": archive_hash,
            "calibration_interval_s": [0, 120],
            "gap_interval_s": [120, 180],
            "validation_start_s": 180,
            "validation_selection": "first 300 eligible rows in dataset order",
            "minimum_pair_samples": MIN_PAIR_SAMPLES,
            "pair_weighting": "square root of calibration sample count",
        },
        "calibration": {
            **calibration_counts,
            **{key: value for key, value in calibration_fit.items() if key != "pairs"},
            "clock_offsets_ns": {str(key): value for key, value in sorted(offsets.items())},
        },
        "validation": {
            "case_count": len(cases),
            "dataset_ids": [case["dataset_id"] for case in cases],
            "dataset_id_sha256": hashlib.sha256(
                ",".join(str(case["dataset_id"]) for case in cases).encode("ascii")
            ).hexdigest(),
            "observation_count": sum(case["receiver_count"] for case in cases),
            "receiver_count_distribution": dict(
                sorted(Counter(case["receiver_count"] for case in cases).items())
            ),
            "unique_receivers": sorted(
                {receiver_id for case in cases for receiver_id in case["receiver_ids"]}
            ),
            "success_count": len(successes),
            "failure_count": len(failures),
            "solver_stage_counts": dict(Counter(case["solver_stage"] for case in cases)),
            "likely_category_counts": dict(Counter(case["likely_category"] for case in cases)),
            "horizontal_error_m": metric_summary("horizontal_error_m", successes),
            "vertical_error_m": metric_summary("vertical_error_m", successes),
            "error_3d_m": metric_summary("error_3d_m", successes),
            "solver_residual_m": metric_summary("solver_residual_m", cases),
            "solver_iterations": metric_summary("solver_iterations", cases),
            "solver_runtime_ms": metric_summary("solver_runtime_ms", cases),
            "known_position_tdoa_error_uncalibrated_m": metric_summary(
                "known_position_tdoa_error_uncalibrated_m", cases
            ),
            "known_position_tdoa_error_m": metric_summary("known_position_tdoa_error_m", cases),
            "geometry_condition_number": metric_summary("geometry_condition_number", cases),
            "rounding_error_ns_max": metric_summary("rounding_error_ns_max", cases),
            "worst_successes": sorted(successes, key=lambda case: case["error_3d_m"], reverse=True)[
                :10
            ],
            "failures": failures,
            "cases": cases,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("/private/tmp/locards-subset-1/subset_1"),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("/private/tmp/locards-subset_1.zip"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    sensors, trusted_aircraft = load_metadata(args.dataset_dir)
    pair_samples, calibration_counts = collect_calibration(
        args.dataset_dir, sensors, trusted_aircraft
    )
    offsets, calibration_fit = fit_clock_offsets(pair_samples)
    cases = collect_validation(args.dataset_dir, sensors, trusted_aircraft, offsets)
    report = summarize(args.archive, calibration_counts, calibration_fit, offsets, cases)
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
