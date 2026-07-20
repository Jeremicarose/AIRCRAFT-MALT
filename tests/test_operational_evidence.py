from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_operational_performance import benchmark_database, git_worktree_dirty, percentile, summarize
from capture_reliability_window import summarize_samples
from capture_grant_evidence import live_gate_failures


def test_operational_percentiles_and_summary():
    values = [1.0, 2.0, 3.0, 4.0, 100.0]

    assert percentile(values, 0.95) == 100.0
    assert summarize(values) == {
        "samples": 5,
        "median": 3.0,
        "p95": 100.0,
        "max": 100.0,
    }
    assert isinstance(git_worktree_dirty(), bool)


def test_database_benchmark_captures_lookup_and_insert_samples():
    metrics = benchmark_database(receiver_count=4, insert_count=8)

    assert metrics["receiver_cache_lookup_ms"]["samples"] == 50
    assert metrics["database_position_insert_ms"]["samples"] == 8
    assert metrics["database_position_insert_ms"]["max"] >= 0


def test_reliability_summary_uses_the_whole_window_as_denominator():
    metrics = summarize_samples(
        [
            {
                "successful": True,
                "health_status": "healthy",
                "active_receivers": 4,
                "fresh": True,
                "last_signal_age_s": 1.0,
                "last_store_age_s": 2.0,
            },
            {"successful": False},
        ],
        started_at=100.0,
        ended_at=110.0,
        minimum_receivers=4,
    )

    assert metrics["api_availability_percent"] == 50.0
    assert metrics["receiver_availability_percent"] == 50.0
    assert metrics["signal_freshness_percent"] == 50.0
    assert metrics["max_store_age_s"] == 2.0


def test_grant_capture_requires_every_live_pipeline_stage():
    mode = {
        "mode": "live",
        "runtime_status": "active",
        "strict_production_mode": True,
        "simulate_if_unavailable": False,
        "synthetic_feed_mode": False,
        "configured_transport": "command-jsonl",
    }
    stage_ids = ["registry", "discovery", "ingest", "correlation", "solve", "storage", "api", "dashboard"]
    pipeline = {
        "provenance": {
            "live_data": True,
            "benchmarkable_output": True,
            "registry_discovery_live": True,
        },
        "stages": [{"id": stage_id, "status": "pass"} for stage_id in stage_ids],
    }

    assert live_gate_failures(mode, pipeline) == []
    pipeline["stages"][2]["status"] = "waiting"
    assert "Pipeline stage 'ingest' is 'waiting', not 'pass'." in live_gate_failures(mode, pipeline)
