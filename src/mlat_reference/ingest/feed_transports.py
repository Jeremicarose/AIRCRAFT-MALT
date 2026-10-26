"""
Feed transport implementations for Mode-S ingestion.

This module separates live and simulated feed adapters from the main
CKB network client so production and demo behavior are explicit.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
import asyncio
import contextlib
from datetime import datetime
import logging
import math
import random
import shlex
import time
from collections import Counter
from urllib.parse import urlsplit
from websockets.legacy.client import Connect
from websockets.exceptions import SecurityError

from mlat_reference.demo import scenario_aircraft_states
from ckb_registry.discovery import ReceiverInfo
from ckb_registry.record import normalize_receiver_identity
from mlat_reference.diagnostics import event
from mlat_reference.ingest.validation import (
    MAX_BATCH_RECORDS,
    MAX_NESTING,
    MAX_PAYLOAD_BYTES,
    integer_nanoseconds,
    mode_s_crc,
    mode_s_frame,
    strict_json,
)

logger = logging.getLogger(__name__)
MessageCallback = Callable[..., Awaitable[None]]


class BoundWebSocketConnect(Connect):
    """A feed URL is a security boundary, including during HTTP redirects."""

    def handle_redirect(self, uri: str) -> None:
        raise SecurityError("Feed redirects are forbidden; configure the final URL explicitly")


class BaseFeedTransport:
    """Base class for feed transports that create async stream tasks."""

    def __init__(self, receivers: Dict[str, ReceiverInfo]):
        self.receivers = receivers

    def create_tasks(self, callback: MessageCallback) -> List[asyncio.Task]:
        """Create the asyncio tasks needed to run the feed transport."""
        raise NotImplementedError


class JsonFeedParsingMixin:
    """Normalize external JSON payloads into MLAT callback records."""

    def reject(self, reason: str, count: int = 1):
        counters = self.__dict__.setdefault("rejection_counts", Counter())
        counters[reason] += count
        event(logger, "observation_rejected", reason=reason, count=count)

    async def dispatch_feed_payload(
        self,
        raw_payload: str | bytes,
        callback: MessageCallback,
        default_receiver_id: Optional[str] = None,
        allowed_receiver_ids: Optional[Set[str]] = None,
    ):
        try:
            payload = strict_json(raw_payload)
        except (ValueError, UnicodeError, RecursionError):
            self.reject("invalid_json_payload")
            return

        for record in self.normalize_feed_records(
            payload,
            default_receiver_id=default_receiver_id,
            allowed_receiver_ids=allowed_receiver_ids,
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
        allowed_receiver_ids: Optional[Set[str]] = None,
        _depth: int = 0,
        _budget: Optional[list[int]] = None,
    ) -> List[Dict[str, Any]]:
        if _budget is None:
            _budget = [MAX_BATCH_RECORDS]
        if _depth > MAX_NESTING or _budget[0] <= 0:
            self.reject("batch_limit")
            return []
        if isinstance(payload, list):
            if len(payload) > MAX_BATCH_RECORDS:
                self.reject("batch_limit", len(payload) - MAX_BATCH_RECORDS)
            records: List[Dict[str, Any]] = []
            for item in payload[:MAX_BATCH_RECORDS]:
                records.extend(
                    self.normalize_feed_records(
                        item,
                        default_receiver_id=default_receiver_id,
                        allowed_receiver_ids=allowed_receiver_ids,
                        _depth=_depth + 1,
                        _budget=_budget,
                    )
                )
            return records

        if not isinstance(payload, dict):
            self.reject("invalid_record_type")
            return []

        if "records" in payload and isinstance(payload["records"], list):
            return self.normalize_feed_records(
                payload["records"],
                default_receiver_id=default_receiver_id,
                allowed_receiver_ids=allowed_receiver_ids,
                _depth=_depth + 1,
                _budget=_budget,
            )

        if "data" in payload and isinstance(payload["data"], (dict, list)):
            nested = self.normalize_feed_records(
                payload["data"],
                default_receiver_id=default_receiver_id,
                allowed_receiver_ids=allowed_receiver_ids,
                _depth=_depth + 1,
                _budget=_budget,
            )
            if nested:
                return nested

        _budget[0] -= 1
        claimed_receiver_id = (
            payload.get("receiver_id")
            or payload.get("receiver")
            or payload.get("sensor_id")
            or payload.get("source")
        )
        receiver_id = self._bound_receiver_id(
            claimed_receiver_id,
            default_receiver_id=default_receiver_id,
            allowed_receiver_ids=allowed_receiver_ids,
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

        message = mode_s_frame(message)
        if not receiver_id or not message:
            self.reject("identity_or_frame_invalid")
            return []

        timestamp_ns = self.parse_timestamp_ns(payload.get("timestamp_ns"))
        if payload.get("timestamp_ns") is not None and timestamp_ns is None:
            self.reject("invalid_timestamp_ns")
            return []
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
        if timestamp is None or not math.isfinite(timestamp) or timestamp <= 0:
            self.reject("missing_or_invalid_timestamp")
            return []
        source = payload.get("clock_source", "unknown")
        if not isinstance(source, str) or len(source) > 128:
            self.reject("invalid_clock_source")
            return []
        clock_synchronized = bool(
            timestamp_ns is not None and payload.get("clock_synchronized") is True
        )

        return [
            {
                "receiver_id": str(receiver_id),
                "timestamp": timestamp,
                "timestamp_ns": timestamp_ns,
                "clock_synchronized": clock_synchronized,
                "clock_source": source,
                "clock_uncertainty_ns": self.parse_optional_float(
                    payload.get("clock_uncertainty_ns")
                ),
                "message": str(message),
            }
        ]

    @staticmethod
    def _bound_receiver_id(
        claimed_receiver_id: Any,
        *,
        default_receiver_id: Optional[str],
        allowed_receiver_ids: Optional[Set[str]],
    ) -> Optional[str]:
        if claimed_receiver_id is not None and (
            not isinstance(claimed_receiver_id, str) or len(claimed_receiver_id) > 128
        ):
            return None
        claimed = claimed_receiver_id or None
        if claimed and claimed.startswith("0x"):
            try:
                claimed = normalize_receiver_identity(claimed)
            except ValueError:
                return None

        bound = default_receiver_id
        if bound and bound.startswith("0x"):
            try:
                bound = normalize_receiver_identity(bound)
            except ValueError:
                return None

        if bound is not None and claimed is not None and claimed != bound:
            logger.warning("Dropping feed payload with a conflicting receiver identity")
            return None

        receiver_id = bound or claimed
        if receiver_id is None:
            return None
        if allowed_receiver_ids is not None and receiver_id not in allowed_receiver_ids:
            logger.warning("Dropping feed payload for an unassigned receiver")
            return None
        return receiver_id

    @staticmethod
    def parse_timestamp_ns(value: Any) -> Optional[int]:
        return integer_nanoseconds(value)

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
    def parse_timestamp(value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None

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

        return None


class WebSocketJsonFeedTransport(BaseFeedTransport, JsonFeedParsingMixin):
    """Consume JSON payloads from one or more websocket endpoints."""

    def __init__(
        self,
        receivers: Dict[str, ReceiverInfo],
        endpoint: str,
        auth_headers: Dict[str, str],
        subscribe_message: Optional[str],
        allowed_endpoints: tuple[str, ...] = (),
    ):
        super().__init__(receivers)
        self.endpoint = endpoint
        self.auth_headers = auth_headers
        self.subscribe_message = subscribe_message
        self.allowed_endpoints = set(allowed_endpoints) | ({endpoint} if endpoint else set())

    def _validate_endpoint(self, endpoint: str) -> None:
        if endpoint not in self.allowed_endpoints:
            raise ValueError("Receiver feed endpoint is not in the operator allowlist")
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme not in {"ws", "wss"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise ValueError("Feed endpoint must be a ws/wss URL without credentials or fragment")

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
            if len(receiver_ids) != 1:
                joined = ", ".join(sorted(receiver_ids))
                raise RuntimeError(
                    "Each WebSocket connection must bind to one receiver identity; "
                    f"endpoint {endpoint} is assigned to: {joined}"
                )
        # Validate the whole batch before starting any task.
        for endpoint in endpoint_to_receivers:
            self._validate_endpoint(endpoint)
        for endpoint, receiver_ids in endpoint_to_receivers.items():
            default_receiver_id = receiver_ids[0]
            tasks.append(
                asyncio.create_task(
                    self._stream_via_websocket(
                        endpoint=endpoint,
                        callback=callback,
                        default_receiver_id=default_receiver_id,
                        allowed_receiver_ids=set(receiver_ids),
                    )
                )
            )

        return tasks

    async def _stream_via_websocket(
        self,
        endpoint: str,
        callback: MessageCallback,
        default_receiver_id: Optional[str] = None,
        allowed_receiver_ids: Optional[Set[str]] = None,
    ):
        while True:
            try:
                self._validate_endpoint(endpoint)
                # Secrets belong only to the exact operator-configured URL.
                headers = self.auth_headers if endpoint == self.endpoint else {}
                async with BoundWebSocketConnect(
                    endpoint,
                    extra_headers=headers,
                    max_size=MAX_PAYLOAD_BYTES,
                    max_queue=16,
                    open_timeout=15,
                    close_timeout=5,
                ) as websocket:
                    event(logger, "feed_connected", receiver_id=default_receiver_id)

                    if self.subscribe_message and endpoint == self.endpoint:
                        await websocket.send(self.subscribe_message)

                    async for raw_payload in websocket:
                        await self.dispatch_feed_payload(
                            raw_payload,
                            callback,
                            default_receiver_id=default_receiver_id,
                            allowed_receiver_ids=allowed_receiver_ids,
                        )

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                event(
                    logger, "feed_failed", level=logging.WARNING, exception_type=type(exc).__name__
                )
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
                    # Never echo a bridge's arbitrary stderr (may contain secrets),
                    # and never allow an undrained pipe to deadlock its stdout.
                    stderr=asyncio.subprocess.DEVNULL,
                    limit=MAX_PAYLOAD_BYTES,
                )
                event(logger, "feed_started")

                assert process.stdout is not None
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    await self.dispatch_feed_payload(
                        line.decode("utf-8"),
                        callback,
                        allowed_receiver_ids=set(self.receivers),
                    )

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                event(
                    logger, "feed_failed", level=logging.WARNING, exception_type=type(exc).__name__
                )
            finally:
                if process is not None and process.returncode is None:
                    with contextlib.suppress(ProcessLookupError):
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=3)
                        except asyncio.TimeoutError:
                            process.kill()
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
                transmit_time_ns = time.time_ns()
                message = f"8D{aircraft['icao']}202CC371C32CE0576098"
                body = message[:-6] + "000000"
                message = body[:-6] + f"{mode_s_crc(body):06X}"
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
