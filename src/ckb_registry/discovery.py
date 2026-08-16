"""
CKB Blockchain Integration for MLAT System

This adapter discovers Registry V2 cells and maps their immutable Type IDs,
owner locks, lifecycle sequences, and current records into runtime receivers.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json
import asyncio
import logging
import ssl
import time
import urllib.request

from ckb_registry.record import ReceiverRegistryRecord, normalize_identity_id

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
    lock_hash: str  # Lock script hash for verification
    identity_id: str = ""
    stream_endpoint: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_format: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def canonical_id(self) -> str:
        return self.identity_id or self.receiver_id


@dataclass
class CKBConfig:
    """Configuration for CKB blockchain connection"""

    network: str = "testnet"  # "mainnet" or "testnet"
    ckb_rpc_url: str = "https://testnet.ckb.dev/rpc"
    ckb_indexer_url: str = "https://testnet.ckb.dev/indexer"
    receiver_registry_type_hash: str = ""  # Type script hash for receiver registry
    api_timeout: int = 30
    ssl_verify: bool = True
    max_record_age_seconds: int = 86400
    max_future_record_skew_seconds: int = 300
    registry_page_size: int = 100
    registry_max_pages: int = 1000


class CKBPeerDiscovery:
    """
    CKB blockchain-based peer discovery.

    Uses Nervos Network to register and discover Mode-S receivers.
    Receivers publish metadata to CKB cells. The chain proves lifecycle and
    owner authorization; physical receiver claims still require external evidence.
    """

    def __init__(self, config: CKBConfig):
        self.config = config
        self.cached_peers: Dict[str, ReceiverInfo] = {}
        self.rpc_url = config.ckb_rpc_url

    async def initialize(self):
        """Initialize CKB RPC client"""
        logger.info(f"Initializing CKB peer discovery on {self.config.network}")

        if not self.config.receiver_registry_type_hash:
            raise RuntimeError("RECEIVER_REGISTRY_TYPE_HASH is required for Registry V2 discovery")

        try:
            normalize_identity_id(self.config.receiver_registry_type_hash)
        except ValueError as exc:
            raise RuntimeError(
                "RECEIVER_REGISTRY_TYPE_HASH must be a 0x-prefixed 32-byte V2 contract code hash"
            ) from exc

        tip = await self._get_tip_block_number()
        logger.info("Connected to CKB node, current block: %s", tip)

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
        logger.info("Discovering peers from CKB blockchain...")
        self.cached_peers.clear()
        receivers_by_identity: Dict[str, ReceiverInfo] = {}
        duplicate_identities: set[str] = set()

        cells = await self._search_receiver_cells()
        logger.info("Found %d receiver cells on CKB", len(cells))

        for cell in cells:
            try:
                receiver = await self._parse_receiver_cell(cell)
                if receiver and self._is_receiver_valid(receiver):
                    identity_id = receiver.canonical_id
                    if identity_id in receivers_by_identity:
                        duplicate_identities.add(identity_id)
                        receivers_by_identity.pop(identity_id, None)
                        self.cached_peers.pop(identity_id, None)
                        logger.error(
                            "Quarantining duplicate live Receiver Identity %s",
                            identity_id,
                        )
                    elif identity_id not in duplicate_identities:
                        receivers_by_identity[identity_id] = receiver
                        self.cached_peers[identity_id] = receiver
            except Exception as exc:
                logger.warning("Failed to parse receiver cell: %s", exc)

        receivers = sorted(
            receivers_by_identity.values(),
            key=lambda receiver: receiver.identity_id,
        )
        logger.info("Discovered %d valid receivers", len(receivers))
        return receivers

    async def _search_receiver_cells(self) -> List[Dict]:
        """
        Search CKB blockchain for receiver registry cells.

        Uses get_cells RPC to find all cells with the receiver registry type script.
        """
        search_key = {
            "script": {
                "code_hash": self.config.receiver_registry_type_hash,
                "hash_type": "type",
                "args": "0x",
            },
            "script_type": "type",
            "script_search_mode": "prefix",
            "filter": {"script_len_range": ["0x0", "0xffffffff"]},
        }

        page_size = max(1, min(self.config.registry_page_size, 1000))
        cells: List[Dict] = []
        cursor: Optional[str] = None
        for _ in range(max(1, self.config.registry_max_pages)):
            params: List[Any] = [search_key, "asc", hex(page_size)]
            if cursor is not None:
                params.append(cursor)
            cells_response = await self._rpc_call(
                "get_cells",
                params,
                url=self.config.ckb_indexer_url,
            )
            page = cells_response.get("objects", [])
            cells.extend(page)
            next_cursor = cells_response.get("last_cursor")
            if len(page) < page_size or not next_cursor or next_cursor == cursor:
                return cells
            cursor = next_cursor

        raise RuntimeError("Receiver registry pagination exceeded registry_max_pages")

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
            data_json = json.loads(data_bytes.decode("utf-8"))
            record = ReceiverRegistryRecord.from_dict(data_json)
            output = cell.get("output", {})
            lock = output.get("lock", {})
            type_script = output.get("type") or {}
            if type_script.get("hash_type") != "type":
                raise ValueError("registry type script must use hash_type=type")
            configured_code_hash = self.config.receiver_registry_type_hash.lower()
            if (
                configured_code_hash
                and str(type_script.get("code_hash", "")).lower() != configured_code_hash
            ):
                raise ValueError("registry cell code hash does not match configured V2 contract")
            identity_id = normalize_identity_id(type_script.get("args", ""))
            out_point = cell.get("out_point") or {}

            receiver = ReceiverInfo(
                receiver_id=record.receiver_id,
                latitude=record.latitude,
                longitude=record.longitude,
                altitude=record.altitude,
                status=record.status,
                last_seen=float(record.updated_at),
                capabilities=record.capabilities,
                ckb_address=lock.get("args", ""),
                lock_hash=lock.get("hash") or cell.get("lock_hash", ""),
                identity_id=identity_id,
                stream_endpoint=record.stream_endpoint,
                stream_protocol=record.stream_protocol,
                stream_format=record.stream_format,
                metadata={
                    "schema_version": record.schema_version,
                    "sequence": record.sequence,
                    "metadata_hash": record.metadata_hash,
                    "owner_lock": lock,
                    "out_point": out_point,
                    "block_number": cell.get("block_number"),
                },
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
        if age_seconds < -self.config.max_future_record_skew_seconds:
            logger.info(
                "Skipping receiver %s: updated_at is %.0f seconds in the future",
                receiver.canonical_id,
                -age_seconds,
            )
            return False
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

    async def shutdown(self):
        """Cleanup CKB connection"""
        logger.info("Shutting down CKB peer discovery")
        self.client = None
