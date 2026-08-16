#!/usr/bin/env python3
"""
Fetch OpenSky state vectors and convert them into benchmark reference JSONL.

Official docs:
https://openskynetwork.github.io/opensky-api/rest.html
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

API_ROOT = "https://opensky-network.org/api/states/all"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
)


@dataclass
class Bounds:
    lamin: float
    lomin: float
    lamax: float
    lomax: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch OpenSky reference data for MLAT benchmarking"
    )
    parser.add_argument("--output", required=True, help="Path to output JSONL file")
    parser.add_argument("--time", type=int, default=None, help="Unix timestamp to query")
    parser.add_argument("--lamin", type=float, required=True)
    parser.add_argument("--lomin", type=float, required=True)
    parser.add_argument("--lamax", type=float, required=True)
    parser.add_argument("--lomax", type=float, required=True)
    parser.add_argument(
        "--icao24",
        action="append",
        dest="icao24_list",
        default=None,
        help="Optional ICAO24 filter, can be supplied more than once",
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("OPENSKY_CLIENT_ID"),
        help="OpenSky OAuth2 client id (defaults to OPENSKY_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.getenv("OPENSKY_CLIENT_SECRET"),
        help="OpenSky OAuth2 client secret (defaults to OPENSKY_CLIENT_SECRET)",
    )
    parser.add_argument(
        "--anonymous",
        action="store_true",
        help="Do not authenticate. Only suitable for recent-current snapshots with OpenSky anonymous limits.",
    )
    return parser.parse_args()


def fetch_access_token(client_id: str, client_secret: str) -> str:
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("OpenSky token response did not contain access_token")
    return token


def build_query_url(time_value: int | None, bounds: Bounds, icao24_list: list[str] | None) -> str:
    query: list[tuple[str, str]] = [
        ("lamin", str(bounds.lamin)),
        ("lomin", str(bounds.lomin)),
        ("lamax", str(bounds.lamax)),
        ("lomax", str(bounds.lomax)),
    ]
    if time_value is not None:
        query.append(("time", str(time_value)))
    for icao24 in icao24_list or []:
        query.append(("icao24", icao24))
    return f"{API_ROOT}?{urllib.parse.urlencode(query)}"


def normalize_state_vector(row: list, fallback_time: int | None = None) -> dict | None:
    if len(row) < 17:
        return None

    icao24 = row[0]
    time_position = row[3]
    last_contact = row[4]
    longitude = row[5]
    latitude = row[6]
    baro_altitude = row[7]
    geo_altitude = row[13] if len(row) > 13 else None

    if not icao24 or latitude is None or longitude is None:
        return None

    timestamp = time_position or last_contact or fallback_time
    if timestamp is None:
        return None

    altitude = geo_altitude if geo_altitude is not None else baro_altitude
    altitude = float(altitude) if altitude is not None else 0.0

    return {
        "aircraft_id": str(icao24).upper(),
        "timestamp": float(timestamp),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "altitude": altitude,
    }


def fetch_states(url: str, bearer_token: str | None) -> dict:
    headers = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    bounds = Bounds(args.lamin, args.lomin, args.lamax, args.lomax)

    token = None
    if not args.anonymous:
        if not args.client_id or not args.client_secret:
            raise SystemExit(
                "OpenSky authenticated access requires --client-id/--client-secret or "
                "OPENSKY_CLIENT_ID/OPENSKY_CLIENT_SECRET env vars. Use --anonymous only for recent-current snapshots."
            )
        token = fetch_access_token(args.client_id, args.client_secret)

    url = build_query_url(args.time, bounds, args.icao24_list)
    payload = fetch_states(url, token)
    states = payload.get("states") or []
    fallback_time = payload.get("time")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    exported = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for row in states:
            normalized = normalize_state_vector(row, fallback_time=fallback_time)
            if normalized is None:
                continue
            handle.write(json.dumps(normalized, sort_keys=True) + "\n")
            exported += 1

    print(
        f"Fetched {len(states)} OpenSky state rows and exported {exported} benchmark reference records to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
