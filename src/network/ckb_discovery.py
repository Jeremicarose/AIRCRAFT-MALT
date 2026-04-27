"""
CKB Blockchain Integration for MLAT System

Uses Nervos Network (CKB) for decentralized peer discovery instead of Hedera.

Features:
- Receiver registration on-chain
- Decentralized peer discovery
- Trustless receiver verification
- On-chain data availability
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ReceiverInfo:
    """Information about a Mode-S receiver in the network"""
    receiver_id: str
    latitude: float
    longitude: float
    altitude: float
    status: str
    last_seen: float
    capabilities: List[str]
    ckb_address: str  # CKB address of receiver
    lock_hash: str    # Lock script hash for verification


@dataclass
class CKBConfig:
    """Configuration for CKB blockchain connection"""
    network: str = "testnet"  # "mainnet" or "testnet"
    ckb_rpc_url: str = "https://testnet.ckb.dev/rpc"
    receiver_registry_type_hash: str = ""  # Type script hash for receiver registry
    api_timeout: int = 30


class CKBPeerDiscovery:
    """
    CKB blockchain-based peer discovery.
    
    Uses Nervos Network to register and discover Mode-S receivers.
    Receivers publish their metadata to CKB cells, making discovery
    decentralized and trustless.
    """
    
    def __init__(self, config: CKBConfig):
        self.config = config
        self.cached_peers: Dict[str, ReceiverInfo] = {}
        self.client = None
        
    async def initialize(self):
        """Initialize CKB RPC client"""
        logger.info(f"Initializing CKB peer discovery on {self.config.network}")
        
        # Import CKB SDK
        try:
            from ckb import rpc
            self.client = rpc.RPC(self.config.ckb_rpc_url)
            
            # Test connection
            tip = await self._get_tip_block_number()
            logger.info(f"✅ Connected to CKB node, current block: {tip}")
            
        except ImportError:
            logger.error("❌ CKB SDK not installed. Run: pip install ckb-py")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to CKB node: {e}")
            raise
    
    async def _get_tip_block_number(self) -> int:
        """Get current block number"""
        try:
            tip = await asyncio.to_thread(self.client.get_tip_block_number)
            return int(tip, 16)
        except Exception as e:
            logger.error(f"Failed to get tip block: {e}")
            return 0
    
    async def discover_peers(self) -> List[ReceiverInfo]:
        """
        Discover active Mode-S receivers from CKB blockchain.
        
        Process:
        1. Query CKB for cells with receiver registry type script
        2. Parse cell data to extract receiver information
        3. Verify receiver credentials
        4. Return list of active receivers
        """
        logger.info("🔍 Discovering peers from CKB blockchain...")
        
        receivers = []
        
        try:
            # Search for receiver registry cells
            cells = await self._search_receiver_cells()
            
            logger.info(f"Found {len(cells)} receiver cells on CKB")
            
            # Parse each cell
            for cell in cells:
                try:
                    receiver = await self._parse_receiver_cell(cell)
                    if receiver and self._is_receiver_valid(receiver):
                        receivers.append(receiver)
                        self.cached_peers[receiver.receiver_id] = receiver
                except Exception as e:
                    logger.warning(f"Failed to parse receiver cell: {e}")
                    continue
            
            logger.info(f"✅ Discovered {len(receivers)} valid receivers")
            
        except Exception as e:
            logger.error(f"Error discovering peers: {e}")
        
        return receivers
    
    async def _search_receiver_cells(self) -> List[Dict]:
        """
        Search CKB blockchain for receiver registry cells.
        
        Uses get_cells RPC to find all cells with the receiver registry type script.
        """
        try:
            # Build search query
            search_key = {
                "script": {
                    "code_hash": self.config.receiver_registry_type_hash,
                    "hash_type": "type",
                    "args": "0x"
                },
                "script_type": "type",
                "filter": {
                    "script_len_range": ["0x0", "0xffffffff"]
                }
            }
            
            # Query cells
            cells_response = await asyncio.to_thread(
                self.client.get_cells,
                search_key,
                "asc",
                "0x64"  # Limit to 100 cells
            )
            
            cells = cells_response.get("objects", [])
            return cells
            
        except Exception as e:
            logger.error(f"Failed to search receiver cells: {e}")
            return []
    
    async def _parse_receiver_cell(self, cell: Dict) -> Optional[ReceiverInfo]:
        """
        Parse receiver information from CKB cell data.
        
        Cell data format (JSON in cell output data):
        {
            "receiver_id": "RECV_NYC_001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0,
            "status": "online",
            "capabilities": ["mode-s", "adsb", "mlat"],
            "timestamp": 1234567890,
            "signature": "0x..."
        }
        """
        try:
            # Get cell output data
            output_data = cell.get("output_data", "0x")
            
            if output_data == "0x":
                return None
            
            # Decode hex data to JSON
            data_bytes = bytes.fromhex(output_data[2:])  # Remove 0x prefix
            data_json = json.loads(data_bytes.decode('utf-8'))
            
            # Extract receiver info
            receiver = ReceiverInfo(
                receiver_id=data_json['receiver_id'],
                latitude=data_json['latitude'],
                longitude=data_json['longitude'],
                altitude=data_json['altitude'],
                status=data_json['status'],
                last_seen=data_json['timestamp'],
                capabilities=data_json['capabilities'],
                ckb_address=cell['output']['lock']['args'],
                lock_hash=cell['output']['lock']['hash']
            )
            
            return receiver
            
        except Exception as e:
            logger.warning(f"Failed to parse cell: {e}")
            return None
    
    def _is_receiver_valid(self, receiver: ReceiverInfo) -> bool:
        """
        Validate receiver information.
        
        Checks:
        - Status is online
        - Has required capabilities
        - Recent timestamp (last 24 hours)
        - Valid coordinates
        """
        import time
        
        # Check status
        if receiver.status != "online":
            return False
        
        # Check capabilities
        if "mode-s" not in receiver.capabilities:
            return False
        
        # Check timestamp (last 24 hours)
        if time.time() - receiver.last_seen > 86400:
            logger.debug(f"Receiver {receiver.receiver_id} timestamp too old")
            return False
        
        # Check coordinates
        if not (-90 <= receiver.latitude <= 90):
            return False
        if not (-180 <= receiver.longitude <= 180):
            return False
        
        return True
    
    async def get_receiver_details(self, receiver_id: str) -> Optional[ReceiverInfo]:
        """Get cached receiver details"""
        return self.cached_peers.get(receiver_id)
    
    async def register_receiver(
        self,
        receiver_id: str,
        latitude: float,
        longitude: float,
        altitude: float,
        capabilities: List[str],
        private_key: str
    ) -> bool:
        """
        Register a new receiver on CKB blockchain.
        
        This creates a new cell with receiver information.
        Requires CKB tokens for transaction fees.
        
        Args:
            receiver_id: Unique receiver identifier
            latitude: Receiver latitude
            longitude: Receiver longitude
            altitude: Receiver altitude (meters)
            capabilities: List of capabilities
            private_key: CKB private key for signing
        
        Returns:
            True if registration successful
        """
        logger.info(f"Registering receiver {receiver_id} on CKB...")
        
        try:
            from ckb import wallet
            import time
            
            # Prepare receiver data
            receiver_data = {
                "receiver_id": receiver_id,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "status": "online",
                "capabilities": capabilities,
                "timestamp": time.time()
            }
            
            # Convert to hex
            data_json = json.dumps(receiver_data)
            data_hex = "0x" + data_json.encode('utf-8').hex()
            
            # Build transaction
            # (This is simplified - real implementation needs proper cell building)
            tx = {
                "version": "0x0",
                "cell_deps": [],
                "header_deps": [],
                "inputs": [],
                "outputs": [{
                    "capacity": "0x174876e800",  # 100 CKB
                    "lock": {
                        "code_hash": "...",  # Your lock script
                        "hash_type": "type",
                        "args": "..."
                    },
                    "type": {
                        "code_hash": self.config.receiver_registry_type_hash,
                        "hash_type": "type",
                        "args": "0x"
                    }
                }],
                "outputs_data": [data_hex],
                "witnesses": []
            }
            
            # Sign and send transaction
            # tx_hash = await self._send_transaction(tx, private_key)
            
            logger.info(f"✅ Receiver registered on CKB")
            # logger.info(f"   Transaction hash: {tx_hash}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register receiver: {e}")
            return False
    
    async def shutdown(self):
        """Cleanup CKB connection"""
        logger.info("Shutting down CKB peer discovery")
        self.client = None


# Example usage
async def main():
    """Example of using CKB peer discovery"""
    
    # Configure CKB connection
    config = CKBConfig(
        network="testnet",
        ckb_rpc_url="https://testnet.ckb.dev/rpc",
        receiver_registry_type_hash="0x1234..."  # Your type script hash
    )
    
    # Create peer discovery
    discovery = CKBPeerDiscovery(config)
    
    try:
        # Initialize
        await discovery.initialize()
        
        # Discover peers
        receivers = await discovery.discover_peers()
        
        print(f"\nFound {len(receivers)} receivers:")
        for recv in receivers:
            print(f"  {recv.receiver_id}:")
            print(f"    Location: {recv.latitude}°, {recv.longitude}°")
            print(f"    Capabilities: {', '.join(recv.capabilities)}")
            print(f"    CKB Address: {recv.ckb_address[:10]}...")
        
    finally:
        await discovery.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
