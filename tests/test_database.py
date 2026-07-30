from database.mlat_db import MLATDatabase
import time


def test_database_stores_receivers_and_positions(tmp_path):
    db_path = tmp_path / "mlat.db"
    db = MLATDatabase(str(db_path))
    db.connect()

    db.store_receiver(
        receiver_id="RECV_NYC_001",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
        receiver_label="New York receiver",
        registry_sequence=4,
        owner_lock_args="0xowner",
        registry_out_point='{"index":"0x0","tx_hash":"0xtx"}',
        metadata_hash="0x" + "aa" * 32,
    )

    receivers = db.get_receivers()
    assert len(receivers) == 1
    assert receivers[0].receiver_id == "RECV_NYC_001"
    assert receivers[0].receiver_label == "New York receiver"
    assert receivers[0].registry_sequence == 4
    assert receivers[0].owner_lock_args == "0xowner"

    assert db.touch_receiver("RECV_NYC_001", last_seen=1_700_000_050.0)
    assert db.get_receivers()[0].last_seen == 1_700_000_050.0
    assert not db.touch_receiver("UNKNOWN", last_seen=1_700_000_050.0)

    position_id = db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1_700_000_100.0,
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

    track = db.get_aircraft_track("A1B2C3")
    assert track.num_positions == 1
    assert track.positions[0].id == position_id

    same_position_id = db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1_700_000_100.0,
        latitude=40.76,
        longitude=-73.84,
        altitude=9050.0,
        uncertainty=110.0,
        num_receivers=5,
        receiver_ids=["RECV_NYC_001", "RECV_BOS_001", "RECV_PHL_001", "RECV_DC_001", "RECV_BUF_001"],
        residual=10.0,
        quality_score=0.91,
        quality_bucket="excellent",
        solver_method="robust_mlat",
        solver_residual_m=10.0,
        solver_iterations=5,
        correlation_time_span_s=0.0010,
        receiver_count=5,
    )

    updated_track = db.get_aircraft_track("A1B2C3")
    assert same_position_id == position_id
    assert updated_track.num_positions == 1
    assert updated_track.positions[0].latitude == 40.76
    assert updated_track.positions[0].num_receivers == 5
    assert updated_track.positions[0].quality_score == 0.91
    assert updated_track.positions[0].quality_bucket == "excellent"
    assert updated_track.positions[0].solver_method == "robust_mlat"
    assert updated_track.positions[0].solver_iterations == 5

    positions_after = db.get_positions_after_id(position_id - 1, limit=10)
    assert len(positions_after) == 1
    assert positions_after[0].id == position_id

    db.close()


def test_database_prunes_old_simulation_data(tmp_path):
    db_path = tmp_path / "mlat_retention.db"
    db = MLATDatabase(str(db_path))
    db.connect()

    now = time.time()
    old_timestamp = now - (48 * 3600)
    recent_timestamp = now - 60

    db.store_position(
        aircraft_id="OLD123",
        timestamp=old_timestamp,
        latitude=40.0,
        longitude=-74.0,
        altitude=8000.0,
        uncertainty=150.0,
        num_receivers=4,
        receiver_ids=["R1", "R2", "R3", "R4"],
        residual=0.0,
    )
    db.store_position(
        aircraft_id="NEW123",
        timestamp=recent_timestamp,
        latitude=41.0,
        longitude=-73.0,
        altitude=9000.0,
        uncertainty=120.0,
        num_receivers=4,
        receiver_ids=["R1", "R2", "R3", "R4"],
        residual=0.0,
    )

    db.store_statistics(
        total_signals=10,
        total_positions=2,
        active_aircraft=2,
        active_receivers=4,
        avg_uncertainty=135.0,
    )
    db.conn.execute(
        "UPDATE statistics SET timestamp = ?, created_at = datetime('now', '-10 days') WHERE id = 1",
        (now - (10 * 86400),),
    )
    db.conn.commit()

    db.cleanup_simulation_data(position_hours=24, statistics_days=7)

    positions = db.get_recent_positions(seconds=7 * 86400, limit=10)
    aircraft_ids = {position.aircraft_id for position in positions}
    assert "OLD123" not in aircraft_ids
    assert "NEW123" in aircraft_ids

    stats_rows = db.get_statistics_history(hours=24 * 14)
    assert len(stats_rows) == 0

    db.close()


def test_database_exposes_position_events_and_sqlite_hardening(tmp_path):
    db_path = tmp_path / "mlat_events.db"
    db = MLATDatabase(str(db_path))
    db.connect()

    position_id = db.store_position(
        aircraft_id="EVENT1",
        timestamp=time.time(),
        latitude=40.0,
        longitude=-74.0,
        altitude=8000.0,
        uncertainty=100.0,
        num_receivers=4,
        receiver_ids=["R1", "R2", "R3", "R4"],
        residual=5.0,
    )

    queue = db.get_or_create_position_queue()
    assert queue.get(timeout=1) == position_id

    stats = db.get_database_stats()
    assert stats["journal_mode"].lower() == "wal"
    assert stats["sqlite_single_node_only"] is True
    assert db.get_latest_position().id == position_id

    db.close()


def test_database_supports_commercial_models_and_metering(tmp_path):
    db_path = tmp_path / "mlat_commercial.db"
    db = MLATDatabase(str(db_path))
    db.connect()

    account_id = db.create_account("acme-air", "ops@acme.test")
    public_plan = db.get_plan_by_code("public_demo")
    premium_plan = db.get_plan_by_code("premium")
    assert public_plan is not None
    assert premium_plan is not None

    public_api_key_id = db.create_api_key(
        account_id=account_id,
        key_name="public",
        raw_key="public-key-123",
        plan_id=public_plan.id,
    )
    db.create_entitlement(account_id=account_id, entitlement_code="live_stream")
    auth = db.authenticate_api_key("public-key-123")

    assert auth is not None
    assert auth["api_key_id"] == public_api_key_id
    assert auth["plan_code"] == "public_demo"
    assert any(item["entitlement_code"] == "live_stream" for item in auth["entitlements"])

    db.record_usage_event(
        account_id=account_id,
        api_key_id=public_api_key_id,
        event_type="rest_request",
        resource="recent_positions",
        quantity=2,
        metadata={"limit": 10},
    )
    usage = db.get_usage_summary(account_id)
    assert usage[0]["total_quantity"] == 2

    db.close()


def test_database_returns_latest_processor_statistics(tmp_path):
    db = MLATDatabase(str(tmp_path / "mlat_stats.db"))
    db.connect()
    db.store_statistics(
        total_signals=20,
        total_positions=2,
        successful_solves=1,
        active_aircraft=1,
        active_receivers=4,
        avg_uncertainty=80.0,
        avg_quality_score=0.9,
        avg_latency_ms=4.5,
        avg_ingest_latency_ms=1.2,
        avg_store_latency_ms=2.3,
        discovery_latency_ms=38.0,
        registry_discovery_live=True,
        process_rss_mb=170.0,
        uptime_s=120.0,
        last_signal_age_s=0.8,
        last_store_age_s=1.1,
        synthetic_feed_mode=False,
        failed_solves=1,
        rejected_groups=2,
        clock_rejected_groups=3,
        clock_synchronized_receivers=4,
        max_clock_uncertainty_ns=75.0,
    )

    latest = db.get_latest_statistics()

    assert latest is not None
    assert latest["active_receivers"] == 4
    assert latest["avg_latency_ms"] == 4.5
    assert latest["avg_ingest_latency_ms"] == 1.2
    assert latest["avg_store_latency_ms"] == 2.3
    assert latest["discovery_latency_ms"] == 38.0
    assert latest["registry_discovery_live"] == 1
    assert latest["process_rss_mb"] == 170.0
    assert latest["successful_solves"] == 1
    assert latest["synthetic_feed_mode"] == 0
    assert latest["failed_solves"] == 1
    assert latest["clock_rejected_groups"] == 3
    assert latest["clock_synchronized_receivers"] == 4
    assert latest["max_clock_uncertainty_ns"] == 75.0
    assert len(db.get_statistics_history(hours=1)) == 1
    db.close()
