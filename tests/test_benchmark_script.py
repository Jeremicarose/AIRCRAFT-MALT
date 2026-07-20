import json
import subprocess
import sys

from database.mlat_db import MLATDatabase
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "scripts"))
from bridge_adapter import normalize_record
from fetch_opensky_reference import normalize_state_vector


def test_benchmark_script_compares_against_reference(tmp_path):
    mlat = tmp_path / "mlat.jsonl"
    reference = tmp_path / "reference.jsonl"

    mlat.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "aircraft_id": "A1B2C3",
                        "timestamp": 1710000000.0,
                        "latitude": 40.75,
                        "longitude": -73.85,
                        "altitude": 9000.0,
                        "uncertainty": 120.5,
                        "quality_score": 0.82,
                        "solver_method": "robust_mlat",
                        "receiver_count": 4,
                        "created_at": "2024-03-09T16:00:00.500000+00:00",
                    }
                )
            ]
        ),
        encoding="utf-8",
    )
    reference.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "aircraft_id": "A1B2C3",
                        "timestamp": 1710000000.2,
                        "latitude": 40.7505,
                        "longitude": -73.8505,
                        "altitude": 9020.0,
                    }
                )
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_mlat_against_reference.py",
            "--mlat",
            str(mlat),
            "--reference",
            str(reference),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["matched_records"] == 1
    assert payload["coverage_ratio_vs_reference"] == 1.0


def test_export_positions_for_benchmark_outputs_jsonl(tmp_path):
    db_path = tmp_path / "mlat.db"
    output_path = tmp_path / "benchmark.jsonl"

    db = MLATDatabase(str(db_path))
    db.connect()
    db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1710000000.0,
        latitude=40.75,
        longitude=-73.85,
        altitude=9000.0,
        uncertainty=120.5,
        num_receivers=4,
        receiver_ids=["R1", "R2", "R3", "R4"],
        residual=12.3,
        quality_score=0.82,
        quality_bucket="good",
        solver_method="robust_mlat",
        solver_residual_m=12.3,
        solver_iterations=7,
        correlation_time_span_s=0.0012,
        receiver_count=4,
    )
    db.close()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_positions_for_benchmark.py",
            "--db",
            str(db_path),
            "--output",
            str(output_path),
            "--seconds",
            "999999999",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Exported 1 position records" in result.stdout
    payload = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert payload["aircraft_id"] == "A1B2C3"
    assert payload["quality_score"] == 0.82
    assert payload["solver_method"] == "robust_mlat"
    assert payload["receiver_ids"] == ["R1", "R2", "R3", "R4"]
    assert payload["created_at"]


def test_benchmark_report_is_publishable_only_with_live_provenance(tmp_path):
    mlat = tmp_path / "mlat.jsonl"
    reference = tmp_path / "reference.jsonl"
    output = tmp_path / "latest.json"
    runtime_snapshot = tmp_path / "readiness.json"
    mlat.write_text(
        json.dumps(
            {
                "aircraft_id": "A1B2C3",
                "timestamp": 1710000000.0,
                "created_at": "2024-03-09T16:00:00.500000+00:00",
                "latitude": 40.75,
                "longitude": -73.85,
                "altitude": 9000.0,
                "quality_score": 0.82,
                "receiver_count": 4,
                "solver_method": "robust_mlat",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    reference.write_text(
        json.dumps(
            {
                "aircraft_id": "A1B2C3",
                "timestamp": 1710000000.2,
                "latitude": 40.7505,
                "longitude": -73.8505,
                "altitude": 9020.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime_snapshot.write_text(
        json.dumps(
            {
                "generated_at": "2026-07-16T12:00:00+00:00",
                "ready": True,
                "dimensions": {
                    "freshness": {"ready": True, "last_store_age_s": 0.5},
                    "reliability": {"ready": True, "active_receivers": 4, "failed_solves": 0},
                },
            }
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_mlat_against_reference.py",
            "--mlat",
            str(mlat),
            "--reference",
            str(reference),
            "--output",
            str(output),
            "--reference-source",
            "OpenSky",
            "--region",
            "Northeast corridor",
            "--data-provenance",
            "live",
            "--runtime-snapshot",
            str(runtime_snapshot),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["evidence_status"] == "publishable"
    assert report["provenance"]["benchmarkable"] is True
    assert report["freshness"]["end_to_store_age_median_ms"] == 500.0
    assert report["runtime_snapshot"]["reliability"]["active_receivers"] == 4
    assert len(report["inputs"]["mlat"]["sha256"]) == 64


def test_benchmark_matching_does_not_reuse_reference_records(tmp_path):
    mlat = tmp_path / "mlat.jsonl"
    reference = tmp_path / "reference.jsonl"
    mlat.write_text(
        "\n".join(
            json.dumps(
                {
                    "aircraft_id": "A1B2C3",
                    "timestamp": timestamp,
                    "latitude": 40.75,
                    "longitude": -73.85,
                    "altitude": 9000.0,
                }
            )
            for timestamp in (1710000000.0, 1710000000.1)
        )
        + "\n",
        encoding="utf-8",
    )
    reference.write_text(
        json.dumps(
            {
                "aircraft_id": "A1B2C3",
                "timestamp": 1710000000.05,
                "latitude": 40.75,
                "longitude": -73.85,
                "altitude": 9000.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_mlat_against_reference.py",
            "--mlat",
            str(mlat),
            "--reference",
            str(reference),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["matched_records"] == 1
    assert report["coverage_ratio_vs_reference"] == 1.0
    assert report["sample"]["match_ratio_vs_mlat"] == 0.5


def test_normalize_opensky_state_vector():
    row = [
        "a1b2c3",
        "TEST123 ",
        "Country",
        1710000000,
        1710000001,
        -73.85,
        40.75,
        9000.0,
        False,
        250.0,
        180.0,
        0.0,
        None,
        9050.0,
        None,
        False,
        0,
    ]

    normalized = normalize_state_vector(row, fallback_time=1710000002)
    assert normalized is not None
    assert normalized["aircraft_id"] == "A1B2C3"
    assert normalized["timestamp"] == 1710000000.0
    assert normalized["altitude"] == 9050.0


def test_sample_live_bridge_once_outputs_valid_json():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/sample_live_bridge.py",
            "--once",
            "--receiver-id",
            "RECV_NYC_001",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.strip())
    assert payload["receiver_id"] == "RECV_NYC_001"
    assert "timestamp" in payload
    assert "message" in payload


def test_bridge_adapter_normalizes_and_maps_receiver_ids():
    payload = {
        "sensor_id": "raw-sensor-1",
        "time": "2026-06-18T12:00:00Z",
        "hex": "8D4840D6202CC371C32CE0576098",
    }
    records = normalize_record(
        payload,
        receiver_map={"raw-sensor-1": "RECV_NYC_001"},
        default_receiver_id=None,
    )
    assert len(records) == 1
    assert records[0]["receiver_id"] == "RECV_NYC_001"
    assert records[0]["message"] == "8D4840D6202CC371C32CE0576098"
