#!/usr/bin/env python3
"""Capture reproducible local Registry V2 build and test evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Registry V2 local CI evidence")
    parser.add_argument(
        "--evidence-dir",
        default="evidence/registry-v2-testnet-2026-07-30-final",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(name: str, command: list[str], cwd: Path) -> dict:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "name": name,
        "command": command,
        "working_directory": str(cwd.relative_to(ROOT)) or ".",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "pass": result.returncode == 0,
    }


def main() -> None:
    args = parse_args()
    evidence_dir = (ROOT / args.evidence_dir).resolve()
    contract_dir = ROOT / "contracts" / "receiver-registry"
    binary = contract_dir / "target/riscv64imac-unknown-none-elf/release/receiver-registry"
    commands = [
        run("rust-format", ["cargo", "fmt", "--", "--check"], contract_dir),
        run("rust-unit-and-ckb-vm", ["make", "test"], contract_dir),
        run("rust-riscv-check", ["make", "check"], contract_dir),
        run(
            "python-registry",
            [
                "python3",
                "-m",
                "pytest",
                "-q",
                "tests/test_ckb_registry.py",
                "tests/test_ckb_client.py",
                "tests/test_contract_layout.py",
                "tests/test_receiver_record_generator.py",
                "tests/test_receiver_registration_template.py",
                "tests/test_receiver_registration_commands.py",
                "tests/test_apply_receiver_type_script.py",
                "tests/test_deploy_helpers.py",
                "tests/test_registry_v2_lifecycle_tool.py",
                "tests/test_registry_v2_evidence_verifier.py",
            ],
            ROOT,
        ),
        run("python-full-suite", ["python3", "-m", "pytest", "-q"], ROOT),
        run("git-diff-check", ["git", "diff", "--check"], ROOT),
    ]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    contract_status = subprocess.run(
        ["git", "status", "--porcelain", "--", "contracts/receiver-registry"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    if not binary.is_file():
        raise SystemExit(f"Contract binary was not produced: {binary}")
    platform_name = platform.system().lower() or "unknown"
    public_binary = evidence_dir / "contract" / f"receiver-registry-local-{platform_name}"
    public_binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, public_binary)
    binary_bytes = public_binary.read_bytes()
    result = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "source_commit": commit,
        "contract_source_clean": contract_status == "",
        "contract_source_status": contract_status,
        "contract_binary": {
            "path": str(public_binary.relative_to(ROOT)),
            "bytes": len(binary_bytes),
            "sha256": hashlib.sha256(binary_bytes).hexdigest(),
            "ckb_data_hash": "0x"
            + hashlib.blake2b(
                binary_bytes, digest_size=32, person=b"ckb-default-hash"
            ).hexdigest(),
        },
        "commands": commands,
        "pass": all(command["pass"] for command in commands) and contract_status == "",
    }
    output = evidence_dir / "ci" / "local.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {output}")
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
