#!/usr/bin/env python3
"""
Generate a canonical receiver-registry JSON record and hex-encoded cell data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import ReceiverRegistryRecord


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate canonical CKB receiver-registry record")
    parser.add_argument("--receiver-id", required=True)
    parser.add_argument("--latitude", required=True, type=float)
    parser.add_argument("--longitude", required=True, type=float)
    parser.add_argument("--altitude", required=True, type=float)
    parser.add_argument("--status", default="online")
    parser.add_argument("--capability", action="append", dest="capabilities", required=True)
    parser.add_argument("--stream-endpoint")
    parser.add_argument("--stream-protocol")
    parser.add_argument("--stream-format")
    parser.add_argument("--metadata-hash")
    parser.add_argument("--sequence", type=int, default=0)
    parser.add_argument("--updated-at", type=int, default=None)
    parser.add_argument("--output-json", default="deploy/receiver-registry-record.json")
    parser.add_argument("--output-hex", default="deploy/receiver-registry-record.hex")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = ReceiverRegistryRecord(
        receiver_id=args.receiver_id,
        latitude=args.latitude,
        longitude=args.longitude,
        altitude=args.altitude,
        status=args.status,
        capabilities=args.capabilities,
        sequence=args.sequence,
        updated_at=args.updated_at if args.updated_at is not None else int(time.time()),
        stream_endpoint=args.stream_endpoint,
        stream_protocol=args.stream_protocol,
        stream_format=args.stream_format,
        metadata_hash=args.metadata_hash,
    )
    if args.sequence == 0:
        record.validate_creation()
    else:
        record.validate()

    json_path = Path(args.output_json)
    hex_path = Path(args.output_hex)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    hex_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(record.to_payload_dict(), indent=2, sort_keys=True)
    json_path.write_text(payload + "\n")
    hex_path.write_text(record.to_cell_data_hex() + "\n")

    print(f"Wrote JSON record to {json_path}")
    print(f"Wrote hex cell data to {hex_path}")


if __name__ == "__main__":
    main()
