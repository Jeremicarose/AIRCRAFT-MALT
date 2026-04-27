"""
CKB Network Client for MLAT System

Integrates CKB blockchain for decentralized peer discovery
with 4DSky for Mode-S data streaming.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import asyncio
import logging

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
            receiver_registry_type_hash=config.receiver_registry_type_hash
        )
        self.peer_discovery = CKBPeerDiscovery(ckb_config)
        
        # Data streaming (4DSky or alternative)
        self.data_stream = None  # Will be initialized with 4DSky SDK
        
        # Active receivers
        self.active_receivers: Dict[str, ReceiverInfo] = {}
        
    async def initialize(self):
        """Initialize the network client"""
        logger.info("=" * 70)
        logger.info("🚀 CKB NEURON NETWORK CLIENT INITIALIZING")
        logger.info("=" * 70)
        
        # Initialize CKB connection
        await self.peer_discovery.initialize()
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
        
        # For each active receiver
        for receiver_id, receiver_info in self.active_receivers.items():
            logger.info(f"   Subscribing to {receiver_id}...")
            
            # In production: connect to 4DSky stream
            # await self.data_stream.subscribe(receiver_id, message_callback)
            
            # For now, simulate streaming
            asyncio.create_task(
                self._simulate_stream(receiver_id, message_callback)
            )
        
        logger.info(f"✅ Streaming from {len(self.active_receivers)} receivers")
    
    async def _simulate_stream(self, receiver_id: str, callback: Callable):
        """
        Simulate Mode-S message stream.
        
        TODO: Replace with actual 4DSky SDK integration
        """
        import random
        
        sample_messages = [
            "8D4840D6202CC371C32CE0576098",
            "8D4840D658C382D690C8AC2863A7",
            "8D4840D6EA1584A8B4FB8D5DCBD5",
        ]
        
        while True:
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            message = random.choice(sample_messages)
            timestamp = asyncio.get_event_loop().time()
            
            await callback(receiver_id, timestamp, message)
    
    async def shutdown(self):
        """Gracefully shutdown all connections"""
        logger.info("🛑 Shutting down CKB network client...")
        
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
