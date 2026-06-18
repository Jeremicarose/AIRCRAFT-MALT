import importlib
import sys
import time


def _seed_commercial_state(db):
    account_id = db.create_account("acme-air", "ops@acme.test")
    public_plan = db.get_plan_by_code("public_demo")
    premium_plan = db.get_plan_by_code("premium")
    assert public_plan is not None
    assert premium_plan is not None
    public_key = "public-key-123"
    premium_key = "premium-key-456"
    public_api_key_id = db.create_api_key(
        account_id=account_id,
        key_name="public",
        raw_key=public_key,
        plan_id=public_plan.id,
    )
    premium_api_key_id = db.create_api_key(
        account_id=account_id,
        key_name="premium",
        raw_key=premium_key,
        plan_id=premium_plan.id,
    )
    db.create_entitlement(account_id=account_id, entitlement_code="live_stream")
    return {
        "account_id": account_id,
        "public_key": public_key,
        "premium_key": premium_key,
        "public_api_key_id": public_api_key_id,
        "premium_api_key_id": premium_api_key_id,
    }


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
        commercial = _seed_commercial_state(db)
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
            quality_score=0.82,
            quality_bucket="good",
            solver_method="robust_mlat",
            solver_residual_m=12.3,
            solver_iterations=7,
            correlation_time_span_s=0.0012,
            receiver_count=4,
        )
        return commercial


def test_api_health_and_data_endpoints(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    client = app.test_client()

    health = client.get("/api/health")
    receivers = client.get("/api/receivers")
    positions = client.get(
        "/api/positions/recent?seconds=600&limit=10",
        headers={"X-API-Key": commercial["public_key"]},
    )

    assert health.status_code == 200
    assert receivers.status_code == 200
    assert positions.status_code == 200
    assert receivers.get_json()["count"] == 1
    assert positions.get_json()["count"] == 1

    health_payload = health.get_json()
    assert health_payload["database"]["sqlite_single_node_only"] is True
    assert health_payload["broadcaster"]["enabled"] is False
    assert "freshness" in health_payload

    payload = positions.get_json()["positions"][0]
    assert payload["quality"]["score"] == 0.82
    assert payload["quality"]["bucket"] == "good"
    assert payload["solver"]["method"] == "robust_mlat"
    assert payload["solver"]["residual_m"] == 12.3
    assert payload["correlation"]["time_span_s"] == 0.0012
    assert payload["correlation"]["receiver_count"] == 4


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


def test_plan_limits_and_usage_metering(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    client = app.test_client()

    denied_recent = client.get(
        "/api/positions/recent?seconds=1000&limit=150",
        headers={"X-API-Key": commercial["public_key"]},
    )
    allowed_recent = client.get(
        "/api/positions/recent?seconds=1000&limit=150",
        headers={"X-API-Key": commercial["premium_key"]},
    )
    denied_track = client.get(
        "/api/aircraft/A1B2C3/track?start_time=0&end_time=999999&limit=1000",
        headers={"X-API-Key": commercial["public_key"]},
    )

    assert denied_recent.status_code == 403
    assert allowed_recent.status_code == 200
    assert denied_track.status_code == 403

    with app.app_context():
        usage = module.get_db().get_usage_summary(commercial["account_id"])
    assert any(row["resource"] == "recent_positions" for row in usage)


def test_websocket_subscription_requires_stream_entitlement(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    commercial = _seed_api_db(module, app)

    emitted = []
    module.emit = lambda event, payload: emitted.append((event, payload))
    with app.app_context():
        module.handle_subscribe({"aircraft_id": "A1B2C3", "api_key": commercial["public_key"]})
        module.handle_subscribe({"aircraft_id": "A1B2C3", "api_key": commercial["premium_key"]})

    assert emitted[0][1]["status"] == "denied"
    assert emitted[1][1]["status"] == "subscribed"


def test_statistics_exposes_operational_metrics(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    client = app.test_client()

    unauthorized = client.get("/api/statistics?hours=24", headers={"X-API-Key": commercial["public_key"]})
    response = client.get("/api/statistics?hours=24", headers={"X-API-Key": commercial["premium_key"]})

    assert unauthorized.status_code == 403
    assert response.status_code == 200
    payload = response.get_json()
    assert "current" in payload
    assert "runtime" in payload
    assert payload["current"]["avg_quality_score"] == 0.82


def test_readiness_exposes_internal_gates_and_unproven_claims(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    _seed_api_db(module, app)
    client = app.test_client()

    response = client.get("/api/readiness")

    assert response.status_code == 200
    payload = response.get_json()
    assert "dimensions" in payload
    assert "quality" in payload["dimensions"]
    assert "freshness" in payload["dimensions"]
    assert "reliability" in payload["dimensions"]
    assert "packaging" in payload["dimensions"]
    assert payload["not_yet_proven"]["more_accurate_than_incumbents"] is False
    assert payload["dimensions"]["quality"]["benchmarkable_output"] is True
