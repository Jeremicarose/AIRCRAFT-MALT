"""Regression cases for the actual untrusted feed and runtime boundaries."""

import asyncio
import json
import time
from unittest.mock import AsyncMock

import pytest

from ckb_registry.discovery import ReceiverInfo
from mlat_reference.ingest.feed_transports import JsonFeedParsingMixin, WebSocketJsonFeedTransport
from mlat_reference.ingest.client import NetworkConfig
from mlat_reference.runtime import ProductionMLATSystem
from mlat_reference.solver.robust import ReceiverPosition

FRAME = "8D4840D6202CC371C32CE0576098"


def test_unassigned_feed_identity_is_not_copied_into_logs(caplog):
    secret = "wss://private.invalid/feed?token=DO-NOT-LOG"
    parser = JsonFeedParsingMixin()
    assert (
        parser.normalize_feed_records(record(receiver_id=secret), allowed_receiver_ids={"R1"}) == []
    )
    assert secret not in caplog.text


def record(**changes):
    return {
        "receiver_id": "R1",
        "timestamp_ns": time.time_ns(),
        "clock_synchronized": True,
        "clock_source": "gps",
        "clock_uncertainty_ns": 50,
        "message": FRAME,
        **changes,
    }


@pytest.mark.parametrize("value", [123.75, True, -1, 0, "1e18", "12.0", 2**64, float("inf")])
def test_feed_rejects_invalid_integer_timestamp(value):
    assert JsonFeedParsingMixin().normalize_feed_records(record(timestamp_ns=value)) == []


@pytest.mark.parametrize("message", ["garbage", "8DABCDEF", {}, "F" * 5000, FRAME[:-1] + "9"])
def test_feed_rejects_invalid_mode_s_frame(message):
    assert JsonFeedParsingMixin().normalize_feed_records(record(message=message)) == []


def test_feed_does_not_replace_missing_timestamp_with_current_time():
    observation = record()
    observation.pop("timestamp_ns")
    assert JsonFeedParsingMixin().normalize_feed_records(observation) == []


def test_duplicate_json_keys_and_oversized_payload_never_reach_callback():
    callback = AsyncMock()
    parser = JsonFeedParsingMixin()
    payload = json.dumps(record())[:-1] + ', "receiver_id":"R2"}'
    asyncio.run(parser.dispatch_feed_payload(payload, callback))
    asyncio.run(parser.dispatch_feed_payload(" " * 1_048_577, callback))
    asyncio.run(parser.dispatch_feed_payload("[" * 2000 + "]" * 2000, callback))
    callback.assert_not_awaited()


def test_registry_endpoint_requires_explicit_operator_permission():
    receiver = ReceiverInfo("R1", 1, 36, 10, "online", 0, ["mode-s", "mlat"], "", "")
    receiver.stream_endpoint = "ws://127.0.0.1:12345/private"
    transport = WebSocketJsonFeedTransport(
        {"R1": receiver},
        endpoint="wss://trusted.example/feed",
        auth_headers={"Authorization": "private-token"},
        subscribe_message="private-subscription",
    )

    async def run():
        with pytest.raises(ValueError, match="allowlist"):
            transport.create_tasks(AsyncMock())

    asyncio.run(run())


def test_future_observation_cannot_evict_valid_runtime_observations(tmp_path):
    system = ProductionMLATSystem(
        NetworkConfig(fourdsky_transport="command-jsonl"), str(tmp_path / "test.db")
    )
    system.database.connect()
    system.receiver_positions["R1"] = ReceiverPosition(1, 36, 10, "R1")

    async def send(timestamp_ns):
        await system.handle_incoming_signal(
            "R1",
            timestamp_ns / 1e9,
            FRAME,
            timestamp_ns=timestamp_ns,
            clock_synchronized=True,
            clock_source="gps",
            clock_uncertainty_ns=50,
        )

    now = time.time_ns()
    try:
        asyncio.run(send(now))
        asyncio.run(send(now + 3600 * 1_000_000_000))
        assert len(system.correlator.signal_buffer) == 1
        assert system.correlator.signal_buffer[0].timestamp_ns == now
    finally:
        system.database.close()
