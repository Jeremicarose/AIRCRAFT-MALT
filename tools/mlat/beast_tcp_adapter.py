#!/usr/bin/env python3
"""
Read Beast-format TCP messages from readsb / dump1090-fa and emit command-jsonl
records suitable for the MLAT Registry V2 reference runtime.

Output lines are JSON objects containing the precision-safe fields MLAT needs:
{
  "receiver_id": "RECV_NYC_001",
  "timestamp_ns": 1714400000123456789,
  "clock_synchronized": true,
  "message": "8D4840D6202CC371C32CE0576098"
}

Without clock calibration, records are still emitted for diagnostics but are
marked unsynchronized and the production solver rejects them.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from typing import Optional

TYPE_TO_MESSAGE_LEN = {
    0x31: 2,  # Mode A/C style short payload
    0x32: 7,  # short Mode-S frame
    0x33: 14,  # long Mode-S frame
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Beast TCP to JSONL adapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30005)
    parser.add_argument("--sensor-id", default="readsb-local")
    parser.add_argument("--receiver-id", default=None)
    parser.add_argument(
        "--receiver-map", help="Optional JSON file mapping sensor ids to canonical receiver ids"
    )
    parser.add_argument(
        "--clock-config",
        help="JSON file containing the receiver's 48-bit Beast clock calibration",
    )
    parser.add_argument(
        "--include-short-frames", action="store_true", help="Include short 7-byte Mode-S frames"
    )
    parser.add_argument("--once", action="store_true", help="Emit one valid record and exit")
    return parser.parse_args()


def load_receiver_map(path: Optional[str]) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("receiver map must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def load_clock_config(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("clock config must be a JSON object")
    return payload


def isoformat_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _config_int(value, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"clock {name} must be an integer")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"clock {name} must be an integer")
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"clock {name} must be an integer") from exc


def normalize_beast_timestamp(raw_timestamp: bytes, clock: Optional[dict]) -> Optional[dict]:
    """Map a 48-bit receiver tick to a common nanosecond timebase."""
    if not clock or clock.get("enabled", True) is not True:
        return None

    source = str(clock.get("source") or "").strip()
    if not source:
        raise ValueError("clock source is required")

    try:
        frequency_hz = float(clock["frequency_hz"])
        uncertainty_ns = float(clock["uncertainty_ns"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("clock frequency_hz and uncertainty_ns are required numbers") from exc
    if not math.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("clock frequency_hz must be positive")
    if not math.isfinite(uncertainty_ns) or uncertainty_ns < 0:
        raise ValueError("clock uncertainty_ns must be non-negative")

    anchor_tick = _config_int(clock.get("anchor_tick"), "anchor_tick")
    anchor_time_ns = _config_int(clock.get("anchor_time_ns"), "anchor_time_ns")
    tick_modulus = 1 << 48
    if not 0 <= anchor_tick < tick_modulus:
        raise ValueError("clock anchor_tick must fit the 48-bit Beast counter")
    if anchor_time_ns <= 0:
        raise ValueError("clock anchor_time_ns must be positive")

    frame_tick = int.from_bytes(raw_timestamp, "big")
    delta_ticks = (frame_tick - anchor_tick) % tick_modulus
    if delta_ticks >= tick_modulus // 2:
        delta_ticks -= tick_modulus
    timestamp_ns = anchor_time_ns + round(delta_ticks * 1_000_000_000 / frequency_hz)

    valid_from_ns = clock.get("valid_from_ns")
    valid_until_ns = clock.get("valid_until_ns")
    if valid_from_ns is not None or valid_until_ns is not None:
        valid_from_ns = _config_int(valid_from_ns, "valid_from_ns")
        valid_until_ns = _config_int(valid_until_ns, "valid_until_ns")
        if not valid_from_ns <= timestamp_ns <= valid_until_ns:
            return None

    evidence = clock.get("evidence") if isinstance(clock.get("evidence"), dict) else {}

    return {
        "timestamp_ns": timestamp_ns,
        "timestamp": timestamp_ns / 1_000_000_000.0,
        "clock_synchronized": True,
        "clock_source": source,
        "clock_uncertainty_ns": uncertainty_ns,
        "clock_valid_from_ns": valid_from_ns,
        "clock_valid_until_ns": valid_until_ns,
        "clock_evidence_sha256": evidence.get("sha256"),
        "beast_timestamp_ticks": frame_tick,
    }


def parse_beast_frames(buffer: bytearray) -> tuple[list[tuple[int, bytes]], bytearray]:
    """
    Decode complete Beast frames from a byte buffer.

    Beast framing uses 0x1a as an escape/start marker. Payload bytes equal to
    0x1a are escaped as 0x1a 0x1a.
    """
    frames: list[tuple[int, bytes]] = []
    idx = 0

    while True:
        while idx < len(buffer) and buffer[idx] != 0x1A:
            idx += 1

        if idx >= len(buffer) - 1:
            break

        type_byte = buffer[idx + 1]
        message_len = TYPE_TO_MESSAGE_LEN.get(type_byte)
        if message_len is None:
            idx += 1
            continue

        expected_len = 6 + 1 + message_len
        decoded = bytearray()
        cursor = idx + 2
        corrupted = False

        while len(decoded) < expected_len:
            if cursor >= len(buffer):
                return frames, bytearray(buffer[idx:])

            byte = buffer[cursor]
            if byte == 0x1A:
                if cursor + 1 >= len(buffer):
                    return frames, bytearray(buffer[idx:])
                escaped = buffer[cursor + 1]
                if escaped == 0x1A:
                    decoded.append(0x1A)
                    cursor += 2
                    continue

                # A new frame marker arrived before this frame was complete.
                idx = cursor
                corrupted = True
                break

            decoded.append(byte)
            cursor += 1

        if corrupted:
            continue

        frames.append((type_byte, bytes(decoded)))
        idx = cursor

    return frames, bytearray(buffer[idx:])


def beast_frame_to_record(
    frame_type: int,
    payload: bytes,
    *,
    sensor_id: str,
    receiver_id: Optional[str],
    receiver_map: dict[str, str],
    received_at: float,
    clock: Optional[dict] = None,
) -> Optional[dict]:
    if frame_type not in TYPE_TO_MESSAGE_LEN:
        return None

    message_len = TYPE_TO_MESSAGE_LEN[frame_type]
    if len(payload) != 7 + message_len:
        return None

    raw_timestamp = payload[:6]
    signal_level = payload[6]
    message_bytes = payload[7:]
    message_hex = message_bytes.hex().upper()

    # Benchmarkable canonical receiver id comes from explicit config/mapping, not
    # from Beast itself.
    canonical_receiver_id = receiver_id or receiver_map.get(sensor_id) or sensor_id
    normalized_timing = normalize_beast_timestamp(raw_timestamp, clock)
    timing = normalized_timing or {
        "timestamp_ns": None,
        "timestamp": received_at,
        "clock_synchronized": False,
        "clock_source": "network-arrival",
        "clock_uncertainty_ns": None,
        "clock_valid_from_ns": None,
        "clock_valid_until_ns": None,
        "clock_evidence_sha256": None,
        "beast_timestamp_ticks": int.from_bytes(raw_timestamp, "big"),
    }

    return {
        "receiver_id": canonical_receiver_id,
        "sensor_id": sensor_id,
        "timestamp": timing["timestamp"],
        "timestamp_ns": timing["timestamp_ns"],
        "time": isoformat_utc(timing["timestamp"]),
        "message": message_hex,
        "hex": message_hex,
        "source": "beast-tcp",
        "beast_frame_type": hex(frame_type),
        "beast_timestamp": raw_timestamp.hex().upper(),
        "beast_timestamp_ticks": timing["beast_timestamp_ticks"],
        "signal_level": signal_level,
        "clock_synchronized": timing["clock_synchronized"],
        "clock_source": timing["clock_source"],
        "clock_uncertainty_ns": timing["clock_uncertainty_ns"],
        "clock_valid_from_ns": timing["clock_valid_from_ns"],
        "clock_valid_until_ns": timing["clock_valid_until_ns"],
        "clock_evidence_sha256": timing["clock_evidence_sha256"],
    }


async def stream_records(args: argparse.Namespace):
    receiver_map = load_receiver_map(args.receiver_map)
    clock = load_clock_config(args.clock_config)

    while True:
        reader, writer = await asyncio.open_connection(args.host, args.port)
        try:
            buffer = bytearray()
            emitted = 0
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break

                buffer.extend(chunk)
                frames, buffer = parse_beast_frames(buffer)
                for frame_type, payload in frames:
                    if frame_type == 0x31:
                        continue
                    if frame_type == 0x32 and not args.include_short_frames:
                        continue

                    record = beast_frame_to_record(
                        frame_type,
                        payload,
                        sensor_id=args.sensor_id,
                        receiver_id=args.receiver_id,
                        receiver_map=receiver_map,
                        received_at=time.time(),
                        clock=clock,
                    )
                    if record is None:
                        continue

                    print(json.dumps(record), flush=True)
                    emitted += 1
                    if args.once and emitted:
                        return
        finally:
            writer.close()
            await writer.wait_closed()

        if args.once:
            return
        await asyncio.sleep(2)


def main() -> int:
    args = parse_args()
    try:
        asyncio.run(stream_records(args))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
