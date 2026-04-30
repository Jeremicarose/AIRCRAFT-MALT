import time

from correlation.correlator import RawSignal, SignalCorrelator


def test_correlator_groups_valid_multi_receiver_signals():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)

    correlator.add_signals([
        RawSignal("RCV1", base_time + 0.0000, "8DA1B2C3", 40.0),
        RawSignal("RCV2", base_time + 0.0005, "8DA1B2C3", 41.0),
        RawSignal("RCV3", base_time + 0.0010, "8DA1B2C3", 42.0),
        RawSignal("RCV4", base_time + 0.0015, "8DA1B2C3", 43.0),
    ])

    groups = correlator.correlate()

    assert len(groups) == 1
    assert groups[0].message == "8DA1B2C3"
    assert len(groups[0].signals) == 4
    assert groups[0].time_span <= 0.005


def test_correlator_rejects_duplicate_receiver_clusters():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)

    correlator.add_signals([
        RawSignal("RCV1", base_time + 0.0000, "8DDEADBE", 40.0),
        RawSignal("RCV1", base_time + 0.0005, "8DDEADBE", 41.0),
        RawSignal("RCV2", base_time + 0.0010, "8DDEADBE", 42.0),
        RawSignal("RCV3", base_time + 0.0015, "8DDEADBE", 43.0),
    ])

    assert correlator.correlate() == []


def test_correlator_does_not_repeat_processed_groups():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)
    correlator.add_signals([
        RawSignal("RCV1", base_time + 0.0000, "8DABCDEF", 40.0),
        RawSignal("RCV2", base_time + 0.0005, "8DABCDEF", 41.0),
        RawSignal("RCV3", base_time + 0.0010, "8DABCDEF", 42.0),
        RawSignal("RCV4", base_time + 0.0015, "8DABCDEF", 43.0),
    ])

    first_groups = correlator.correlate()
    second_groups = correlator.correlate()

    assert len(first_groups) == 1
    assert second_groups == []
