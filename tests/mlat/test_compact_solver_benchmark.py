import json
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from mlat_reference.benchmarks.compact_solver import (
    SourceIntegrityError,
    build_compact_benchmark_report,
    evaluate_compact_dataset,
    evaluate_fixture_event,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reference" / "mlat" / "benchmarks" / "fixtures" / "mpyc-gps-five-event.json"
SOURCE_MANIFEST = FIXTURE.with_name("mpyc-gps-five-source.json")


def test_synthetic_control_solves_below_one_metre_without_live_claim():
    result = evaluate_fixture_event(FIXTURE, timing_mode="synthetic")

    assert result["solved"] is True
    assert result["errors_m"]["three_dimensional"] < 1.0
    assert result["data_source"] == "SIMULATION"
    assert result["claim_scope"] == "solver_only"
    assert result["is_live"] is False
    assert result["receiver_count"] == 5
    assert json.loads(FIXTURE.read_text())["event_id"] == "5711382"


def test_published_event_reports_measured_accuracy_and_source_limitations():
    result = evaluate_fixture_event(FIXTURE, timing_mode="published")

    assert result["solved"] is True
    assert (
        0 < result["errors_m"]["horizontal"] < 100
    )  # Historical reference, not an exact acceptance target.
    assert 0 < result["errors_m"]["three_dimensional"] < 150
    assert result["data_source"] == "HISTORICAL_RECORDING"
    assert result["source"]["license"] == "CC-BY-SA-4.0"
    assert result["source"]["original_dataset"] == "https://doi.org/10.5281/zenodo.4739276"
    assert any("not a live receiver feed" in item for item in result["source"]["limitations"])
    assert result["is_live"] is False
    assert result["ground_truth"]["altitude_m"] == 7711.44
    assert len(result["receiver_geometry"]) == 5
    assert {receiver["receiver_id"] for receiver in result["receiver_geometry"]} == {
        "locards:10",
        "locards:141",
        "locards:263",
        "locards:598",
        "locards:663",
    }


def test_compact_dataset_rejects_source_files_that_do_not_match_manifest(tmp_path):
    sensors = tmp_path / "sensors.csv"
    measurements = tmp_path / "set_1.csv"
    sensors.write_text("changed source\n", encoding="utf-8")
    measurements.write_text("changed source\n", encoding="utf-8")

    with pytest.raises(SourceIntegrityError, match=r"sensors\.csv SHA-256 mismatch"):
        evaluate_compact_dataset(
            sensors,
            measurements,
            source_manifest_path=SOURCE_MANIFEST,
        )


def test_compact_dataset_counts_every_event_and_summarizes_solved_accuracy(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sensors = tmp_path / "sensors.csv"
    measurements = tmp_path / "set_1.csv"
    manifest = tmp_path / "source.json"

    sensor_lines = ["serial,latitude,longitude,height,type,good"]
    measured = []
    for receiver in fixture["receivers"]:
        serial = receiver["receiver_id"].split(":", maxsplit=1)[1]
        sensor_lines.append(
            f"{serial},{receiver['latitude']},{receiver['longitude']},"
            f"{receiver['altitude_m']},Radarcape,TRUE"
        )
        measured.append([serial, receiver["published_timestamp_ns"], receiver["signal_strength"]])
    sensors.write_text("\n".join(sensor_lines) + "\n", encoding="utf-8")

    truth = fixture["ground_truth"]
    header = (
        "id,timeAtServer,aircraft,latitude,longitude,baroAltitude,"
        "geoAltitude,numMeasurements,measurements"
    )
    encoded_measurements = json.dumps(measured, separators=(",", ":"))
    event = (
        f'5711382,3178.18799996376,2742,{truth["latitude"]},'
        f'{truth["longitude"]},7772.4,{truth["altitude_m"]},5,'
        f'"{encoded_measurements.replace(chr(34), chr(34) * 2)}"'
    )
    measurements.write_text(f"{header}\n{event}\n{event.replace('5711382', '5711383', 1)}\n")

    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_id": "test-source",
                "data_source": "HISTORICAL_RECORDING",
                "claim_scope": "solver_only",
                "license": "CC-BY-SA-4.0",
                "expected_event_count": 2,
                "limitations": ["Test fixture, not live data."],
                "files": {
                    "sensors": {
                        "name": "sensors.csv",
                        "sha256": hashlib.sha256(sensors.read_bytes()).hexdigest(),
                    },
                    "measurements": {
                        "name": "set_1.csv",
                        "sha256": hashlib.sha256(measurements.read_bytes()).hexdigest(),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_compact_dataset(
        sensors,
        measurements,
        source_manifest_path=manifest,
    )

    assert report["event_counts"] == {"total": 2, "solved": 2, "unsolved": 0}
    assert report["solve_rate"] == 1.0
    assert report["residual_m"]["count"] == 2
    assert report["iterations"]["successful"]["count"] == 2
    assert report["failure_categories"] == {}
    assert (
        report["accuracy_m"]["horizontal"]["median"]
        == report["events"][0]["errors_m"]["horizontal"]
    )
    assert (
        report["accuracy_m"]["three_dimensional"]["p95"]
        == report["events"][0]["errors_m"]["three_dimensional"]
    )
    assert len(report["events"]) == 2
    assert report["data_source"] == "HISTORICAL_RECORDING"
    assert report["is_live"] is False

    combined = build_compact_benchmark_report(
        sensors,
        measurements,
        source_manifest_path=manifest,
        event_fixture_path=FIXTURE,
    )

    assert combined["synthetic_control"]["acceptance"]["passed"] is True
    assert combined["synthetic_control"]["acceptance"]["maximum_3d_error_m"] == 1.0
    assert combined["published_event"]["is_live"] is False
    assert combined["compact_dataset"]["event_counts"]["total"] == 2
    assert combined["interpretation"]["production_pipeline_validated"] is False
    assert combined["interpretation"]["registry_identity_validated"] is False
    assert len(combined["implementation"]["benchmark_module_sha256"]) == 64
    assert len(combined["implementation"]["solver_module_sha256"]) == 64

    output = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "mlat" / "run_compact_solver_benchmark.py"),
            "--sensors",
            str(sensors),
            "--measurements",
            str(measurements),
            "--source-manifest",
            str(manifest),
            "--event-fixture",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Solved 2 of 2 events" in completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["claim_scope"] == "solver_only"
