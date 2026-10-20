import json

from test_api import _load_api_module, _seed_api_db
from tools.mlat.capture_reliability_window import capture_sample


def test_diagnostic_export_drops_unexpected_nested_fields(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    monkeypatch.setattr(module.production_main, "CURRENT_RUNTIME", None)
    app = module.create_app()
    _seed_api_db(module, app)
    secret = "NEVER-EXPORT-NESTED-CREDENTIAL"
    with app.app_context():
        db = module.get_db()
        db.bind_runtime_provenance(
            "SYNTHETIC",
            "test",
            {"password": secret, "source_manifest": {"license": "CC-BY-SA-4.0", "api_key": secret}},
        )
        db.store_receiver_qualification(
            "RECV_NYC_001", {"state": "UNQUALIFIED", "credentials": {"token": secret}}
        )
        db.store_runtime_snapshot(
            {
                "is_running": True,
                "last_storage_error": secret,
                "observation_diagnostics": [
                    {"reason": "clock_not_qualified", "private_key": secret}
                ],
            }
        )
    response = app.test_client().get("/api/diagnostics/bundle")
    assert response.status_code == 200
    assert secret not in json.dumps(response.get_json())


def test_operational_sampling_does_not_count_registry_declarations_as_live_receivers(monkeypatch):
    responses = iter(
        [
            {"status": "degraded", "runtime": {}},
            {"dimensions": {"freshness": {}}},
            {
                "receivers": [
                    {
                        "status": "online",
                        "last_seen": 0,
                        "operational_state": "OFFLINE",
                        "qualification": {"state": "UNQUALIFIED"},
                    }
                    for _ in range(4)
                ]
            },
        ]
    )
    monkeypatch.setattr(
        "tools.mlat.capture_reliability_window.fetch_json", lambda *args: next(responses)
    )
    assert capture_sample("http://localhost", 1, 10)["active_receivers"] == 0


def test_diagnostics_do_not_export_arbitrary_feed_clock_labels(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    monkeypatch.setattr(module.production_main, "CURRENT_RUNTIME", None)
    app = module.create_app()
    _seed_api_db(module, app)
    secret = "wss://private.invalid/feed?token=DO-NOT-EXPORT"
    with app.app_context():
        module.get_db().store_receiver_qualification(
            "RECV_NYC_001", {"state": "UNQUALIFIED", "clock_source": secret}
        )
    response = app.test_client().get("/api/diagnostics/bundle")
    assert response.status_code == 200
    assert secret not in response.get_data(as_text=True)
