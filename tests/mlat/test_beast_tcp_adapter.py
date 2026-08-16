from pathlib import Path
from io import StringIO
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beast_tcp_adapter import parse_beast_frames, beast_frame_to_record
from multi_receiver_beast_bridge import emit_record, load_config


def _encode_beast_frame(
    frame_type: int, timestamp_bytes: bytes, signal: int, message_bytes: bytes
) -> bytes:
    payload = timestamp_bytes + bytes([signal]) + message_bytes
    escaped = bytearray([0x1A, frame_type])
    for byte in payload:
        escaped.append(byte)
        if byte == 0x1A:
            escaped.append(0x1A)
    return bytes(escaped)


def test_parse_beast_frames_extracts_long_mode_s_frame():
    message = bytes.fromhex("8D4840D6202CC371C32CE0576098")
    frame = _encode_beast_frame(0x33, bytes.fromhex("010203040506"), 0x7F, message)
    frames, remainder = parse_beast_frames(bytearray(frame))

    assert len(frames) == 1
    assert remainder == bytearray()
    frame_type, payload = frames[0]
    assert frame_type == 0x33
    assert payload[7:].hex().upper() == "8D4840D6202CC371C32CE0576098"


def test_beast_frame_to_record_maps_sensor_to_receiver():
    payload = (
        bytes.fromhex("010203040506")
        + bytes([0x20])
        + bytes.fromhex("8D4840D6202CC371C32CE0576098")
    )
    record = beast_frame_to_record(
        0x33,
        payload,
        sensor_id="raw-nyc",
        receiver_id=None,
        receiver_map={"raw-nyc": "RECV_NYC_001"},
        received_at=1710000000.0,
    )

    assert record is not None
    assert record["receiver_id"] == "RECV_NYC_001"
    assert record["sensor_id"] == "raw-nyc"
    assert record["message"] == "8D4840D6202CC371C32CE0576098"
    assert record["clock_synchronized"] is False
    assert record["timestamp_ns"] is None


def test_beast_frame_uses_receiver_clock_calibration():
    anchor_tick = int.from_bytes(bytes.fromhex("010203040000"), "big")
    frame_tick = anchor_tick + 12_000
    payload = (
        frame_tick.to_bytes(6, "big")
        + bytes([0x20])
        + bytes.fromhex("8D4840D6202CC371C32CE0576098")
    )
    anchor_time_ns = 1_710_000_000_000_000_000

    record = beast_frame_to_record(
        0x33,
        payload,
        sensor_id="raw-nyc",
        receiver_id="RECV_NYC_001",
        receiver_map={},
        received_at=1_710_000_001.0,
        clock={
            "source": "gps-disciplined-beast",
            "frequency_hz": 12_000_000,
            "anchor_tick": anchor_tick,
            "anchor_time_ns": anchor_time_ns,
            "uncertainty_ns": 50,
        },
    )

    assert record is not None
    assert record["timestamp_ns"] == anchor_time_ns + 1_000_000
    assert record["clock_synchronized"] is True
    assert record["clock_source"] == "gps-disciplined-beast"
    assert record["clock_uncertainty_ns"] == 50


def test_beast_clock_calibration_handles_48_bit_wraparound():
    max_tick = 1 << 48
    anchor_tick = max_tick - 6_000
    frame_tick = 6_000
    payload = (
        frame_tick.to_bytes(6, "big")
        + bytes([0x20])
        + bytes.fromhex("8D4840D6202CC371C32CE0576098")
    )
    anchor_time_ns = 1_710_000_000_000_000_000

    record = beast_frame_to_record(
        0x33,
        payload,
        sensor_id="raw-nyc",
        receiver_id="RECV_NYC_001",
        receiver_map={},
        received_at=1_710_000_001.0,
        clock={
            "source": "gps-disciplined-beast",
            "frequency_hz": 12_000_000,
            "anchor_tick": anchor_tick,
            "anchor_time_ns": anchor_time_ns,
            "uncertainty_ns": 50,
        },
    )

    assert record is not None
    assert record["timestamp_ns"] == anchor_time_ns + 1_000_000


def test_beast_clock_calibration_fails_closed_outside_validity_window():
    anchor_tick = int.from_bytes(bytes.fromhex("010203040000"), "big")
    payload = (
        (anchor_tick + 24_000).to_bytes(6, "big")
        + bytes([0x20])
        + bytes.fromhex("8D4840D6202CC371C32CE0576098")
    )
    anchor_time_ns = 1_710_000_000_000_000_000

    record = beast_frame_to_record(
        0x33,
        payload,
        sensor_id="raw-nyc",
        receiver_id="RECV_NYC_001",
        receiver_map={},
        received_at=1_710_000_001.0,
        clock={
            "source": "gps-disciplined-beast",
            "frequency_hz": 12_000_000,
            "anchor_tick": anchor_tick,
            "anchor_time_ns": anchor_time_ns,
            "uncertainty_ns": 50,
            "valid_from_ns": anchor_time_ns,
            "valid_until_ns": anchor_time_ns + 1_000_000,
        },
    )

    assert record is not None
    assert record["timestamp_ns"] is None
    assert record["clock_synchronized"] is False


def test_multi_receiver_bridge_loads_receiver_config(tmp_path):
    config_path = tmp_path / "receivers.json"
    config_path.write_text(
        json.dumps(
            {
                "receivers": [
                    {
                        "receiver_id": "0x" + "ab" * 32,
                        "sensor_id": "raw-nyc",
                        "host": "127.0.0.1",
                        "port": 30005,
                    },
                    {
                        "receiver_id": "0x" + "bc" * 32,
                        "sensor_id": "raw-bos",
                        "host": "127.0.0.1",
                        "port": 30006,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    receivers = load_config(str(config_path), require_mlat_ready=False)
    assert len(receivers) == 2
    assert receivers[0]["receiver_id"] == "0x" + "ab" * 32


def test_multi_receiver_bridge_audit_log_matches_stdout(capsys):
    audit = StringIO()
    record = {"receiver_id": "0x" + "ab" * 32, "timestamp_ns": 123}

    emit_record(record, audit)

    assert capsys.readouterr().out == audit.getvalue()
    assert json.loads(audit.getvalue()) == record
