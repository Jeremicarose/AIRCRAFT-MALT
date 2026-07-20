"""
CKB Network Client for MLAT System

Integrates CKB blockchain for decentralized peer discovery
with 4DSky for Mode-S data streaming.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
import contextlib
import logging
import time

from network.ckb_discovery import CKBPeerDiscovery, CKBConfig, ReceiverInfo
from network.feed_transports import (
    BaseFeedTransport,
    CommandJsonlFeedTransport,
    SimulationFeedTransport,
    WebSocketJsonFeedTransport,
)

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
    strict_production_mode: bool = False
    ssl_verify: bool = True
    max_record_age_seconds: int = 86400
    hybrid_simulation_min_receivers: int = 4
    demo_scenario: str = "default"


class CKBReceiverNetworkClient:
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
            strict_production_mode=config.strict_production_mode,
            ssl_verify=config.ssl_verify,
            max_record_age_seconds=config.max_record_age_seconds,
            demo_scenario=config.demo_scenario,
        )
        self.peer_discovery = CKBPeerDiscovery(ckb_config)

        self.active_receivers: Dict[str, ReceiverInfo] = {}
        self._stream_tasks: List[asyncio.Task] = []
        self._feed_transport: Optional[BaseFeedTransport] = None
        self.discovery_latency_ms = 0.0

    async def initialize(self):
        """Initialize the network client"""
        logger.info("=" * 70)
        logger.info("🚀 CKB RECEIVER NETWORK CLIENT INITIALIZING")
        logger.info("=" * 70)

        await self.peer_discovery.initialize()
        if self.peer_discovery.simulation_mode:
            logger.info("✅ CKB discovery initialized in simulation mode")
        else:
            logger.info("✅ CKB blockchain connection established")

        discovery_started_at = time.perf_counter()
        receivers = await self.peer_discovery.discover_peers()
        self.discovery_latency_ms = (time.perf_counter() - discovery_started_at) * 1000
        logger.info(f"✅ Discovered {len(receivers)} receivers from CKB")

        selected = self._select_receivers(receivers)
        logger.info(f"✅ Selected {len(selected)} receivers for MLAT")

        for receiver in selected:
            self.active_receivers[receiver.receiver_id] = receiver

        self._augment_receivers_for_simulation()

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

    async def start_streaming(self, message_callback):
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
            self._feed_transport = CommandJsonlFeedTransport(
                self.active_receivers,
                self.config.fourdsky_bridge_command,
            )
            self._stream_tasks.extend(self._feed_transport.create_tasks(message_callback))
            logger.info("✅ Streaming via local 4DSky/ADEX bridge command")
            return

        if transport == "websocket-json":
            self._feed_transport = WebSocketJsonFeedTransport(
                self.active_receivers,
                endpoint=self.config.fourdskyendpoint,
                auth_headers=self._build_auth_headers(),
                subscribe_message=self.config.fourdsky_subscribe_message,
            )
            websocket_tasks = self._feed_transport.create_tasks(message_callback)
            if websocket_tasks:
                self._stream_tasks.extend(websocket_tasks)
                logger.info(
                    f"✅ Streaming from {len(self.active_receivers)} receivers via WebSocket JSON feed"
                )
                return
            if self.config.strict_production_mode:
                raise RuntimeError(
                    "STRICT_PRODUCTION_MODE forbids falling back to simulation when live WebSocket streaming is unavailable"
                )

        if self.config.strict_production_mode:
            raise RuntimeError(
                f"STRICT_PRODUCTION_MODE forbids selecting {transport!r} synthetic feed transport"
            )

        self._feed_transport = SimulationFeedTransport(
            self.active_receivers,
            scenario_name=self.config.demo_scenario,
        )
        self._stream_tasks.extend(self._feed_transport.create_tasks(message_callback))
        logger.info(
            f"✅ Streaming from {len(self.active_receivers)} receivers"
            " (CKB discovery + simulated 4DSky feed)"
        )

    def _determine_transport(self) -> str:
        """Resolve the active 4DSky transport."""
        configured = (self.config.fourdsky_transport or "auto").strip().lower()
        if configured != "auto":
            if self.config.strict_production_mode and configured == "simulation":
                raise RuntimeError(
                    "STRICT_PRODUCTION_MODE requires a live 4DSky transport and forbids FOURDSKY_TRANSPORT=simulation"
                )
            return configured

        if self.config.fourdsky_bridge_command:
            return "command-jsonl"

        if self.config.fourdskyendpoint or any(
            receiver.stream_endpoint for receiver in self.active_receivers.values()
        ):
            return "websocket-json"

        if self.config.strict_production_mode:
            raise RuntimeError(
                "STRICT_PRODUCTION_MODE forbids FOURDSKY_TRANSPORT=auto from resolving to simulation"
            )

        return "simulation"

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

    def _augment_receivers_for_simulation(self):
        """
        In simulation transport mode, top up the discovered receiver set with
        simulated peers so the demo can still produce MLAT groups when the live
        registry has fewer than the minimum receiver count.
        """
        transport = self._determine_transport()
        min_receivers = max(1, self.config.hybrid_simulation_min_receivers)

        if self.config.strict_production_mode or transport != "simulation":
            return
        if len(self.active_receivers) >= min_receivers:
            return

        simulated_receivers = self.peer_discovery._get_simulated_receivers()
        added = 0
        for receiver in simulated_receivers:
            if receiver.receiver_id in self.active_receivers:
                continue
            self.active_receivers[receiver.receiver_id] = receiver
            added += 1
            if len(self.active_receivers) >= min_receivers:
                break

        if added > 0:
            logger.info(
                "🧪 Added %d simulated receivers to supplement the live registry for hybrid demo mode",
                added,
            )

    async def shutdown(self):
        """Gracefully shutdown all connections"""
        logger.info("🛑 Shutting down CKB network client...")

        for task in self._stream_tasks:
            task.cancel()

        for task in self._stream_tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        self._stream_tasks.clear()
        self._feed_transport = None
        await self.peer_discovery.shutdown()
        self.active_receivers.clear()
        logger.info("✅ Network client shut down")

    @property
    def stream_tasks(self) -> tuple[asyncio.Task, ...]:
        """Return active feed tasks so the owning runtime can monitor them."""
        return tuple(self._stream_tasks)

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

    client = CKBReceiverNetworkClient(config)

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
