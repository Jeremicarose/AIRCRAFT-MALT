#!/usr/bin/env python3
"""Measure the real in-process input/correlation/solver/SQLite path with synthetic feeds."""

import argparse
import asyncio
import json
import logging
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ckb_registry.discovery import ReceiverInfo
from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.ingest.feed_transports import JsonFeedParsingMixin
from mlat_reference.ingest.validation import mode_s_crc
from mlat_reference.runtime import ProductionMLATSystem, get_process_rss_mb
from mlat_reference.solver.robust import ReceiverPosition


def summary(values):
    ordered = sorted(values)
    return {
        "samples": len(ordered),
        "median_ms": statistics.median(ordered) if ordered else None,
        "p95_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] if ordered else None,
        "p99_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))] if ordered else None,
        "maximum_ms": max(ordered) if ordered else None,
    }


async def workload(receiver_count, events, target_rate, directory):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"),
        str(Path(directory) / f"{receiver_count}-{target_rate}.db"),
    )
    system.database.connect()
    system.database.bind_runtime_provenance("SYNTHETIC", "pipeline-envelope")
    fixture = json.loads(
        (ROOT / "reference/mlat/benchmarks/fixtures/mpyc-gps-five-event.json").read_text()
    )
    geometry = fixture["receivers"]
    for index in range(receiver_count):
        row = geometry[index % 5]
        receiver = ReceiverInfo(
            f"PERF-{index}",
            row["latitude"] + (0.1 if index >= 5 else 0),
            row["longitude"] + (0.15 if index >= 5 else 0),
            row["altitude_m"],
            "online",
            0,
            ["mode-s", "mlat"],
            "",
            "",
            data_source="simulation",
        )
        system.network_client.active_receivers[receiver.runtime_id] = receiver
    system._cache_receiver_positions()
    target = ReceiverPosition(
        48.5541687011719, 9.18773944561298, 7711.44, "synthetic-aircraft"
    ).to_ecef()
    ranges_ns = {
        receiver_id: round(
            float(((target - position.to_ecef()) ** 2).sum()) ** 0.5 / 299792458.0 * 1e9
        )
        for receiver_id, position in system.receiver_positions.items()
    }
    parser = JsonFeedParsingMixin()
    ingest = []
    correlation = []
    pipeline = []
    cpu_start = time.process_time()
    started = time.perf_counter()
    try:
        for event_index in range(events):
            event_started = time.perf_counter()
            now_ns = time.time_ns()
            body = f"8D{0xA10000 + event_index % 3:06X}{event_index:014X}000000"
            frame = body[:-6] + f"{mode_s_crc(body):06X}"

            async def feed(receiver_id, offset):
                record = {
                    "receiver_id": receiver_id,
                    "timestamp_ns": now_ns + offset,
                    "message": frame,
                    "clock_synchronized": True,
                    "clock_source": "synthetic-common-clock",
                    "clock_uncertainty_ns": 1.0,
                }
                tick = time.perf_counter()
                await parser.dispatch_feed_payload(
                    json.dumps(record),
                    system.handle_incoming_signal,
                    default_receiver_id=receiver_id,
                )
                ingest.append((time.perf_counter() - tick) * 1000)

            await asyncio.gather(
                *(feed(receiver_id, offset) for receiver_id, offset in ranges_ns.items())
            )
            tick = time.perf_counter()
            groups = system.correlator.correlate()
            correlation.append((time.perf_counter() - tick) * 1000)
            for group in groups:
                await system._process_signal_group(group)
            pipeline.append((time.perf_counter() - event_started) * 1000)
            due = started + (event_index + 1) * receiver_count / target_rate
            if due > time.perf_counter():
                await asyncio.sleep(due - time.perf_counter())
        elapsed = time.perf_counter() - started
        return {
            "receivers": receiver_count,
            "simultaneous_feed_callbacks": receiver_count,
            "aircraft": 3,
            "events": events,
            "target_observations_per_second": target_rate,
            "observations_received": system.stats["total_signals"],
            "achieved_observations_per_second": system.stats["total_signals"] / elapsed,
            "successful_solves": system.stats["successful_solves"],
            "failed_solves": system.stats["failed_solves"],
            "stored_positions": system.database.get_database_stats()["total_positions"],
            "storage_failures": system.storage_failures,
            "wall_seconds": elapsed,
            "cpu_seconds": time.process_time() - cpu_start,
            "peak_process_rss_mb": get_process_rss_mb(),
            "ingestion": summary(ingest),
            "correlation": summary(correlation),
            "solver": summary(system.solve_latencies_ms),
            "storage": summary(system.store_latencies_ms),
            "pipeline": summary(pipeline),
            "buffer_size": len(system.correlator.signal_buffer),
            "dedup_entries": len(system.correlator.processed_groups),
        }
    finally:
        system.database.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--events", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.events <= 10000:
        parser.error("--events must be 1..10000")
    logging.getLogger().setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory(prefix="mlat-envelope-") as directory:
        measurements = [
            asyncio.run(workload(count, args.events, rate, directory))
            for count in (4, 5, 10)
            for rate in (100, 1000, 10000)
        ]
    report = {
        "schema_version": 1,
        "data_provenance": "SYNTHETIC",
        "claim_scope": "local_in_process_pipeline",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "limitations": [
            "Cooperative feed callbacks, not external TCP or WebSocket load.",
            "Synthetic receiver geometry and ideal clock metadata, not physical validation.",
            "Per-event correlation; does not measure the runtime's scheduled 100 ms batching delay.",
            "Peak memory is process-wide, not incremental memory per scenario.",
            "No claim beyond the measured rate, event count, and local single-node SQLite deployment.",
        ],
        "measurements": measurements,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Measured {len(measurements)} scenarios; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
