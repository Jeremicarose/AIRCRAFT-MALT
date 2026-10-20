import asyncio
from dataclasses import replace
import sqlite3

from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.runtime import ProductionMLATSystem
from test_production_mlat_pipeline import build_group
from test_solver import build_known_position_observations


def test_coincident_receiver_locations_never_reach_solver(tmp_path):
    _target, observations = build_known_position_observations()
    shared = observations[0].receiver_position
    observations = [
        replace(
            item,
            receiver_position=replace(shared, receiver_id=item.receiver_id),
            timestamp=observations[0].timestamp,
            timestamp_ns=observations[0].timestamp_ns,
        )
        for item in observations
    ]
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"), str(tmp_path / "geometry.db")
    )
    system.database.connect()
    system.receiver_positions = {item.receiver_id: item.receiver_position for item in observations}
    try:
        asyncio.run(system._process_signal_group(build_group(observations, synchronized=True)))
        assert system.stats["successful_solves"] == 0
        assert system.database.get_latest_position() is None
        assert system.rejected_groups == 1
    finally:
        system.database.close()


def test_partial_feed_and_database_failure_recover_without_false_storage_success(tmp_path):
    _target, observations = build_known_position_observations()
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"), str(tmp_path / "recovery.db")
    )
    system.database.connect()
    system.receiver_positions = {item.receiver_id: item.receiver_position for item in observations}
    try:
        asyncio.run(system._process_signal_group(build_group(observations[:3], synchronized=True)))
        assert system.stats["successful_solves"] == 0
        system.database.conn.set_authorizer(
            lambda action, table, *args: (
                sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_INSERT and table == "positions"
                else sqlite3.SQLITE_OK
            )
        )
        asyncio.run(system._process_signal_group(build_group(observations, synchronized=True)))
        assert system.storage_failures == 1
        assert system.last_store_at == 0
        assert system.database.get_latest_position() is None
        system.database.conn.set_authorizer(None)
        asyncio.run(system._process_signal_group(build_group(observations, synchronized=True)))
        assert system.last_store_at > 0
        assert system.last_storage_error is None
        assert system.database.get_latest_position().data_provenance == "SYNTHETIC"
    finally:
        system.database.close()
