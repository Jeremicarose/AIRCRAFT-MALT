from tools.mlat.capture_grant_evidence import live_gate_failures, raw_position_link_failures
from tools.mlat.capture_reliability_window import positive_duration
from tools.mlat.verify_live_evidence import verify_bundle, REQUIRED_ARTIFACTS

import argparse
import pytest


def test_backend_cannot_attest_frontend_and_clock_stage_is_required():
    mode = {
        "mode": "live",
        "runtime_status": "active",
        "strict_production_mode": True,
        "simulate_if_unavailable": False,
        "synthetic_feed_mode": False,
        "configured_transport": "command-jsonl",
    }
    pipeline = {
        "provenance": {
            "live_data": True,
            "benchmarkable_output": True,
            "registry_discovery_live": True,
        },
        "stages": [
            {"id": name, "status": "pass"}
            for name in (
                "registry",
                "discovery",
                "ingest",
                "clock",
                "correlation",
                "solve",
                "storage",
                "api",
            )
        ]
        + [{"id": "dashboard", "status": "waiting"}],
    }
    frontend = {"status": "ok", "service": "receiver-registry-operations"}
    assert live_gate_failures(mode, pipeline, frontend) == []
    assert live_gate_failures(mode, pipeline, None)
    pipeline["stages"][3]["status"] = "blocked"
    assert any("clock" in reason for reason in live_gate_failures(mode, pipeline, frontend))


def test_synthetic_position_cannot_be_promoted_by_live_runtime_metadata():
    assert any(
        "provenance" in reason.lower()
        for reason in raw_position_link_failures(
            [], [{"data_provenance": "SYNTHETIC", "aircraft_id": "ABCDEF"}]
        )
    )


@pytest.mark.parametrize("value", ["nan", "inf", "-1", "0", "1000000"])
def test_soak_duration_cannot_run_forever(value):
    with pytest.raises(argparse.ArgumentTypeError):
        positive_duration(value)


def test_evidence_symlinks_cannot_read_outside_the_bundle(tmp_path, monkeypatch):
    import hashlib
    import json

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifacts = {}
    for name in REQUIRED_ARTIFACTS:
        (bundle / name).write_text("{}\n")
        artifacts[name] = {"bytes": 3, "sha256": hashlib.sha256(b"{}\n").hexdigest()}
    outside = tmp_path / "outside.txt"
    outside.write_text("{}\n")
    (bundle / "untrusted-link").symlink_to(outside)
    artifacts["untrusted-link"] = {"bytes": 3, "sha256": hashlib.sha256(b"{}\n").hexdigest()}
    (bundle / "manifest.json").write_text(json.dumps({"schema_version": 2, "artifacts": artifacts}))
    result = verify_bundle(bundle)
    assert result["valid"] is False
    assert any("leaves the evidence bundle" in reason for reason in result["failures"])
