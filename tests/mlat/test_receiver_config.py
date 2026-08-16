import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "mlat"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from receiver_config import load_receiver_config

NOW_NS = 1_800_000_000_000_000_000


def _receivers() -> list[dict]:
    result = []
    for index, octet in enumerate(("ab", "bc", "cd", "de")):
        result.append(
            {
                "receiver_id": "0x" + octet * 32,
                "sensor_id": f"sensor-{index}",
                "host": "receiver.local",
                "port": 30005 + index,
                "clock": {
                    "enabled": True,
                    "source": f"gpsdo-{index}",
                    "frequency_hz": 12_000_000,
                    "anchor_tick": 1000 + index,
                    "anchor_time_ns": NOW_NS,
                    "uncertainty_ns": 50,
                    "valid_from_ns": NOW_NS - 1_000_000_000,
                    "valid_until_ns": NOW_NS + 1_000_000_000,
                },
            }
        )
    return result


def _write_config(tmp_path: Path, receivers: list[dict]) -> Path:
    for index, receiver in enumerate(receivers):
        evidence_path = tmp_path / f"clock-{index}.json"
        evidence_bytes = (json.dumps({"receiver": index, "qualified": True}) + "\n").encode()
        evidence_path.write_bytes(evidence_bytes)
        receiver["clock"].setdefault(
            "evidence",
            {
                "method": "gpsdo-1pps-calibration",
                "file": evidence_path.name,
                "sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            },
        )
    path = tmp_path / "receivers.json"
    path.write_text(json.dumps({"receivers": receivers}), encoding="utf-8")
    return path


def test_strict_config_accepts_four_unique_current_receivers(tmp_path):
    path = _write_config(tmp_path, _receivers())

    loaded = load_receiver_config(path, now_ns=NOW_NS)

    assert len(loaded) == 4
    assert loaded[0]["receiver_id"] == "0x" + "ab" * 32
    assert all(receiver["clock"]["enabled"] for receiver in loaded)


def test_strict_config_rejects_fewer_than_four_receivers(tmp_path):
    path = _write_config(tmp_path, _receivers()[:3])

    with pytest.raises(ValueError, match="at least 4 receivers"):
        load_receiver_config(path, now_ns=NOW_NS)


def test_strict_config_rejects_duplicate_identity(tmp_path):
    receivers = _receivers()
    receivers[3]["receiver_id"] = receivers[0]["receiver_id"]
    path = _write_config(tmp_path, receivers)

    with pytest.raises(ValueError, match="duplicate receiver identity"):
        load_receiver_config(path, now_ns=NOW_NS)


def test_strict_config_rejects_example_identity(tmp_path):
    receivers = _receivers()
    receivers[0]["receiver_id"] = "0x" + "11" * 32
    path = _write_config(tmp_path, receivers)

    with pytest.raises(ValueError, match="example Registry V2 identity"):
        load_receiver_config(path, now_ns=NOW_NS)


def test_strict_config_rejects_disabled_or_expired_clock(tmp_path):
    disabled = _receivers()
    disabled[0]["clock"]["enabled"] = False
    disabled_path = _write_config(tmp_path, disabled)

    with pytest.raises(ValueError, match="enabled=true"):
        load_receiver_config(disabled_path, now_ns=NOW_NS)

    expired = copy.deepcopy(_receivers())
    expired[0]["clock"]["valid_from_ns"] = NOW_NS - 2_000_000_000
    expired[0]["clock"]["valid_until_ns"] = NOW_NS - 1
    expired[0]["clock"]["anchor_time_ns"] = NOW_NS - 1_000_000_000
    expired_path = _write_config(tmp_path, expired)

    with pytest.raises(ValueError, match="not valid at launch time"):
        load_receiver_config(expired_path, now_ns=NOW_NS)


def test_strict_config_rejects_excessive_clock_uncertainty(tmp_path):
    receivers = _receivers()
    receivers[2]["clock"]["uncertainty_ns"] = 101
    path = _write_config(tmp_path, receivers)

    with pytest.raises(ValueError, match="exceeds 100"):
        load_receiver_config(path, max_uncertainty_ns=100, now_ns=NOW_NS)


def test_strict_config_rejects_clock_evidence_hash_mismatch(tmp_path):
    receivers = _receivers()
    path = _write_config(tmp_path, receivers)
    receivers[0]["clock"]["evidence"]["sha256"] = "00" * 32
    path.write_text(json.dumps({"receivers": receivers}), encoding="utf-8")

    with pytest.raises(ValueError, match="sha256 does not match"):
        load_receiver_config(path, now_ns=NOW_NS)
