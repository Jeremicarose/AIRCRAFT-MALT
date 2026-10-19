#!/usr/bin/env python3
"""Run a bounded synthetic processor/API soak with one restart and persistent SQLite."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mlat.capture_reliability_window import (
    capture_sample,
    positive_duration,
    summarize_samples,
)


def wait_ready(base, process):
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Synthetic service exited during startup; inspect service.log")
        try:
            with urllib.request.urlopen(base + "/api/positions/recent", timeout=2) as response:
                rows = json.load(response)["positions"]
            if rows:
                assert all(row["data_provenance"] == "SYNTHETIC" for row in rows)
                return rows
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.25)
    raise RuntimeError("No synthetic solution reached the API within 45 seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-seconds", type=positive_duration, default=120)
    parser.add_argument("--interval-seconds", type=positive_duration, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    database = args.output_dir.resolve() / "synthetic.db"
    env = {
        **os.environ,
        "MLAT_ENV_FILE": "/dev/null",
        "API_HOST": "127.0.0.1",
        "API_PORT": str(port),
        "DATABASE_PATH": str(database),
        "STATS_INTERVAL_SECONDS": "5",
        "RATE_LIMIT_ENABLED": "true",
        "RATE_LIMIT_REQUESTS": "10000",
        "LOG_LEVEL": "INFO",
    }
    samples = []
    restart = None
    process = None
    report = {
        "status": "NOT RUN",
        "data_provenance": "SYNTHETIC",
        "physical_validation": "BLOCKED",
        "scope": "single-node synthetic processor/API, real HTTP polling and SQLite; not physical receiver transport or an SLO",
    }
    with (args.output_dir / "service.log").open("w") as log:

        def start():
            return subprocess.Popen(
                [str(ROOT / "run-demo.sh")], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
            )

        try:
            startup = time.monotonic()
            process = start()
            first = wait_ready(base, process)
            report["startup_seconds"] = time.monotonic() - startup
            first_id = min(item["id"] for item in first)
            started = time.time()
            tick = time.monotonic()
            deadline = tick + args.duration_seconds
            while time.monotonic() < deadline:
                if restart is None and time.monotonic() - tick >= args.duration_seconds / 2:
                    restart_started = time.monotonic()
                    process.terminate()
                    process.wait(timeout=15)
                    samples.append(capture_sample(base, 1, 10))
                    process = start()
                    wait_ready(base, process)
                    restart = {
                        "duration_seconds": time.monotonic() - restart_started,
                        "first_position_id_preserved": False,
                    }
                    import sqlite3

                    with sqlite3.connect(database) as connection:
                        row = connection.execute(
                            "SELECT data_provenance FROM positions WHERE id=?", (first_id,)
                        ).fetchone()
                    restart["first_position_id_preserved"] = (
                        row is not None and row[0] == "SYNTHETIC"
                    )
                    assert restart["first_position_id_preserved"]
                samples.append(capture_sample(base, 2, 10))
                time.sleep(min(args.interval_seconds, max(0, deadline - time.monotonic())))
            report.update(
                status="PASS",
                metrics=summarize_samples(
                    samples, started_at=started, ended_at=time.time(), minimum_receivers=4
                ),
                restart=restart,
                samples=samples,
            )
            gaps = [
                later["timestamp"] - earlier["timestamp"]
                for earlier, later in zip(samples, samples[1:])
            ]
            report["timing"] = {
                "requested_active_seconds": args.duration_seconds,
                "observed_monotonic_seconds": time.monotonic() - tick,
                "observed_wall_seconds": time.time() - started,
                "largest_sample_gap_seconds": max(gaps, default=0),
                "sampling_continuity": (
                    "FAIL" if max(gaps, default=0) > max(3 * args.interval_seconds, 15) else "PASS"
                ),
                "interpretation": "Wall/monotonic differences and sampling gaps may reflect host sleep, clock adjustment or pauses. This is sampled availability, not a production SLO.",
            }
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            subprocess.TimeoutExpired,
        ) as exc:
            report.update(status="FAIL", reason=str(exc), samples=samples)
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    report.update(status="FAIL", reason="forced shutdown")
            report["shutdown_exit_code"] = process.returncode if process else None
            (args.output_dir / "report.json").write_text(
                json.dumps(report, indent=2, allow_nan=False) + "\n"
            )
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
