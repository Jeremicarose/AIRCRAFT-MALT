#!/usr/bin/env python3
"""Capture a hashed, provenance-aware evidence bundle from a running live system."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "mlat"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from receiver_config import load_receiver_config


def fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            rows.append(row)
    return rows


def raw_observation_failures(
    records: list[dict[str, Any]], configured_receiver_ids: set[str]
) -> list[str]:
    failures: list[str] = []
    if not records:
        return ["The raw-observation audit log is empty."]

    receiver_ids = {str(record.get("receiver_id") or "") for record in records}
    receiver_ids.discard("")
    if len(receiver_ids) < 4:
        failures.append(f"Raw observations contain only {len(receiver_ids)} unique receivers.")
    unexpected = sorted(receiver_ids - configured_receiver_ids)
    if unexpected:
        failures.append(f"Raw observations contain unconfigured receivers: {unexpected}")

    invalid_records = 0
    for record in records:
        timestamp_ns = record.get("timestamp_ns")
        message = str(record.get("message") or "")
        try:
            bytes.fromhex(message)
            valid_message = len(message) in {14, 28}
        except ValueError:
            valid_message = False
        if (
            record.get("clock_synchronized") is not True
            or isinstance(timestamp_ns, bool)
            or not isinstance(timestamp_ns, int)
            or timestamp_ns <= 0
            or not valid_message
        ):
            invalid_records += 1
    if invalid_records:
        failures.append(
            f"Raw observations contain {invalid_records} records without qualified integer "
            "timing or valid Mode-S hex."
        )

    candidates: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        candidates.setdefault(str(record.get("message") or ""), []).append(record)
    has_four_receiver_group = False
    for message_records in candidates.values():
        timed = sorted(
            (
                record
                for record in message_records
                if isinstance(record.get("timestamp_ns"), int)
                and not isinstance(record.get("timestamp_ns"), bool)
            ),
            key=lambda record: record["timestamp_ns"],
        )
        for start, first in enumerate(timed):
            window = [
                record
                for record in timed[start:]
                if record["timestamp_ns"] - first["timestamp_ns"] <= 5_000_000
            ]
            if len({record.get("receiver_id") for record in window}) >= 4:
                has_four_receiver_group = True
                break
        if has_four_receiver_group:
            break
    if not has_four_receiver_group:
        failures.append("Raw observations contain no four-receiver message group within 5 ms.")
    return failures


def raw_clock_config_failures(
    records: list[dict[str, Any]], configured_receivers: list[dict[str, Any]]
) -> list[str]:
    clocks = {receiver["receiver_id"]: receiver["clock"] for receiver in configured_receivers}
    mismatches = 0
    for record in records:
        clock = clocks.get(str(record.get("receiver_id")))
        timestamp_ns = record.get("timestamp_ns")
        if clock is None:
            continue
        evidence = clock.get("evidence", {})
        if (
            record.get("clock_source") != clock.get("source")
            or record.get("clock_uncertainty_ns") != clock.get("uncertainty_ns")
            or record.get("clock_valid_from_ns") != clock.get("valid_from_ns")
            or record.get("clock_valid_until_ns") != clock.get("valid_until_ns")
            or record.get("clock_evidence_sha256") != evidence.get("sha256")
            or not isinstance(timestamp_ns, int)
            or not clock.get("valid_from_ns") <= timestamp_ns <= clock.get("valid_until_ns")
        ):
            mismatches += 1
    return (
        [f"{mismatches} raw observations do not match their pinned clock configuration."]
        if mismatches
        else []
    )


def raw_position_link_failures(
    records: list[dict[str, Any]], positions: list[dict[str, Any]]
) -> list[str]:
    if not positions:
        return ["The MLAT position export is empty."]

    raw_by_aircraft: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for record in records:
        message = str(record.get("message") or "")
        if len(message) >= 8:
            raw_by_aircraft.setdefault(message[2:8].upper(), {}).setdefault(message, []).append(
                record
            )

    unlinked = 0
    for position in positions:
        aircraft_id = str(position.get("aircraft_id") or "").upper()
        position_time_ns = round(float(position.get("timestamp", 0)) * 1_000_000_000)
        position_receivers = {str(value) for value in position.get("receiver_ids", [])}
        message_groups = raw_by_aircraft.get(aircraft_id, {})
        linked = False
        for message_records in message_groups.values():
            matching_receivers = {
                str(record.get("receiver_id"))
                for record in message_records
                if position_time_ns - 2_000
                <= int(record.get("timestamp_ns") or 0)
                <= position_time_ns + 5_000_000
            }
            if position_receivers and position_receivers.issubset(matching_receivers):
                linked = True
                break
        if (
            not linked
            or len(position_receivers) < 4
            or position.get("solver_method") != "robust_mlat"
        ):
            unlinked += 1
    return (
        [
            f"{unlinked} of {len(positions)} exported positions cannot be linked to "
            "qualified raw observations."
        ]
        if unlinked
        else []
    )


def live_gate_failures(mode: dict[str, Any], pipeline: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if mode.get("mode") != "live" or mode.get("runtime_status") != "active":
        failures.append("Runtime is not actively processing live observations.")
    if mode.get("strict_production_mode") is not True:
        failures.append("Strict production mode is not enabled.")
    if mode.get("simulate_if_unavailable") is not False:
        failures.append("Simulation fallback is not disabled.")
    if mode.get("synthetic_feed_mode") is not False:
        failures.append("Synthetic feed mode is not explicitly false.")
    if mode.get("configured_transport") == "simulation":
        failures.append("Configured transport is simulation.")
    if pipeline.get("provenance", {}).get("live_data") is not True:
        failures.append("Pipeline provenance is not live.")
    if pipeline.get("provenance", {}).get("benchmarkable_output") is not True:
        failures.append("Recent output is not benchmarkable live MLAT output.")
    if pipeline.get("provenance", {}).get("registry_discovery_live") is not True:
        failures.append("Receiver discovery is not verified as live CKB discovery.")

    required_stages = {
        "registry",
        "discovery",
        "ingest",
        "correlation",
        "solve",
        "storage",
        "api",
        "dashboard",
    }
    statuses = {stage.get("id"): stage.get("status") for stage in pipeline.get("stages", [])}
    for stage_id in sorted(required_stages):
        if statuses.get(stage_id) != "pass":
            failures.append(
                f"Pipeline stage {stage_id!r} is {statuses.get(stage_id, 'missing')!r}, not 'pass'."
            )
    return failures


def run_command(
    args: list[str], allowed_codes: set[int] | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode not in (allowed_codes or {0}):
        detail = completed.stderr.strip() or completed.stdout.strip() or "no command output"
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(args)}\n{detail}")
    return completed


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return {"git_commit": commit or None, "git_worktree_dirty": bool(status)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:5057")
    parser.add_argument("--db", default="data/mlat_live.db")
    parser.add_argument("--reference", required=True, help="Aligned trusted-reference JSONL file")
    parser.add_argument(
        "--receiver-config",
        required=True,
        help="The exact strict receiver/clock config used for this run.",
    )
    parser.add_argument(
        "--preflight-report",
        required=True,
        help="Saved JSON output from check_live_ingest_readiness.py at launch.",
    )
    parser.add_argument(
        "--raw-observations",
        required=True,
        help="Run-scoped JSONL audit log emitted by the multi-receiver bridge.",
    )
    parser.add_argument("--reference-source", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--reliability-seconds", type=float, default=300.0)
    parser.add_argument("--reliability-interval", type=float, default=5.0)
    parser.add_argument("--output-dir", help="Bundle directory; defaults to a timestamped path")
    parser.add_argument(
        "--allow-non-live",
        action="store_true",
        help="Capture a validation bundle despite failed live gates; never labels it live.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_path = Path(args.reference).resolve()
    receiver_config_path = Path(args.receiver_config).resolve()
    preflight_path = Path(args.preflight_report).resolve()
    raw_observations_path = Path(args.raw_observations).resolve()
    required_inputs = {
        "Reference file": reference_path,
        "Receiver config": receiver_config_path,
        "Preflight report": preflight_path,
        "Raw-observation log": raw_observations_path,
    }
    missing = [
        f"{label} does not exist: {path}"
        for label, path in required_inputs.items()
        if not path.is_file()
    ]
    if missing:
        raise SystemExit("\n".join(missing))

    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to load preflight report: {exc}") from exc
    preflight_failures = []
    if preflight.get("ready_for_evidence_run") is not True:
        preflight_failures.append("Saved launch preflight did not pass its evidence gates.")
    if Path(preflight.get("receiver_config", {}).get("path", "")).resolve() != receiver_config_path:
        preflight_failures.append("Saved preflight references a different receiver config.")
    if (
        Path(preflight.get("raw_observation_log", {}).get("path", "")).resolve()
        != raw_observations_path
    ):
        preflight_failures.append("Saved preflight references a different raw-observation log.")

    try:
        configured_receivers = load_receiver_config(receiver_config_path, require_mlat_ready=True)
    except ValueError as exc:
        preflight_failures.append(f"Receiver config no longer passes strict validation: {exc}")
        configured_receivers = []
    if preflight_failures and not args.allow_non_live:
        raise SystemExit("Evidence input gates failed:\n- " + "\n- ".join(preflight_failures))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = (
        Path(args.output_dir)
        if args.output_dir
        else ROOT / "evidence" / "mlat-reference" / "live" / "captures" / stamp
    )
    bundle = bundle.resolve()
    bundle.mkdir(parents=True, exist_ok=False)

    api_base = args.api_base.rstrip("/")
    mode = fetch_json(f"{api_base}/api/system/mode")
    pipeline = fetch_json(f"{api_base}/api/pipeline")
    readiness = fetch_json(f"{api_base}/api/readiness")
    receivers_snapshot = fetch_json(f"{api_base}/api/receivers")
    failures = preflight_failures + live_gate_failures(mode, pipeline)
    if failures and not args.allow_non_live:
        shutil.rmtree(bundle)
        raise SystemExit("Live evidence gates failed:\n- " + "\n- ".join(failures))

    write_json(bundle / "mode.json", mode)
    write_json(bundle / "pipeline.json", pipeline)
    write_json(bundle / "readiness.json", readiness)
    write_json(bundle / "receivers.json", receivers_snapshot)
    shutil.copy2(preflight_path, bundle / "preflight.json")
    shutil.copy2(receiver_config_path, bundle / "receiver-config.json")
    shutil.copy2(reference_path, bundle / "reference.jsonl")

    clock_evidence_dir = bundle / "clock-evidence"
    clock_evidence_dir.mkdir()
    clock_evidence_artifacts = {}
    for receiver in configured_receivers:
        evidence = receiver["clock"]["evidence"]
        source = Path(evidence["file"]).expanduser()
        if not source.is_absolute():
            source = receiver_config_path.parent / source
        suffix = source.suffix or ".artifact"
        destination = clock_evidence_dir / f'{receiver["receiver_id"][2:]}{suffix}'
        shutil.copy2(source, destination)
        clock_evidence_artifacts[receiver["receiver_id"]] = {
            "artifact": destination.relative_to(bundle).as_posix(),
            "method": evidence["method"],
            "sha256": evidence["sha256"],
        }

    reliability_path = bundle / "reliability.json"
    run_command(
        [
            sys.executable,
            "tools/mlat/capture_reliability_window.py",
            "--api-base",
            api_base,
            "--duration-seconds",
            str(args.reliability_seconds),
            "--interval-seconds",
            str(args.reliability_interval),
            "--output",
            str(reliability_path),
        ],
        allowed_codes={0, 2},
    )

    mlat_path = bundle / "mlat.jsonl"
    run_command(
        [
            sys.executable,
            "tools/mlat/export_positions_for_benchmark.py",
            "--db",
            str(Path(args.db).resolve()),
            "--output",
            str(mlat_path),
            "--seconds",
            str(args.seconds),
        ]
    )

    shutil.copy2(raw_observations_path, bundle / "raw-observations.jsonl")
    raw_records = load_jsonl(bundle / "raw-observations.jsonl")
    positions = load_jsonl(mlat_path)
    failures.extend(
        raw_observation_failures(
            raw_records,
            {receiver["receiver_id"] for receiver in configured_receivers},
        )
    )
    failures.extend(raw_clock_config_failures(raw_records, configured_receivers))
    failures.extend(raw_position_link_failures(raw_records, positions))
    if failures and not args.allow_non_live:
        shutil.rmtree(bundle)
        raise SystemExit("Live evidence gates failed:\n- " + "\n- ".join(failures))
    live_capture = not failures

    performance_path = bundle / "performance.json"
    markdown_path = bundle / "BENCHMARKS.md"
    benchmark_markdown_publish_path = ROOT / "evidence" / "mlat-reference" / "live" / "README.md"
    run_command(
        [
            sys.executable,
            "tools/mlat/benchmark_operational_performance.py",
            "--api-base",
            api_base,
            "--output",
            str(performance_path),
            "--markdown",
            str(markdown_path),
        ],
        allowed_codes={0, 2},
    )

    accuracy_path = bundle / "accuracy.json"
    run_command(
        [
            sys.executable,
            "tools/mlat/benchmark_mlat_against_reference.py",
            "--mlat",
            str(mlat_path),
            "--reference",
            str(bundle / "reference.jsonl"),
            "--runtime-snapshot",
            str(bundle / "readiness.json"),
            "--reference-source",
            args.reference_source,
            "--region",
            args.region,
            "--data-provenance",
            "live" if live_capture else "replay",
            "--output",
            str(accuracy_path),
        ]
    )

    accuracy = json.loads(accuracy_path.read_text(encoding="utf-8"))
    reliability = json.loads(reliability_path.read_text(encoding="utf-8"))
    performance = json.loads(performance_path.read_text(encoding="utf-8"))
    software = git_state()
    publishable = bool(
        live_capture
        and accuracy.get("evidence_status") == "publishable"
        and reliability.get("provenance", {}).get("live_data") is True
        and performance.get("provenance", {}).get("live_data") is True
        and software.get("git_commit")
        and software.get("git_worktree_dirty") is False
    )

    artifact_paths = sorted(path for path in bundle.rglob("*") if path.is_file())
    manifest = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "publishable" if publishable else "validation_only",
        "software": software,
        "live_gate_failures": failures,
        "reference_source": args.reference_source,
        "region": args.region,
        "clock_evidence": clock_evidence_artifacts,
        "artifacts": {
            path.relative_to(bundle).as_posix(): {
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in artifact_paths
        },
    }
    write_json(bundle / "manifest.json", manifest)

    if publishable:
        publish_dir = ROOT / "evidence" / "mlat-reference" / "live"
        publish_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(accuracy_path, publish_dir / "latest.json")
        shutil.copy2(performance_path, publish_dir / "performance-latest.json")
        shutil.copy2(reliability_path, publish_dir / "reliability-latest.json")
        shutil.copy2(markdown_path, benchmark_markdown_publish_path)

    print(json.dumps({"bundle": str(bundle), **manifest}, indent=2, sort_keys=True))
    return 0 if publishable else 2


if __name__ == "__main__":
    raise SystemExit(main())
