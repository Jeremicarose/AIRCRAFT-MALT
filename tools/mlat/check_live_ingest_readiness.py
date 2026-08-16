#!/usr/bin/env python3
"""
Check whether this machine is actually ready for real live aircraft ingest.

This does not make the feed live. It reports the blockers clearly.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import shlex

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import normalize_identity_id
from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery

SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from receiver_config import load_receiver_config


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
    parser.add_argument(
        "--receiver-config",
        help="Override MLAT_RECEIVER_CONFIG with a concrete multi-receiver JSON file.",
    )
    parser.add_argument("--output", help="Write the JSON report to this path as well as stdout.")
    return parser.parse_args()


def _option_value(tokens: list[str], name: str) -> str:
    for index, token in enumerate(tokens):
        if token == name and index + 1 < len(tokens):
            return tokens[index + 1]
        if token.startswith(name + "="):
            return token.split("=", 1)[1]
    return ""


def validate_bridge_command(
    command: str,
    receiver_config_path: Path,
    raw_observation_log_path: Path | None,
) -> tuple[str, str]:
    """Return launch and evidence errors for the configured bridge command."""
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return f"FOURDSKY_BRIDGE_COMMAND is not valid shell syntax: {exc}", ""
    if not tokens:
        return "FOURDSKY_BRIDGE_COMMAND is empty.", ""

    script_indexes = [
        index
        for index, token in enumerate(tokens)
        if Path(token).name == "multi_receiver_beast_bridge.py"
    ]
    if len(script_indexes) != 1:
        return "FOURDSKY_BRIDGE_COMMAND must launch multi_receiver_beast_bridge.py.", ""
    script_path = Path(tokens[script_indexes[0]]).expanduser()
    if not script_path.is_absolute():
        script_path = ROOT / script_path
    if not script_path.is_file():
        return f"Configured multi-receiver bridge does not exist: {script_path}", ""

    configured_path = _option_value(tokens, "--config")
    if not configured_path:
        return "FOURDSKY_BRIDGE_COMMAND must pass --config.", ""

    bridge_config_path = Path(configured_path).expanduser()
    if not bridge_config_path.is_absolute():
        bridge_config_path = ROOT / bridge_config_path
    if bridge_config_path.resolve() != receiver_config_path.resolve():
        return "FOURDSKY_BRIDGE_COMMAND --config does not match MLAT_RECEIVER_CONFIG.", ""
    if "--diagnostic" in tokens:
        return "FOURDSKY_BRIDGE_COMMAND cannot use --diagnostic for a live launch.", ""

    if raw_observation_log_path is None:
        return "", "MLAT_RAW_OBSERVATION_LOG is not configured."
    configured_audit_log = _option_value(tokens, "--audit-log")
    if not configured_audit_log:
        return "", "FOURDSKY_BRIDGE_COMMAND must pass --audit-log for an evidence run."
    bridge_audit_path = Path(configured_audit_log).expanduser()
    if not bridge_audit_path.is_absolute():
        bridge_audit_path = ROOT / bridge_audit_path
    if bridge_audit_path.resolve() != raw_observation_log_path.resolve():
        return "", "FOURDSKY_BRIDGE_COMMAND --audit-log does not match MLAT_RAW_OBSERVATION_LOG."
    if raw_observation_log_path.exists() and raw_observation_log_path.stat().st_size:
        return "", "MLAT_RAW_OBSERVATION_LOG must be new or empty for a run-scoped capture."
    return "", ""


async def _discover_registry_identities(env: dict[str, str]) -> set[str]:
    discovery = CKBPeerDiscovery(
        CKBConfig(
            network=env.get("CKB_NETWORK", "testnet"),
            ckb_rpc_url=env.get("CKB_RPC_URL", "https://testnet.ckb.dev/rpc"),
            ckb_indexer_url=env.get("CKB_INDEXER_URL", "https://testnet.ckb.dev/indexer"),
            receiver_registry_type_hash=env.get("RECEIVER_REGISTRY_TYPE_HASH", ""),
            api_timeout=int(env.get("CKB_API_TIMEOUT", "15")),
            ssl_verify=env.get("CKB_SSL_VERIFY", "true").lower() == "true",
            max_record_age_seconds=int(env.get("CKB_MAX_RECORD_AGE_SECONDS", "86400")),
        )
    )
    await discovery.initialize()
    try:
        return {receiver.identity_id for receiver in await discovery.discover_peers()}
    finally:
        await discovery.shutdown()


def discover_registry_identities(env: dict[str, str]) -> set[str]:
    return asyncio.run(_discover_registry_identities(env))


def build_report(
    env: dict[str, str],
    *,
    registry_identity_ids: set[str] | None = None,
    registry_query_error: str = "",
) -> dict:
    transport = env.get("FOURDSKY_TRANSPORT", "")
    bridge_command = env.get("FOURDSKY_BRIDGE_COMMAND", "")
    benchmark_required = env.get("REQUIRE_LIVE_BENCHMARKABLE_OUTPUT", "false").lower() == "true"
    strict_mode = env.get("STRICT_PRODUCTION_MODE", "false").lower() == "true"
    simulate_fallback = env.get("SIMULATE_IF_UNAVAILABLE", "true").lower() == "true"
    registry_type_hash = env.get("RECEIVER_REGISTRY_TYPE_HASH", "").strip()
    receiver_config_value = env.get("MLAT_RECEIVER_CONFIG", "").strip()
    receiver_config_path = (
        Path(receiver_config_value).expanduser()
        if Path(receiver_config_value).is_absolute()
        else ROOT / receiver_config_value
    )
    raw_observation_log_value = env.get("MLAT_RAW_OBSERVATION_LOG", "").strip()
    raw_observation_log_path = None
    if raw_observation_log_value:
        raw_observation_log_path = Path(raw_observation_log_value).expanduser()
        if not raw_observation_log_path.is_absolute():
            raw_observation_log_path = ROOT / raw_observation_log_path
    max_clock_uncertainty_raw = env.get("MAX_CLOCK_UNCERTAINTY_NS", "100")
    try:
        max_clock_uncertainty_ns = float(max_clock_uncertainty_raw)
        if not math.isfinite(max_clock_uncertainty_ns) or max_clock_uncertainty_ns < 0:
            raise ValueError
        max_clock_uncertainty_valid = True
    except (TypeError, ValueError):
        max_clock_uncertainty_ns = 100.0
        max_clock_uncertainty_valid = False
    bridge_command_error, raw_observation_log_error = (
        validate_bridge_command(
            bridge_command,
            receiver_config_path,
            raw_observation_log_path,
        )
        if bridge_command
        else ("", "")
    )
    try:
        normalize_identity_id(registry_type_hash)
        registry_type_hash_valid = True
    except ValueError:
        registry_type_hash_valid = False
    external_source_attested = (
        env.get("FOURDSKY_EXTERNAL_SOURCE_ATTESTED", "false").lower() == "true"
    )
    synchronized_clocks_attested = (
        env.get("FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED", "false").lower() == "true"
    )

    rtl_test_available = command_exists("rtl_test")
    readsb_available = command_exists("readsb")

    rtl_present = False
    rtl_output = ""
    if rtl_test_available:
        code, rtl_output = run_command(["rtl_test", "-t"])
        rtl_present = code == 0 and "No supported devices found." not in rtl_output

    common_ports = [30005, 30006, 30002]
    reachable_ports = [port for port in common_ports if probe_tcp("127.0.0.1", port)]

    receiver_config_error = ""
    receivers: list[dict] = []
    receiver_checks: list[dict] = []
    if receiver_config_value and max_clock_uncertainty_valid:
        try:
            receivers = load_receiver_config(
                receiver_config_path,
                require_mlat_ready=True,
                max_uncertainty_ns=max_clock_uncertainty_ns,
            )
        except ValueError as exc:
            receiver_config_error = str(exc)

    for receiver in receivers:
        reachable = probe_tcp(receiver["host"], receiver["port"])
        receiver_checks.append(
            {
                "receiver_id": receiver["receiver_id"],
                "sensor_id": receiver["sensor_id"],
                "endpoint": f'{receiver["host"]}:{receiver["port"]}',
                "endpoint_reachable": reachable,
                "clock_source": receiver["clock"]["source"],
                "clock_uncertainty_ns": receiver["clock"]["uncertainty_ns"],
                "clock_valid_until_ns": receiver["clock"]["valid_until_ns"],
                "clock_evidence_method": receiver["clock"]["evidence"]["method"],
                "clock_evidence_sha256": receiver["clock"]["evidence"]["sha256"],
            }
        )

    all_configured_endpoints_reachable = bool(receiver_checks) and all(
        check["endpoint_reachable"] for check in receiver_checks
    )
    configured_identity_ids = {receiver["receiver_id"] for receiver in receivers}
    discovered_identity_ids = registry_identity_ids or set()
    missing_registry_identities = sorted(configured_identity_ids - discovered_identity_ids)
    registry_identities_verified = bool(
        configured_identity_ids
        and registry_identity_ids is not None
        and not registry_query_error
        and not missing_registry_identities
    )
    source_ready = bool(receivers) and all_configured_endpoints_reachable
    report = {
        "transport": transport,
        "bridge_command": bridge_command,
        "bridge_command_valid": bool(bridge_command and receiver_config_value)
        and not bridge_command_error,
        "raw_observation_log": {
            "path": str(raw_observation_log_path) if raw_observation_log_path else "",
            "ready": bool(raw_observation_log_path and bridge_command and receiver_config_value)
            and not raw_observation_log_error,
            "error": raw_observation_log_error,
        },
        "strict_production_mode": strict_mode,
        "simulate_if_unavailable": simulate_fallback,
        "require_live_benchmarkable_output": benchmark_required,
        "receiver_registry_type_hash_configured": registry_type_hash_valid,
        "receiver_config": {
            "path": str(receiver_config_path) if receiver_config_value else "",
            "valid": bool(receivers) and not receiver_config_error,
            "receiver_count": len(receivers),
            "all_endpoints_reachable": all_configured_endpoints_reachable,
            "receivers": receiver_checks,
            "error": receiver_config_error,
        },
        "registry_discovery": {
            "queried": registry_identity_ids is not None or bool(registry_query_error),
            "active_receiver_count": len(discovered_identity_ids),
            "configured_identities_verified": registry_identities_verified,
            "missing_configured_identities": missing_registry_identities,
            "error": registry_query_error,
        },
        "checks": {
            "readsb_installed": readsb_available,
            "rtl_test_installed": rtl_test_available,
            "rtl_sdr_detected": rtl_present,
            "local_common_beast_ports": reachable_ports,
            "external_source_attested": external_source_attested,
            "synchronized_clocks_attested": synchronized_clocks_attested,
            "max_clock_uncertainty_ns": max_clock_uncertainty_ns,
        },
        "ready_for_real_live_ingest": bool(
            transport == "command-jsonl"
            and bridge_command
            and not bridge_command_error
            and source_ready
            and synchronized_clocks_attested
        ),
        "ready_for_evidence_run": False,
        "blockers": [],
    }

    if transport != "command-jsonl":
        report["blockers"].append("FOURDSKY_TRANSPORT is not set to command-jsonl.")
    if not bridge_command:
        report["blockers"].append("FOURDSKY_BRIDGE_COMMAND is not set.")
    elif bridge_command_error:
        report["blockers"].append(bridge_command_error)
    if receiver_config_value and bridge_command and raw_observation_log_error:
        report["blockers"].append(raw_observation_log_error)
    if not receiver_config_value:
        report["blockers"].append("MLAT_RECEIVER_CONFIG is not configured.")
    elif not max_clock_uncertainty_valid:
        report["blockers"].append("MAX_CLOCK_UNCERTAINTY_NS must be non-negative.")
    elif receiver_config_error:
        report["blockers"].append(f"Receiver config is not MLAT-ready: {receiver_config_error}")
    elif not all_configured_endpoints_reachable:
        unreachable = [
            check["endpoint"] for check in receiver_checks if not check["endpoint_reachable"]
        ]
        report["blockers"].append(
            "Configured Beast endpoints are unreachable: " + ", ".join(unreachable)
        )
    if not source_ready:
        report["blockers"].append(
            "No complete four-receiver Beast source is available from the configured endpoints."
        )
    if not synchronized_clocks_attested:
        report["blockers"].append("Synchronized receiver clocks have not been attested.")
    if receivers:
        if registry_query_error:
            report["blockers"].append(f"Live Registry V2 discovery failed: {registry_query_error}")
        elif registry_identity_ids is None:
            report["blockers"].append("Live Registry V2 identities were not queried.")
        elif missing_registry_identities:
            report["blockers"].append(
                "Configured receiver identities are not active in Registry V2: "
                + ", ".join(missing_registry_identities)
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
    elif not registry_type_hash_valid:
        report["blockers"].append(
            "RECEIVER_REGISTRY_TYPE_HASH is not a 0x-prefixed 32-byte V2 code hash."
        )

    report["ready_for_evidence_run"] = bool(
        report["ready_for_real_live_ingest"]
        and strict_mode
        and not simulate_fallback
        and benchmark_required
        and registry_type_hash_valid
        and not raw_observation_log_error
        and raw_observation_log_path is not None
        and registry_identities_verified
    )
    return report


def main() -> int:
    args = parse_args()
    env = {**read_env_file(), **os.environ}
    if args.receiver_config:
        env["MLAT_RECEIVER_CONFIG"] = args.receiver_config
    registry_identity_ids = None
    registry_query_error = ""
    if env.get("MLAT_RECEIVER_CONFIG") and env.get("RECEIVER_REGISTRY_TYPE_HASH"):
        try:
            registry_identity_ids = discover_registry_identities(env)
        except Exception as exc:
            registry_query_error = str(exc)
    report = build_report(
        env,
        registry_identity_ids=registry_identity_ids,
        registry_query_error=registry_query_error,
    )

    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 2 if args.require_ready and not report["ready_for_evidence_run"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
