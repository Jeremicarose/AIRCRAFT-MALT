#!/usr/bin/env python3
"""Sample runtime availability and freshness over a bounded evidence window."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any
import urllib.error
import urllib.request


def fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def capture_sample(api_base: str, timeout: float, freshness_threshold_s: float) -> dict[str, Any]:
    started = time.time()
    try:
        health = fetch_json(f"{api_base.rstrip('/')}/api/health", timeout)
        readiness = fetch_json(f"{api_base.rstrip('/')}/api/readiness", timeout)
        receivers = fetch_json(f"{api_base.rstrip('/')}/api/receivers", timeout)
        successful = True
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return {"timestamp": started, "successful": False, "error": str(exc)}

    receiver_rows = receivers.get("receivers", receivers if isinstance(receivers, list) else [])
    if not isinstance(receiver_rows, list):
        receiver_rows = []
    active_receivers = sum(1 for receiver in receiver_rows if receiver.get("status") in {"active", "online"})
    freshness = readiness.get("dimensions", {}).get("freshness", {})
    runtime = health.get("runtime", {})
    last_store_age = freshness.get("last_store_age_s")
    last_signal_age = freshness.get("last_signal_age_s", runtime.get("last_signal_age_s"))
    fresh = last_store_age is not None and float(last_store_age) <= freshness_threshold_s
    return {
        "timestamp": started,
        "successful": successful,
        "health_status": health.get("status"),
        "ready": bool(readiness.get("ready")),
        "active_receivers": active_receivers,
        "last_signal_age_s": last_signal_age,
        "last_store_age_s": last_store_age,
        "fresh": fresh,
    }


def summarize_samples(
    samples: list[dict[str, Any]],
    *,
    started_at: float,
    ended_at: float,
    minimum_receivers: int,
) -> dict[str, Any]:
    successful = [sample for sample in samples if sample.get("successful")]
    receiver_available = [sample for sample in successful if sample.get("active_receivers", 0) >= minimum_receivers]
    fresh = [sample for sample in successful if sample.get("fresh")]
    health_ok = [sample for sample in successful if sample.get("health_status") in {"healthy", "ok"}]
    denominator = len(samples)
    signal_ages = [float(sample["last_signal_age_s"]) for sample in successful if sample.get("last_signal_age_s") is not None]
    store_ages = [float(sample["last_store_age_s"]) for sample in successful if sample.get("last_store_age_s") is not None]
    return {
        "window_seconds": max(0.0, ended_at - started_at),
        "samples": denominator,
        "successful_requests": len(successful),
        "api_availability_percent": len(successful) / denominator * 100 if denominator else 0.0,
        "healthy_response_percent": len(health_ok) / denominator * 100 if denominator else 0.0,
        "receiver_availability_percent": len(receiver_available) / denominator * 100 if denominator else 0.0,
        "signal_freshness_percent": len(fresh) / denominator * 100 if denominator else 0.0,
        "minimum_receivers": minimum_receivers,
        "max_signal_age_s": max(signal_ages) if signal_ages else None,
        "max_store_age_s": max(store_ages) if store_ages else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:5057")
    parser.add_argument("--duration-seconds", type=float, default=300.0)
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    parser.add_argument("--freshness-threshold-seconds", type=float, default=10.0)
    parser.add_argument("--minimum-receivers", type=int, default=4)
    parser.add_argument("--output", default="benchmark/reliability-latest.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_seconds <= 0 or args.interval_seconds <= 0 or args.timeout_seconds <= 0:
        raise SystemExit("Durations and intervals must be positive")

    try:
        mode = fetch_json(f"{args.api_base.rstrip('/')}/api/system/mode", args.timeout_seconds)
    except (OSError, ValueError, urllib.error.URLError):
        mode = {}
    live_data = bool(
        mode.get("mode") == "live"
        and mode.get("runtime_status") == "active"
        and mode.get("synthetic_feed_mode") is False
        and mode.get("configured_transport") != "simulation"
        and mode.get("registry_discovery_live") is True
    )

    started_at = time.time()
    deadline = started_at + args.duration_seconds
    samples: list[dict[str, Any]] = []
    while True:
        samples.append(capture_sample(args.api_base, args.timeout_seconds, args.freshness_threshold_seconds))
        if time.time() + args.interval_seconds > deadline:
            break
        time.sleep(args.interval_seconds)
    ended_at = time.time()
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "sampled_window",
        "provenance": {
            "data_provenance": "live_runtime_window" if live_data else "local_non_live_window",
            "live_data": live_data,
            "runtime_mode": mode.get("mode", "unavailable"),
            "configured_transport": mode.get("configured_transport", "unavailable"),
            "registry_discovery_live": mode.get("registry_discovery_live", False),
        },
        "parameters": {
            "interval_seconds": args.interval_seconds,
            "freshness_threshold_seconds": args.freshness_threshold_seconds,
        },
        "metrics": summarize_samples(
            samples,
            started_at=started_at,
            ended_at=ended_at,
            minimum_receivers=args.minimum_receivers,
        ),
        "samples": samples,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["metrics"]["api_availability_percent"] == 100.0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
