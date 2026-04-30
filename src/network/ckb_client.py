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
        self._feed_transport: Optional[BaseFeedTransport] = None

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

        self._feed_transport = SimulationFeedTransport(self.active_receivers)
        self._stream_tasks.extend(self._feed_transport.create_tasks(message_callback))
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
