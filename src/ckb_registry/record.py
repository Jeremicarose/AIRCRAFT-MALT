"""Registry V2 record, identity, and lifecycle invariants."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Dict, List, Optional

REGISTRY_SCHEMA_VERSION = 2
_IDENTITY_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_RECEIVER_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,63}$")
_CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
_METADATA_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_ALLOWED_FIELDS = {
    "schema_version",
    "receiver_id",
    "latitude",
    "longitude",
    "altitude",
    "status",
    "capabilities",
    "sequence",
    "updated_at",
    "stream_endpoint",
    "stream_protocol",
    "stream_format",
    "metadata_hash",
}


def normalize_identity_id(value: str) -> str:
    """Validate and normalize a 32-byte receiver Type ID argument."""
    if not isinstance(value, str) or not _IDENTITY_RE.fullmatch(value):
        raise ValueError("identity_id must be 0x-prefixed 32-byte hex")
    return value.lower()


def calculate_type_id(
    *,
    first_input_tx_hash: str,
    first_input_index: int,
    first_input_since: int = 0,
    output_index: int = 0,
) -> str:
    """Calculate CKB's Type-ID-style argument for a registry creation output."""
    tx_hash = normalize_identity_id(first_input_tx_hash)
    if not 0 <= first_input_index <= 0xFFFF_FFFF:
        raise ValueError("first_input_index must fit u32")
    if not 0 <= first_input_since <= 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError("first_input_since must fit u64")
    if not 0 <= output_index <= 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError("output_index must fit u64")

    cell_input = (
        first_input_since.to_bytes(8, "little")
        + bytes.fromhex(tx_hash[2:])
        + first_input_index.to_bytes(4, "little")
    )
    hasher = hashlib.blake2b(digest_size=32, person=b"ckb-default-hash")
    hasher.update(cell_input)
    hasher.update(output_index.to_bytes(8, "little"))
    return "0x" + hasher.hexdigest()


@dataclass(frozen=True)
class ReceiverRegistryRecord:
    """Versioned metadata stored in one Registry V2 identity cell."""

    receiver_id: str
    latitude: float
    longitude: float
    altitude: float
    status: str
    capabilities: List[str]
    sequence: int
    updated_at: int
    stream_endpoint: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_format: Optional[str] = None
    metadata_hash: Optional[str] = None
    schema_version: int = REGISTRY_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != REGISTRY_SCHEMA_VERSION:
            raise ValueError("schema_version must be 2")
        if not isinstance(self.receiver_id, str) or not _RECEIVER_ID_RE.fullmatch(self.receiver_id):
            raise ValueError("receiver_id must be 1-64 uppercase ASCII identifier characters")

        coordinates = (self.latitude, self.longitude, self.altitude)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in coordinates
        ):
            raise ValueError("coordinates must be finite numbers")
        if not -90.0 <= float(self.latitude) <= 90.0:
            raise ValueError("latitude out of bounds")
        if not -180.0 <= float(self.longitude) <= 180.0:
            raise ValueError("longitude out of bounds")
        if not -500.0 <= float(self.altitude) <= 20_000.0:
            raise ValueError("altitude out of bounds")

        if self.status not in {"online", "offline", "degraded", "revoked"}:
            raise ValueError("unsupported receiver status")
        if not isinstance(self.capabilities, list) or not 1 <= len(self.capabilities) <= 8:
            raise ValueError("capabilities must contain 1-8 values")
        if any(
            not isinstance(capability, str) or not _CAPABILITY_RE.fullmatch(capability)
            for capability in self.capabilities
        ):
            raise ValueError("capabilities contain an invalid value")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        if "mode-s" not in self.capabilities:
            raise ValueError("capabilities must include mode-s")

        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 0
        ):
            raise ValueError("sequence must be a non-negative integer")
        if (
            isinstance(self.updated_at, bool)
            or not isinstance(self.updated_at, int)
            or self.updated_at <= 0
        ):
            raise ValueError("updated_at must be a positive integer")

        self._validate_optional_text(self.stream_endpoint, "stream_endpoint", 256)
        self._validate_optional_text(self.stream_protocol, "stream_protocol", 32)
        self._validate_optional_text(self.stream_format, "stream_format", 16)
        if self.stream_protocol is not None and self.stream_protocol not in {
            "websocket-json",
            "command-jsonl",
        }:
            raise ValueError("unsupported stream_protocol")
        if self.stream_format is not None and self.stream_format not in {"json", "jsonl"}:
            raise ValueError("unsupported stream_format")
        if self.stream_endpoint is not None and self.stream_protocol is None:
            raise ValueError("stream_endpoint requires stream_protocol")
        if self.metadata_hash is not None and not _METADATA_HASH_RE.fullmatch(self.metadata_hash):
            raise ValueError("metadata_hash must be 0x-prefixed 32-byte hex")
        if self.status == "revoked" and any(
            value is not None
            for value in (self.stream_endpoint, self.stream_protocol, self.stream_format)
        ):
            raise ValueError("revoked records cannot advertise a stream")

    @staticmethod
    def _validate_optional_text(value: Optional[str], field: str, max_bytes: int) -> None:
        if value is None:
            return
        if not isinstance(value, str) or not value or len(value.encode("utf-8")) > max_bytes:
            raise ValueError(f"{field} must contain 1-{max_bytes} UTF-8 bytes")

    def validate_creation(self) -> None:
        self.validate()
        if self.sequence != 0:
            raise ValueError("creation sequence must be 0")
        if self.status == "revoked":
            raise ValueError("a receiver cannot be created revoked")

    def validate_successor(self, previous: "ReceiverRegistryRecord") -> None:
        previous.validate()
        self.validate()
        if previous.status == "revoked":
            raise ValueError("revoked receiver identities are terminal")
        if self.receiver_id != previous.receiver_id:
            raise ValueError("receiver_id is immutable")
        if self.sequence != previous.sequence + 1:
            raise ValueError("sequence must increment by exactly one")
        if self.updated_at < previous.updated_at:
            raise ValueError("updated_at cannot move backwards")

    def to_payload_dict(self) -> Dict[str, Any]:
        self.validate()
        payload: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "receiver_id": self.receiver_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "status": self.status,
            "capabilities": self.capabilities,
            "sequence": self.sequence,
            "updated_at": self.updated_at,
        }
        for field in (
            "stream_endpoint",
            "stream_protocol",
            "stream_format",
            "metadata_hash",
        ):
            value = getattr(self, field)
            if value is not None:
                payload[field] = value
        return payload

    def to_cell_data_hex(self) -> str:
        payload = json.dumps(self.to_payload_dict(), separators=(",", ":"), sort_keys=True)
        return "0x" + payload.encode("utf-8").hex()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiverRegistryRecord":
        if not isinstance(data, dict):
            raise ValueError("receiver record must be a JSON object")
        unknown = set(data) - _ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"receiver record contains unknown fields: {sorted(unknown)}")
        record = cls(
            schema_version=data["schema_version"],
            receiver_id=data["receiver_id"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            altitude=data["altitude"],
            status=data["status"],
            capabilities=data["capabilities"],
            sequence=data["sequence"],
            updated_at=data["updated_at"],
            stream_endpoint=data.get("stream_endpoint"),
            stream_protocol=data.get("stream_protocol"),
            stream_format=data.get("stream_format"),
            metadata_hash=data.get("metadata_hash"),
        )
        record.validate()
        return record
