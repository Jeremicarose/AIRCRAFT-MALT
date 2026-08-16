from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_operational_performance import (
    benchmark_database,
    git_worktree_dirty,
    percentile,
    summarize,
)
from capture_reliability_window import summarize_samples
from capture_grant_evidence import (
    live_gate_failures,
    raw_clock_config_failures,
    raw_observation_failures,
    raw_position_link_failures,
)
from mlat_reference.solver.robust import (
    SPEED_OF_LIGHT,
    ReceiverPosition,
    RobustMLATSolver,
    SignalObservation,
)
from verify_live_evidence import resolve_positions


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
    stage_ids = [
        "registry",
        "discovery",
        "ingest",
        "correlation",
        "solve",
        "storage",
        "api",
        "dashboard",
    ]
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


def _raw_records():
    message = "8D4840D6202CC371C32CE0576098"
    return [
        {
            "receiver_id": "0x" + octet * 32,
            "timestamp_ns": 1_800_000_000_000_000_000 + index * 100,
            "message": message,
            "clock_synchronized": True,
            "clock_source": f"gpsdo-{index}",
            "clock_uncertainty_ns": 50.0,
            "clock_valid_from_ns": 1_799_999_999_000_000_000,
            "clock_valid_until_ns": 1_800_000_001_000_000_000,
            "clock_evidence_sha256": octet * 32,
        }
        for index, octet in enumerate(("ab", "bc", "cd", "de"))
    ]


def test_raw_observation_gate_requires_four_qualified_receivers():
    records = _raw_records()
    configured = {record["receiver_id"] for record in records}

    assert raw_observation_failures(records, configured) == []
    failures = raw_observation_failures(records[:3], configured)
    assert "Raw observations contain only 3 unique receivers." in failures
    assert "Raw observations contain no four-receiver message group within 5 ms." in failures


def test_raw_observation_clocks_must_match_pinned_config():
    records = _raw_records()
    receivers = [
        {
            "receiver_id": record["receiver_id"],
            "clock": {
                "source": record["clock_source"],
                "uncertainty_ns": record["clock_uncertainty_ns"],
                "valid_from_ns": record["clock_valid_from_ns"],
                "valid_until_ns": record["clock_valid_until_ns"],
                "evidence": {"sha256": record["clock_evidence_sha256"]},
            },
        }
        for record in records
    ]

    assert raw_clock_config_failures(records, receivers) == []
    records[0]["clock_evidence_sha256"] = "00" * 32
    assert "1 raw observations" in raw_clock_config_failures(records, receivers)[0]


def test_position_export_must_link_to_same_raw_transmission_and_receivers():
    records = _raw_records()
    position = {
        "aircraft_id": "4840D6",
        "timestamp": records[0]["timestamp_ns"] / 1_000_000_000,
        "receiver_ids": [record["receiver_id"] for record in records],
        "solver_method": "robust_mlat",
    }

    assert raw_position_link_failures(records, [position]) == []
    position["aircraft_id"] = "ABCDEF"
    assert "1 of 1 exported positions" in raw_position_link_failures(records, [position])[0]


def test_evidence_verifier_resolves_position_from_raw_arrival_times():
    target = ReceiverPosition(40.75, -73.90, 9_000.0, "TARGET")
    receivers = [
        ReceiverPosition(40.55, -74.15, 20.0, "R1"),
        ReceiverPosition(40.55, -73.65, 25.0, "R2"),
        ReceiverPosition(40.95, -74.15, 15.0, "R3"),
        ReceiverPosition(40.95, -73.65, 30.0, "R4"),
        ReceiverPosition(40.75, -74.30, 10.0, "R5"),
        ReceiverPosition(40.75, -73.50, 12.0, "R6"),
    ]
    transmit_time_ns = 1_800_000_000_000_000_000
    message = "8DABCDEF202CC371C32CE0576098"
    target_ecef = target.to_ecef()
    raw_records = []
    observations = []
    for receiver in receivers:
        timestamp_ns = transmit_time_ns + round(
            np.linalg.norm(target_ecef - receiver.to_ecef()) * 1_000_000_000 / SPEED_OF_LIGHT
        )
        raw_records.append(
            {
                "receiver_id": receiver.receiver_id,
                "timestamp_ns": timestamp_ns,
                "message": message,
                "clock_synchronized": True,
            }
        )
        observations.append(
            SignalObservation(
                receiver.receiver_id,
                timestamp_ns / 1_000_000_000,
                message,
                receiver,
                timestamp_ns=timestamp_ns,
            )
        )
    solved = RobustMLATSolver(min_receivers=4).solve_position(observations)
    assert solved is not None
    positions = [
        {
            "aircraft_id": "ABCDEF",
            "timestamp": solved.timestamp,
            "latitude": solved.latitude,
            "longitude": solved.longitude,
            "altitude": solved.altitude,
            "receiver_ids": solved.receiver_ids,
            "solver_method": "robust_mlat",
        }
    ]
    receiver_rows = [
        {
            "identity_id": receiver.receiver_id,
            "latitude": receiver.latitude,
            "longitude": receiver.longitude,
            "altitude": receiver.altitude,
        }
        for receiver in receivers
    ]

    report = resolve_positions(positions, raw_records, receiver_rows)

    assert report["failures"] == []
    assert report["resolved"] == 1
    assert report["max_horizontal_difference_m"] < 0.001
