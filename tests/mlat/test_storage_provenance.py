import time

import pytest

from mlat_reference.database.database import MLATDatabase


def store(db, provenance="UNKNOWN", timestamp=None):
    return db.store_position(
        aircraft_id="ABCDEF",
        timestamp=timestamp or time.time(),
        latitude=1,
        longitude=36,
        altitude=9000,
        uncertainty=10,
        num_receivers=4,
        receiver_ids=["a", "b", "c", "d"],
        data_provenance=provenance,
        source_id="test",
        timestamp_ns=1_700_000_000_123_456_789,
        receiver_geometry=[{"receiver_id": "a", "latitude": 1, "longitude": 36, "altitude_m": 0}],
    )


def test_separate_memory_connections_each_get_schema():
    for _ in range(2):
        db = MLATDatabase(":memory:")
        db.connect()
        try:
            assert db.get_receivers() == []
        finally:
            db.close()


def test_provenance_and_precise_time_survive_restart(tmp_path):
    path = str(tmp_path / "positions.db")
    db = MLATDatabase(path)
    db.connect()
    row_id = store(db, "SYNTHETIC")
    db.close()
    reopened = MLATDatabase(path)
    reopened.connect()
    try:
        row = reopened.get_position_by_id(row_id)
        assert row.data_provenance == "SYNTHETIC"
        assert row.timestamp_ns == "1700000000123456789"
        assert row.source_id == "test"
        assert '"receiver_id": "a"' in row.receiver_geometry
    finally:
        reopened.close()


def test_runtime_database_cannot_switch_from_live_to_replay(tmp_path):
    db = MLATDatabase(str(tmp_path / "positions.db"))
    db.connect()
    try:
        db.bind_runtime_provenance("LIVE", "receiver-feeds")
        with pytest.raises(ValueError, match="separate database"):
            db.bind_runtime_provenance("HISTORICAL_REPLAY", "historical-data")
    finally:
        db.close()


def test_simulation_retention_preserves_live_and_unknown_rows(tmp_path):
    db = MLATDatabase(str(tmp_path / "positions.db"))
    db.connect()
    try:
        old = time.time() - 172800
        live = store(db, "LIVE", old)
        unknown = store(db, "UNKNOWN", old + 1)
        synthetic = store(db, "SYNTHETIC", old + 2)
        db.cleanup_simulation_data(position_hours=24)
        assert db.get_position_by_id(live) is not None
        assert db.get_position_by_id(unknown) is not None
        assert db.get_position_by_id(synthetic) is None
    finally:
        db.close()


def test_identical_time_from_another_source_cannot_overwrite_live(tmp_path):
    db = MLATDatabase(str(tmp_path / "positions.db"))
    db.connect()
    try:
        timestamp = time.time()
        row_id = store(db, "LIVE", timestamp)
        with pytest.raises(ValueError, match="provenance"):
            store(db, "SYNTHETIC", timestamp)
        assert db.get_position_by_id(row_id).data_provenance == "LIVE"
    finally:
        db.close()


def test_notification_queue_is_bounded_without_a_subscriber(tmp_path):
    db = MLATDatabase(str(tmp_path / "positions.db"))
    for position_id in range(10000):
        db.publish_position_event(position_id)
    assert db.get_or_create_position_queue().qsize() <= 1024
