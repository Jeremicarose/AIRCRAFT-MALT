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
DEPLOYED_BUNDLE = ROOT / "evidence/registry-v2-testnet-2026-09-11-data1-final"
PINNED_NODE_VERSION = (ROOT / ".nvmrc").read_text(encoding="ascii").strip()


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
        "immutable-testnet-evidence",
        (
            sys.executable,
            "tools/registry/verify_registry_v2_evidence.py",
            "--bundle",
            "evidence/registry-v2-testnet-2026-09-11-data1-final",
            "--saved-chain-only",
        ),
    ),
    Check(
        "environment-documentation",
        (sys.executable, "tools/check_environment_documentation.py"),
    ),
    Check(
        "repository-release-readiness",
        (sys.executable, "tools/check_release_readiness.py", "--profile", "repository"),
    ),
    Check(
        "deterministic-mlat-evidence",
        (sys.executable, "tools/mlat/run_reproducible_benchmark.py", "--verify-only"),
    ),
    Check("contract-clean", ("make", "clean"), CONTRACT),
    Check("contract-tests", ("make", "test"), CONTRACT),
    Check("contract-target-check", ("make", "check"), CONTRACT),
    Check("typescript-sdk-tests", ("npm", "test"), SDK),
    Check("frontend-tests", ("npm", "test"), FRONTEND),
    Check("frontend-typecheck", ("npm", "run", "typecheck"), FRONTEND),
    Check("frontend-build", ("npm", "run", "build"), FRONTEND),
)

REVIEW_PATHS = (
    ".env.example",
    ".github/workflows/pilot-readiness.yml",
    ".github/workflows/reproducibility.yml",
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
    "reference/mlat/frontend/lib/standalone.mjs",
    "reference/mlat/frontend/lib/receiver-freshness.ts",
    "reference/mlat/frontend/lib/receiver-reference.ts",
    "reference/mlat/frontend/lib/receiver-state.ts",
    "reference/mlat/frontend/lib/registry.ts",
    "reference/mlat/frontend/lib/routes.ts",
    "reference/mlat/frontend/package.json",
    "reference/mlat/frontend/playwright.config.mjs",
    "reference/mlat/frontend/scripts/start-standalone.mjs",
    "reference/mlat/frontend/test/e2e/evidence-reporter.mjs",
    "reference/mlat/frontend/test/e2e/registry-accessibility.spec.mjs",
    "reference/mlat/frontend/test/e2e/release.spec.mjs",
    "reference/mlat/frontend/test/evidence-reporter.test.mjs",
    "reference/mlat/frontend/test/playwright-config.test.mjs",
    "reference/mlat/frontend/test/registry-workflow-contract.test.mjs",
    "reference/mlat/frontend/test/standalone.test.mjs",
    "reference/mlat/frontend/test/receiver-freshness.test.mjs",
    "reference/mlat/frontend/test/receiver-reference.test.mjs",
    "tests/registry/fixtures/registry_v2_conformance.json",
    "evidence/registry-v2-testnet-2026-09-11-data1-final/manifest.json",
    "evidence/registry-v2-testnet-2026-09-11-data1-final/checksums.sha256",
    "tests/registry/test_deployment_and_indexer_health.py",
    "tests/registry/test_registry_v2_conformance_report.py",
    "tests/registry/test_registry_v2_review_evidence.py",
    "tests/test_environment_documentation.py",
    "tests/test_release_readiness.py",
    "tools/check_environment_documentation.py",
    "tools/registry/generate_registry_v2_conformance_report.py",
    "tools/registry/generate_registry_v2_review_evidence.py",
    "tools/registry/registry_v2_conformance.py",
    "tools/registry/check_registry_indexer_health.py",
    "tools/registry/verify_data1_deployment.py",
    "tools/registry/verify_registry_v2_review_evidence.py",
    "EVIDENCE.md",
    "REPRODUCIBILITY.md",
    "docs/pilot/READINESS_GATE.md",
    "docs/pilot/IMPLEMENTATION_STATUS_2026-09-11.md",
    "docs/ENVIRONMENT.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New bundle directory")
    parser.add_argument(
        "--browser-report",
        type=Path,
        required=True,
        help="Passing browser QA report produced from the clean source tree",
    )
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


def require_clean_worktree(allowed_output: Path | None = None) -> None:
    allowed_prefix: str | None = None
    if allowed_output is not None:
        try:
            allowed_prefix = allowed_output.resolve().relative_to(ROOT).as_posix().rstrip("/")
        except ValueError:
            pass

    unexpected = []
    for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if line.startswith("?? ") and allowed_prefix is not None:
            relative = line[3:]
            if relative == allowed_prefix or relative.startswith(f"{allowed_prefix}/"):
                continue
        unexpected.append(line)
    if unexpected:
        raise RuntimeError(
            "worktree contains tracked or untracked changes; commit or remove them "
            "before generating evidence:\n" + "\n".join(unexpected)
        )


def validate_browser_report(path: Path, source_commit: str, source_tree: str) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"browser report cannot be read: {path}: {exc}") from exc

    failures = []
    expected_values = {
        "schema_version": 1,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "worktree_clean": True,
        "route": "/app/registry",
        "failed_tests": 0,
        "failures": [],
        "accessibility_violations": 0,
        "pass": True,
    }
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"{field} must be {expected!r}")

    total = report.get("total_tests")
    completed = report.get("completed_tests")
    passed = report.get("passed_tests")
    if not isinstance(total, int) or isinstance(total, bool) or total < 9:
        failures.append("total_tests must be an integer of at least 9")
    elif completed != total or passed != total:
        failures.append("all expected browser tests must be completed and pass")

    if failures:
        raise RuntimeError("browser report is not release evidence: " + "; ".join(failures))
    return report


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


def require_pinned_node_version() -> None:
    try:
        observed = tool_version(("node", "--version")).removeprefix("v")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"Node.js {PINNED_NODE_VERSION} is required; run `nvm use` before "
            "generating review evidence"
        ) from exc
    if observed != PINNED_NODE_VERSION:
        raise RuntimeError(
            f"Node.js {PINNED_NODE_VERSION} is required, but {observed or 'an unknown version'} "
            "is active; run `nvm use` before generating review evidence"
        )


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

    require_clean_worktree()
    require_pinned_node_version()
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    repository = git("remote", "get-url", "origin")
    browser_report = validate_browser_report(
        args.browser_report.resolve(), source_commit, source_tree
    )

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

    require_clean_worktree(output)
    binary_dir = output / "contract"
    binary_dir.mkdir()
    copied_binary = binary_dir / "receiver-registry"
    shutil.copy2(CONTRACT_BINARY, copied_binary)
    shutil.copy2(args.browser_report.resolve(), output / "browser-qa-report.json")

    historical = json.loads((HISTORICAL_BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    deployed = json.loads((DEPLOYED_BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    deployed_contract = deployed["contract"]
    if (
        sha256(copied_binary) != deployed_contract["binary_sha256"]
        or ckb_hash(copied_binary) != deployed_contract["binary_ckb_data_hash"]
    ):
        raise RuntimeError("review binary does not match the immutable testnet deployment")
    manifest = {
        "schema_version": 1,
        "status": "verified_immutable_testnet_deployment",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "repository": repository,
            "commit": source_commit,
            "tree": source_tree,
            "tracked_worktree_clean": True,
            "untracked_worktree_clean": True,
            "review_paths": list(REVIEW_PATHS),
        },
        "contract_candidate": {
            "deployment_status": "deployed_testnet_data1",
            "binary": "contract/receiver-registry",
            "binary_bytes": copied_binary.stat().st_size,
            "binary_sha256": sha256(copied_binary),
            "binary_ckb_data_hash": ckb_hash(copied_binary),
            "registry_code_hash": deployed_contract["type_script_hash_for_registry_code_hash"],
        },
        "conformance": {
            "report": "conformance-report.json",
            "corpus": "tests/registry/fixtures/registry_v2_conformance.json",
            "corpus_sha256": sha256(CORPUS),
            "summary": conformance["summary"],
        },
        "verification": {"checks": checks, "all_passed": True},
        "browser_evidence": {
            "report": "browser-qa-report.json",
            "route": browser_report["route"],
            "total_tests": browser_report["total_tests"],
            "accessibility_violations": browser_report["accessibility_violations"],
            "source_commit": browser_report["source_commit"],
            "source_tree": browser_report["source_tree"],
            "worktree_clean": browser_report["worktree_clean"],
            "pass": browser_report["pass"],
        },
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
        "immutable_testnet_deployment": {
            "status": "signed_chain_evidence_complete_ci_provenance_pending",
            "bundle": "evidence/registry-v2-testnet-2026-09-11-data1-final",
            "manifest_sha256": sha256(DEPLOYED_BUNDLE / "manifest.json"),
            "checksums_sha256": sha256(DEPLOYED_BUNDLE / "checksums.sha256"),
            "contract_source_commit": deployed["source"]["contract_source_commit"],
            "deployment_tx_hash": deployed_contract["deployment_tx_hash"],
            "contract_out_point": deployed_contract["out_point"],
            "registry_code_hash": deployed_contract["type_script_hash_for_registry_code_hash"],
            "registry_hash_type": deployed_contract["registry_script_hash_type"],
            "receiver_identity": deployed["receiver"]["receiver_identity"],
            "accepted_transactions": deployed["accepted_transactions"],
        },
        "external_dependencies": {
            "fresh_sdk_testnet_lifecycle": "blocked_browser_wallet_approval",
            "independent_security_review": "not_completed",
            "github_ci_provenance": "not_completed",
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
        "The included contract binary matches the immutable `data1` Pudge deployment "
        "and its signed CKB CLI lifecycle evidence. The July mutable deployment is "
        "retained separately for historical comparison. No private key is included. "
        "The browser QA report is bound to the same clean source tree. A "
        "browser/TypeScript-SDK signed lifecycle and independent security review "
        "remain external steps.\n\n"
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
