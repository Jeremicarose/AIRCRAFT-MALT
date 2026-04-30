import importlib
import sys
import time


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


def _seed_api_db(module, app):
    now = time.time()
    with app.app_context():
        db = module.get_db()
        db.store_receiver(
            receiver_id="RECV_NYC_001",
            latitude=40.7128,
            longitude=-74.0060,
            altitude=10.0,
            status="online",
            last_seen=now,
            capabilities=["mode-s", "mlat"],
        )
        db.store_position(
            aircraft_id="A1B2C3",
            timestamp=now,
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
    app = module.create_app()
    _seed_api_db(module, app)
    client = app.test_client()

    health = client.get("/api/health")
    receivers = client.get("/api/receivers")
    positions = client.get("/api/positions/recent?seconds=600&limit=10")

    assert health.status_code == 200
    assert receivers.status_code == 200
    assert positions.status_code == 200
    assert receivers.get_json()["count"] == 1
    assert positions.get_json()["count"] == 1


def test_api_restricts_cors_to_allowed_origins(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    client = app.test_client()

    allowed = client.get("/api/health", headers={"Origin": "http://localhost:8080"})
    denied = client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
    assert denied.headers.get("Access-Control-Allow-Origin") in (None, "https://evil.example")


def test_admin_cleanup_is_disabled_by_default(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    client = app.test_client()

    response = client.post("/api/admin/cleanup", json={"days": 7})

    assert response.status_code == 404


def test_admin_cleanup_requires_api_key_and_validates_payload(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        ENABLE_ADMIN_API="true",
        ADMIN_API_KEY="secret-key",
    )
    app = module.create_app()
    client = app.test_client()

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
