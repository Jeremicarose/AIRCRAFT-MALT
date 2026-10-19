import asyncio
import json
import shlex
import sys
import time

import pytest

from ckb_registry.discovery import ReceiverInfo
from mlat_reference.ingest.feed_transports import (
    BoundWebSocketConnect,
    CommandJsonlFeedTransport,
    WebSocketJsonFeedTransport,
)
from websockets.exceptions import SecurityError


def test_feed_redirects_never_forward_credentials():
    async def run():
        connection = BoundWebSocketConnect(
            "wss://operator.example/feed", extra_headers={"Authorization": "test-secret"}
        )
        with pytest.raises(SecurityError, match="redirects are forbidden"):
            connection.handle_redirect("ws://127.0.0.1:8080/private")

    asyncio.run(run())


def test_allowlisted_secondary_feed_does_not_receive_primary_credentials(monkeypatch):
    captured = {}

    class Socket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def send(self, value):
            raise AssertionError("primary subscription leaked to secondary URL")

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise asyncio.CancelledError

    def connect(endpoint, **options):
        captured.update(options)
        return Socket()

    monkeypatch.setattr("mlat_reference.ingest.feed_transports.BoundWebSocketConnect", connect)
    transport = WebSocketJsonFeedTransport(
        {},
        "wss://primary.example/feed",
        {"Authorization": "private"},
        "private",
        ("wss://secondary.example/feed",),
    )
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(transport._stream_via_websocket("wss://secondary.example/feed", None))
    assert captured["extra_headers"] == {}


def test_noisy_stubborn_bridge_is_readable_and_stops_within_deadline(tmp_path, caplog):
    child = tmp_path / "bridge.py"
    record = {
        "receiver_id": "R1",
        "timestamp_ns": time.time_ns(),
        "clock_synchronized": True,
        "clock_source": "gps",
        "clock_uncertainty_ns": 10,
        "message": "8D4840D6202CC371C32CE0576098",
    }
    child.write_text(
        "import json, signal, sys, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "sys.stderr.write('private-stderr-value' * 100000)\n"
        "sys.stderr.flush()\n"
        f"print({json.dumps(json.dumps(record))}, flush=True)\n"
        "time.sleep(30)\n"
    )
    receiver = ReceiverInfo("R1", 1, 36, 0, "online", 0, ["mode-s"], "", "")
    transport = CommandJsonlFeedTransport(
        {"R1": receiver}, f"{shlex.quote(sys.executable)} {shlex.quote(str(child))}"
    )

    async def run():
        received = asyncio.Event()

        async def callback(*args, **kwargs):
            received.set()

        task = asyncio.create_task(transport._stream_via_command(callback))
        try:
            await asyncio.wait_for(received.wait(), timeout=5)
        finally:
            started = time.monotonic()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=5)
            assert time.monotonic() - started < 5

    asyncio.run(run())
    assert "private-stderr-value" not in caplog.text
