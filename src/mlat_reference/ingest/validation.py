"""Bounded observation decoding. Never invent arrival time or clock precision."""

from __future__ import annotations

import json
import math
import re
from typing import Any

MAX_PAYLOAD_BYTES = 1_048_576
MAX_BATCH_RECORDS = 1024
MAX_NESTING = 8
U64_MAX = (1 << 64) - 1


def strict_json(payload: str | bytes) -> Any:
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("payload_too_large")
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="strict")
    if len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("payload_too_large")

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError("non_finite_json_number")

    try:
        return json.loads(payload, object_pairs_hook=object_pairs, parse_constant=reject_constant)
    except RecursionError as exc:
        raise ValueError("payload_too_deep") from exc


def integer_nanoseconds(value: Any) -> int | None:
    # Decimal strings support clients whose JSON numbers cannot preserve u64.
    if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]{0,19}", value):
        value = int(value)
    if type(value) is not int or not 0 < value <= U64_MAX:
        return None
    return value


def mode_s_crc(frame: str) -> int:
    """Mode-S polynomial division, including the 24 parity bits."""
    value = int(frame, 16)
    for bit in range(len(frame) * 4 - 1, 23, -1):
        if value & (1 << bit):
            value ^= 0x1FFF409 << (bit - 24)
    return value & 0xFFFFFF


def mode_s_frame(value: Any) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(
        r"(?:[0-9a-fA-F]{14}|[0-9a-fA-F]{28})", value
    ):
        return None
    frame = value.upper()
    df = int(frame[:2], 16) >> 3
    if len(frame) != (28 if df >= 16 else 14):
        return None
    # Other DFs overlay parity with an address/interrogator code. Do not claim
    # to verify that parity without the additional decoder state it requires.
    if df in {17, 18} and mode_s_crc(frame) != 0:
        return None
    return frame


def clock_qualified(
    synchronized: Any, timestamp_ns: Any, source: Any, uncertainty: Any, maximum: float
) -> bool:
    return bool(
        synchronized is True
        and integer_nanoseconds(timestamp_ns) is not None
        and isinstance(source, str)
        and 0 < len(source) <= 128
        and source.strip().lower() not in {"", "unknown", "network-arrival"}
        and not isinstance(uncertainty, bool)
        and isinstance(uncertainty, (int, float))
        and math.isfinite(uncertainty)
        and 0 <= uncertainty <= maximum
    )
