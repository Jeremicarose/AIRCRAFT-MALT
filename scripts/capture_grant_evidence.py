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


ROOT = Path(__file__).resolve().parents[1]


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

    required_stages = {"registry", "discovery", "ingest", "correlation", "solve", "storage", "api", "dashboard"}
    statuses = {stage.get("id"): stage.get("status") for stage in pipeline.get("stages", [])}
    for stage_id in sorted(required_stages):
        if statuses.get(stage_id) != "pass":
            failures.append(f"Pipeline stage {stage_id!r} is {statuses.get(stage_id, 'missing')!r}, not 'pass'.")
    return failures


def run_command(args: list[str], allowed_codes: set[int] | None = None) -> subprocess.CompletedProcess[str]:
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
    if not reference_path.exists():
        raise SystemExit(f"Reference file does not exist: {reference_path}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = Path(args.output_dir) if args.output_dir else ROOT / "benchmark" / "captures" / stamp
    bundle = bundle.resolve()
    bundle.mkdir(parents=True, exist_ok=False)

    api_base = args.api_base.rstrip("/")
    mode = fetch_json(f"{api_base}/api/system/mode")
    pipeline = fetch_json(f"{api_base}/api/pipeline")
    readiness = fetch_json(f"{api_base}/api/readiness")
    failures = live_gate_failures(mode, pipeline)
    if failures and not args.allow_non_live:
        shutil.rmtree(bundle)
        raise SystemExit("Live evidence gates failed:\n- " + "\n- ".join(failures))

    live_capture = not failures
    write_json(bundle / "mode.json", mode)
    write_json(bundle / "pipeline.json", pipeline)
    write_json(bundle / "readiness.json", readiness)
    shutil.copy2(reference_path, bundle / "reference.jsonl")

    reliability_path = bundle / "reliability.json"
    run_command(
        [
            sys.executable,
            "scripts/capture_reliability_window.py",
            "--api-base", api_base,
            "--duration-seconds", str(args.reliability_seconds),
            "--interval-seconds", str(args.reliability_interval),
            "--output", str(reliability_path),
        ],
        allowed_codes={0, 2},
    )

    mlat_path = bundle / "mlat.jsonl"
    run_command(
        [
            sys.executable,
            "scripts/export_positions_for_benchmark.py",
            "--db", str(Path(args.db).resolve()),
            "--output", str(mlat_path),
            "--seconds", str(args.seconds),
        ]
    )

    performance_path = bundle / "performance.json"
    markdown_path = bundle / "BENCHMARKS.md"
    run_command(
        [
            sys.executable,
            "scripts/benchmark_operational_performance.py",
            "--api-base", api_base,
            "--output", str(performance_path),
            "--markdown", str(markdown_path),
        ],
        allowed_codes={0, 2},
    )

    accuracy_path = bundle / "accuracy.json"
    run_command(
        [
            sys.executable,
            "scripts/benchmark_mlat_against_reference.py",
            "--mlat", str(mlat_path),
            "--reference", str(bundle / "reference.jsonl"),
            "--runtime-snapshot", str(bundle / "readiness.json"),
            "--reference-source", args.reference_source,
            "--region", args.region,
            "--data-provenance", "live" if live_capture else "replay",
            "--output", str(accuracy_path),
        ]
    )

    accuracy = json.loads(accuracy_path.read_text(encoding="utf-8"))
    reliability = json.loads(reliability_path.read_text(encoding="utf-8"))
    performance = json.loads(performance_path.read_text(encoding="utf-8"))
    publishable = bool(
        live_capture
        and accuracy.get("evidence_status") == "publishable"
        and reliability.get("provenance", {}).get("live_data") is True
        and performance.get("provenance", {}).get("live_data") is True
    )

    artifact_paths = sorted(path for path in bundle.iterdir() if path.is_file())
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "publishable" if publishable else "validation_only",
        "software": git_state(),
        "live_gate_failures": failures,
        "reference_source": args.reference_source,
        "region": args.region,
        "artifacts": {
            path.name: {"sha256": file_sha256(path), "bytes": path.stat().st_size}
            for path in artifact_paths
        },
    }
    write_json(bundle / "manifest.json", manifest)

    publish_dir = ROOT / "benchmark"
    publish_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(accuracy_path, publish_dir / "latest.json")
    shutil.copy2(performance_path, publish_dir / "performance-latest.json")
    shutil.copy2(reliability_path, publish_dir / "reliability-latest.json")
    shutil.copy2(markdown_path, ROOT / "BENCHMARKS.md")

    print(json.dumps({"bundle": str(bundle), **manifest}, indent=2, sort_keys=True))
    return 0 if publishable else 2


if __name__ == "__main__":
    raise SystemExit(main())
