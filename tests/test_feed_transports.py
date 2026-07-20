import asyncio
import time

from network.ckb_discovery import ReceiverInfo
from network.feed_transports import SimulationFeedTransport


def _receiver(receiver_id: str, latitude: float, longitude: float) -> ReceiverInfo:
    return ReceiverInfo(
        receiver_id=receiver_id,
        latitude=latitude,
        longitude=longitude,
        altitude=20.0,
        status="online",
        last_seen=time.time(),
        capabilities=["mode-s", "mlat"],
        ckb_address="simulation",
        lock_hash="simulation",
    )


def test_simulation_feed_dispatches_scenario_aircraft_to_receivers():
    receivers = {
        "R1": _receiver("R1", 40.7, -74.0),
        "R2": _receiver("R2", 41.0, -73.5),
        "R3": _receiver("R3", 40.2, -75.1),
        "R4": _receiver("R4", 42.0, -71.2),
    }
    transport = SimulationFeedTransport(receivers, scenario_name="northeast-corridor")
    received = []

    class FeedObserved(Exception):
        pass

    async def observe_first_message(receiver_id, timestamp, message):
        received.append((receiver_id, timestamp, message))
        raise FeedObserved

    async def run_once():
        try:
            await transport._simulate_network_traffic(observe_first_message)
        except FeedObserved:
            return

    asyncio.run(run_once())

    assert len(received) == 1
    assert received[0][0] in receivers
    assert received[0][1] > 0
    assert received[0][2].startswith("8DA1B2C3")
