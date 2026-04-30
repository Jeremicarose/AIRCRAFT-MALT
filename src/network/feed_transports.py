"""
Feed transport implementations for Mode-S ingestion.

This module separates live and simulated feed adapters from the main
CKB network client so production and demo behavior are explicit.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional
import asyncio
import contextlib
from datetime import datetime
import json
import logging
import math
import random
import time

from network.ckb_discovery import ReceiverInfo


logger = logging.getLogger(__name__)
MessageCallback = Callable[[str, float, str], Awaitable[None]]


class BaseFeedTransport:
    """Base class for feed transports that create async stream tasks."""

    def __init__(self, receivers: Dict[str, ReceiverInfo]):
        self.receivers = receivers

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        """Create the asyncio tasks needed to run the feed transport."""
        raise NotImplementedError


class JsonFeedParsingMixin:
    """Normalize external JSON payloads into MLAT callback records."""

    async def dispatch_feed_payload(
        self,
        raw_payload: str,
        callback: MessageCallback,
        default_receiver_id: Optional[str] = None,
    ):
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.debug("Skipping non-JSON 4DSky payload: %s", raw_payload[:200])
            return

        for record in self.normalize_feed_records(
            payload,
            default_receiver_id=default_receiver_id,
        ):
            await callback(record["receiver_id"], record["timestamp"], record["message"])

    def normalize_feed_records(
        self,
        payload: Any,
        default_receiver_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            records: List[Dict[str, Any]] = []
            for item in payload:
                records.extend(
                    self.normalize_feed_records(
                        item,
                        default_receiver_id=default_receiver_id,
                    )
                )
            return records

        if not isinstance(payload, dict):
            return []

        if "records" in payload and isinstance(payload["records"], list):
            return self.normalize_feed_records(
                payload["records"],
                default_receiver_id=default_receiver_id,
            )

        if "data" in payload and isinstance(payload["data"], (dict, list)):
            nested = self.normalize_feed_records(
                payload["data"],
                default_receiver_id=default_receiver_id,
            )
            if nested:
                return nested

        receiver_id = (
            payload.get("receiver_id")
            or payload.get("receiver")
            or payload.get("sensor_id")
            or payload.get("source")
            or default_receiver_id
        )

        message_value = payload.get("message")
        if isinstance(message_value, dict):
            message_value = (
                message_value.get("hex")
                or message_value.get("raw")
                or message_value.get("frame")
            )

        message = (
            message_value
            or payload.get("hex")
            or payload.get("raw")
            or payload.get("frame")
            or payload.get("payload")
        )

        if not receiver_id or not message:
            return []

        return [
            {
                "receiver_id": str(receiver_id),
                "timestamp": self.parse_timestamp(
                    payload.get("timestamp")
                    or payload.get("time")
                    or payload.get("ts")
                    or payload.get("observed_at")
                ),
                "message": str(message),
            }
        ]

    @staticmethod
    def parse_timestamp(value: Any) -> float:
        if value is None:
            return time.time()

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass

            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                logger.debug("Unsupported 4DSky timestamp format: %s", value)

        return time.time()


class WebSocketJsonFeedTransport(BaseFeedTransport, JsonFeedParsingMixin):
    """Consume JSON payloads from one or more websocket endpoints."""

    def __init__(
        self,
        receivers: Dict[str, ReceiverInfo],
        endpoint: str,
        auth_headers: Dict[str, str],
        subscribe_message: Optional[str],
    ):
        super().__init__(receivers)
        self.endpoint = endpoint
        self.auth_headers = auth_headers
        self.subscribe_message = subscribe_message

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        endpoint_to_receivers: Dict[str, List[str]] = {}
        tasks: List[asyncio.Task] = []

        for receiver_id, receiver in self.receivers.items():
            if receiver.stream_protocol and receiver.stream_protocol not in {
                "websocket-json",
                "simulation",
            }:
                continue

            endpoint = receiver.stream_endpoint or self.endpoint
            if not endpoint:
                continue

            endpoint_to_receivers.setdefault(endpoint, []).append(receiver_id)

        for endpoint, receiver_ids in endpoint_to_receivers.items():
            default_receiver_id = receiver_ids[0] if len(receiver_ids) == 1 else None
            tasks.append(
                asyncio.create_task(
                    self._stream_via_websocket(
                        endpoint=endpoint,
                        callback=callback,
                        default_receiver_id=default_receiver_id,
                    )
                )
            )

        return tasks

    async def _stream_via_websocket(
        self,
        endpoint: str,
        callback: MessageCallback,
        default_receiver_id: Optional[str] = None,
    ):
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed. Run: pip install websockets")
            return

        while True:
            try:
                async with websockets.connect(endpoint, extra_headers=self.auth_headers) as websocket:
                    logger.info("Connected to 4DSky websocket: %s", endpoint)

                    if self.subscribe_message:
                        await websocket.send(self.subscribe_message)

                    async for raw_payload in websocket:
                        await self.dispatch_feed_payload(
                            raw_payload,
                            callback,
                            default_receiver_id=default_receiver_id,
                        )

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("4DSky websocket stream error (%s): %s", endpoint, exc)
                await asyncio.sleep(3)


class CommandJsonlFeedTransport(BaseFeedTransport, JsonFeedParsingMixin):
    """Read newline-delimited JSON messages from a local bridge command."""

    def __init__(self, receivers: Dict[str, ReceiverInfo], command: str):
        super().__init__(receivers)
        self.command = command

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        return [asyncio.create_task(self._stream_via_command(callback))]

    async def _stream_via_command(self, callback: MessageCallback):
        while True:
            process = None
            try:
                process = await asyncio.create_subprocess_shell(
                    self.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                logger.info("Started 4DSky bridge command: %s", self.command)

                assert process.stdout is not None
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    await self.dispatch_feed_payload(line.decode("utf-8"), callback)

                if process.stderr is not None:
                    stderr_output = await process.stderr.read()
                    if stderr_output:
                        logger.warning(
                            "4DSky bridge stderr: %s",
                            stderr_output.decode("utf-8", errors="ignore").strip(),
                        )

            except asyncio.CancelledError:
                if process is not None and process.returncode is None:
                    process.terminate()
                    with contextlib.suppress(ProcessLookupError):
                        await process.wait()
                raise
            except Exception as exc:
                logger.warning("4DSky bridge command failed: %s", exc)
            finally:
                if process is not None and process.returncode is None:
                    process.terminate()
                    with contextlib.suppress(ProcessLookupError):
                        await process.wait()

            await asyncio.sleep(3)


class SimulationFeedTransport(BaseFeedTransport):
    """Generate a shared simulated 4DSky stream for local development."""

    def __init__(self, receivers: Dict[str, ReceiverInfo]):
        super().__init__(receivers)
        self.simulated_aircraft = [
            {
                "icao": "A1B2C3",
                "lat": 40.55,
                "lon": -74.25,
                "alt": 9200.0,
                "heading": 55.0,
                "speed_kmh": 470.0,
            },
            {
                "icao": "D4E5F6",
                "lat": 41.10,
                "lon": -73.40,
                "alt": 8400.0,
                "heading": 225.0,
                "speed_kmh": 510.0,
            },
        ]

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        return [asyncio.create_task(self._simulate_network_traffic(callback))]

    async def _simulate_network_traffic(self, callback: MessageCallback):
        while True:
            for aircraft in self.simulated_aircraft:
                self._advance_aircraft(aircraft, dt_seconds=0.5)

                transmit_time = time.time()
                message = f"8D{aircraft['icao']}202CC371C32CE0576098"
                receiver_ids = list(self.receivers.keys())

                if len(receiver_ids) < 4:
                    await asyncio.sleep(0.5)
                    continue

                if len(receiver_ids) > 4 and random.random() < 0.25:
                    dropped = random.choice(receiver_ids)
                    receiver_ids = [rid for rid in receiver_ids if rid != dropped]

                for receiver_id in receiver_ids:
                    receiver = self.receivers[receiver_id]
                    timestamp = self._calculate_reception_time(
                        aircraft,
                        receiver,
                        transmit_time,
                    )
                    await callback(receiver_id, timestamp, message)

                await asyncio.sleep(0.5)

    @staticmethod
    def _advance_aircraft(aircraft: Dict[str, float], dt_seconds: float):
        speed_ms = aircraft["speed_kmh"] * 1000.0 / 3600.0
        distance_m = speed_ms * dt_seconds

        heading_rad = math.radians(aircraft["heading"])
        dlat = (distance_m * math.cos(heading_rad)) / 111000.0
        lon_scale = max(math.cos(math.radians(aircraft["lat"])), 0.1)
        dlon = (distance_m * math.sin(heading_rad)) / (111000.0 * lon_scale)

        aircraft["lat"] += dlat
        aircraft["lon"] += dlon

        if random.random() < 0.1:
            aircraft["heading"] = (
                aircraft["heading"] + random.uniform(-10.0, 10.0)
            ) % 360.0

    def _calculate_reception_time(
        self,
        aircraft: Dict[str, float],
        receiver: ReceiverInfo,
        transmit_time: float,
    ) -> float:
        speed_of_light = 299792458.0
        aircraft_ecef = self._to_ecef(aircraft["lat"], aircraft["lon"], aircraft["alt"])
        receiver_ecef = self._to_ecef(receiver.latitude, receiver.longitude, receiver.altitude)

        distance = math.sqrt(
            sum((aircraft_ecef[i] - receiver_ecef[i]) ** 2 for i in range(3))
        )
        jitter = random.gauss(0.0, 5e-9)
        return transmit_time + (distance / speed_of_light) + jitter

    @staticmethod
    def _to_ecef(latitude: float, longitude: float, altitude: float) -> tuple[float, float, float]:
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)

        a = 6378137.0
        e2 = 0.00669437999014
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)

        x = (N + altitude) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + altitude) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + altitude) * math.sin(lat_rad)

        return x, y, z
