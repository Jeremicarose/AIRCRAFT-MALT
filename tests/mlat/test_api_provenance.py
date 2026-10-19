import time

import pytest

from test_api import _load_api_module, _seed_api_db


def app_for(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        DEMO_MODE="false",
        STRICT_PRODUCTION_MODE="false",
        FOURDSKY_TRANSPORT="command-jsonl",
    )
    monkeypatch.setattr(module.production_main, "CURRENT_RUNTIME", None)
    return module, module.create_app()


def test_unattended_api_entrypoint_uses_production_server(monkeypatch, tmp_path):
    module, _app = app_for(monkeypatch, tmp_path)
    monkeypatch.setenv("API_DEBUG", "false")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "4555")
    calls = []
    monkeypatch.setattr(module.os, "execvp", lambda command, args: calls.append((command, args)))
    module.main()
    assert calls[0][0] == "gunicorn"
    assert "127.0.0.1:4555" in calls[0][1]
    assert calls[0][1][-1] == "mlat_reference.api.rest_api:app"


def test_no_telemetry_does_not_claim_live_pipeline(monkeypatch, tmp_path):
    module, app = app_for(monkeypatch, tmp_path)
    result = app.test_client().get("/api/pipeline").get_json()
    assert result["provenance"]["live_data"] is False
    assert result["provenance"]["data_provenance"] == "UNKNOWN"
    dashboard = next(item for item in result["stages"] if item["id"] == "dashboard")
    assert dashboard["status"] == "waiting"


def test_legacy_positions_are_unknown_and_quality_is_not_confidence(monkeypatch, tmp_path):
    module, app = app_for(monkeypatch, tmp_path)
    _seed_api_db(module, app)
    result = app.test_client().get("/api/positions/recent").get_json()
    position = result["positions"][0]
    assert position["data_provenance"] == "UNKNOWN"
    assert position["quality"]["confidence_calibrated"] is False
    assert result["data_provenance"] == "UNKNOWN"


@pytest.mark.parametrize("seconds", ["bad", "-1", "0", "1e999", "9" * 400])
def test_aircraft_window_is_validated_and_bounded(monkeypatch, tmp_path, seconds):
    _module, app = app_for(monkeypatch, tmp_path)
    result = app.test_client().get(f"/api/aircraft?seconds={seconds}")
    assert result.status_code == 400


def test_health_has_actionable_component_states(monkeypatch, tmp_path):
    _module, app = app_for(monkeypatch, tmp_path)
    health = app.test_client().get("/api/health").get_json()
    assert {item["component"] for item in health["components"]} >= {
        "frontend",
        "backend",
        "database",
        "ckb_rpc",
        "ckb_indexer",
        "receiver_discovery",
        "feed_transport",
        "correlation",
        "solver",
        "storage",
        "replay_engine",
    }
    for component in health["components"]:
        assert component["status"] in {"HEALTHY", "DEGRADED", "FAILED", "NOT CONFIGURED"}
        assert component["reason"] and component["action"]


def test_old_qualified_receiver_becomes_unqualified(monkeypatch, tmp_path):
    module, app = app_for(monkeypatch, tmp_path)
    _seed_api_db(module, app)
    with app.app_context():
        module.get_db().store_receiver_qualification(
            "RECV_NYC_001", {"state": "QUALIFIED", "received_at": time.time() - 1000}
        )
    row = app.test_client().get("/api/receivers").get_json()["receivers"][0]
    assert row["qualification"]["state"] == "UNQUALIFIED"
