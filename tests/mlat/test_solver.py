import numpy as np

from mlat_reference.demo import get_demo_scenario, scenario_aircraft_states
from mlat_reference.solver.robust import (
    SPEED_OF_LIGHT,
    ReceiverPosition,
    SignalObservation,
    RobustMLATSolver,
)


def build_known_position_observations(*, include_timestamp_ns: bool = True):
    target = ReceiverPosition(40.75, -73.90, 9_000.0, "TARGET")
    receivers = [
        ReceiverPosition(40.55, -74.15, 20.0, "R1"),
        ReceiverPosition(40.55, -73.65, 25.0, "R2"),
        ReceiverPosition(40.95, -74.15, 15.0, "R3"),
        ReceiverPosition(40.95, -73.65, 30.0, "R4"),
        ReceiverPosition(40.75, -74.30, 10.0, "R5"),
        ReceiverPosition(40.75, -73.50, 12.0, "R6"),
    ]
    transmit_time_ns = 1_700_000_000_000_000_000
    target_ecef = target.to_ecef()
    observations = []
    for receiver in receivers:
        travel_time_ns = round(
            np.linalg.norm(target_ecef - receiver.to_ecef()) * 1_000_000_000 / SPEED_OF_LIGHT
        )
        arrival_time_ns = transmit_time_ns + travel_time_ns
        observations.append(
            SignalObservation(
                receiver.receiver_id,
                arrival_time_ns / 1_000_000_000,
                "8DABCDEF202CC371C32CE0576098",
                receiver,
                timestamp_ns=arrival_time_ns if include_timestamp_ns else None,
            )
        )
    return target, observations


def test_ecef_roundtrip_is_stable():
    receiver = ReceiverPosition(40.7128, -74.0060, 10.0, "NYC")
    solver = RobustMLATSolver()

    ecef = receiver.to_ecef()
    latitude, longitude, altitude = solver._ecef_to_lla(ecef)

    assert abs(latitude - receiver.latitude) < 1e-6
    assert abs(longitude - receiver.longitude) < 1e-6
    assert abs(altitude - receiver.altitude) < 1e-3


def test_robust_solver_rejects_too_few_receivers():
    observations = [
        SignalObservation(
            "NYC",
            1_700_000_000.0,
            "MSG",
            ReceiverPosition(40.7128, -74.0060, 10, "NYC"),
        ),
        SignalObservation(
            "BOS",
            1_700_000_000.001,
            "MSG",
            ReceiverPosition(42.3601, -71.0589, 20, "BOS"),
        ),
        SignalObservation(
            "PHL",
            1_700_000_000.002,
            "MSG",
            ReceiverPosition(39.9526, -75.1652, 15, "PHL"),
        ),
    ]

    solver = RobustMLATSolver(min_receivers=4)
    assert solver.solve_position(observations) is None


def test_robust_solver_rejects_duplicate_receivers():
    receiver = ReceiverPosition(40.7128, -74.0060, 10, "NYC")
    observations = [
        SignalObservation("NYC", 1_700_000_000.0, "MSG", receiver),
        SignalObservation("NYC", 1_700_000_000.001, "MSG", receiver),
        SignalObservation(
            "BOS", 1_700_000_000.002, "MSG", ReceiverPosition(42.3601, -71.0589, 20, "BOS")
        ),
        SignalObservation(
            "PHL", 1_700_000_000.003, "MSG", ReceiverPosition(39.9526, -75.1652, 15, "PHL")
        ),
    ]

    solver = RobustMLATSolver(min_receivers=4)
    assert solver.solve_position(observations) is None


def test_quality_normalization_returns_shared_contract():
    solver = RobustMLATSolver(min_receivers=4)

    quality_score, quality_bucket = solver._normalize_quality(
        uncertainty=120.0,
        residual=18.0,
        iterations=6,
        receiver_count=5,
        correlation_time_span_s=0.0015,
    )

    assert 0.0 <= quality_score <= 1.0
    assert quality_bucket in {"poor", "fair", "good", "excellent"}
    assert quality_score > 0.5


def test_robust_solver_recovers_exact_known_position():
    target, observations = build_known_position_observations()

    position = RobustMLATSolver(min_receivers=4).solve_position(observations)

    assert position is not None
    solved_ecef = ReceiverPosition(
        position.latitude,
        position.longitude,
        position.altitude,
        "SOLVED",
    ).to_ecef()
    assert np.linalg.norm(solved_ecef - target.to_ecef()) < 10.0
    assert position.solver_method == "robust_mlat"
    assert position.solver_residual_m < 1.0


def test_robust_solver_recovers_exact_position_with_four_receivers():
    target, observations = build_known_position_observations()
    target_ecef = target.to_ecef()
    four_receiver_observations = []
    for observation in observations[:4]:
        relative_arrival_s = (
            np.linalg.norm(target_ecef - observation.receiver_position.to_ecef()) / SPEED_OF_LIGHT
        )
        four_receiver_observations.append(
            SignalObservation(
                observation.receiver_id,
                relative_arrival_s,
                observation.signal_data,
                observation.receiver_position,
            )
        )

    position = RobustMLATSolver(min_receivers=4).solve_position(four_receiver_observations)

    assert position is not None
    solved_ecef = ReceiverPosition(
        position.latitude,
        position.longitude,
        position.altitude,
        "SOLVED",
    ).to_ecef()
    assert np.linalg.norm(solved_ecef - target_ecef) < 1.0


def test_solver_recovers_replay_scenario_positions_across_receiver_footprint():
    scenario = get_demo_scenario("northeast-corridor")
    solver = RobustMLATSolver(min_receivers=4)
    receiver_positions = [
        ReceiverPosition(
            receiver.latitude,
            receiver.longitude,
            receiver.altitude,
            receiver.receiver_id,
        )
        for receiver in scenario.receivers
    ]

    for sample_time in (0, 90, 180, 270):
        for aircraft in scenario_aircraft_states(sample_time, scenario.slug):
            target = ReceiverPosition(
                float(aircraft["latitude"]),
                float(aircraft["longitude"]),
                float(aircraft["altitude"]),
                "TARGET",
            )
            target_ecef = target.to_ecef()
            transmit_time_ns = 1_700_000_000_000_000_000 + sample_time * 1_000_000_000
            observations = []
            for receiver in receiver_positions:
                arrival_time_ns = transmit_time_ns + round(
                    np.linalg.norm(target_ecef - receiver.to_ecef())
                    * 1_000_000_000
                    / SPEED_OF_LIGHT
                )
                observations.append(
                    SignalObservation(
                        receiver.receiver_id,
                        arrival_time_ns / 1_000_000_000,
                        f"8D{aircraft['icao']}",
                        receiver,
                        timestamp_ns=arrival_time_ns,
                    )
                )

            position = solver.solve_position(observations)

            assert position is not None, (sample_time, aircraft["icao"])
            solved_ecef = ReceiverPosition(
                position.latitude,
                position.longitude,
                position.altitude,
                "SOLVED",
            ).to_ecef()
            assert np.linalg.norm(solved_ecef - target_ecef) < 50.0


def test_solver_rejects_epoch_float_timestamps_without_precision_metadata():
    _target, observations = build_known_position_observations(include_timestamp_ns=False)

    assert RobustMLATSolver(min_receivers=4).solve_position(observations) is None
