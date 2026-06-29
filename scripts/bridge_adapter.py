#!/usr/bin/env python3
"""
General-purpose command-jsonl bridge adapter.

Supported sources:
- stdin
- tcp socket
- unix socket
- subprocess source

Output format:
{"receiver_id":"RECV_NYC_001","timestamp":1714400000.123,"message":"8D4840D6202CC371C32CE0576098"}
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bridge raw local feed sources into MLAT command-jsonl format")
    parser.add_argument(
        "--source",
        required=True,
        choices=["stdin", "tcp", "unix", "subprocess"],
        help="Input source type",
    )
    parser.add_argument("--tcp-host", default="127.0.0.1")
    parser.add_argument("--tcp-port", type=int)
    parser.add_argument("--unix-path")
    parser.add_argument("--command", help="Subprocess command when --source=subprocess")
    parser.add_argument(
        "--receiver-map",
        help="Optional JSON file mapping source receiver ids to canonical receiver ids",
    )
    parser.add_argument(
        "--default-receiver-id",
        default=None,
        help="Default receiver id when the input payload does not include one",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Read a single payload and exit",
    )
    return parser.parse_args()


def load_receiver_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("receiver map must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def normalize_timestamp(value: Any) -> float:
    if value is None:
        return datetime.now().timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    return datetime.now().timestamp()


def normalize_record(payload: Any, receiver_map: dict[str, str], default_receiver_id: str | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for item in payload:
            rows.extend(normalize_record(item, receiver_map, default_receiver_id))
        return rows

    if not isinstance(payload, dict):
        return []

    if "records" in payload and isinstance(payload["records"], list):
        return normalize_record(payload["records"], receiver_map, default_receiver_id)
    if "data" in payload and isinstance(payload["data"], (dict, list)):
        nested = normalize_record(payload["data"], receiver_map, default_receiver_id)
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

    canonical_receiver_id = receiver_map.get(str(receiver_id), str(receiver_id))
    return [
        {
            "receiver_id": canonical_receiver_id,
            "timestamp": normalize_timestamp(
                payload.get("timestamp")
                or payload.get("time")
                or payload.get("ts")
                or payload.get("observed_at")
            ),
            "message": str(message),
        }
    ]


async def emit_from_line(
    line: str,
    receiver_map: dict[str, str],
    default_receiver_id: str | None,
) -> int:
    line = line.strip()
    if not line:
        return 0
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return 0

    emitted = 0
    for record in normalize_record(payload, receiver_map, default_receiver_id):
        print(json.dumps(record), flush=True)
        emitted += 1
    return emitted


async def read_stdin(args: argparse.Namespace, receiver_map: dict[str, str]) -> None:
    emitted_total = 0
    for line in sys.stdin:
        emitted_total += await emit_from_line(line, receiver_map, args.default_receiver_id)
        if args.once and emitted_total:
            return


async def read_tcp(args: argparse.Namespace, receiver_map: dict[str, str]) -> None:
    if args.tcp_port is None:
        raise ValueError("--tcp-port is required for --source=tcp")

    reader, _writer = await asyncio.open_connection(args.tcp_host, args.tcp_port)
    emitted_total = 0
    while True:
        line = await reader.readline()
        if not line:
            return
        emitted_total += await emit_from_line(line.decode("utf-8"), receiver_map, args.default_receiver_id)
        if args.once and emitted_total:
            return


async def read_unix(args: argparse.Namespace, receiver_map: dict[str, str]) -> None:
    if not args.unix_path:
        raise ValueError("--unix-path is required for --source=unix")

    reader, _writer = await asyncio.open_unix_connection(args.unix_path)
    emitted_total = 0
    while True:
        line = await reader.readline()
        if not line:
            return
        emitted_total += await emit_from_line(line.decode("utf-8"), receiver_map, args.default_receiver_id)
        if args.once and emitted_total:
            return


async def read_subprocess(args: argparse.Namespace, receiver_map: dict[str, str]) -> None:
    if not args.command:
        raise ValueError("--command is required for --source=subprocess")

    process = await asyncio.create_subprocess_shell(
        args.command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert process.stdout is not None
    emitted_total = 0
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        emitted_total += await emit_from_line(line.decode("utf-8"), receiver_map, args.default_receiver_id)
        if args.once and emitted_total:
            process.terminate()
            await process.wait()
            return

    await process.wait()


async def async_main() -> int:
    args = parse_args()
    receiver_map = load_receiver_map(args.receiver_map)

    if args.source == "stdin":
        await read_stdin(args, receiver_map)
    elif args.source == "tcp":
        await read_tcp(args, receiver_map)
    elif args.source == "unix":
        await read_unix(args, receiver_map)
    elif args.source == "subprocess":
        await read_subprocess(args, receiver_map)
    else:
        raise ValueError(f"Unsupported source: {args.source}")

    return 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
