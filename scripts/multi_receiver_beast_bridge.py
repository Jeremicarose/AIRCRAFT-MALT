#!/usr/bin/env python3
"""
Launch one Beast TCP adapter per receiver and multiplex all JSONL output to stdout.

Config file format:
{
  "receivers": [
    {
      "receiver_id": "RECV_NYC_001",
      "sensor_id": "raw-nyc",
      "host": "127.0.0.1",
      "port": 30005
    },
    {
      "receiver_id": "RECV_BOS_001",
      "sensor_id": "raw-bos",
      "host": "127.0.0.1",
      "port": 30006
    }
  ]
}
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beast_tcp_adapter import beast_frame_to_record, parse_beast_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-receiver Beast TCP bridge")
    parser.add_argument("--config", required=True, help="Path to receiver config JSON")
    parser.add_argument("--include-short-frames", action="store_true")
    return parser.parse_args()


def load_config(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    receivers = payload.get("receivers")
    if not isinstance(receivers, list) or not receivers:
        raise ValueError("config must contain a non-empty 'receivers' list")
    return receivers


async def stream_one_receiver(receiver: dict, include_short_frames: bool):
    reader, writer = await asyncio.open_connection(receiver["host"], receiver["port"])
    try:
        buffer = bytearray()
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                return
            buffer.extend(chunk)
            frames, buffer = parse_beast_frames(buffer)
            for frame_type, payload in frames:
                if frame_type == 0x31:
                    continue
                if frame_type == 0x32 and not include_short_frames:
                    continue
                record = beast_frame_to_record(
                    frame_type,
                    payload,
                    sensor_id=receiver.get("sensor_id", receiver["receiver_id"]),
                    receiver_id=receiver["receiver_id"],
                    receiver_map={},
                    received_at=asyncio.get_running_loop().time(),
                )
                if record is None:
                    continue
                print(json.dumps(record), flush=True)
    finally:
        writer.close()
        await writer.wait_closed()


async def async_main() -> int:
    args = parse_args()
    receivers = load_config(args.config)
    tasks = [
        asyncio.create_task(stream_one_receiver(receiver, args.include_short_frames))
        for receiver in receivers
    ]
    await asyncio.gather(*tasks)
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
