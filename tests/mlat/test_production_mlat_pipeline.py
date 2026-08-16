import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from mlat_reference.correlation.correlator import CorrelatedSignalGroup, RawSignal
from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.runtime import ProductionMLATSystem
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
