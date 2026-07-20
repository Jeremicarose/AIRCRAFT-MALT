#!/usr/bin/env python3
"""
Check whether this machine is actually ready for real live aircraft ingest.

This does not make the feed live. It reports the blockers clearly.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def read_env_file() -> dict[str, str]:
    env_path = ROOT / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def command_exists(name: str) -> bool:
    from shutil import which
    return which(name) is not None


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, check=False)
        return completed.returncode, (completed.stdout + completed.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def probe_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless all strict live-evidence launch gates pass.",
    )
    return parser.parse_args()


def build_report(env: dict[str, str]) -> dict:
    transport = env.get("FOURDSKY_TRANSPORT", "")
    bridge_command = env.get("FOURDSKY_BRIDGE_COMMAND", "")
    benchmark_required = env.get("REQUIRE_LIVE_BENCHMARKABLE_OUTPUT", "false").lower() == "true"
    strict_mode = env.get("STRICT_PRODUCTION_MODE", "false").lower() == "true"
    simulate_fallback = env.get("SIMULATE_IF_UNAVAILABLE", "true").lower() == "true"
    registry_type_hash = env.get("RECEIVER_REGISTRY_TYPE_HASH", "").strip()
    external_source_attested = env.get("FOURDSKY_EXTERNAL_SOURCE_ATTESTED", "false").lower() == "true"

    rtl_test_available = command_exists("rtl_test")
    readsb_available = command_exists("readsb")

    rtl_present = False
    rtl_output = ""
    if rtl_test_available:
        code, rtl_output = run_command(["rtl_test", "-t"])
        rtl_present = code == 0 and "No supported devices found." not in rtl_output

    common_ports = [30005, 30006, 30002]
    reachable_ports = [port for port in common_ports if probe_tcp("127.0.0.1", port)]

    source_ready = rtl_present or bool(reachable_ports) or external_source_attested
    report = {
        "transport": transport,
        "bridge_command": bridge_command,
        "strict_production_mode": strict_mode,
        "simulate_if_unavailable": simulate_fallback,
        "require_live_benchmarkable_output": benchmark_required,
        "receiver_registry_type_hash_configured": bool(registry_type_hash),
        "checks": {
            "readsb_installed": readsb_available,
            "rtl_test_installed": rtl_test_available,
            "rtl_sdr_detected": rtl_present,
            "local_common_beast_ports": reachable_ports,
            "external_source_attested": external_source_attested,
        },
        "ready_for_real_live_ingest": bool(
            transport == "command-jsonl"
            and bridge_command
            and source_ready
        ),
        "ready_for_evidence_run": False,
        "blockers": [],
    }

    if transport != "command-jsonl":
        report["blockers"].append("FOURDSKY_TRANSPORT is not set to command-jsonl.")
    if not bridge_command:
        report["blockers"].append("FOURDSKY_BRIDGE_COMMAND is not set.")
    if not readsb_available:
        report["blockers"].append("readsb is not installed.")
    if not source_ready:
        report["blockers"].append(
            "No local RTL-SDR hardware, local Beast TCP endpoint, or explicitly attested external source is available."
        )
    if benchmark_required and transport == "simulation":
        report["blockers"].append(
            "Benchmarkable output is required, but transport is still simulation."
        )

    if not strict_mode:
        report["blockers"].append("STRICT_PRODUCTION_MODE is not enabled.")
    if simulate_fallback:
        report["blockers"].append("SIMULATE_IF_UNAVAILABLE must be false for a live evidence run.")
    if not benchmark_required:
        report["blockers"].append("REQUIRE_LIVE_BENCHMARKABLE_OUTPUT is not enabled.")
    if not registry_type_hash:
        report["blockers"].append("RECEIVER_REGISTRY_TYPE_HASH is not configured.")

    report["ready_for_evidence_run"] = bool(
        report["ready_for_real_live_ingest"]
        and strict_mode
        and not simulate_fallback
        and benchmark_required
        and registry_type_hash
    )
    return report


def main() -> int:
    args = parse_args()
    env = {**read_env_file(), **os.environ}
    report = build_report(env)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if args.require_ready and not report["ready_for_evidence_run"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
