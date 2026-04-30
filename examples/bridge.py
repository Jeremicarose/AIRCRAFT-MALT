#!/usr/bin/env python3
"""
Normalize external 4DSky/ADEX feeds into the JSONL format expected by
FOURDSKY_BRIDGE_COMMAND.

Supported input modes:
- `--stdin-jsonl`: read JSON lines from stdin
- `--websocket URL`: connect to a websocket feed and normalize messages

Output format:
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123,"message":"8D..."}

Examples:
  your-adex-client | python examples/bridge.py --stdin-jsonl

  python examples/bridge.py \
      --websocket wss://feed.example/ws \
      --auth-header X-API-Key \
      --auth-token your_token
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
import sys
import time
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize 4DSky/ADEX feed data to JSONL")
    parser.add_argument("--stdin-jsonl", action="store_true", help="Read JSON lines from stdin")
    parser.add_argument("--websocket", help="Connect to a websocket feed")
    parser.add_argument("--auth-header", default="X-API-Key", help="Header name for websocket auth")
    parser.add_argument("--auth-token", default="", help="Token value for websocket auth")
    parser.add_argument("--auth-scheme", default="", help="Optional auth scheme, e.g. Bearer")
    parser.add_argument("--subscribe-message", default="", help="Optional websocket subscribe payload")
    return parser.parse_args()


def parse_timestamp(value: Any) -> float:
    if value is None:
        return time.time()

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass

    return time.time()


def normalize_records(payload: Any, default_receiver_id: str | None = None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records: list[dict[str, Any]] = []
        for item in payload:
            records.extend(normalize_records(item, default_receiver_id=default_receiver_id))
        return records

    if not isinstance(payload, dict):
        return []

    if "records" in payload and isinstance(payload["records"], list):
        return normalize_records(payload["records"], default_receiver_id=default_receiver_id)

    if "data" in payload and isinstance(payload["data"], (dict, list)):
        nested = normalize_records(payload["data"], default_receiver_id=default_receiver_id)
        if nested:
            return nested

    receiver_id = (
        payload.get("receiver_id")
        or payload.get("receiver")
        or payload.get("sensor_id")
        or payload.get("source")
        or default_receiver_id
    )

    message_value = payload.get("message")
    if isinstance(message_value, dict):
        message_value = (
            message_value.get("hex")
            or message_value.get("raw")
            or message_value.get("frame")
        )

    message = (
        message_value
        or payload.get("hex")
        or payload.get("raw")
        or payload.get("frame")
        or payload.get("payload")
    )

    if not receiver_id or not message:
        return []

    return [
        {
            "receiver_id": str(receiver_id),
            "timestamp": parse_timestamp(
                payload.get("timestamp")
                or payload.get("time")
                or payload.get("ts")
                or payload.get("observed_at")
            ),
            "message": str(message),
        }
    ]


def emit_records(records: list[dict[str, Any]]) -> None:
    for record in records:
        sys.stdout.write(json.dumps(record) + "\n")
    sys.stdout.flush()


async def run_stdin_jsonl() -> None:
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        emit_records(normalize_records(payload))


async def run_websocket(args: argparse.Namespace) -> None:
    try:
        import websockets
    except ImportError:
        raise SystemExit("Install websockets first: pip install websockets")

    headers = {}
    if args.auth_token:
        if args.auth_scheme:
            headers[args.auth_header] = f"{args.auth_scheme} {args.auth_token}"
        else:
            headers[args.auth_header] = args.auth_token

    while True:
        try:
            async with websockets.connect(args.websocket, extra_headers=headers) as websocket:
                if args.subscribe_message:
                    await websocket.send(args.subscribe_message)

                async for raw_payload in websocket:
                    try:
                        payload = json.loads(raw_payload)
                    except json.JSONDecodeError:
                        continue
                    emit_records(normalize_records(payload))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"bridge reconnecting after websocket error: {exc}", file=sys.stderr)
            await asyncio.sleep(3)


async def main() -> None:
    args = parse_args()

    if args.websocket:
        await run_websocket(args)
        return

    if args.stdin_jsonl or not sys.stdin.isatty():
        await run_stdin_jsonl()
        return

    raise SystemExit("Choose --stdin-jsonl or --websocket URL")


if __name__ == "__main__":
    asyncio.run(main())
