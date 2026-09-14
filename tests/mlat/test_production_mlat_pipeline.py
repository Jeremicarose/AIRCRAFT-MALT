import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from mlat_reference.correlation.correlator import CorrelatedSignalGroup, RawSignal
from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.runtime import ProductionMLATSystem
from ckb_registry.discovery import ReceiverInfo
from test_solver import build_known_position_observations


def build_group(observations, *, synchronized: bool):
    signals = [
        RawSignal(
            receiver_id=observation.receiver_id,
            timestamp=observation.timestamp,
            message=observation.signal_data,
            timestamp_ns=observation.timestamp_ns,
            clock_synchronized=synchronized,
            clock_source="synthetic-common-clock" if synchronized else "network-arrival",
            clock_uncertainty_ns=1 if synchronized else None,
        )
        for observation in observations
    ]
    return CorrelatedSignalGroup(
        message=signals[0].message,
        signals=signals,
        first_timestamp=signals[0].timestamp,
        time_span=0.0,
    )


def test_simulation_pipeline_stores_solver_output_not_scenario_truth(tmp_path):
    target, observations = build_known_position_observations()
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.database.connect()
    system.receiver_positions = {
        observation.receiver_id: observation.receiver_position for observation in observations
    }

    try:
        asyncio.run(system._process_signal_group(build_group(observations, synchronized=True)))
        stored = system.database.get_recent_positions(seconds=10_000_000_000, limit=10)
    finally:
        system.database.close()

    assert len(stored) == 1
    assert stored[0].solver_method == "robust_mlat"
    assert abs(stored[0].latitude - target.latitude) < 0.0001
    assert abs(stored[0].longitude - target.longitude) < 0.0001
    assert abs(stored[0].altitude - target.altitude) < 10.0
    assert system.stats["successful_solves"] == 1


def test_live_pipeline_rejects_unsynchronized_receiver_group(tmp_path):
    _target, observations = build_known_position_observations()
    system = ProductionMLATSystem(
        NetworkConfig(
            fourdsky_transport="command-jsonl",
            simulate_if_unavailable=False,
        ),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.database.connect()
    system.receiver_positions = {
        observation.receiver_id: observation.receiver_position for observation in observations
    }
    system.solver = SimpleNamespace(
        solve_position=lambda _observations: (_ for _ in ()).throw(
            AssertionError("unsynchronized observations reached the solver")
        )
    )

    try:
        asyncio.run(system._process_signal_group(build_group(observations, synchronized=False)))
        stored = system.database.get_recent_positions(seconds=10_000_000_000, limit=10)
    finally:
        system.database.close()

    assert stored == []
    assert system.clock_rejected_groups == 1
    assert system.stats["total_positions"] == 0


def test_clock_qualification_rejects_unnamed_source(tmp_path):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="command-jsonl"),
        db_path=str(tmp_path / "mlat.db"),
    )
    signal = RawSignal(
        receiver_id="R1",
        timestamp=1_700_000_000.0,
        message="8DABCDEF",
        timestamp_ns=1_700_000_000_000_000_000,
        clock_synchronized=True,
        clock_source="unknown",
        clock_uncertainty_ns=1.0,
    )

    assert system._signal_clock_is_qualified(signal) is False


def test_registry_refresh_removes_receiver_from_solver_and_inventory(tmp_path):
    identity = "0x" + "a1" * 32
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="command-jsonl"),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.database.connect()
    receiver = ReceiverInfo(
        receiver_id="RECEIVER_A",
        receiver_identity=identity,
        data_source="ckb_registry",
        latitude=1.0,
        longitude=36.0,
        altitude=1_700.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
        ckb_address="0xowner",
        lock_hash="0xlock",
    )
    system.network_client.active_receivers[identity] = receiver
    system._cache_receiver_positions()
    assert system.database.get_receivers()[0].receiver_identity == identity

    system.network_client.active_receivers.clear()
    system._cache_receiver_positions()

    assert identity not in system.receiver_positions
    assert system.database.get_receivers() == []
    before = system.stats["total_signals"]
    asyncio.run(
        system.handle_incoming_signal(
            identity,
            1_700_000_001.0,
            "8DABCDEF",
            timestamp_ns=1_700_000_001_000_000_000,
            clock_synchronized=True,
            clock_source="gps",
            clock_uncertainty_ns=1.0,
        )
    )
    assert system.stats["total_signals"] == before
    system.database.close()


def test_registry_transfer_refresh_updates_running_inventory_owner(monkeypatch, tmp_path):
    identity = "0x" + "b2" * 32
    system = ProductionMLATSystem(
        NetworkConfig(
            receiver_registry_type_hash="0x" + "4" * 64,
            fourdsky_transport="command-jsonl",
        ),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.database.connect()
    owner_a = ReceiverInfo(
        receiver_id="RECEIVER_TRANSFER",
        receiver_identity=identity,
        data_source="ckb_registry",
        latitude=1.0,
        longitude=36.0,
        altitude=1_700.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
        ckb_address="0xowner-a",
        lock_hash="0xlock-a",
        metadata={"sequence": 1},
    )
    owner_b = ReceiverInfo(
        receiver_id="RECEIVER_TRANSFER",
        receiver_identity=identity,
        data_source="ckb_registry",
        latitude=1.0,
        longitude=36.0,
        altitude=1_700.0,
        status="online",
        last_seen=1_700_000_001.0,
        capabilities=["mode-s", "mlat"],
        ckb_address="0xowner-b",
        lock_hash="0xlock-b",
        metadata={"sequence": 2},
    )
    system.network_client.active_receivers[identity] = owner_a
    system._cache_receiver_positions()

    async def refreshed_receivers():
        return [owner_b]

    monkeypatch.setattr(
        system.network_client.peer_discovery,
        "discover_peers",
        refreshed_receivers,
    )

    try:
        assert asyncio.run(system.network_client.refresh_registry_receivers()) is True
        system._cache_receiver_positions()
        stored = system.database.get_receivers()
    finally:
        system.database.close()

    assert len(stored) == 1
    assert stored[0].receiver_identity == identity
    assert stored[0].owner_lock_args == "0xowner-b"
    assert stored[0].registry_sequence == 2


def test_initial_discovery_removes_stale_registry_rows_but_keeps_simulation(tmp_path):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="command-jsonl"),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.database.connect()
    system.database.store_receiver(
        receiver_id="0x" + "d1" * 32,
        receiver_identity="0x" + "d1" * 32,
        data_source="ckb_registry",
        latitude=1.0,
        longitude=36.0,
        altitude=1_700.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
    )
    system.database.store_receiver(
        receiver_id="simulation:RECEIVER_B",
        data_source="simulation",
        latitude=2.0,
        longitude=37.0,
        altitude=1_700.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
    )

    system._cache_receiver_positions()

    assert [row.receiver_id for row in system.database.get_receivers()] == ["simulation:RECEIVER_B"]
    system.database.close()


def test_production_shutdown_is_idempotent(tmp_path):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.is_running = True
    system.network_client.shutdown = AsyncMock()
    system.database.close = Mock()

    async def stop_twice():
        await asyncio.gather(system.stop(), system.stop())

    asyncio.run(stop_twice())

    system.network_client.shutdown.assert_awaited_once()
    system.database.close.assert_called_once()


def test_statistics_loop_does_not_query_database_after_shutdown(tmp_path):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="simulation"),
        db_path=str(tmp_path / "mlat.db"),
    )
    system.is_running = True
    system.database.get_active_aircraft = Mock(
        side_effect=AssertionError("statistics queried the database after shutdown")
    )

    async def stop_during_sleep(_seconds):
        system.is_running = False

    with patch("mlat_reference.runtime.asyncio.sleep", side_effect=stop_during_sleep):
        asyncio.run(system._statistics_loop())

    system.database.get_active_aircraft.assert_not_called()
