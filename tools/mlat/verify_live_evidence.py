#!/usr/bin/env python3
"""Verify and independently re-solve a captured physical MLAT evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
TOOLS = ROOT / "tools" / "mlat"
for search_path in (SRC, TOOLS):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

from capture_grant_evidence import (
    load_jsonl,
    raw_clock_config_failures,
    raw_observation_failures,
    raw_position_link_failures,
)
from mlat_reference.solver.robust import RobustMLATSolver, ReceiverPosition, SignalObservation

REQUIRED_ARTIFACTS = {
    "BENCHMARKS.md",
    "accuracy.json",
    "mlat.jsonl",
    "mode.json",
    "performance.json",
    "pipeline.json",
    "preflight.json",
    "raw-observations.jsonl",
    "readiness.json",
    "receiver-config.json",
    "receivers.json",
    "reference.jsonl",
    "reliability.json",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    value = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_m * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _matching_raw_group(
    position: dict[str, Any], raw_records: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    aircraft_id = str(position.get("aircraft_id") or "").upper()
    expected_receivers = {str(value) for value in position.get("receiver_ids", [])}
    position_time_ns = round(float(position.get("timestamp", 0)) * 1_000_000_000)
    by_message: dict[str, list[dict[str, Any]]] = {}
    for record in raw_records:
        message = str(record.get("message") or "").upper()
        if len(message) >= 8 and message[2:8] == aircraft_id:
            by_message.setdefault(message, []).append(record)

    for records in by_message.values():
        window = [
            record
            for record in records
            if position_time_ns - 2_000
            <= int(record.get("timestamp_ns") or 0)
            <= position_time_ns + 5_000_000
        ]
        available = {str(record.get("receiver_id")) for record in window}
        if expected_receivers and expected_receivers.issubset(available):
            return [
                min(
                    (record for record in window if str(record.get("receiver_id")) == receiver_id),
                    key=lambda record: int(record["timestamp_ns"]),
                )
                for receiver_id in expected_receivers
            ]
    return None


def resolve_positions(
    positions: list[dict[str, Any]],
    raw_records: list[dict[str, Any]],
    receiver_rows: list[dict[str, Any]],
    *,
    tolerance_m: float = 1.0,
) -> dict[str, Any]:
    receiver_geometry = {
        str(receiver.get("identity_id") or receiver.get("receiver_id")): ReceiverPosition(
            latitude=float(receiver["latitude"]),
            longitude=float(receiver["longitude"]),
            altitude=float(receiver["altitude"]),
            receiver_id=str(receiver.get("identity_id") or receiver.get("receiver_id")),
        )
        for receiver in receiver_rows
    }
    solver = RobustMLATSolver(min_receivers=4)
    failures: list[str] = []
    horizontal_errors: list[float] = []
    altitude_errors: list[float] = []

    for index, position in enumerate(positions):
        raw_group = _matching_raw_group(position, raw_records)
        if raw_group is None:
            failures.append(f"position {index} has no matching four-receiver raw group")
            continue
        observations = []
        for record in raw_group:
            receiver_id = str(record["receiver_id"])
            geometry = receiver_geometry.get(receiver_id)
            if geometry is None:
                failures.append(f"position {index} receiver {receiver_id} has no geometry")
                observations = []
                break
            timestamp_ns = int(record["timestamp_ns"])
            observations.append(
                SignalObservation(
                    receiver_id=receiver_id,
                    timestamp=timestamp_ns / 1_000_000_000,
                    timestamp_ns=timestamp_ns,
                    signal_data=str(record["message"]),
                    receiver_position=geometry,
                )
            )
        if len(observations) < 4:
            continue
        solved = solver.solve_position(observations)
        if solved is None:
            failures.append(f"position {index} could not be independently re-solved")
            continue
        horizontal_error = haversine_m(
            solved.latitude,
            solved.longitude,
            float(position["latitude"]),
            float(position["longitude"]),
        )
        altitude_error = abs(solved.altitude - float(position["altitude"]))
        horizontal_errors.append(horizontal_error)
        altitude_errors.append(altitude_error)
        if horizontal_error > tolerance_m or altitude_error > tolerance_m:
            failures.append(
                f"position {index} differs from the independent re-solve by "
                f"{horizontal_error:.3f} m horizontal / {altitude_error:.3f} m altitude"
            )

    return {
        "positions": len(positions),
        "resolved": len(horizontal_errors),
        "tolerance_m": tolerance_m,
        "max_horizontal_difference_m": max(horizontal_errors) if horizontal_errors else None,
        "max_altitude_difference_m": max(altitude_errors) if altitude_errors else None,
        "failures": failures,
    }


def verify_bundle(bundle: Path, *, require_publishable: bool = False) -> dict[str, Any]:
    bundle = bundle.resolve()
    failures: list[str] = []
    manifest_path = bundle / "manifest.json"
    try:
        manifest = load_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "failures": [f"Unable to load manifest: {exc}"]}
    if manifest.get("schema_version") != 2:
        failures.append("manifest schema_version must be 2")
    if require_publishable and manifest.get("evidence_status") != "publishable":
        failures.append("bundle is not marked publishable")
    if manifest.get("evidence_status") == "publishable":
        if manifest.get("live_gate_failures"):
            failures.append("publishable bundle contains live gate failures")
        software = manifest.get("software", {})
        if not software.get("git_commit") or software.get("git_worktree_dirty") is not False:
            failures.append("publishable bundle was not captured from a clean commit")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return {"valid": False, "failures": failures + ["manifest artifacts must be an object"]}
    missing_required = sorted(REQUIRED_ARTIFACTS - set(artifacts))
    if missing_required:
        failures.append(f"manifest is missing required artifacts: {missing_required}")
    for relative, metadata in artifacts.items():
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            failures.append(f"unsafe artifact path: {relative}")
            continue
        path = bundle / relative_path
        if not path.is_file():
            failures.append(f"artifact is missing: {relative}")
            continue
        if path.stat().st_size != metadata.get("bytes"):
            failures.append(f"artifact size mismatch: {relative}")
        if file_sha256(path) != metadata.get("sha256"):
            failures.append(f"artifact sha256 mismatch: {relative}")

    try:
        receiver_config = load_json(bundle / "receiver-config.json")
        preflight = load_json(bundle / "preflight.json")
        receiver_snapshot = load_json(bundle / "receivers.json")
        raw_records = load_jsonl(bundle / "raw-observations.jsonl")
        positions = load_jsonl(bundle / "mlat.jsonl")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "failures": failures + [f"Unable to load evidence: {exc}"]}

    configured_ids = {
        str(receiver.get("receiver_id")) for receiver in receiver_config.get("receivers", [])
    }
    failures.extend(raw_observation_failures(raw_records, configured_ids))
    configured_receivers = receiver_config.get("receivers", [])
    if not isinstance(configured_receivers, list):
        configured_receivers = []
    failures.extend(raw_clock_config_failures(raw_records, configured_receivers))
    failures.extend(raw_position_link_failures(raw_records, positions))
    if preflight.get("ready_for_evidence_run") is not True:
        failures.append("captured preflight did not pass")

    declared_clock_evidence = manifest.get("clock_evidence", {})
    for receiver in receiver_config.get("receivers", []):
        receiver_id = str(receiver.get("receiver_id"))
        clock_evidence = receiver.get("clock", {}).get("evidence", {})
        captured = declared_clock_evidence.get(receiver_id, {})
        artifact = captured.get("artifact")
        artifact_path = bundle / str(artifact or "missing")
        if (
            not artifact
            or not artifact_path.is_file()
            or captured.get("method") != clock_evidence.get("method")
            or captured.get("sha256") != clock_evidence.get("sha256")
            or file_sha256(artifact_path) != clock_evidence.get("sha256")
        ):
            failures.append(f"clock evidence mismatch for {receiver_id}")

    receiver_rows = receiver_snapshot.get("receivers", [])
    if not isinstance(receiver_rows, list):
        receiver_rows = []
    reproduction = resolve_positions(positions, raw_records, receiver_rows)
    failures.extend(reproduction["failures"])
    return {
        "schema_version": 1,
        "valid": not failures,
        "evidence_status": manifest.get("evidence_status"),
        "artifact_count": len(artifacts),
        "raw_observation_count": len(raw_records),
        "reproduction": reproduction,
        "failures": failures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--require-publishable", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = verify_bundle(Path(args.bundle), require_publishable=args.require_publishable)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
