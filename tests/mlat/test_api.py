import importlib
import json
from datetime import datetime, timezone
import pytest
import sqlite3
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


MODULE_NAME = "mlat_reference.api.rest_api"


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
    receiver_payload = receivers.get_json()["receivers"][0]
    assert receiver_payload["identity_id"] == "RECV_NYC_001"
    assert receiver_payload["receiver_label"] == "RECV_NYC_001"
    assert receiver_payload["registry"]["sequence"] == 0
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
    assert payload["correlation"]["receiver_ids"] == [
        "RECV_NYC_001",
        "RECV_BOS_001",
        "RECV_PHL_001",
        "RECV_DC_001",
    ]


def test_liveness_does_not_depend_on_database(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()

    def fail_if_database_is_opened():
        raise AssertionError("liveness must not open SQLite")

    monkeypatch.setattr(module, "get_db", fail_if_database_is_opened)
    response = app.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_reads_while_processor_holds_write_transaction(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    _seed_api_db(module, app)

    writer = sqlite3.connect(app.config["DATABASE_PATH"])
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("BEGIN IMMEDIATE")
    try:
        response = app.test_client().get("/api/health")
    finally:
        writer.rollback()
        writer.close()

    assert response.status_code == 200
    assert response.get_json()["database"]["journal_mode"] == "wal"


def test_request_connections_do_not_repeat_schema_initialization(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    _seed_api_db(module, app)
    original_connect = module.MLATDatabase.connect
    initialize_schema_values = []

    def tracked_connect(database, *args, **kwargs):
        initialize_schema_values.append(kwargs.get("initialize_schema", True))
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(module.MLATDatabase, "connect", tracked_connect)
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert initialize_schema_values == [False]


def test_api_reads_processor_telemetry_from_shared_database(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        FOURDSKY_TRANSPORT="command-jsonl",
        SIMULATE_IF_UNAVAILABLE="false",
    )
    app = module.create_app()
    _seed_api_db(module, app)
    with app.app_context():
        module.get_db().store_statistics(
            total_signals=100,
            total_positions=10,
            successful_solves=10,
            active_aircraft=1,
            active_receivers=4,
            avg_uncertainty=120.5,
            avg_quality_score=0.82,
            avg_latency_ms=3.5,
            avg_ingest_latency_ms=1.5,
            avg_store_latency_ms=2.5,
            discovery_latency_ms=38.0,
            registry_discovery_live=True,
            process_rss_mb=170.0,
            uptime_s=300.0,
            last_signal_age_s=0.5,
            last_store_age_s=0.7,
            synthetic_feed_mode=False,
            failed_solves=0,
            rejected_groups=1,
            clock_rejected_groups=2,
            clock_synchronized_receivers=4,
            max_clock_uncertainty_ns=100.0,
        )
    client = app.test_client()

    health = client.get("/api/health").get_json()
    readiness = client.get("/api/readiness").get_json()
    mode = client.get("/api/system/mode").get_json()

    assert health["runtime"]["telemetry_source"] == "database"
    assert health["runtime"]["telemetry_fresh"] is True
    assert health["runtime"]["avg_ingest_latency_ms"] == 1.5
    assert health["runtime"]["avg_store_latency_ms"] == 2.5
    assert health["runtime"]["process_rss_mb"] == 170.0
    assert readiness["dimensions"]["reliability"]["active_receivers"] == 4
    assert readiness["dimensions"]["reliability"]["signal_fresh"] is True
    assert readiness["dimensions"]["clock"]["ready"] is True
    assert readiness["dimensions"]["clock"]["rejected_groups"] == 2
    assert mode["runtime_status"] == "active"
    assert mode["mode"] == "live"
    assert mode["registry_discovery_live"] is True
    assert mode["benchmarkable_output"] is True


def test_public_pipeline_and_metrics_evidence_endpoints(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        FOURDSKY_TRANSPORT="command-jsonl",
        SIMULATE_IF_UNAVAILABLE="false",
        RECEIVER_REGISTRY_TYPE_HASH="0x" + "12" * 32,
    )
    app = module.create_app()
    _seed_api_db(module, app)
    with app.app_context():
        module.get_db().store_statistics(
            total_signals=120,
            total_positions=12,
            successful_solves=11,
            active_aircraft=1,
            active_receivers=4,
            avg_uncertainty=120.5,
            avg_quality_score=0.82,
            avg_latency_ms=3.5,
            avg_ingest_latency_ms=1.5,
            avg_store_latency_ms=2.5,
            discovery_latency_ms=38.0,
            registry_discovery_live=True,
            process_rss_mb=170.0,
            uptime_s=300.0,
            last_signal_age_s=0.5,
            last_store_age_s=0.7,
            synthetic_feed_mode=False,
            failed_solves=1,
            rejected_groups=2,
            clock_synchronized_receivers=4,
            max_clock_uncertainty_ns=100.0,
        )
    client = app.test_client()

    pipeline = client.get("/api/pipeline")
    metrics = client.get("/api/evidence/metrics?hours=24&limit=100")

    assert pipeline.status_code == 200
    pipeline_payload = pipeline.get_json()
    assert pipeline_payload["provenance"]["mode"] == "live"
    assert pipeline_payload["provenance"]["registry_discovery_live"] is True
    assert pipeline_payload["stages"][0]["status"] == "pass"
    assert pipeline_payload["stages"][0]["id"] == "registry"
    assert pipeline_payload["stages"][-1]["id"] == "dashboard"
    assert any(stage["id"] == "ingest" for stage in pipeline_payload["stages"])
    assert any(stage["id"] == "clock" for stage in pipeline_payload["stages"])

    assert metrics.status_code == 200
    metrics_payload = metrics.get_json()
    assert metrics_payload["sample_count"] == 1
    assert metrics_payload["current"]["total_signals"] == 120
    assert metrics_payload["current"]["solve_success_percent"] == 91.67
    assert metrics_payload["history"][0]["process_rss_mb"] == 170.0


def test_public_performance_evidence_artifact(monkeypatch, tmp_path):
    report_path = tmp_path / "performance-latest.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-07-17T12:00:00Z",
                "evidence_status": "local_baseline",
                "provenance": {"environment": "local", "live_data": False},
                "metrics": {"api_latency_ms": {"median": 12.0, "p95": 18.0}},
            }
        ),
        encoding="utf-8",
    )
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        PERFORMANCE_REPORT_PATH=str(report_path),
    )
    app = module.create_app()
    client = app.test_client()

    response = client.get("/api/evidence/performance/latest")

    assert response.status_code == 200
    assert response.get_json()["evidence_status"] == "local_baseline"


def test_evidence_metrics_handles_processor_counter_reset(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    with app.app_context():
        database = module.get_db()
        database.store_statistics(
            total_signals=1000,
            total_positions=100,
            successful_solves=100,
            active_aircraft=2,
            active_receivers=4,
            avg_uncertainty=20.0,
            uptime_s=100.0,
        )
        database.store_statistics(
            total_signals=20,
            total_positions=4,
            successful_solves=4,
            active_aircraft=1,
            active_receivers=4,
            avg_uncertainty=20.0,
            uptime_s=10.0,
        )

    response = app.test_client().get("/api/evidence/metrics?hours=1&limit=2")
    history = response.get_json()["history"]

    assert response.status_code == 200
    assert history[-1]["signals_per_minute"] == 120.0
    assert history[-1]["positions_per_minute"] == 24.0


def test_system_mode_does_not_claim_live_activity_without_processor_telemetry(
    monkeypatch, tmp_path
):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        FOURDSKY_TRANSPORT="command-jsonl",
        SIMULATE_IF_UNAVAILABLE="false",
    )
    app = module.create_app()
    client = app.test_client()

    mode = client.get("/api/system/mode").get_json()

    assert mode["mode"] == "configured_live"
    assert mode["runtime_status"] == "unavailable"
    assert mode["benchmarkable_output"] is False


def test_system_mode_does_not_treat_fallback_capability_as_simulation(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        FOURDSKY_TRANSPORT="command-jsonl",
        SIMULATE_IF_UNAVAILABLE="true",
    )
    app = module.create_app()
    client = app.test_client()

    mode = client.get("/api/system/mode").get_json()

    assert mode["simulation_mode"] is False
    assert mode["mode"] == "configured_live"
    assert mode["synthetic_feed_mode"] is False


def test_system_mode_exposes_strict_production_configuration(monkeypatch, tmp_path):
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        STRICT_PRODUCTION_MODE="true",
        FOURDSKY_TRANSPORT="command-jsonl",
        SIMULATE_IF_UNAVAILABLE="false",
    )
    app = module.create_app()
    client = app.test_client()

    mode = client.get("/api/system/mode").get_json()

    assert mode["strict_production_mode"] is True
    assert mode["startup_guardrail_status"] == "strict_waiting"
    assert mode["configured_transport"] == "command-jsonl"
    assert mode["simulate_if_unavailable"] is False


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


def test_anonymous_history_queries_use_public_plan_limits(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    _seed_api_db(module, app)
    client = app.test_client()

    recent = client.get("/api/positions/recent?seconds=999999999&limit=100")
    denied_recent = client.get("/api/positions/recent?seconds=60&limit=101")
    invalid_recent = client.get("/api/positions/recent?seconds=60&limit=-1")
    denied_track = client.get("/api/aircraft/A1B2C3/track?limit=251")
    track = client.get("/api/aircraft/A1B2C3/track")

    assert recent.status_code == 200
    assert recent.get_json()["time_window_seconds"] == 900
    assert denied_recent.status_code == 403
    assert invalid_recent.status_code == 400
    assert denied_track.status_code == 403
    assert track.status_code == 200


def test_websocket_subscription_requires_stream_entitlement(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    if module.SocketIO is None:
        pytest.skip("Flask-SocketIO is not installed in this environment")
    app = module.create_app()
    commercial = _seed_api_db(module, app)

    client = module.socketio.test_client(app)
    assert client.is_connected()
    client.get_received()

    client.emit(
        "subscribe_aircraft",
        {"aircraft_id": "A1B2C3", "api_key": commercial["public_key"]},
    )
    denied = client.get_received()
    client.emit(
        "subscribe_aircraft",
        {"aircraft_id": "A1B2C3", "api_key": commercial["premium_key"]},
    )
    subscribed = client.get_received()
    client.disconnect()

    assert denied[0]["name"] == "subscription_response"
    assert denied[0]["args"][0]["status"] == "denied"
    assert subscribed[0]["name"] == "subscription_response"
    assert subscribed[0]["args"][0]["status"] == "subscribed"


@pytest.mark.parametrize(
    ("starts_offset", "ends_offset", "expected_status"),
    [
        (-3600, 3600, "subscribed"),
        (3600, 7200, "denied"),
        (-7200, -3600, "denied"),
    ],
)
def test_websocket_subscription_enforces_entitlement_window(
    monkeypatch, tmp_path, starts_offset, ends_offset, expected_status
):
    module = _load_api_module(monkeypatch, tmp_path)
    if module.SocketIO is None:
        pytest.skip("Flask-SocketIO is not installed in this environment")
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    now = time.time()

    with app.app_context():
        db = module.get_db()
        db.conn.execute(
            "DELETE FROM entitlements WHERE account_id = ?", (commercial["account_id"],)
        )
        db.conn.commit()
        db.create_entitlement(
            account_id=commercial["account_id"],
            entitlement_code="live_stream",
            starts_at=datetime.fromtimestamp(now + starts_offset, tz=timezone.utc).isoformat(),
            ends_at=datetime.fromtimestamp(now + ends_offset, tz=timezone.utc).isoformat(),
        )

    client = module.socketio.test_client(app)
    client.get_received()
    client.emit(
        "subscribe_aircraft",
        {"aircraft_id": "A1B2C3", "api_key": commercial["premium_key"]},
    )
    response = client.get_received()
    client.disconnect()

    assert response[0]["name"] == "subscription_response"
    assert response[0]["args"][0]["status"] == expected_status


def test_malformed_entitlement_window_fails_closed(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    if module.SocketIO is None:
        pytest.skip("Flask-SocketIO is not installed in this environment")
    app = module.create_app()
    commercial = _seed_api_db(module, app)

    with app.app_context():
        db = module.get_db()
        db.conn.execute(
            "DELETE FROM entitlements WHERE account_id = ?", (commercial["account_id"],)
        )
        db.conn.commit()
        db.create_entitlement(
            account_id=commercial["account_id"],
            entitlement_code="live_stream",
            starts_at="not-a-timestamp",
        )

    client = module.socketio.test_client(app)
    client.get_received()
    client.emit(
        "subscribe_aircraft",
        {"aircraft_id": "A1B2C3", "api_key": commercial["premium_key"]},
    )
    response = client.get_received()
    client.disconnect()

    assert response[0]["args"][0]["status"] == "denied"


def test_position_updates_only_reach_entitled_subscribers(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    if module.SocketIO is None:
        pytest.skip("Flask-SocketIO is not installed in this environment")
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    anonymous = module.socketio.test_client(app)
    subscribed = module.socketio.test_client(app)
    anonymous.get_received()
    subscribed.get_received()

    subscribed.emit(
        "subscribe_aircraft",
        {"aircraft_id": "A1B2C3", "api_key": commercial["premium_key"]},
    )
    subscribed.get_received()
    with app.app_context():
        position = module.get_db().get_latest_position()
        module.broadcast_position_update(
            position.aircraft_id, module._build_position_payload(position)
        )

    assert anonymous.get_received() == []
    updates = subscribed.get_received()
    assert [event["name"] for event in updates] == ["position_update"]
    assert updates[0]["args"][0]["aircraft_id"] == "A1B2C3"
    anonymous.disconnect()
    subscribed.disconnect()


def test_broadcast_position_update_includes_receiver_ids(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    _seed_api_db(module, app)

    emitted = []

    class _FakeSocket:
        def emit(self, event, payload, room=None):
            emitted.append((event, payload, room))

    module.socketio = _FakeSocket()

    with app.app_context():
        position = module.get_db().get_latest_position()
        payload = module._build_position_payload(position)
        module.broadcast_position_update(position.aircraft_id, payload)

    assert emitted[0][0] == "position_update"
    assert emitted[0][1]["aircraft_id"] == "A1B2C3"
    assert emitted[0][1]["position"]["correlation"]["receiver_ids"] == [
        "RECV_NYC_001",
        "RECV_BOS_001",
        "RECV_PHL_001",
        "RECV_DC_001",
    ]
    assert emitted[0][2] == "A1B2C3"


def test_statistics_exposes_operational_metrics(monkeypatch, tmp_path):
    module = _load_api_module(monkeypatch, tmp_path)
    app = module.create_app()
    commercial = _seed_api_db(module, app)
    client = app.test_client()

    unauthorized = client.get(
        "/api/statistics?hours=24", headers={"X-API-Key": commercial["public_key"]}
    )
    response = client.get(
        "/api/statistics?hours=24", headers={"X-API-Key": commercial["premium_key"]}
    )

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
    assert payload["external_benchmark"]["available"] is False


def test_api_publishes_valid_benchmark_artifact(monkeypatch, tmp_path):
    report_path = tmp_path / "latest.json"
    report = {
        "schema_version": 1,
        "generated_at": "2026-07-16T12:00:00Z",
        "evidence_status": "publishable",
        "provenance": {"benchmarkable": True},
        "sample": {"matched_records": 10},
        "accuracy": {"horizontal_error_median_m": 42.0},
        "freshness": {"end_to_store_age_p95_ms": 180.0},
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        BENCHMARK_REPORT_PATH=str(report_path),
    )
    app = module.create_app()
    client = app.test_client()

    response = client.get("/api/benchmark/latest")
    readiness = client.get("/api/readiness")

    assert response.status_code == 200
    assert response.get_json()["provenance"]["benchmarkable"] is True
    assert readiness.get_json()["external_benchmark"]["publishable"] is True


def test_api_rejects_malformed_benchmark_artifact(monkeypatch, tmp_path):
    report_path = tmp_path / "latest.json"
    report_path.write_text('{"schema_version": 1}', encoding="utf-8")
    module = _load_api_module(
        monkeypatch,
        tmp_path,
        BENCHMARK_REPORT_PATH=str(report_path),
    )
    app = module.create_app()
    client = app.test_client()

    response = client.get("/api/benchmark/latest")

    assert response.status_code == 503
    assert response.get_json()["available"] is False
    assert response.get_json()["status"] == "invalid"
