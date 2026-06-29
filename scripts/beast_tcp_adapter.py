#!/usr/bin/env python3
"""
Read Beast-format TCP messages from readsb / dump1090-fa and emit command-jsonl
records suitable for MLAT Airspace Console.

Output lines are JSON objects containing canonical fields the runtime can ingest:
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123456,"message":"8D4840D6202CC371C32CE0576098"}

Additional fields are included for debugging/provenance.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional


TYPE_TO_MESSAGE_LEN = {
    0x31: 2,   # Mode A/C style short payload
    0x32: 7,   # short Mode-S frame
    0x33: 14,  # long Mode-S frame
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Beast TCP to JSONL adapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30005)
    parser.add_argument("--sensor-id", default="readsb-local")
    parser.add_argument("--receiver-id", default=None)
    parser.add_argument("--receiver-map", help="Optional JSON file mapping sensor ids to canonical receiver ids")
    parser.add_argument("--include-short-frames", action="store_true", help="Include short 7-byte Mode-S frames")
    parser.add_argument("--once", action="store_true", help="Emit one valid record and exit")
    return parser.parse_args()


def load_receiver_map(path: Optional[str]) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("receiver map must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def isoformat_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


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

    return {
        "receiver_id": canonical_receiver_id,
        "sensor_id": sensor_id,
        "timestamp": received_at,
        "time": isoformat_utc(received_at),
        "message": message_hex,
        "hex": message_hex,
        "source": "beast-tcp",
        "beast_frame_type": hex(frame_type),
        "beast_timestamp": raw_timestamp.hex().upper(),
        "signal_level": signal_level,
    }


async def stream_records(args: argparse.Namespace):
    receiver_map = load_receiver_map(args.receiver_map)

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
                        received_at=asyncio.get_running_loop().time(),
                    )
                    if record is None:
                        continue

                    # Convert loop monotonic time to wall clock
                    record["timestamp"] = datetime.now(tz=timezone.utc).timestamp()
                    record["time"] = isoformat_utc(record["timestamp"])
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
