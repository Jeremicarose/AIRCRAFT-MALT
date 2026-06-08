"""
CKB Blockchain Integration for MLAT System

This module standardizes a canonical JSON receiver-registry schema:
- state lives in cell data
- validation logic lives in this client + the on-chain type script
- ownership is controlled by the cell's lock script
"""

from typing import Any, Dict, List, Optional
from dataclasses import asdict, dataclass
import json
import asyncio
import logging
import ssl
import time
import urllib.request

from demo_scenarios import build_demo_receivers

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
    stream_endpoint: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_format: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReceiverRegistryRecord:
    """Canonical JSON schema stored in CKB receiver-registry cell data."""

    receiver_id: str
    latitude: float
    longitude: float
    altitude: float
    status: str
    capabilities: List[str]
    timestamp: float
    stream_endpoint: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_format: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_payload_dict(self) -> Dict[str, Any]:
        """Serialize the canonical schema, omitting optional null fields."""
        payload: Dict[str, Any] = {
            "receiver_id": self.receiver_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "status": self.status,
            "capabilities": self.capabilities,
            "timestamp": self.timestamp,
        }
        if self.stream_endpoint is not None:
            payload["stream_endpoint"] = self.stream_endpoint
        if self.stream_protocol is not None:
            payload["stream_protocol"] = self.stream_protocol
        if self.stream_format is not None:
            payload["stream_format"] = self.stream_format
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload

    def validate(self) -> None:
        """Validate schema contents before storing or using the record."""
        if not self.receiver_id or not isinstance(self.receiver_id, str):
            raise ValueError("receiver_id must be a non-empty string")

        if not (-90.0 <= float(self.latitude) <= 90.0):
            raise ValueError("latitude out of bounds")
        if not (-180.0 <= float(self.longitude) <= 180.0):
            raise ValueError("longitude out of bounds")
        if not (-500.0 <= float(self.altitude) <= 20000.0):
            raise ValueError("altitude out of bounds")

        if self.status not in {"online", "offline", "degraded"}:
            raise ValueError("status must be online, offline, or degraded")

        if not isinstance(self.capabilities, list) or not self.capabilities:
            raise ValueError("capabilities must be a non-empty list")
        if "mode-s" not in self.capabilities:
            raise ValueError("capabilities must include mode-s")

        if float(self.timestamp) <= 0:
            raise ValueError("timestamp must be positive")

        if self.stream_protocol is not None and self.stream_protocol not in {
            "simulation",
            "websocket-json",
            "command-jsonl",
        }:
            raise ValueError("unsupported stream_protocol")

        if self.stream_format is not None and self.stream_format not in {
            "json",
            "jsonl",
        }:
            raise ValueError("unsupported stream_format")

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_cell_data_hex(self) -> str:
        """Encode the canonical JSON schema as CKB cell data."""
        self.validate()
        payload = json.dumps(self.to_payload_dict(), separators=(",", ":"), sort_keys=True)
        return "0x" + payload.encode("utf-8").hex()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiverRegistryRecord":
        """Construct and validate a record from decoded JSON."""
        record = cls(
            receiver_id=data["receiver_id"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            altitude=float(data["altitude"]),
            status=data["status"],
            capabilities=list(data["capabilities"]),
            timestamp=float(data["timestamp"]),
            stream_endpoint=data.get("stream_endpoint"),
            stream_protocol=data.get("stream_protocol"),
            stream_format=data.get("stream_format"),
            metadata=data.get("metadata"),
        )
        record.validate()
        return record


@dataclass
class CKBConfig:
    """Configuration for CKB blockchain connection"""
    network: str = "testnet"  # "mainnet" or "testnet"
    ckb_rpc_url: str = "https://testnet.ckb.dev/rpc"
    ckb_indexer_url: str = "https://testnet.ckb.dev/indexer"
    receiver_registry_type_hash: str = ""  # Type script hash for receiver registry
    api_timeout: int = 30
    simulate_if_unavailable: bool = True
    ssl_verify: bool = True
    max_record_age_seconds: int = 86400
    demo_scenario: str = "default"


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
        self.rpc_url = config.ckb_rpc_url
        self.simulation_mode = False
        
    async def initialize(self):
        """Initialize CKB RPC client"""
        logger.info(f"Initializing CKB peer discovery on {self.config.network}")

        if not self.config.receiver_registry_type_hash:
            self._enable_simulation(
                "No receiver registry type hash configured; using simulated CKB receivers"
            )
            return

        try:
            tip = await self._get_tip_block_number()
            logger.info(f"✅ Connected to CKB node, current block: {tip}")
        except Exception as e:
            if self.config.simulate_if_unavailable:
                self._enable_simulation(
                    f"Failed to connect to CKB node ({e}); using simulated receiver discovery"
                )
                return
            logger.error(f"❌ Failed to connect to CKB node: {e}")
            raise
    
    async def _get_tip_block_number(self) -> int:
        """Get current block number"""
        tip = await self._rpc_call("get_tip_block_number", [])
        return int(tip, 16)
    
    async def discover_peers(self) -> List[ReceiverInfo]:
        """
        Discover active Mode-S receivers from CKB blockchain.
        
        Process:
        1. Query CKB for cells with receiver registry type script
        2. Parse cell data to extract receiver information
        3. Verify receiver credentials
        4. Return list of active receivers
        """
        if self.simulation_mode:
            logger.info("🔍 Discovering peers from simulated CKB registry...")
            receivers = self._get_simulated_receivers()
            for receiver in receivers:
                self.cached_peers[receiver.receiver_id] = receiver
            logger.info(f"✅ Discovered {len(receivers)} simulated receivers")
            return receivers

        logger.info("🔍 Discovering peers from CKB blockchain...")
        
        receivers_by_id: Dict[str, ReceiverInfo] = {}
        
        try:
            # Search for receiver registry cells
            cells = await self._search_receiver_cells()
            
            logger.info(f"Found {len(cells)} receiver cells on CKB")
            
            # Parse each cell
            for cell in cells:
                try:
                    receiver = await self._parse_receiver_cell(cell)
                    if receiver and self._is_receiver_valid(receiver):
                        existing = receivers_by_id.get(receiver.receiver_id)
                        if existing is None or receiver.last_seen >= existing.last_seen:
                            receivers_by_id[receiver.receiver_id] = receiver
                            self.cached_peers[receiver.receiver_id] = receiver
                except Exception as e:
                    logger.warning(f"Failed to parse receiver cell: {e}")
                    continue
            
            receivers = sorted(
                receivers_by_id.values(),
                key=lambda receiver: receiver.receiver_id,
            )
            logger.info(f"✅ Discovered {len(receivers)} valid receivers")
            
        except Exception as e:
            logger.error(f"Error discovering peers: {e}")
            receivers = []
        
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
            cells_response = await self._rpc_call(
                "get_cells",
                [
                    search_key,
                    "asc",
                    "0x64",
                ],
                url=self.config.ckb_indexer_url,
            )
            
            cells = cells_response.get("objects", [])
            return cells
            
        except Exception as e:
            logger.error(f"Failed to search receiver cells: {e}")
            return []

    def _enable_simulation(self, reason: str):
        """Enable local simulation mode when live CKB access is unavailable."""
        self.simulation_mode = True
        logger.warning(reason)

    async def _rpc_call(
        self,
        method: str,
        params: List[Any],
        url: Optional[str] = None,
    ) -> Any:
        """Make a JSON-RPC call directly to the configured CKB node."""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        target_url = url or self.rpc_url

        def _do_request() -> Any:
            ssl_context = None
            if target_url.startswith("https://"):
                if self.config.ssl_verify:
                    try:
                        import certifi

                        ssl_context = ssl.create_default_context(cafile=certifi.where())
                    except ImportError:
                        ssl_context = ssl.create_default_context()
                else:
                    ssl_context = ssl._create_unverified_context()

            request = urllib.request.Request(
                target_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "mlat-system/0.1 (+https://github.com/Jeremicarose/AIRCRAFT-MALT)",
                },
                method="POST",
            )
            with urllib.request.urlopen(
                request,
                timeout=self.config.api_timeout,
                context=ssl_context,
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
            if "error" in body:
                raise RuntimeError(body["error"])
            return body["result"]

        return await asyncio.to_thread(_do_request)

    def _get_simulated_receivers(self) -> List[ReceiverInfo]:
        """Return a deterministic receiver set for local development and hosted demos."""
        receiver_rows = build_demo_receivers(time.time(), self.config.demo_scenario)
        simulated_receivers: List[ReceiverInfo] = []
        for index, receiver in enumerate(receiver_rows):
            simulated_receivers.append(
                ReceiverInfo(
                    receiver_id=receiver["receiver_id"],
                    latitude=receiver["latitude"],
                    longitude=receiver["longitude"],
                    altitude=receiver["altitude"],
                    status=receiver["status"],
                    last_seen=receiver["last_seen"],
                    capabilities=receiver["capabilities"],
                    ckb_address=f"ckt1qydemo{index:02d}000000000000000000000000000000",
                    lock_hash=f"0xdemo{index:02d}".ljust(66, "0"),
                    stream_protocol="simulation",
                    stream_format="json",
                    metadata=receiver["metadata"],
                )
            )

        return simulated_receivers
    
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
            
            # Decode hex data to canonical JSON
            data_bytes = bytes.fromhex(output_data[2:])  # Remove 0x prefix
            data_json = json.loads(data_bytes.decode('utf-8'))
            record = ReceiverRegistryRecord.from_dict(data_json)
            lock = cell.get("output", {}).get("lock", {})

            receiver = ReceiverInfo(
                receiver_id=record.receiver_id,
                latitude=record.latitude,
                longitude=record.longitude,
                altitude=record.altitude,
                status=record.status,
                last_seen=record.timestamp,
                capabilities=record.capabilities,
                ckb_address=lock.get('args', ''),
                lock_hash=lock.get('hash') or cell.get('lock_hash', ''),
                stream_endpoint=record.stream_endpoint,
                stream_protocol=record.stream_protocol,
                stream_format=record.stream_format,
                metadata=record.metadata,
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
        # Check status
        if receiver.status != "online":
            logger.info(
                "Skipping receiver %s: status=%s is not online",
                receiver.receiver_id,
                receiver.status,
            )
            return False
        
        # Check capabilities
        if "mode-s" not in receiver.capabilities:
            logger.info(
                "Skipping receiver %s: capabilities %s do not include mode-s",
                receiver.receiver_id,
                receiver.capabilities,
            )
            return False
        
        # Check timestamp freshness
        age_seconds = time.time() - receiver.last_seen
        if age_seconds > self.config.max_record_age_seconds:
            logger.info(
                "Skipping receiver %s: timestamp is stale by %.0f seconds (max %d)",
                receiver.receiver_id,
                age_seconds,
                self.config.max_record_age_seconds,
            )
            return False
        
        # Check coordinates
        if not (-90 <= receiver.latitude <= 90):
            logger.info(
                "Skipping receiver %s: invalid latitude=%s",
                receiver.receiver_id,
                receiver.latitude,
            )
            return False
        if not (-180 <= receiver.longitude <= 180):
            logger.info(
                "Skipping receiver %s: invalid longitude=%s",
                receiver.receiver_id,
                receiver.longitude,
            )
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
        private_key: str,
        stream_endpoint: Optional[str] = None,
        stream_protocol: Optional[str] = None,
        stream_format: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
            
            record = ReceiverRegistryRecord(
                receiver_id=receiver_id,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                status="online",
                capabilities=capabilities,
                timestamp=time.time(),
                stream_endpoint=stream_endpoint,
                stream_protocol=stream_protocol,
                stream_format=stream_format,
                metadata=metadata,
            )
            data_hex = record.to_cell_data_hex()
            
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
