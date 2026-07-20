from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_live_ingest_readiness import build_report, read_env_file


def test_read_env_file_parses_dotenv(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    env_path = repo_root / ".env"
    env_path.write_text(
        "FOURDSKY_TRANSPORT=command-jsonl\nFOURDSKY_BRIDGE_COMMAND=python3 scripts/bridge_adapter.py --source stdin\n",
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
        "STRICT_PRODUCTION_MODE=true\nFOURDSKY_TRANSPORT=command-jsonl\nSIMULATE_IF_UNAVAILABLE=false\n",
        encoding="utf-8",
    )

    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "ROOT", repo_root)
    parsed = module.read_env_file()

    assert parsed["STRICT_PRODUCTION_MODE"] == "true"
    assert parsed["SIMULATE_IF_UNAVAILABLE"] == "false"


def test_evidence_readiness_requires_registry_and_strict_live_gates(monkeypatch):
    module = __import__("check_live_ingest_readiness")
    monkeypatch.setattr(module, "command_exists", lambda _name: True)
    monkeypatch.setattr(module, "run_command", lambda _args: (1, "No supported devices found."))
    monkeypatch.setattr(module, "probe_tcp", lambda _host, _port: False)
    report = build_report(
        {
            "FOURDSKY_TRANSPORT": "command-jsonl",
            "FOURDSKY_BRIDGE_COMMAND": "python3 scripts/bridge_adapter.py --source remote",
            "FOURDSKY_EXTERNAL_SOURCE_ATTESTED": "true",
            "STRICT_PRODUCTION_MODE": "true",
            "SIMULATE_IF_UNAVAILABLE": "false",
            "REQUIRE_LIVE_BENCHMARKABLE_OUTPUT": "true",
            "RECEIVER_REGISTRY_TYPE_HASH": "0xabc",
        }
    )

    assert report["ready_for_real_live_ingest"] is True
    assert report["ready_for_evidence_run"] is True
    assert report["blockers"] == []


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
