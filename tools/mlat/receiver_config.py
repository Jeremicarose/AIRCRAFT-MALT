"""Validation for the multi-receiver Beast field-trial configuration."""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import normalize_identity_id

MIN_MLAT_RECEIVERS = 4
BEAST_TICK_MODULUS = 1 << 48
EXAMPLE_IDENTITY_IDS = {"0x" + octet * 32 for octet in ("11", "22", "33", "44")}
PLACEHOLDER_CLOCK_SOURCES = {
    "replace-with-qualified-clock-source",
    "unknown",
    "placeholder",
}
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field} must be an integer")
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_clock(
    clock: Any,
    *,
    receiver_name: str,
    max_uncertainty_ns: float,
    require_current: bool,
    now_ns: int,
    config_dir: Path,
) -> dict[str, Any]:
    prefix = f"receiver {receiver_name} clock"
    if not isinstance(clock, dict):
        if not require_current and clock is None:
            return {}
        raise ValueError(f"{prefix} must be an object")
    if clock.get("enabled") is not True:
        if require_current:
            raise ValueError(f"{prefix} must set enabled=true")
        return dict(clock)

    source = str(clock.get("source") or "").strip()
    if not source or source.lower() in PLACEHOLDER_CLOCK_SOURCES:
        raise ValueError(f"{prefix} source must identify a qualified clock")

    frequency_hz = _number(clock.get("frequency_hz"), f"{prefix} frequency_hz")
    if frequency_hz <= 0:
        raise ValueError(f"{prefix} frequency_hz must be positive")

    anchor_tick = _integer(clock.get("anchor_tick"), f"{prefix} anchor_tick")
    if not 0 <= anchor_tick < BEAST_TICK_MODULUS:
        raise ValueError(f"{prefix} anchor_tick must fit the 48-bit Beast counter")

    anchor_time_ns = _integer(clock.get("anchor_time_ns"), f"{prefix} anchor_time_ns")
    if anchor_time_ns <= 0:
        raise ValueError(f"{prefix} anchor_time_ns must be positive")

    uncertainty_ns = _number(clock.get("uncertainty_ns"), f"{prefix} uncertainty_ns")
    if uncertainty_ns < 0:
        raise ValueError(f"{prefix} uncertainty_ns must be non-negative")
    if uncertainty_ns > max_uncertainty_ns:
        raise ValueError(
            f"{prefix} uncertainty_ns {uncertainty_ns:g} exceeds {max_uncertainty_ns:g}"
        )

    validated = dict(clock)
    validated.update(
        {
            "source": source,
            "frequency_hz": frequency_hz,
            "anchor_tick": anchor_tick,
            "anchor_time_ns": anchor_time_ns,
            "uncertainty_ns": uncertainty_ns,
        }
    )
    if not require_current:
        return validated

    valid_from_ns = _integer(clock.get("valid_from_ns"), f"{prefix} valid_from_ns")
    valid_until_ns = _integer(clock.get("valid_until_ns"), f"{prefix} valid_until_ns")
    if valid_from_ns <= 0 or valid_until_ns <= valid_from_ns:
        raise ValueError(f"{prefix} validity window is invalid")
    if not valid_from_ns <= anchor_time_ns <= valid_until_ns:
        raise ValueError(f"{prefix} anchor_time_ns is outside its validity window")
    if not valid_from_ns <= now_ns <= valid_until_ns:
        raise ValueError(f"{prefix} calibration is not valid at launch time")

    evidence = clock.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError(f"{prefix} evidence must be an object")
    method = str(evidence.get("method") or "").strip()
    if not method or method.lower() in PLACEHOLDER_CLOCK_SOURCES:
        raise ValueError(f"{prefix} evidence method is required")
    evidence_value = str(evidence.get("file") or "").strip()
    if not evidence_value:
        raise ValueError(f"{prefix} evidence file is required")
    evidence_path = Path(evidence_value).expanduser()
    if not evidence_path.is_absolute():
        evidence_path = config_dir / evidence_path
    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        raise ValueError(f"{prefix} evidence file is missing or empty: {evidence_path}")
    expected_sha256 = str(evidence.get("sha256") or "").strip().lower()
    if not _SHA256_RE.fullmatch(expected_sha256):
        raise ValueError(f"{prefix} evidence sha256 must be 64 hex characters")
    digest = _file_sha256(evidence_path)
    if digest != expected_sha256:
        raise ValueError(f"{prefix} evidence sha256 does not match {evidence_path}")

    validated["valid_from_ns"] = valid_from_ns
    validated["valid_until_ns"] = valid_until_ns
    validated["evidence"] = {
        "method": method,
        "file": evidence_value,
        "sha256": expected_sha256,
    }
    return validated


def load_receiver_config(
    path: str | Path,
    *,
    require_mlat_ready: bool = True,
    max_uncertainty_ns: float = 100.0,
    now_ns: int | None = None,
) -> list[dict[str, Any]]:
    """Load a receiver config and reject ambiguous field-trial inputs."""
    config_path = Path(path).expanduser()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"receiver config does not exist: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"receiver config is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("receiver config must be a JSON object")
    receivers = payload.get("receivers")
    minimum = MIN_MLAT_RECEIVERS if require_mlat_ready else 1
    if not isinstance(receivers, list) or len(receivers) < minimum:
        raise ValueError(f"receiver config must contain at least {minimum} receivers")

    launch_time_ns = time.time_ns() if now_ns is None else now_ns
    normalized: list[dict[str, Any]] = []
    identity_ids: set[str] = set()
    sensor_ids: set[str] = set()
    endpoints: set[tuple[str, int]] = set()

    for index, raw_receiver in enumerate(receivers):
        name = f"at index {index}"
        if not isinstance(raw_receiver, dict):
            raise ValueError(f"receiver {name} must be an object")

        try:
            identity_id = normalize_identity_id(raw_receiver.get("receiver_id"))
        except ValueError as exc:
            raise ValueError(f"receiver {name} has an invalid Registry V2 identity") from exc
        if require_mlat_ready and identity_id in EXAMPLE_IDENTITY_IDS:
            raise ValueError(f"receiver {name} still uses an example Registry V2 identity")
        if identity_id in identity_ids:
            raise ValueError(f"duplicate receiver identity: {identity_id}")

        sensor_id = str(raw_receiver.get("sensor_id") or "").strip()
        if not sensor_id or len(sensor_id.encode("utf-8")) > 64:
            raise ValueError(f"receiver {identity_id} sensor_id must contain 1-64 UTF-8 bytes")
        if sensor_id in sensor_ids:
            raise ValueError(f"duplicate sensor_id: {sensor_id}")

        host = str(raw_receiver.get("host") or "").strip()
        if not host or any(character.isspace() for character in host):
            raise ValueError(f"receiver {identity_id} host is invalid")
        port = _integer(raw_receiver.get("port"), f"receiver {identity_id} port")
        if not 1 <= port <= 65535:
            raise ValueError(f"receiver {identity_id} port must be between 1 and 65535")
        endpoint = (host, port)
        if endpoint in endpoints:
            raise ValueError(f"duplicate receiver endpoint: {host}:{port}")

        clock = validate_clock(
            raw_receiver.get("clock"),
            receiver_name=identity_id,
            max_uncertainty_ns=max_uncertainty_ns,
            require_current=require_mlat_ready,
            now_ns=launch_time_ns,
            config_dir=config_path.resolve().parent,
        )
        normalized.append(
            {
                **raw_receiver,
                "receiver_id": identity_id,
                "sensor_id": sensor_id,
                "host": host,
                "port": port,
                "clock": clock,
            }
        )
        identity_ids.add(identity_id)
        sensor_ids.add(sensor_id)
        endpoints.add(endpoint)

    return normalized
