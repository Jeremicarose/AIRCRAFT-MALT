#!/usr/bin/env python3
"""Publish a reproducible local performance baseline for the MLAT control plane."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from database.mlat_db import MLATDatabase  # noqa: E402


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def summarize(values: list[float]) -> dict[str, float | int]:
    return {
        "samples": len(values),
        "median": statistics.median(values) if values else 0.0,
        "p95": percentile(values, 0.95),
        "max": max(values) if values else 0.0,
    }


def timed_ms(callback: Callable[[], Any]) -> float:
    started = time.perf_counter_ns()
    callback()
    return (time.perf_counter_ns() - started) / 1_000_000


def benchmark_database(receiver_count: int, insert_count: int) -> dict[str, dict[str, float | int]]:
    with tempfile.TemporaryDirectory(prefix="mlat-benchmark-") as directory:
        database = MLATDatabase(str(Path(directory) / "baseline.db"))
        database.connect()
        now = time.time()
        for index in range(receiver_count):
            database.store_receiver(
                receiver_id=f"BENCH-{index:03d}",
                latitude=40.0 + index * 0.001,
                longitude=-74.0 - index * 0.001,
                altitude=10.0,
                status="active",
                last_seen=now,
                capabilities=["ads-b", "mlat"],
            )

        lookup_times = [timed_ms(database.get_receivers) for _ in range(max(50, receiver_count * 4))]
        insert_times: list[float] = []
        for index in range(insert_count):
            insert_times.append(
                timed_ms(
                    lambda position_index=index: database.store_position(
                        aircraft_id=f"B{position_index % 128:05X}",
                        timestamp=now + position_index * 0.001,
                        latitude=40.7 + position_index * 0.000001,
                        longitude=-74.0 - position_index * 0.000001,
                        altitude=10_000.0,
                        uncertainty=120.0,
                        num_receivers=4,
                        receiver_ids=["BENCH-000", "BENCH-001", "BENCH-002", "BENCH-003"],
                        residual=18.0,
                        quality_score=0.92,
                        quality_bucket="good",
                        solver_method="benchmark_fixture",
                        solver_residual_m=18.0,
                        solver_iterations=7,
                        correlation_time_span_s=0.001,
                        receiver_count=4,
                    )
                )
            )
        database.close()

    return {
        "receiver_cache_lookup_ms": summarize(lookup_times),
        "database_position_insert_ms": summarize(insert_times),
    }


def fetch_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def timed_api_request(url: str) -> tuple[bool, float]:
    started = time.perf_counter_ns()
    try:
        fetch_json(url)
        success = True
    except (OSError, ValueError, urllib.error.URLError):
        success = False
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return success, elapsed_ms


def benchmark_api(api_base: str, request_count: int, concurrency: int) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}/api/health"
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        samples = list(executor.map(lambda _index: timed_api_request(url), range(request_count)))
    elapsed = max(time.perf_counter() - started, 0.000001)
    successful_times = [latency for success, latency in samples if success]
    successful = len(successful_times)
    latency = summarize(successful_times)
    latency["success_percent"] = successful / request_count * 100 if request_count else 0.0
    return {
        "api_latency_ms": latency,
        "api_throughput": {
            "endpoint": "/api/health",
            "requests": request_count,
            "concurrency": concurrency,
            "successful_requests": successful,
            "success_percent": successful / request_count * 100 if request_count else 0.0,
            "requests_per_second": successful / elapsed,
        },
    }


def peak_rss_mb() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024


def git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() or None


def git_worktree_dirty() -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(completed.stdout.strip())


def runtime_provenance(api_base: str) -> dict[str, Any]:
    try:
        mode = fetch_json(f"{api_base.rstrip('/')}/api/system/mode")
    except (OSError, ValueError, urllib.error.URLError):
        mode = {}
    live_data = bool(
        mode.get("mode") == "live"
        and mode.get("runtime_status") == "active"
        and mode.get("synthetic_feed_mode") is False
        and mode.get("configured_transport") != "simulation"
        and mode.get("registry_discovery_live") is True
    )
    return {
        "data_provenance": "live_runtime_baseline" if live_data else "local_non_live_baseline",
        "live_data": live_data,
        "runtime_mode": mode.get("mode", "unavailable"),
        "configured_transport": mode.get("configured_transport", "unavailable"),
        "registry_discovery_live": mode.get("registry_discovery_live", False),
    }


def build_report(
    *,
    database_metrics: dict[str, Any],
    api_metrics: dict[str, Any],
    provenance: dict[str, Any],
    receiver_count: int,
    insert_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_status": "operational_baseline",
        "provenance": {
            **provenance,
            "environment": "local",
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "git_commit": git_commit(),
            "git_worktree_dirty": git_worktree_dirty(),
        },
        "parameters": {
            "receiver_records": receiver_count,
            "position_inserts": insert_count,
            "database": "temporary SQLite WAL database",
        },
        "metrics": {
            **database_metrics,
            **api_metrics,
            "process_peak_rss_mb": {"value": peak_rss_mb()},
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    provenance = report["provenance"]

    def metric(name: str, field: str = "median", digits: int = 3) -> str:
        value = metrics.get(name, {}).get(field)
        return "n/a" if value is None else f"{float(value):.{digits}f}"

    return f"""# Operational Benchmarks

Generated: `{report['generated_at']}`  
Commit: `{provenance.get('git_commit') or 'unavailable'}`  
Worktree dirty: `{str(provenance.get('git_worktree_dirty', True)).lower()}`  
Provenance: `{provenance['data_provenance']}`  
Live data: `{str(provenance['live_data']).lower()}`

These are reproducible operational baselines, not MLAT accuracy claims. Accuracy is published separately through the external reference benchmark.

| Measurement | Median | P95 | Sample |
| --- | ---: | ---: | ---: |
| Receiver database lookup | {metric('receiver_cache_lookup_ms')} ms | {metric('receiver_cache_lookup_ms', 'p95')} ms | {metrics['receiver_cache_lookup_ms']['samples']} |
| SQLite position insert | {metric('database_position_insert_ms')} ms | {metric('database_position_insert_ms', 'p95')} ms | {metrics['database_position_insert_ms']['samples']} |
| Health API latency | {metric('api_latency_ms')} ms | {metric('api_latency_ms', 'p95')} ms | {metrics['api_latency_ms']['samples']} |

API throughput: `{metric('api_throughput', 'requests_per_second', 1)} requests/s` at concurrency `{metrics['api_throughput']['concurrency']}`.  
Successful API requests: `{metric('api_throughput', 'success_percent', 2)}%`.  
Benchmark process peak RSS: `{metric('process_peak_rss_mb', 'value', 1)} MB`.

Reproduce with:

```bash
python3 scripts/benchmark_operational_performance.py --api-base http://127.0.0.1:5057
```
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:5057")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--receiver-count", type=int, default=25)
    parser.add_argument("--insert-count", type=int, default=500)
    parser.add_argument("--output", default="benchmark/performance-latest.json")
    parser.add_argument("--markdown", default="BENCHMARKS.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if min(args.requests, args.concurrency, args.receiver_count, args.insert_count) <= 0:
        raise SystemExit("Benchmark counts and concurrency must be positive")
    database_metrics = benchmark_database(args.receiver_count, args.insert_count)
    api_metrics = benchmark_api(args.api_base, args.requests, args.concurrency)
    report = build_report(
        database_metrics=database_metrics,
        api_metrics=api_metrics,
        provenance=runtime_provenance(args.api_base),
        receiver_count=args.receiver_count,
        insert_count=args.insert_count,
    )
    output_path = Path(args.output)
    markdown_path = Path(args.markdown)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["metrics"]["api_latency_ms"]["success_percent"] == 100.0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
