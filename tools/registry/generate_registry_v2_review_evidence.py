#!/usr/bin/env python3
"""Build a source-bound, offline-verifiable Registry V2 review bundle."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts/registry-v2"
SDK = ROOT / "sdk/typescript"
FRONTEND = ROOT / "reference/mlat/frontend"
CORPUS = ROOT / "tests/registry/fixtures/registry_v2_conformance.json"
CONTRACT_BINARY = CONTRACT / "target/riscv64imac-unknown-none-elf/release/receiver-registry"
HISTORICAL_BUNDLE = ROOT / "evidence/registry-v2-testnet-2026-07-30-final"


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    cwd: Path = ROOT


CHECKS = (
    Check("python-tests", (sys.executable, "-m", "pytest", "-q")),
    Check(
        "python-format",
        (
            sys.executable,
            "-m",
            "black",
            "--check",
            "src/ckb_registry",
            "src/mlat_reference",
            "tools",
            "tests",
        ),
    ),
    Check(
        "python-lint",
        (
            sys.executable,
            "-m",
            "flake8",
            "src/ckb_registry",
            "src/mlat_reference",
            "tools",
            "tests",
        ),
    ),
    Check("documentation", (sys.executable, "tools/check_documentation.py")),
    Check(
        "historical-testnet-evidence",
        (
            sys.executable,
            "tools/registry/verify_registry_v2_evidence.py",
            "--bundle",
            "evidence/registry-v2-testnet-2026-07-30-final",
        ),
    ),
    Check(
        "deterministic-mlat-evidence",
        (sys.executable, "tools/mlat/run_reproducible_benchmark.py", "--verify-only"),
    ),
    Check("contract-tests", ("make", "test"), CONTRACT),
    Check("contract-target-check", ("make", "check"), CONTRACT),
    Check("typescript-sdk-tests", ("npm", "test"), SDK),
    Check("frontend-tests", ("npm", "test"), FRONTEND),
    Check("frontend-typecheck", ("npm", "run", "typecheck"), FRONTEND),
    Check("frontend-build", ("npm", "run", "build"), FRONTEND),
)

REVIEW_PATHS = (
    ".github/workflows/registry-v2.yml",
    "contracts/registry-v2/Cargo.lock",
    "contracts/registry-v2/examples/conformance.rs",
    "contracts/registry-v2/src/entry.rs",
    "contracts/registry-v2/src/error.rs",
    "contracts/registry-v2/src/record.rs",
    "contracts/registry-v2/tests/lifecycle.rs",
    "src/ckb_registry/discovery.py",
    "src/ckb_registry/record.py",
    "src/mlat_reference/api/rest_api.py",
    "src/mlat_reference/config.py",
    "src/mlat_reference/database/database.py",
    "src/mlat_reference/ingest/client.py",
    "src/mlat_reference/runtime.py",
    "sdk/typescript/src/deployments.ts",
    "sdk/typescript/src/discovery.ts",
    "sdk/typescript/src/history.ts",
    "sdk/typescript/src/index.ts",
    "sdk/typescript/src/lifecycle.ts",
    "sdk/typescript/src/record.ts",
    "sdk/typescript/src/strict-json.ts",
    "sdk/typescript/test/conformance-runner.ts",
    "sdk/typescript/test/conformance.test.ts",
    "sdk/typescript/test/deployments.test.ts",
    "sdk/typescript/test/lifecycle.test.ts",
    "reference/mlat/frontend/app/app/registry/page.tsx",
    "reference/mlat/frontend/components/pages/receivers-page.tsx",
    "reference/mlat/frontend/components/registry-action-panel.tsx",
    "reference/mlat/frontend/lib/receiver-freshness.ts",
    "reference/mlat/frontend/lib/receiver-reference.ts",
    "reference/mlat/frontend/lib/receiver-state.ts",
    "reference/mlat/frontend/lib/registry.ts",
    "reference/mlat/frontend/lib/routes.ts",
    "reference/mlat/frontend/test/receiver-freshness.test.mjs",
    "reference/mlat/frontend/test/receiver-reference.test.mjs",
    "tests/registry/fixtures/registry_v2_conformance.json",
    "tests/registry/test_registry_v2_conformance_report.py",
    "tools/registry/generate_registry_v2_conformance_report.py",
    "tools/registry/registry_v2_conformance.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New bundle directory")
    return parser.parse_args()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def ckb_hash(path: Path) -> str:
    digest = hashlib.blake2b(path.read_bytes(), digest_size=32, person=b"ckb-default-hash")
    return "0x" + digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def require_clean_tracked_tree() -> None:
    status = git("status", "--short", "--untracked-files=no")
    if status:
        raise RuntimeError(
            "tracked files are modified; commit the review target before generating evidence"
        )


def run_check(check: Check, logs: Path) -> dict[str, Any]:
    completed = subprocess.run(
        list(check.command),
        cwd=check.cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    relative_log = f"logs/{check.name}.txt"
    (logs / f"{check.name}.txt").write_text(
        f"$ {' '.join(check.command)}\n"
        f"cwd: {check.cwd.relative_to(ROOT) or Path('.')}\n"
        f"exit_code: {completed.returncode}\n\n"
        f"STDOUT\n{completed.stdout}\nSTDERR\n{completed.stderr}",
        encoding="utf-8",
    )
    result = {
        "name": check.name,
        "command": list(check.command),
        "cwd": (check.cwd.relative_to(ROOT).as_posix() or "."),
        "exit_code": completed.returncode,
        "log": relative_log,
    }
    if completed.returncode != 0:
        raise RuntimeError(f"{check.name} failed; see {relative_log}")
    return result


def tool_version(command: tuple[str, ...]) -> str:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or completed.stderr).strip()


def write_checksums(bundle: Path) -> None:
    entries = []
    for path in sorted(item for item in bundle.rglob("*") if item.is_file()):
        if path.name == "checksums.sha256":
            continue
        entries.append(f"{sha256(path)}  {path.relative_to(bundle).as_posix()}")
    (bundle / "checksums.sha256").write_text("\n".join(entries) + "\n", encoding="ascii")


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise RuntimeError(f"output directory is not empty: {output}")

    require_clean_tracked_tree()
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    repository = git("remote", "get-url", "origin")

    output.mkdir(parents=True, exist_ok=True)
    logs = output / "logs"
    logs.mkdir()
    checks = [run_check(check, logs) for check in CHECKS]

    conformance_path = output / "conformance-report.json"
    conformance_check = Check(
        "cross-language-conformance",
        (
            sys.executable,
            "tools/registry/generate_registry_v2_conformance_report.py",
            "--output",
            str(conformance_path),
        ),
    )
    checks.append(run_check(conformance_check, logs))
    conformance = json.loads(conformance_path.read_text(encoding="utf-8"))

    require_clean_tracked_tree()
    binary_dir = output / "contract"
    binary_dir.mkdir()
    copied_binary = binary_dir / "receiver-registry"
    shutil.copy2(CONTRACT_BINARY, copied_binary)

    historical = json.loads((HISTORICAL_BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 1,
        "status": "verified_undeployed_review_candidate",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "repository": repository,
            "commit": source_commit,
            "tree": source_tree,
            "tracked_worktree_clean": True,
            "review_paths": list(REVIEW_PATHS),
        },
        "contract_candidate": {
            "deployment_status": "not_deployed",
            "binary": "contract/receiver-registry",
            "binary_bytes": copied_binary.stat().st_size,
            "binary_sha256": sha256(copied_binary),
            "binary_ckb_data_hash": ckb_hash(copied_binary),
            "future_registry_code_hash": None,
        },
        "conformance": {
            "report": "conformance-report.json",
            "corpus": "tests/registry/fixtures/registry_v2_conformance.json",
            "corpus_sha256": sha256(CORPUS),
            "summary": conformance["summary"],
        },
        "verification": {"checks": checks, "all_passed": True},
        "tool_versions": {
            "python": tool_version((sys.executable, "--version")),
            "node": tool_version(("node", "--version")),
            "npm": tool_version(("npm", "--version")),
            "rustc": tool_version(("rustc", "-Vv")),
            "cargo": tool_version(("cargo", "-V")),
        },
        "historical_testnet_deployment": {
            "status": "immutable_historical_evidence",
            "bundle": "evidence/registry-v2-testnet-2026-07-30-final",
            "contract_source_commit": historical["source"]["contract_source_commit"],
            "deployment_tx_hash": historical["contract"]["deployment_tx_hash"],
            "contract_out_point": historical["contract"]["out_point"],
            "registry_code_hash": historical["contract"]["type_script_hash_for_registry_code_hash"],
            "binary_sha256": historical["contract"]["binary_sha256"],
        },
        "external_dependencies": {
            "fresh_sdk_testnet_lifecycle": "blocked_external_signer_and_testnet_funds",
            "independent_security_review": "not_completed",
        },
        "private_keys_included": False,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    try:
        displayed_output = output.relative_to(ROOT)
    except ValueError:
        displayed_output = output
    (output / "README.md").write_text(
        "# Registry V2 Review Evidence\n\n"
        f"This bundle is bound to source commit `{source_commit}` and Git tree "
        f"`{source_tree}`. All recorded checks passed.\n\n"
        "The included contract binary is an undeployed review candidate. The July "
        "testnet deployment is separate historical evidence and does not claim to "
        "run this binary. No private key or new testnet transaction is included.\n\n"
        "Verify this bundle from the repository with:\n\n"
        "```bash\n"
        "python tools/registry/verify_registry_v2_review_evidence.py "
        f"--bundle {displayed_output}\n"
        "```\n",
        encoding="utf-8",
    )
    write_checksums(output)
    print(
        json.dumps(
            {
                "bundle": str(output),
                "source_commit": source_commit,
                "source_tree": source_tree,
                "checks": len(checks),
                "conformant": conformance["summary"]["conformant"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
