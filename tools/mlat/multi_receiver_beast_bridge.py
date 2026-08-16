#!/usr/bin/env python3
"""
Launch one Beast TCP adapter per receiver and multiplex all JSONL output to stdout.

Config file format:
{
  "receivers": [
    {
      "receiver_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
      "sensor_id": "raw-nyc",
      "host": "127.0.0.1",
      "port": 30005,
      "clock": {
        "enabled": true,
        "source": "gpsdo-nyc",
        "frequency_hz": 12000000,
        "anchor_tick": 123456,
        "anchor_time_ns": 1714400000123456789,
        "uncertainty_ns": 50
      }
    },
    {
      "receiver_id": "0x2222222222222222222222222222222222222222222222222222222222222222",
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
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beast_tcp_adapter import beast_frame_to_record, parse_beast_frames
from receiver_config import load_receiver_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-receiver Beast TCP bridge")
    parser.add_argument("--config", required=True, help="Path to receiver config JSON")
    parser.add_argument("--include-short-frames", action="store_true")
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Allow fewer than four receivers and clocks without a current validity window.",
    )
    parser.add_argument(
        "--max-clock-uncertainty-ns",
        type=float,
        default=float(os.getenv("MAX_CLOCK_UNCERTAINTY_NS", "100")),
        help="Maximum declared clock uncertainty for an MLAT-ready receiver.",
    )
    parser.add_argument("--connect-timeout", type=float, default=3.0)
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument(
        "--audit-log",
        help="Append every emitted raw observation to this evidence JSONL file.",
    )
    return parser.parse_args()


def load_config(
    path: str,
    *,
    require_mlat_ready: bool = True,
    max_uncertainty_ns: float = 100.0,
    now_ns: int | None = None,
) -> list[dict]:
    return load_receiver_config(
        path,
        require_mlat_ready=require_mlat_ready,
        max_uncertainty_ns=max_uncertainty_ns,
        now_ns=now_ns,
    )


def _log_event(event: str, receiver: dict, **details) -> None:
    print(
        json.dumps(
            {
                "event": event,
                "receiver_id": receiver["receiver_id"],
                "endpoint": f'{receiver["host"]}:{receiver["port"]}',
                **details,
            },
            separators=(",", ":"),
            sort_keys=True,
        ),
        file=sys.stderr,
        flush=True,
    )


def emit_record(record: dict, audit_stream=None) -> None:
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    print(line, flush=True)
    if audit_stream is not None:
        audit_stream.write(line + "\n")
        audit_stream.flush()


async def stream_one_receiver(
    receiver: dict,
    include_short_frames: bool,
    *,
    connect_timeout: float,
    reconnect_delay: float,
    audit_stream=None,
):
    while True:
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(receiver["host"], receiver["port"]),
                timeout=connect_timeout,
            )
            _log_event("receiver_connected", receiver)
            buffer = bytearray()
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    raise ConnectionError("receiver closed the Beast stream")
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
                        sensor_id=receiver["sensor_id"],
                        receiver_id=receiver["receiver_id"],
                        receiver_map={},
                        received_at=time.time(),
                        clock=receiver.get("clock"),
                    )
                    if record is not None:
                        emit_record(record, audit_stream)
        except asyncio.CancelledError:
            raise
        except (ConnectionError, OSError, asyncio.TimeoutError) as exc:
            _log_event("receiver_disconnected", receiver, error=str(exc))
        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
        await asyncio.sleep(reconnect_delay)


async def async_main() -> int:
    args = parse_args()
    if args.connect_timeout <= 0 or args.reconnect_delay < 0:
        raise ValueError("connect timeout must be positive and reconnect delay non-negative")
    receivers = load_config(
        args.config,
        require_mlat_ready=not args.diagnostic,
        max_uncertainty_ns=args.max_clock_uncertainty_ns,
    )
    audit_stream = None
    if args.audit_log:
        audit_path = Path(args.audit_log).expanduser()
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_stream = audit_path.open("a", encoding="utf-8")
    try:
        tasks = [
            asyncio.create_task(
                stream_one_receiver(
                    receiver,
                    args.include_short_frames,
                    connect_timeout=args.connect_timeout,
                    reconnect_delay=args.reconnect_delay,
                    audit_stream=audit_stream,
                )
            )
            for receiver in receivers
        ]
        await asyncio.gather(*tasks)
    finally:
        if audit_stream is not None:
            audit_stream.close()
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
