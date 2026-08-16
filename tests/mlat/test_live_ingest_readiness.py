from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_live_ingest_readiness import build_report


def _write_ready_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "receivers.json"
    receivers = []
    for index, octet in enumerate(("ab", "bc", "cd", "de")):
        evidence_path = tmp_path / f"clock-{index}.json"
        evidence_bytes = (json.dumps({"receiver": index, "qualified": True}) + "\n").encode()
        evidence_path.write_bytes(evidence_bytes)
        receivers.append(
            {
                "receiver_id": "0x" + octet * 32,
                "sensor_id": f"sensor-{index}",
                "host": "127.0.0.1",
                "port": 31000 + index,
                "clock": {
                    "enabled": True,
                    "source": f"gpsdo-{index}",
                    "frequency_hz": 12_000_000,
                    "anchor_tick": 1000 + index,
                    "anchor_time_ns": 1_800_000_000_000_000_000,
                    "uncertainty_ns": 50,
                    "valid_from_ns": 1,
                    "valid_until_ns": (1 << 63) - 1,
                    "evidence": {
                        "method": "gpsdo-1pps-calibration",
                        "file": evidence_path.name,
                        "sha256": hashlib.sha256(evidence_bytes).hexdigest(),
                    },
                },
            }
        )
    config_path.write_text(json.dumps({"receivers": receivers}), encoding="utf-8")
    return config_path


def _bridge_command(config_path: Path, raw_log_path: Path) -> str:
    return (
        "python3 tools/mlat/multi_receiver_beast_bridge.py "
        f"--config {config_path} --audit-log {raw_log_path}"
    )


def test_read_env_file_parses_dotenv(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    env_path = repo_root / ".env"
    env_path.write_text(
        "FOURDSKY_TRANSPORT=command-jsonl\n"
        "FOURDSKY_BRIDGE_COMMAND=python3 tools/mlat/bridge_adapter.py --source stdin\n",
        encoding="utf-8",
    )

    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "ROOT", repo_root)
    parsed = module.read_env_file()

    assert parsed["FOURDSKY_TRANSPORT"] == "command-jsonl"
    assert parsed["FOURDSKY_BRIDGE_COMMAND"].startswith("python3")


def test_read_env_file_preserves_strict_production_flag(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    env_path = repo_root / ".env"
    env_path.write_text(
        "STRICT_PRODUCTION_MODE=true\n"
        "FOURDSKY_TRANSPORT=command-jsonl\n"
        "SIMULATE_IF_UNAVAILABLE=false\n",
        encoding="utf-8",
    )

    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "ROOT", repo_root)
    parsed = module.read_env_file()

    assert parsed["STRICT_PRODUCTION_MODE"] == "true"
    assert parsed["SIMULATE_IF_UNAVAILABLE"] == "false"


def test_evidence_readiness_requires_registry_and_strict_live_gates(tmp_path, monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: True)
    monkeypatch.setattr(module, "run_command", lambda _args: (1, "No supported devices found."))
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)
    config_path = _write_ready_config(tmp_path)
    raw_log_path = tmp_path / "raw.jsonl"
    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": _bridge_command(config_path, raw_log_path),
            "FOURDSKY_EXTERNAL_SOURCE_ATTESTED": "true",
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "MLAT_RECEIVER_CONFIG": str(config_path),
            "MLAT_RAW_OBSERVATION_LOG": str(raw_log_path),
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
        },
        registry_identity_ids={"0x" + octet * 32 for octet in ("ab", "bc", "cd", "de")},
    )

    assert report["ready_for_real_live_ingest"] is True
    assert report["ready_for_evidence_run"] is True
    assert report["blockers"] == []


def test_evidence_readiness_fails_closed_without_synchronized_clock_attestation(
    tmp_path, monkeypatch
):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: True)
    monkeypatch.setattr(module, "run_command", lambda _args: (1, "No supported devices found."))
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)
    config_path = _write_ready_config(tmp_path)
    raw_log_path = tmp_path / "raw.jsonl"

    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": _bridge_command(config_path, raw_log_path),
            "FOURDSKY_EXTERNAL_SOURCE_ATTESTED": "true",
            "MLAT_RECEIVER_CONFIG": str(config_path),
            "MLAT_RAW_OBSERVATION_LOG": str(raw_log_path),
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
        }
    )

    assert report["ready_for_real_live_ingest"] is False
    assert report["ready_for_evidence_run"] is False
    assert "Synchronized receiver clocks have not been attested." in report["blockers"]


def test_evidence_readiness_fails_closed_without_registry_hash(monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: False)
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: False)
    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": "bridge",
            "FOURDSKY_EXTERNAL_SOURCE_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
        }
    )

    assert report["ready_for_evidence_run"] is False
    assert "RECEIVER_REGISTRY_TYPE_HASH is not configured." in report["blockers"]


def test_evidence_readiness_rejects_malformed_registry_hash(monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: True)
    monkeypatch.setattr(module, "run_command", lambda _args: (0, "receiver present"))
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)
    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": "bridge",
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0xabc",
        }
    )

    assert report["ready_for_evidence_run"] is False
    assert any("32-byte V2" in blocker for blocker in report["blockers"])


def test_external_source_attestation_cannot_replace_receiver_config(monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: True)
    monkeypatch.setattr(module, "run_command", lambda _args: (0, "receiver present"))
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)

    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": "bridge",
            "FOURDSKY_EXTERNAL_SOURCE_ATTESTED": "true",
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
        }
    )

    assert report["ready_for_evidence_run"] is False
    assert "MLAT_RECEIVER_CONFIG is not configured." in report["blockers"]


def test_readiness_reports_each_unreachable_receiver(tmp_path, monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: False)
    config_path = _write_ready_config(tmp_path)
    raw_log_path = tmp_path / "raw.jsonl"
    monkeypatch.setattr(module, "probe_tcp", lambda _host, port: port != 31002)

    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": _bridge_command(config_path, raw_log_path),
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
            "MLAT_RECEIVER_CONFIG": str(config_path),
            "MLAT_RAW_OBSERVATION_LOG": str(raw_log_path),
        }
    )

    assert report["ready_for_evidence_run"] is False
    assert report["receiver_config"]["receiver_count"] == 4
    assert report["receiver_config"]["receivers"][2]["endpoint_reachable"] is False
    assert any("127.0.0.1:31002" in blocker for blocker in report["blockers"])


def test_readiness_rejects_bridge_using_a_different_config(tmp_path, monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: False)
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)
    config_path = _write_ready_config(tmp_path)
    raw_log_path = tmp_path / "raw.jsonl"

    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": (
                "python3 tools/mlat/multi_receiver_beast_bridge.py --config other.json"
            ),
            "MLAT_RECEIVER_CONFIG": str(config_path),
            "MLAT_RAW_OBSERVATION_LOG": str(raw_log_path),
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
        }
    )

    assert report["ready_for_evidence_run"] is False
    assert report["bridge_command_valid"] is False
    assert any("does not match MLAT_RECEIVER_CONFIG" in item for item in report["blockers"])


def test_readiness_rejects_configured_identity_missing_from_live_registry(tmp_path, monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: False)
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: True)
    config_path = _write_ready_config(tmp_path)
    raw_log_path = tmp_path / "raw.jsonl"

    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": _bridge_command(config_path, raw_log_path),
            "MLAT_RECEIVER_CONFIG": str(config_path),
            "MLAT_RAW_OBSERVATION_LOG": str(raw_log_path),
            "FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0x" + "ab" * 32,
        },
        registry_identity_ids={"0x" + octet * 32 for octet in ("ab", "bc", "cd")},
    )

    assert report["ready_for_real_live_ingest"] is True
    assert report["ready_for_evidence_run"] is False
    assert report["registry_discovery"]["active_receiver_count"] == 3
    assert report["registry_discovery"]["missing_configured_identities"] == ["0x" + "de" * 32]
