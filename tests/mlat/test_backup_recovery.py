import os
import sqlite3

import pytest

from mlat_reference.database.backup import copy_database
from mlat_reference.database.database import MLATDatabase
from test_storage_provenance import store


def test_backup_includes_committed_wal_and_restore_preserves_identity_and_provenance(tmp_path):
    source = tmp_path / "active.db"
    db = MLATDatabase(str(source))
    db.connect()
    db.bind_runtime_provenance("LIVE", "receiver-feeds")
    first_id = store(db, "LIVE")
    backup = tmp_path / "backup.db"
    try:
        assert source.with_name(source.name + "-wal").stat().st_size > 0
        report = copy_database(source, backup)
        assert report["integrity"] == "ok"
        if os.name != "nt":
            assert backup.stat().st_mode & 0o777 == 0o600
        restored_path = tmp_path / "restored.db"
        copy_database(backup, restored_path)
        restored = MLATDatabase(str(restored_path))
        restored.connect()
        try:
            position = restored.get_position_by_id(first_id)
            assert position.data_provenance == "LIVE"
            assert position.timestamp_ns == "1700000000123456789"
            assert restored.get_runtime_context()["data_provenance"] == "LIVE"
            with pytest.raises(ValueError, match="separate database"):
                restored.bind_runtime_provenance("SYNTHETIC", "test")
            assert store(restored, "LIVE") > first_id
        finally:
            restored.close()
    finally:
        db.close()


def test_backup_does_not_overwrite_destination_or_create_missing_source(tmp_path):
    existing = tmp_path / "existing.db"
    existing.write_bytes(b"preserve me")
    with pytest.raises(FileNotFoundError):
        copy_database(tmp_path / "missing.db", existing)
    assert not (tmp_path / "missing.db").exists()
    assert existing.read_bytes() == b"preserve me"
    with pytest.raises(FileExistsError):
        copy_database(existing, existing)


def test_invalid_backup_does_not_leave_a_false_success_file(tmp_path):
    source = tmp_path / "not-mlat.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE unrelated(value TEXT)")
    destination = tmp_path / "backup.db"
    with pytest.raises(ValueError, match="not an MLAT"):
        copy_database(source, destination)
    assert not destination.exists()


def test_schema_upgrade_rollback_preserves_legacy_rows(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE positions (id INTEGER PRIMARY KEY AUTOINCREMENT, aircraft_id TEXT, timestamp REAL, latitude REAL, longitude REAL, altitude REAL, uncertainty REAL, num_receivers INTEGER, receiver_ids TEXT, residual REAL, quality_score REAL DEFAULT 0, quality_bucket TEXT DEFAULT 'poor', solver_method TEXT DEFAULT 'unknown', solver_residual_m REAL DEFAULT 0, solver_iterations INTEGER DEFAULT 0, correlation_time_span_s REAL DEFAULT 0, receiver_count INTEGER DEFAULT 0, created_at TEXT, UNIQUE(aircraft_id, timestamp))"
        )
        connection.execute(
            "INSERT INTO positions(aircraft_id, timestamp, latitude, longitude, altitude, uncertainty, num_receivers, receiver_ids, residual, created_at) VALUES ('ABCDEF', 123, 1, 36, 1000, 100, 4, '[]', 0, 'legacy')"
        )
    db = MLATDatabase(str(path))
    db.connect(initialize_schema=False)
    try:
        db.conn.set_authorizer(
            lambda action, table, *args: (
                sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_DROP_TABLE and table == "positions_legacy"
                else sqlite3.SQLITE_OK
            )
        )
        with pytest.raises(sqlite3.DatabaseError):
            db._ensure_schema()
        db.conn.set_authorizer(None)
        assert db.conn.execute("SELECT aircraft_id FROM positions").fetchone()[0] == "ABCDEF"
        assert "data_provenance" not in {
            row[1] for row in db.conn.execute("PRAGMA table_info(positions)")
        }
        db._ensure_schema()
        assert db.get_position_by_id(1).data_provenance == "UNKNOWN"
        assert db.conn.execute("PRAGMA user_version").fetchone()[0] == 2
    finally:
        db.close()
