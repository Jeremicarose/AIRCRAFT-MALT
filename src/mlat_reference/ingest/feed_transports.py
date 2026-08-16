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
import shlex
import time

from mlat_reference.demo import scenario_aircraft_states
from ckb_registry.discovery import ReceiverInfo

logger = logging.getLogger(__name__)
MessageCallback = Callable[..., Awaitable[None]]


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
            await callback(
                record["receiver_id"],
                record["timestamp"],
                record["message"],
                timestamp_ns=record["timestamp_ns"],
                clock_synchronized=record["clock_synchronized"],
                clock_source=record["clock_source"],
                clock_uncertainty_ns=record["clock_uncertainty_ns"],
            )

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
                message_value.get("hex") or message_value.get("raw") or message_value.get("frame")
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

        timestamp_ns = self.parse_timestamp_ns(payload.get("timestamp_ns"))
        timestamp = (
            timestamp_ns / 1_000_000_000.0
            if timestamp_ns is not None
            else self.parse_timestamp(
                payload.get("timestamp")
                or payload.get("time")
                or payload.get("ts")
                or payload.get("observed_at")
            )
        )
        clock_synchronized = bool(
            timestamp_ns is not None and payload.get("clock_synchronized") is True
        )

        return [
            {
                "receiver_id": str(receiver_id),
                "timestamp": timestamp,
                "timestamp_ns": timestamp_ns,
                "clock_synchronized": clock_synchronized,
                "clock_source": str(payload.get("clock_source") or "unknown"),
                "clock_uncertainty_ns": self.parse_optional_float(
                    payload.get("clock_uncertainty_ns")
                ),
                "message": str(message),
            }
        ]

    @staticmethod
    def parse_timestamp_ns(value: Any) -> Optional[int]:
        if value is None or isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def parse_optional_float(value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if math.isfinite(parsed) and parsed >= 0 else None

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
                async with websockets.connect(
                    endpoint, extra_headers=self.auth_headers
                ) as websocket:
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
                process = await asyncio.create_subprocess_exec(
                    *shlex.split(self.command),
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

    def __init__(self, receivers: Dict[str, ReceiverInfo], scenario_name: str = "default"):
        super().__init__(receivers)
        self.scenario_name = scenario_name

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        return [asyncio.create_task(self._simulate_network_traffic(callback))]

    async def _simulate_network_traffic(self, callback: MessageCallback):
        while True:
            transmit_time_ns = time.time_ns()
            replay_states = scenario_aircraft_states(
                transmit_time_ns / 1_000_000_000.0,
                self.scenario_name,
            )
            for aircraft in replay_states:
                message = f"8D{aircraft['icao']}202CC371C32CE0576098"
                receiver_ids = list(self.receivers.keys())

                if len(receiver_ids) < 4:
                    await asyncio.sleep(0.5)
                    continue

                for receiver_id in receiver_ids:
                    receiver = self.receivers[receiver_id]
                    timestamp_ns = self._calculate_reception_time_ns(
                        aircraft,
                        receiver,
                        transmit_time_ns,
                    )
                    await callback(
                        receiver_id,
                        timestamp_ns / 1_000_000_000.0,
                        message,
                        timestamp_ns=timestamp_ns,
                        clock_synchronized=True,
                        clock_source="synthetic-common-clock",
                        clock_uncertainty_ns=1.0,
                    )

                await asyncio.sleep(0.5)

    def _calculate_reception_time_ns(
        self,
        aircraft: Dict[str, float | str],
        receiver: ReceiverInfo,
        transmit_time_ns: int,
    ) -> int:
        speed_of_light = 299792458.0
        aircraft_ecef = self._to_ecef(
            float(aircraft["latitude"]),
            float(aircraft["longitude"]),
            float(aircraft["altitude"]),
        )
        receiver_ecef = self._to_ecef(receiver.latitude, receiver.longitude, receiver.altitude)

        distance = math.sqrt(sum((aircraft_ecef[i] - receiver_ecef[i]) ** 2 for i in range(3)))
        jitter_ns = random.gauss(0.0, 1.0)
        return transmit_time_ns + round((distance / speed_of_light) * 1_000_000_000 + jitter_ns)

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
