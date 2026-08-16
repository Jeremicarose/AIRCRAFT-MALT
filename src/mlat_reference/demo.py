"""Shared deterministic demo scenario definitions for hosted and local replay modes."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Dict, List


@dataclass(frozen=True)
class DemoReceiverDefinition:
    receiver_id: str
    latitude: float
    longitude: float
    altitude: float
    capabilities: tuple[str, ...]
    status: str = "online"
    city_label: str = ""


@dataclass(frozen=True)
class DemoAircraftDefinition:
    icao: str
    callsign: str
    base_latitude: float
    base_longitude: float
    base_altitude: float
    lat_amplitude: float
    lon_amplitude: float
    period_seconds: float
    phase_offset: float
    altitude_amplitude: float


@dataclass(frozen=True)
class DemoMapDefinition:
    center_latitude: float
    center_longitude: float
    zoom: int
    north: float
    south: float
    east: float
    west: float


@dataclass(frozen=True)
class DemoScenario:
    slug: str
    label: str
    summary: str
    receivers: tuple[DemoReceiverDefinition, ...]
    aircraft: tuple[DemoAircraftDefinition, ...]
    map_view: DemoMapDefinition


_NORTHEAST_CORRIDOR = DemoScenario(
    slug="northeast-corridor",
    label="Hosted demo · Northeast replay",
    summary="Sample traffic replay across a stable Northeast receiver footprint.",
    receivers=(
        DemoReceiverDefinition(
            receiver_id="RECV_NYC_001",
            latitude=40.7128,
            longitude=-74.0060,
            altitude=10.0,
            capabilities=("mode-s", "adsb", "mlat"),
            city_label="New York",
        ),
        DemoReceiverDefinition(
            receiver_id="RECV_BOS_001",
            latitude=42.3601,
            longitude=-71.0589,
            altitude=20.0,
            capabilities=("mode-s", "adsb", "mlat"),
            city_label="Boston",
        ),
        DemoReceiverDefinition(
            receiver_id="RECV_PHL_001",
            latitude=39.9526,
            longitude=-75.1652,
            altitude=15.0,
            capabilities=("mode-s", "mlat"),
            city_label="Philadelphia",
        ),
        DemoReceiverDefinition(
            receiver_id="RECV_DC_001",
            latitude=38.9072,
            longitude=-77.0369,
            altitude=25.0,
            capabilities=("mode-s", "adsb", "mlat"),
            city_label="Washington",
        ),
        DemoReceiverDefinition(
            receiver_id="RECV_BUF_001",
            latitude=42.8864,
            longitude=-78.8784,
            altitude=18.0,
            capabilities=("mode-s", "mlat"),
            city_label="Buffalo",
        ),
    ),
    aircraft=(
        DemoAircraftDefinition(
            icao="A1B2C3",
            callsign="DEMO101",
            base_latitude=40.82,
            base_longitude=-73.64,
            base_altitude=8700.0,
            lat_amplitude=0.42,
            lon_amplitude=0.86,
            period_seconds=360.0,
            phase_offset=0.0,
            altitude_amplitude=380.0,
        ),
        DemoAircraftDefinition(
            icao="D4E5F6",
            callsign="DEMO202",
            base_latitude=40.28,
            base_longitude=-74.96,
            base_altitude=8100.0,
            lat_amplitude=0.36,
            lon_amplitude=0.74,
            period_seconds=420.0,
            phase_offset=110.0,
            altitude_amplitude=320.0,
        ),
        DemoAircraftDefinition(
            icao="112233",
            callsign="DEMO303",
            base_latitude=41.58,
            base_longitude=-72.94,
            base_altitude=9300.0,
            lat_amplitude=0.48,
            lon_amplitude=0.68,
            period_seconds=510.0,
            phase_offset=210.0,
            altitude_amplitude=450.0,
        ),
    ),
    map_view=DemoMapDefinition(
        center_latitude=40.82,
        center_longitude=-74.35,
        zoom=7,
        north=43.25,
        south=38.55,
        east=-70.6,
        west=-79.2,
    ),
)


_SCENARIOS: Dict[str, DemoScenario] = {
    _NORTHEAST_CORRIDOR.slug: _NORTHEAST_CORRIDOR,
    "default": _NORTHEAST_CORRIDOR,
}


def get_demo_scenario(name: str | None) -> DemoScenario:
    """Return the requested demo scenario, falling back to the default."""
    if not name:
        return _SCENARIOS["default"]
    return _SCENARIOS.get(name, _SCENARIOS["default"])


def build_demo_receivers(timestamp: float, scenario_name: str | None) -> List[Dict[str, Any]]:
    """Build deterministic receiver payloads for simulation/demo discovery."""
    scenario = get_demo_scenario(scenario_name)
    return [
        {
            "receiver_id": receiver.receiver_id,
            "latitude": receiver.latitude,
            "longitude": receiver.longitude,
            "altitude": receiver.altitude,
            "status": receiver.status,
            "last_seen": timestamp,
            "capabilities": list(receiver.capabilities),
            "metadata": {
                "source": "simulation",
                "scenario": scenario.slug,
                "city": receiver.city_label,
            },
        }
        for receiver in scenario.receivers
    ]


def aircraft_state_at(timestamp: float, aircraft: DemoAircraftDefinition) -> Dict[str, float | str]:
    """Calculate a deterministic replay state for a single aircraft."""
    cycle_position = (
        (timestamp + aircraft.phase_offset) % aircraft.period_seconds
    ) / aircraft.period_seconds
    angle = cycle_position * math.tau

    latitude = aircraft.base_latitude + aircraft.lat_amplitude * math.sin(angle)
    longitude = aircraft.base_longitude + aircraft.lon_amplitude * math.cos(angle)
    altitude = aircraft.base_altitude + aircraft.altitude_amplitude * math.sin(angle * 1.7)

    dlat_dt = aircraft.lat_amplitude * math.cos(angle)
    dlon_dt = -aircraft.lon_amplitude * math.sin(angle)
    heading = (math.degrees(math.atan2(dlon_dt, dlat_dt)) + 360.0) % 360.0

    return {
        "icao": aircraft.icao,
        "callsign": aircraft.callsign,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "heading": heading,
    }


def scenario_aircraft_states(
    timestamp: float, scenario_name: str | None
) -> List[Dict[str, float | str]]:
    """Calculate the full deterministic aircraft state set for a scenario."""
    scenario = get_demo_scenario(scenario_name)
    return [aircraft_state_at(timestamp, aircraft) for aircraft in scenario.aircraft]


def get_scenario_metadata(scenario_name: str | None) -> Dict[str, Any]:
    """Return API-friendly metadata describing the demo scenario."""
    scenario = get_demo_scenario(scenario_name)
    return {
        "slug": scenario.slug,
        "label": scenario.label,
        "summary": scenario.summary,
        "receiver_count": len(scenario.receivers),
        "aircraft_count": len(scenario.aircraft),
        "map": {
            "center": {
                "latitude": scenario.map_view.center_latitude,
                "longitude": scenario.map_view.center_longitude,
            },
            "zoom": scenario.map_view.zoom,
            "bounds": {
                "north": scenario.map_view.north,
                "south": scenario.map_view.south,
                "east": scenario.map_view.east,
                "west": scenario.map_view.west,
            },
        },
    }
