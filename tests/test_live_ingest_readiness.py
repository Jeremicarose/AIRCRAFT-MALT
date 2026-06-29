from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_live_ingest_readiness import read_env_file


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
