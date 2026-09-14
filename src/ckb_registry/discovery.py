"""
CKB Blockchain Integration for MLAT System

This adapter discovers Registry V2 cells and maps their immutable Type IDs,
owner locks, lifecycle sequences, and current records into runtime receivers.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import json
import asyncio
import logging
import ssl
import time
import urllib.request

from ckb_registry.record import (
    DEFAULT_MAX_RECORD_BYTES,
    decode_registry_v2_record,
    normalize_receiver_identity,
)

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
    receiver_identity: Optional[str] = None
    data_source: str = "runtime"
    stream_endpoint: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_format: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    registry_updated_at: Optional[int] = None

    def __post_init__(self) -> None:
        if self.receiver_identity is not None:
            self.receiver_identity = normalize_receiver_identity(self.receiver_identity)
        if self.data_source == "ckb_registry" and self.receiver_identity is None:
            raise ValueError("CKB Registry receivers require receiver_identity")

    @property
    def runtime_id(self) -> str:
        """Return the routing key without treating a human label as CKB identity."""
        if self.receiver_identity is not None:
            return self.receiver_identity
        return f"{self.data_source}:{self.receiver_id}"


@dataclass
class CKBConfig:
    """Configuration for CKB blockchain connection"""

    network: str = "testnet"  # "mainnet" or "testnet"
    ckb_rpc_url: str = "https://testnet.ckb.dev/rpc"
    ckb_indexer_url: str = "https://testnet.ckb.dev/indexer"
    receiver_registry_type_hash: str = ""  # Type script hash for receiver registry
    receiver_registry_hash_type: str = "data1"
    allow_mutable_registry_code: bool = False
    api_timeout: int = 30
    ssl_verify: bool = True
    max_record_age_seconds: Optional[int] = None
    max_future_record_skew_seconds: int = 300
    registry_page_size: int = 100
    registry_max_pages: int = 1000
    registry_max_cells: int = 10_000
    max_record_bytes: int = DEFAULT_MAX_RECORD_BYTES
    time_provider: Callable[[], float] = time.time


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
        self.quarantined_identities: List[str] = []
        self.rpc_url = config.ckb_rpc_url

    async def initialize(self):
        """Initialize CKB RPC client"""
        logger.info(f"Initializing CKB peer discovery on {self.config.network}")

        if not self.config.receiver_registry_type_hash:
            raise RuntimeError("RECEIVER_REGISTRY_TYPE_HASH is required for Registry V2 discovery")

        if self.config.receiver_registry_hash_type not in {"data1", "type"}:
            raise RuntimeError("RECEIVER_REGISTRY_HASH_TYPE must be data1 or type")
        try:
            normalize_receiver_identity(self.config.receiver_registry_type_hash)
        except ValueError as exc:
            raise RuntimeError(
                "RECEIVER_REGISTRY_TYPE_HASH must be a 0x-prefixed 32-byte V2 contract code hash"
            ) from exc

        if (
            self.config.receiver_registry_hash_type == "type"
            and not self.config.allow_mutable_registry_code
        ):
            raise RuntimeError(
                "Registry hash_type=type permits mutable contract code; "
                "set ALLOW_MUTABLE_REGISTRY_CODE=true only for explicit historical read-only compatibility"
            )

        tip = await self._get_tip_block_number()
        logger.info("Connected to CKB node, current block: %s", tip)

    async def _get_tip_block_number(self) -> int:
        """Get current block number"""
        tip = await self._rpc_call("get_tip_block_number", [])
        return int(tip, 16)

    async def discover_peers(
        self,
        *,
        include_inactive: bool = False,
        include_revoked: bool = False,
    ) -> List[ReceiverInfo]:
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
        self.quarantined_identities = []
        receivers_by_identity: Dict[str, ReceiverInfo] = {}
        seen_identities: set[str] = set()
        duplicate_identities: set[str] = set()

        cells = await self._search_receiver_cells()
        logger.info("Found %d receiver cells on CKB", len(cells))

        for cell in cells:
            try:
                receiver_identity = self._receiver_identity_from_cell(cell)
                if receiver_identity in duplicate_identities:
                    continue
                if receiver_identity in seen_identities:
                    duplicate_identities.add(receiver_identity)
                    receivers_by_identity.pop(receiver_identity, None)
                    logger.error(
                        "Quarantining duplicate live Receiver Identity %s",
                        receiver_identity,
                    )
                    continue
                seen_identities.add(receiver_identity)

                receiver = await self._parse_receiver_cell(cell, receiver_identity)
                if receiver is not None:
                    receivers_by_identity[receiver_identity] = receiver
            except Exception as exc:
                logger.warning("Failed to parse receiver cell: %s", exc)

        active_receivers = [
            receiver
            for receiver in receivers_by_identity.values()
            if self._is_receiver_valid(
                receiver,
                include_inactive=include_inactive,
                include_revoked=include_revoked,
            )
        ]
        self.cached_peers = {
            receiver.receiver_identity: receiver
            for receiver in active_receivers
            if receiver.receiver_identity is not None
        }
        self.quarantined_identities = sorted(duplicate_identities)
        receivers = sorted(active_receivers, key=lambda receiver: receiver.receiver_identity or "")
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
                "hash_type": self.config.receiver_registry_hash_type,
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
            if not isinstance(cells_response, dict):
                raise RuntimeError("CKB indexer returned a non-object get_cells result")
            page = cells_response.get("objects", [])
            if not isinstance(page, list):
                raise RuntimeError("CKB indexer get_cells objects must be a list")
            cells.extend(page)
            if len(cells) > self.config.registry_max_cells:
                raise RuntimeError("Receiver registry discovery exceeded registry_max_cells")
            next_cursor = cells_response.get("last_cursor")
            if not page:
                return cells
            if not isinstance(next_cursor, str) or not next_cursor:
                raise RuntimeError("CKB indexer omitted last_cursor after a non-empty page")
            if next_cursor == cursor:
                raise RuntimeError("CKB indexer repeated last_cursor after a non-empty page")
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

    def _receiver_identity_from_cell(self, cell: Dict) -> str:
        """Validate Registry V2 script binding and return its canonical Type ID."""
        output = cell.get("output", {})
        type_script = output.get("type") or {}
        if type_script.get("hash_type") != self.config.receiver_registry_hash_type:
            raise ValueError(
                "registry type script hash_type does not match the configured deployment"
            )
        configured_code_hash = self.config.receiver_registry_type_hash.lower()
        if (
            configured_code_hash
            and str(type_script.get("code_hash", "")).lower() != configured_code_hash
        ):
            raise ValueError("registry cell code hash does not match configured V2 contract")
        return normalize_receiver_identity(type_script.get("args", ""))

    async def _parse_receiver_cell(
        self,
        cell: Dict,
        receiver_identity: Optional[str] = None,
    ) -> Optional[ReceiverInfo]:
        """
        Parse receiver information from CKB cell data.

        Registry V2 JSON is decoded separately from the Type ID script binding.
        For example:
        {
            "receiver_id": "RECV_NYC_001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0,
            "status": "online",
            "capabilities": ["mode-s", "adsb", "mlat"],
            "sequence": 0,
            "updated_at": 1234567890
        }
        """
        try:
            output_data = cell.get("output_data", "0x")

            if not isinstance(output_data, str) or output_data == "0x":
                return None
            if not output_data.startswith("0x") or len(output_data) % 2 != 0:
                raise ValueError("registry cell data must be 0x-prefixed hexadecimal")

            data_bytes = bytes.fromhex(output_data[2:])
            record = decode_registry_v2_record(
                data_bytes,
                max_bytes=self.config.max_record_bytes,
            )
            output = cell.get("output", {})
            lock = output.get("lock", {})
            receiver_identity = receiver_identity or self._receiver_identity_from_cell(cell)
            out_point = cell.get("out_point") or {}

            receiver = ReceiverInfo(
                receiver_id=record.receiver_id,
                latitude=record.latitude,
                longitude=record.longitude,
                altitude=record.altitude,
                status=record.status,
                last_seen=0.0,
                capabilities=record.capabilities,
                ckb_address=lock.get("args", ""),
                lock_hash=lock.get("hash") or cell.get("lock_hash", ""),
                receiver_identity=receiver_identity,
                data_source="ckb_registry",
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
                    "updated_at": record.updated_at,
                },
                registry_updated_at=record.updated_at,
            )

            return receiver

        except Exception as e:
            logger.warning(f"Failed to parse cell: {e}")
            return None

    def _is_receiver_valid(
        self,
        receiver: ReceiverInfo,
        *,
        include_inactive: bool = False,
        include_revoked: bool = False,
    ) -> bool:
        """
        Validate receiver information.

        Checks status, capabilities, optional record-age policy, and coordinates.
        """
        # Check status
        if receiver.status == "revoked" and not include_revoked:
            logger.info("Skipping receiver %s: identity is revoked", receiver.receiver_identity)
            return False
        if receiver.status not in {"online", "revoked"} and not include_inactive:
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

        # `updated_at` is lifecycle time, not a heartbeat. Only future skew is
        # rejected by default; deployments may opt into a maximum record age.
        if receiver.registry_updated_at is None:
            logger.info(
                "Skipping receiver %s: Registry updated_at is missing", receiver.receiver_id
            )
            return False
        age_seconds = self.config.time_provider() - receiver.registry_updated_at
        if age_seconds < -self.config.max_future_record_skew_seconds:
            logger.info(
                "Skipping receiver %s: updated_at is %.0f seconds in the future",
                receiver.receiver_identity,
                -age_seconds,
            )
            return False
        if (
            self.config.max_record_age_seconds is not None
            and age_seconds > self.config.max_record_age_seconds
        ):
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

    async def get_receiver_details(self, receiver_identity: str) -> Optional[ReceiverInfo]:
        """Get cached receiver details by canonical CKB Receiver Identity."""
        return self.cached_peers.get(normalize_receiver_identity(receiver_identity))

    async def shutdown(self):
        """Cleanup CKB connection"""
        logger.info("Shutting down CKB peer discovery")
        self.client = None
