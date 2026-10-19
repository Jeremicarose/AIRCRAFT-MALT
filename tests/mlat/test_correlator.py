import time

from mlat_reference.correlation.correlator import RawSignal, SignalCorrelator


def test_correlator_groups_valid_multi_receiver_signals():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)

    correlator.add_signals(
        [
            RawSignal("RCV1", base_time + 0.0000, "8DA1B2C3", 40.0),
            RawSignal("RCV2", base_time + 0.0005, "8DA1B2C3", 41.0),
            RawSignal("RCV3", base_time + 0.0010, "8DA1B2C3", 42.0),
            RawSignal("RCV4", base_time + 0.0015, "8DA1B2C3", 43.0),
        ]
    )

    groups = correlator.correlate()

    assert len(groups) == 1
    assert groups[0].message == "8DA1B2C3"
    assert len(groups[0].signals) == 4
    assert groups[0].time_span <= 0.005
    assert groups[0].quality is not None
    assert 0.0 <= groups[0].quality.quality_score <= 1.0
    assert groups[0].quality.quality_bucket in {"poor", "fair", "good", "excellent"}
    assert groups[0].quality.receiver_count == 4


def test_correlator_rejects_duplicate_receiver_clusters():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)

    correlator.add_signals(
        [
            RawSignal("RCV1", base_time + 0.0000, "8DDEADBE", 40.0),
            RawSignal("RCV1", base_time + 0.0005, "8DDEADBE", 41.0),
            RawSignal("RCV2", base_time + 0.0010, "8DDEADBE", 42.0),
            RawSignal("RCV3", base_time + 0.0015, "8DDEADBE", 43.0),
        ]
    )

    assert correlator.correlate() == []


def test_correlator_does_not_repeat_processed_groups():
    base_time = time.time()
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)
    correlator.add_signals(
        [
            RawSignal("RCV1", base_time + 0.0000, "8DABCDEF", 40.0),
            RawSignal("RCV2", base_time + 0.0005, "8DABCDEF", 41.0),
            RawSignal("RCV3", base_time + 0.0010, "8DABCDEF", 42.0),
            RawSignal("RCV4", base_time + 0.0015, "8DABCDEF", 43.0),
        ]
    )

    first_groups = correlator.correlate()
    second_groups = correlator.correlate()

    assert len(first_groups) == 1
    assert second_groups == []


def test_correlator_uses_integer_nanoseconds_for_epoch_time_spans():
    base_time = 1_700_000_000.0
    base_time_ns = 1_700_000_000_000_000_000
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)
    correlator.add_signals(
        [
            RawSignal("RCV1", base_time, "8DPRECISE", timestamp_ns=base_time_ns),
            RawSignal("RCV2", base_time, "8DPRECISE", timestamp_ns=base_time_ns + 500),
            RawSignal("RCV3", base_time, "8DPRECISE", timestamp_ns=base_time_ns + 1_000),
            RawSignal("RCV4", base_time, "8DPRECISE", timestamp_ns=base_time_ns + 1_500),
        ]
    )

    groups = correlator.correlate()

    assert len(groups) == 1
    assert groups[0].time_span == 0.0000015


def test_deduplication_expires_with_retained_observations():
    correlator = SignalCorrelator()
    for event in range(1000):
        correlator.add_signals([RawSignal(str(i), event + 1.0, str(event)) for i in range(4)])
        assert len(correlator.correlate()) == 1
        assert correlator.correlate() == []
    assert len(correlator.processed_groups) <= 3


def test_exact_duplicate_observation_does_not_poison_valid_group():
    correlator = SignalCorrelator()
    signals = [
        RawSignal(str(i), 100.0, "frame", timestamp_ns=100_000_000_000 + i) for i in range(4)
    ]
    correlator.add_signals(signals + [signals[0]])
    groups = correlator.correlate()
    assert len(groups) == 1
    assert len(groups[0].signals) == 4


def test_conflicting_timestamps_from_one_receiver_are_not_silently_chosen():
    correlator = SignalCorrelator()
    signals = [
        RawSignal(str(i), 100.0, "frame", timestamp_ns=100_000_000_000 + i) for i in range(4)
    ]
    signals.append(RawSignal("0", 100.0, "frame", timestamp_ns=100_000_000_010))
    correlator.add_signals(signals)
    assert correlator.correlate() == []


def test_buffer_is_bounded_even_when_timestamps_never_advance():
    correlator = SignalCorrelator(max_buffer_signals=100)
    for i in range(1000):
        correlator.add_signal(RawSignal("one-receiver", 1.0, str(i)))
    assert len(correlator.signal_buffer) == 100
    assert correlator.dropped_signals == 900


def test_expiring_first_receiver_does_not_resolve_same_transmission_twice():
    correlator = SignalCorrelator(buffer_duration=2)
    signals = [RawSignal(str(i), 100 + i * 0.0001, "original") for i in range(5)]
    correlator.add_signals(signals)
    assert len(correlator.correlate()) == 1
    correlator.add_signal(RawSignal("other", 102.00005, "new"))
    assert correlator.correlate() == []
