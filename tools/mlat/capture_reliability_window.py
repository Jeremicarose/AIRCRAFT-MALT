#!/usr/bin/env python3
"""Sample runtime availability and freshness over a bounded evidence window."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import statistics
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
    tick = time.perf_counter()
    try:
        health = fetch_json(f"{api_base.rstrip('/')}/api/health", timeout)
        readiness = fetch_json(f"{api_base.rstrip('/')}/api/readiness", timeout)
        receivers = fetch_json(f"{api_base.rstrip('/')}/api/receivers", timeout)
        successful = True
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return {
            "timestamp": started,
            "successful": False,
            "error": type(exc).__name__,
            "request_latency_ms": (time.perf_counter() - tick) * 1000,
        }

    receiver_rows = receivers.get("receivers", []) if isinstance(receivers, dict) else []
    if not isinstance(receiver_rows, list):
        receiver_rows = []
    operational = [
        receiver
        for receiver in receiver_rows
        if receiver.get("operational_state") == "ONLINE"
        and isinstance(receiver.get("last_seen"), (int, float))
        and 0 <= started - receiver["last_seen"] <= freshness_threshold_s
    ]
    active_receivers = len(operational)
    qualified_receivers = sum(
        1
        for receiver in operational
        if receiver.get("qualification", {}).get("state") == "QUALIFIED"
    )
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
        "qualified_receivers": qualified_receivers,
        "data_provenance": health.get("data_provenance", "UNKNOWN"),
        "request_latency_ms": (time.perf_counter() - tick) * 1000,
        "runtime_metrics": {
            key: runtime.get(key)
            for key in (
                "total_signals",
                "total_positions",
                "successful_solves",
                "failed_solves",
                "clock_rejected_groups",
                "storage_failures",
                "observation_counts",
                "transport_rejections",
                "correlation_dropped_signals",
                "avg_solve_latency_ms",
                "max_solve_latency_ms",
                "process_rss_mb",
                "process_cpu_seconds",
                "start_time",
            )
        },
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
    receiver_available = [
        sample for sample in successful if sample.get("active_receivers", 0) >= minimum_receivers
    ]
    fresh = [sample for sample in successful if sample.get("fresh")]
    health_ok = [
        sample for sample in successful if sample.get("health_status") in {"healthy", "ok"}
    ]
    denominator = len(samples)
    signal_ages = [
        float(sample["last_signal_age_s"])
        for sample in successful
        if sample.get("last_signal_age_s") is not None
    ]
    store_ages = [
        float(sample["last_store_age_s"])
        for sample in successful
        if sample.get("last_store_age_s") is not None
    ]
    return {
        "window_seconds": max(0.0, ended_at - started_at),
        "samples": denominator,
        "successful_requests": len(successful),
        "api_availability_percent": len(successful) / denominator * 100 if denominator else 0.0,
        "healthy_response_percent": len(health_ok) / denominator * 100 if denominator else 0.0,
        "receiver_availability_percent": (
            len(receiver_available) / denominator * 100 if denominator else 0.0
        ),
        "signal_freshness_percent": len(fresh) / denominator * 100 if denominator else 0.0,
        "minimum_receivers": minimum_receivers,
        "qualified_receiver_availability_percent": (
            sum(sample.get("qualified_receivers", 0) >= minimum_receivers for sample in successful)
            / denominator
            * 100
            if denominator
            else 0.0
        ),
        "request_latency_ms": metric_summary(
            [sample["request_latency_ms"] for sample in samples if "request_latency_ms" in sample]
        ),
        "max_signal_age_s": max(signal_ages) if signal_ages else None,
        "max_store_age_s": max(store_ages) if store_ages else None,
    }


def metric_summary(values):
    if not values:
        return {"median": None, "p95": None, "maximum": None}
    ordered = sorted(values)
    return {
        "median": statistics.median(ordered),
        "p95": ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)],
        "maximum": max(ordered),
    }


def positive_duration(value):
    duration = float(value)
    if not math.isfinite(duration) or not 0 < duration <= 86_400:
        raise argparse.ArgumentTypeError("duration must be finite and within (0, 86400] seconds")
    return duration


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:5057")
    parser.add_argument("--duration-seconds", type=positive_duration, default=300.0)
    parser.add_argument("--interval-seconds", type=positive_duration, default=5.0)
    parser.add_argument("--timeout-seconds", type=positive_duration, default=3.0)
    parser.add_argument("--freshness-threshold-seconds", type=positive_duration, default=10.0)
    parser.add_argument("--minimum-receivers", type=int, default=4)
    parser.add_argument(
        "--output",
        default="evidence/mlat-reference/experimental/reliability-local-simulation.json",
    )
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
        samples.append(
            capture_sample(args.api_base, args.timeout_seconds, args.freshness_threshold_seconds)
        )
        if time.time() + args.interval_seconds > deadline:
            break
        time.sleep(args.interval_seconds)
    ended_at = time.time()
    observed_sources = {
        sample.get("data_provenance", "UNKNOWN") for sample in samples if sample.get("successful")
    }
    live_data = live_data and observed_sources == {"LIVE"}
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "sampled_window",
        "provenance": {
            "observed_data_provenance": sorted(observed_sources),
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
