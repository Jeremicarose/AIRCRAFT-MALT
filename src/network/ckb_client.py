"""
CKB Network Client for MLAT System

Integrates CKB blockchain for decentralized peer discovery
with 4DSky for Mode-S data streaming.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import asyncio
import contextlib
from datetime import datetime
import json
import logging
import math
import random
import time

from network.ckb_discovery import CKBPeerDiscovery, CKBConfig, ReceiverInfo

logger = logging.getLogger(__name__)


@dataclass
class NetworkConfig:
    """Configuration for CKB-based network"""
    # CKB Configuration
    ckb_network: str = "testnet"
    ckb_rpc_url: str = "https://testnet.ckb.dev/rpc"
    ckb_indexer_url: str = "https://testnet.ckb.dev/indexer"
    receiver_registry_type_hash: str = ""

    # 4DSky Configuration
    api_key: Optional[str] = None
    fourdskyendpoint: str = ""
    fourdsky_transport: str = "auto"
    fourdsky_auth_header: str = "X-API-Key"
    fourdsky_auth_scheme: Optional[str] = None
    fourdsky_auth_token: Optional[str] = None
    fourdsky_subscribe_message: Optional[str] = None
    fourdsky_bridge_command: Optional[str] = None

    # System Configuration
    max_receivers: int = 20
    simulate_if_unavailable: bool = True


class CKBNeuronNetworkClient:
    """
    Network client using CKB blockchain for peer discovery.

    Combines:
    - CKB for decentralized peer discovery
    - 4DSky for Mode-S data streaming
    """

    def __init__(self, config: NetworkConfig):
        self.config = config

        ckb_config = CKBConfig(
            network=config.ckb_network,
            ckb_rpc_url=config.ckb_rpc_url,
            ckb_indexer_url=config.ckb_indexer_url,
            receiver_registry_type_hash=config.receiver_registry_type_hash,
            simulate_if_unavailable=config.simulate_if_unavailable,
        )
        self.peer_discovery = CKBPeerDiscovery(ckb_config)

        self.active_receivers: Dict[str, ReceiverInfo] = {}
        self._stream_tasks: List[asyncio.Task] = []
        self._simulated_aircraft = [
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

    async def initialize(self):
        """Initialize the network client"""
        logger.info("=" * 70)
        logger.info("🚀 CKB NEURON NETWORK CLIENT INITIALIZING")
        logger.info("=" * 70)

        await self.peer_discovery.initialize()
        if self.peer_discovery.simulation_mode:
            logger.info("✅ CKB discovery initialized in simulation mode")
        else:
            logger.info("✅ CKB blockchain connection established")

        receivers = await self.peer_discovery.discover_peers()
        logger.info(f"✅ Discovered {len(receivers)} receivers from CKB")

        selected = self._select_receivers(receivers)
        logger.info(f"✅ Selected {len(selected)} receivers for MLAT")

        for receiver in selected:
            self.active_receivers[receiver.receiver_id] = receiver

        logger.info("=" * 70)
        logger.info(f"✅ Network client ready with {len(self.active_receivers)} receivers")
        logger.info("=" * 70)

    def _select_receivers(self, receivers: List[ReceiverInfo]) -> List[ReceiverInfo]:
        """Select the best currently available receivers for MLAT."""
        candidates = [
            receiver for receiver in receivers
            if "mlat" in receiver.capabilities and receiver.status == "online"
        ]
        candidates.sort(key=lambda receiver: receiver.last_seen, reverse=True)
        return candidates[:self.config.max_receivers]

    async def start_streaming(self, message_callback: Callable):
        """
        Start receiving Mode-S data from the configured 4DSky transport.

        Supported modes:
        - `simulation`
        - `websocket-json`
        - `command-jsonl`
        - `auto`
        """
        logger.info("📡 Starting Mode-S data streaming...")

        if self._stream_tasks:
            logger.info("Streaming already active; keeping current tasks")
            return

        transport = self._determine_transport()

        if transport == "command-jsonl" and self.config.fourdsky_bridge_command:
            self._stream_tasks.append(
                asyncio.create_task(
                    self._stream_via_command(
                        self.config.fourdsky_bridge_command,
                        message_callback,
                    )
                )
            )
            logger.info("✅ Streaming via local 4DSky/ADEX bridge command")
            return

        if transport == "websocket-json":
            websocket_tasks = self._create_websocket_tasks(message_callback)
            if websocket_tasks:
                self._stream_tasks.extend(websocket_tasks)
                logger.info(
                    f"✅ Streaming from {len(self.active_receivers)} receivers via WebSocket JSON feed"
                )
                return

        self._stream_tasks.append(
            asyncio.create_task(self._simulate_network_traffic(message_callback))
        )
        logger.info(
            f"✅ Streaming from {len(self.active_receivers)} receivers"
            " (CKB discovery + simulated 4DSky feed)"
        )

    def _determine_transport(self) -> str:
        """Resolve the active 4DSky transport."""
        configured = (self.config.fourdsky_transport or "auto").strip().lower()
        if configured != "auto":
            return configured

        if self.config.fourdsky_bridge_command:
            return "command-jsonl"

        if self.config.fourdskyendpoint or any(
            receiver.stream_endpoint for receiver in self.active_receivers.values()
        ):
            return "websocket-json"

        return "simulation"

    def _create_websocket_tasks(self, message_callback: Callable) -> List[asyncio.Task]:
        """Create one task per unique websocket endpoint."""
        endpoint_to_receivers: Dict[str, List[str]] = {}
        tasks: List[asyncio.Task] = []

        for receiver_id, receiver in self.active_receivers.items():
            if receiver.stream_protocol and receiver.stream_protocol not in {
                "websocket-json",
                "simulation",
            }:
                continue

            endpoint = receiver.stream_endpoint or self.config.fourdskyendpoint
            if not endpoint:
                continue

            endpoint_to_receivers.setdefault(endpoint, []).append(receiver_id)

        for endpoint, receiver_ids in endpoint_to_receivers.items():
            default_receiver_id = receiver_ids[0] if len(receiver_ids) == 1 else None
            tasks.append(
                asyncio.create_task(
                    self._stream_via_websocket(
                        endpoint=endpoint,
                        callback=message_callback,
                        default_receiver_id=default_receiver_id,
                    )
                )
            )

        return tasks

    def _build_auth_headers(self) -> Dict[str, str]:
        """Build auth headers for WebSocket-based 4DSky connections."""
        headers: Dict[str, str] = {}
        token = self.config.fourdsky_auth_token or self.config.api_key
        if not token:
            return headers

        header_name = self.config.fourdsky_auth_header or "X-API-Key"
        if self.config.fourdsky_auth_scheme:
            headers[header_name] = f"{self.config.fourdsky_auth_scheme} {token}"
        else:
            headers[header_name] = token

        return headers

    async def _stream_via_websocket(
        self,
        endpoint: str,
        callback: Callable,
        default_receiver_id: Optional[str] = None,
    ):
        """Consume a websocket stream that emits JSON payloads."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed. Run: pip install websockets")
            return

        headers = self._build_auth_headers()

        while True:
            try:
                async with websockets.connect(endpoint, extra_headers=headers) as websocket:
                    logger.info(f"Connected to 4DSky websocket: {endpoint}")

                    if self.config.fourdsky_subscribe_message:
                        await websocket.send(self.config.fourdsky_subscribe_message)

                    async for raw_payload in websocket:
                        await self._dispatch_feed_payload(
                            raw_payload,
                            callback,
                            default_receiver_id=default_receiver_id,
                        )

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(f"4DSky websocket stream error ({endpoint}): {exc}")
                await asyncio.sleep(3)

    async def _stream_via_command(self, command: str, callback: Callable):
        """Read newline-delimited JSON messages from a local bridge command."""
        while True:
            process = None
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                logger.info(f"Started 4DSky bridge command: {command}")

                assert process.stdout is not None
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    await self._dispatch_feed_payload(line.decode("utf-8"), callback)

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
                logger.warning(f"4DSky bridge command failed: {exc}")
            finally:
                if process is not None and process.returncode is None:
                    process.terminate()
                    with contextlib.suppress(ProcessLookupError):
                        await process.wait()

            await asyncio.sleep(3)

    async def _dispatch_feed_payload(
        self,
        raw_payload: str,
        callback: Callable,
        default_receiver_id: Optional[str] = None,
    ):
        """Normalize a feed payload and push records into the processor callback."""
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.debug("Skipping non-JSON 4DSky payload: %s", raw_payload[:200])
            return

        for record in self._normalize_feed_records(
            payload,
            default_receiver_id=default_receiver_id,
        ):
            await callback(record["receiver_id"], record["timestamp"], record["message"])

    def _normalize_feed_records(
        self,
        payload: Any,
        default_receiver_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Support a few common JSON feed shapes from external bridges."""
        if isinstance(payload, list):
            records: List[Dict[str, Any]] = []
            for item in payload:
                records.extend(
                    self._normalize_feed_records(
                        item,
                        default_receiver_id=default_receiver_id,
                    )
                )
            return records

        if not isinstance(payload, dict):
            return []

        if "records" in payload and isinstance(payload["records"], list):
            return self._normalize_feed_records(
                payload["records"],
                default_receiver_id=default_receiver_id,
            )

        if "data" in payload and isinstance(payload["data"], (dict, list)):
            nested = self._normalize_feed_records(
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
                "timestamp": self._parse_timestamp(
                    payload.get("timestamp")
                    or payload.get("time")
                    or payload.get("ts")
                    or payload.get("observed_at")
                ),
                "message": str(message),
            }
        ]

    def _parse_timestamp(self, value: Any) -> float:
        """Parse numeric or ISO-like timestamps into Unix seconds."""
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

    async def _simulate_network_traffic(self, callback: Callable):
        """Generate a shared simulated 4DSky stream for local development."""
        while True:
            for aircraft in self._simulated_aircraft:
                self._advance_aircraft(aircraft, dt_seconds=0.5)

                transmit_time = time.time()
                message = f"8D{aircraft['icao']}202CC371C32CE0576098"
                receiver_ids = list(self.active_receivers.keys())

                if len(receiver_ids) < 4:
                    await asyncio.sleep(0.5)
                    continue

                if len(receiver_ids) > 4 and random.random() < 0.25:
                    dropped = random.choice(receiver_ids)
                    receiver_ids = [rid for rid in receiver_ids if rid != dropped]

                for receiver_id in receiver_ids:
                    receiver = self.active_receivers[receiver_id]
                    timestamp = self._calculate_reception_time(
                        aircraft,
                        receiver,
                        transmit_time,
                    )
                    await callback(receiver_id, timestamp, message)

                await asyncio.sleep(0.5)

    def _advance_aircraft(self, aircraft: Dict[str, float], dt_seconds: float):
        """Move a simulated aircraft along a simple great-circle approximation."""
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
        """Calculate time of arrival from simulated aircraft to receiver."""
        speed_of_light = 299792458.0
        aircraft_ecef = self._to_ecef(aircraft["lat"], aircraft["lon"], aircraft["alt"])
        receiver_ecef = self._to_ecef(receiver.latitude, receiver.longitude, receiver.altitude)

        distance = math.sqrt(
            sum((aircraft_ecef[i] - receiver_ecef[i]) ** 2 for i in range(3))
        )
        jitter = random.gauss(0.0, 5e-9)
        return transmit_time + (distance / speed_of_light) + jitter

    def _to_ecef(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
    ) -> tuple[float, float, float]:
        """Convert geodetic coordinates to ECEF."""
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)

        a = 6378137.0
        e2 = 0.00669437999014
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)

        x = (N + altitude) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + altitude) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + altitude) * math.sin(lat_rad)

        return x, y, z

    async def shutdown(self):
        """Gracefully shutdown all connections"""
        logger.info("🛑 Shutting down CKB network client...")

        for task in self._stream_tasks:
            task.cancel()

        for task in self._stream_tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        self._stream_tasks.clear()
        await self.peer_discovery.shutdown()
        self.active_receivers.clear()
        logger.info("✅ Network client shut down")

    def get_receiver_positions(self) -> Dict[str, tuple]:
        """Get positions of all active receivers"""
        return {
            receiver_id: (info.latitude, info.longitude, info.altitude)
            for receiver_id, info in self.active_receivers.items()
        }


async def main():
    """Example of using the CKB network client"""
    config = NetworkConfig(
        ckb_network="testnet",
        ckb_rpc_url="https://testnet.ckb.dev/rpc",
        receiver_registry_type_hash="0x...",
        max_receivers=5,
    )

    client = CKBNeuronNetworkClient(config)

    try:
        await client.initialize()

        async def handle_message(receiver_id: str, timestamp: float, message: str):
            print(f"📨 {receiver_id} @ {timestamp:.6f}: {message}")

        await client.start_streaming(handle_message)
        await asyncio.sleep(10)
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
