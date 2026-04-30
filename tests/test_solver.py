from mlat.robust_solver import ReceiverPosition, SignalObservation, RobustMLATSolver


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
        SignalObservation("BOS", 1_700_000_000.002, "MSG", ReceiverPosition(42.3601, -71.0589, 20, "BOS")),
        SignalObservation("PHL", 1_700_000_000.003, "MSG", ReceiverPosition(39.9526, -75.1652, 15, "PHL")),
    ]

    solver = RobustMLATSolver(min_receivers=4)
    assert solver.solve_position(observations) is None
