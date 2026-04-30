import importlib
import sys


MODULE_NAME = "api.rest_api"


def _load_api_module(monkeypatch, tmp_path, **env):
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ENABLE_BACKGROUND_BROADCASTER", "false")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    )

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    existing = sys.modules.get(MODULE_NAME)
    if existing is not None and hasattr(existing, "db"):
        existing.db.close()

    module = importlib.import_module(MODULE_NAME)
    module = importlib.reload(module)
    return module


def _seed_api_db(module):
    module.db.store_receiver(
        receiver_id="RECV_NYC_001",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
    )
    module.db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1_700_000_100.0,
        latitude=40.75,
        longitude=-73.85,
        altitude=9000.0,
        uncertainty=120.5,
        num_receivers=4,
        receiver_ids=["RECV_NYC_001", "RECV_BOS_001", "RECV_PHL_001", "RECV_DC_001"],
        residual=12.3,
    )


def test_api_health_and_data_endpoints(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    _seed_api_db(module)
    client = module.app.test_client()

    health = client.get("/api/health")
    receivers = client.get("/api/receivers")
    positions = client.get("/api/positions/recent?seconds=600&limit=10")

    assert health.status_code == 200
    assert receivers.status_code == 200
    assert positions.status_code == 200
    assert receivers.get_json()["count"] == 1
    assert positions.get_json()["count"] == 1

    module.db.close()


def test_api_restricts_cors_to_allowed_origins(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    client = module.app.test_client()

    allowed = client.get("/api/health", headers={"Origin": "http://localhost:8080"})
    denied = client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
    assert denied.headers.get("Access-Control-Allow-Origin") in (None, "https://evil.example")

    module.db.close()


def test_admin_cleanup_is_disabled_by_default(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    client = module.app.test_client()

    response = client.post("/api/admin/cleanup", json={"days": 7})

    assert response.status_code == 404
    module.db.close()


def test_admin_cleanup_requires_api_key_and_validates_payload(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        ENABLE_ADMIN_API="true",
        ADMIN_API_KEY="secret-key",
    )
    client = module.app.test_client()

    unauthorized = client.post("/api/admin/cleanup", json={"days": 7})
    bad_request = client.post(
        "/api/admin/cleanup",
        json={"days": 0},
        headers={"X-API-Key": "secret-key"},
    )
    authorized = client.post(
        "/api/admin/cleanup",
        json={"days": 7},
        headers={"X-API-Key": "secret-key"},
    )

    assert unauthorized.status_code == 403
    assert bad_request.status_code == 400
    assert authorized.status_code == 200

    module.db.close()
