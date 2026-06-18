#!/usr/bin/env python3
"""
Export stored MLAT positions from SQLite into the benchmark JSONL format.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export MLAT positions into benchmark JSONL format")
    parser.add_argument("--db", default="data/mlat_data.db", help="Path to SQLite database")
    parser.add_argument("--output", required=True, help="Path to output JSONL file")
    parser.add_argument("--seconds", type=int, default=86400, help="How far back to export")
    parser.add_argument("--limit", type=int, default=100000, help="Maximum positions to export")
    return parser.parse_args()


def row_value(row: sqlite3.Row, field: str, default):
    return row[field] if field in row.keys() else default


def main() -> int:
    args = parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM positions
            WHERE timestamp >= (strftime('%s','now') - ?)
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (args.seconds, args.limit),
        )
        positions = cursor.fetchall()
    finally:
        conn.close()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for position in positions:
            record = {
                "aircraft_id": position["aircraft_id"],
                "timestamp": position["timestamp"],
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "altitude": position["altitude"],
                "uncertainty": position["uncertainty"],
                "quality_score": row_value(position, "quality_score", 0.0),
                "quality_bucket": row_value(position, "quality_bucket", "unknown"),
                "solver_residual_m": row_value(position, "solver_residual_m", row_value(position, "residual", 0.0)),
                "receiver_count": row_value(position, "receiver_count", row_value(position, "num_receivers", 0)),
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    print(f"Exported {len(positions)} position records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
