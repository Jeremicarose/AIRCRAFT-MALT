import json
from pathlib import Path

import pytest

from mlat_reference.database.database import MLATDatabase
from mlat_reference.replay import replay_compact_dataset
from test_api import _load_api_module

FIXTURES = Path(__file__).resolve().parents[2] / "reference/mlat/benchmarks/fixtures"


def replay(path):
    return replay_compact_dataset(
        path,
        FIXTURES / "compact-public/sensors.csv",
        FIXTURES / "compact-public/set_1.csv",
        FIXTURES / "mpyc-gps-five-source.json",
    )


def test_complete_historical_replay_to_storage_and_api(monkeypatch, tmp_path):
    path = tmp_path / "api.db"
    summary = replay(path)
    assert summary["event_count"] == 362
    assert summary["successful_solves"] + summary["failed_solves"] == 362
    assert summary["failed_solves"] > 0
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        FOURDSKY_TRANSPORT="historical-replay",
        DEMO_MODE="false",
        STRICT_PRODUCTION_MODE="false",
    )
    monkeypatch.setattr(module.production_main, "CURRENT_RUNTIME", None)
    app = module.create_app()
    client = app.test_client()
    assert client.get("/api/system/mode").get_json()["data_provenance"] == "HISTORICAL_REPLAY"
    assert client.get("/api/system/mode").get_json()["mode"] == "historical_replay"
    listing = client.get("/api/replay?limit=100").get_json()
    assert listing["configured"] and len(listing["events"]) == 100
    assert client.get("/api/replay?limit=101").status_code == 400
    example = client.get("/api/replay/events/5711382").get_json()
    assert example["solved"] is True
    assert len(example["observations"]) == len(example["receiver_geometry"]) == 5
    position = example["position"]
    assert position["data_provenance"] == "HISTORICAL_REPLAY"
    assert position["timestamp"] < 10000  # Original relative time, never today's time.
    assert position["timestamp_ns"] == position["source_timestamp_ns"]
    assert position["observation_evidence"]["raw_mode_s_frame_available"] is False
    assert position["observation_evidence"]["live_qualified"] is False
    for receiver in client.get("/api/receivers").get_json()["receivers"]:
        assert receiver["receiver_identity"] is None
        assert receiver["last_seen"] == 0
        assert receiver["operational_state"] == "OFFLINE"
        assert receiver["qualification"]["state"] == "UNQUALIFIED"
    assert client.get("/api/pipeline").get_json()["provenance"]["live_data"] is False
    health = client.get("/api/health").get_json()
    assert (
        next(item for item in health["components"] if item["component"] == "replay_engine")[
            "status"
        ]
        == "HEALTHY"
    )
    with app.app_context():
        db = module.get_db()
        count = db.conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
        assert count == summary["successful_solves"]
    # Restart/replay of the same source is idempotent.
    assert replay(path)["successful_solves"] == count


def test_replay_cannot_open_live_database(tmp_path):
    path = tmp_path / "live.db"
    database = MLATDatabase(str(path))
    database.connect()
    database.bind_runtime_provenance("LIVE", "receiver-feeds")
    database.close()
    with pytest.raises(ValueError, match="separate database"):
        replay(path)


def test_diagnostic_bundle_omits_deployment_credentials(monkeypatch, tmp_path):
    secret = "DO-NOT-EXPORT-THIS-TOKEN"
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        ADMIN_API_KEY=secret,
        FOURDSKY_AUTH_TOKEN=secret,
        FOURDSKY_BRIDGE_COMMAND=f"bridge --token {secret}",
    )
    monkeypatch.setattr(module.production_main, "CURRENT_RUNTIME", None)
    payload = module.create_app().test_client().get("/api/diagnostics/bundle")
    assert payload.status_code == 200
    assert secret not in json.dumps(payload.get_json())
