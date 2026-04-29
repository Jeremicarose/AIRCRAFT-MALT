"""
CKB Network Client for MLAT System

Integrates CKB blockchain for decentralized peer discovery
with 4DSky for Mode-S data streaming.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import asyncio
import contextlib
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
    fourdskyendpoint: str = "wss://api.4dsky.com/stream"
    
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
        
        # Initialize CKB peer discovery
        ckb_config = CKBConfig(
            network=config.ckb_network,
            ckb_rpc_url=config.ckb_rpc_url,
            ckb_indexer_url=config.ckb_indexer_url,
            receiver_registry_type_hash=config.receiver_registry_type_hash,
            simulate_if_unavailable=config.simulate_if_unavailable,
        )
        self.peer_discovery = CKBPeerDiscovery(ckb_config)
        
        # Data streaming (4DSky or alternative)
        self.data_stream = None  # Will be initialized with 4DSky SDK
        
        # Active receivers
        self.active_receivers: Dict[str, ReceiverInfo] = {}
        self._simulation_task: Optional[asyncio.Task] = None
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
        
        # Initialize CKB connection
        await self.peer_discovery.initialize()
        if self.peer_discovery.simulation_mode:
            logger.info("✅ CKB discovery initialized in simulation mode")
        else:
            logger.info("✅ CKB blockchain connection established")
        
        # Discover receivers from CKB
        receivers = await self.peer_discovery.discover_peers()
        logger.info(f"✅ Discovered {len(receivers)} receivers from CKB")
        
        # Select best receivers
        selected = self._select_receivers(receivers)
        logger.info(f"✅ Selected {len(selected)} receivers for MLAT")
        
        # Store active receivers
        for receiver in selected:
            self.active_receivers[receiver.receiver_id] = receiver
        
        logger.info("=" * 70)
        logger.info(f"✅ Network client ready with {len(self.active_receivers)} receivers")
        logger.info("=" * 70)
    
    def _select_receivers(self, receivers: List[ReceiverInfo]) -> List[ReceiverInfo]:
        """
        Select best receivers for MLAT.
        
        Criteria:
        - Geographic diversity (spread out)
        - MLAT capability
        - Online status
        - Recent activity
        """
        # Filter for MLAT-capable and online
        candidates = [
            r for r in receivers
            if "mlat" in r.capabilities and r.status == "online"
        ]
        
        # Sort by recent activity
        candidates.sort(key=lambda r: r.last_seen, reverse=True)
        
        # Take top N
        return candidates[:self.config.max_receivers]
    
    async def start_streaming(self, message_callback: Callable):
        """
        Start receiving Mode-S data from all active receivers.
        
        In production, this would:
        1. Connect to 4DSky SDK
        2. Subscribe to each receiver's stream
        3. Call message_callback for each message
        
        Args:
            message_callback: async function(receiver_id, timestamp, message)
        """
        logger.info("📡 Starting Mode-S data streaming...")
        
        if self._simulation_task is None:
            self._simulation_task = asyncio.create_task(
                self._simulate_network_traffic(message_callback)
            )

        logger.info(
            f"✅ Streaming from {len(self.active_receivers)} receivers"
            " (CKB discovery + simulated 4DSky feed)"
        )

    async def _simulate_network_traffic(self, callback: Callable):
        """
        Simulate a shared 4DSky feed so the MLAT pipeline receives
        correlated multi-receiver observations.
        """
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
            aircraft["heading"] = (aircraft["heading"] + random.uniform(-10.0, 10.0)) % 360.0

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

    def _to_ecef(self, latitude: float, longitude: float, altitude: float) -> tuple[float, float, float]:
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

        if self._simulation_task is not None:
            self._simulation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._simulation_task
            self._simulation_task = None
        
        # Shutdown CKB connection
        await self.peer_discovery.shutdown()
        
        # Shutdown data streams
        # await self.data_stream.shutdown()
        
        self.active_receivers.clear()
        logger.info("✅ Network client shut down")
    
    def get_receiver_positions(self) -> Dict[str, tuple]:
        """Get positions of all active receivers"""
        return {
            receiver_id: (info.latitude, info.longitude, info.altitude)
            for receiver_id, info in self.active_receivers.items()
        }


# Example usage
async def main():
    """Example of using CKB network client"""
    
    # Configure
    config = NetworkConfig(
        ckb_network="testnet",
        ckb_rpc_url="https://testnet.ckb.dev/rpc",
        receiver_registry_type_hash="0x...",  # Your type script hash
        max_receivers=5
    )
    
    # Create client
    client = CKBNeuronNetworkClient(config)
    
    try:
        # Initialize
        await client.initialize()
        
        # Message handler
        async def handle_message(receiver_id: str, timestamp: float, message: str):
            print(f"📨 {receiver_id} @ {timestamp:.6f}: {message}")
        
        # Start streaming
        await client.start_streaming(handle_message)
        
        # Run for 10 seconds
        await asyncio.sleep(10)
        
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
