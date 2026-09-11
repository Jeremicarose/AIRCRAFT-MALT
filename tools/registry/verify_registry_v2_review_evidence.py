#!/usr/bin/env python3
"""Verify a source-bound Registry V2 review evidence bundle offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def ckb_hash(path: Path) -> str:
    digest = hashlib.blake2b(path.read_bytes(), digest_size=32, person=b"ckb-default-hash")
    return "0x" + digest.hexdigest()


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


class Verification:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks.append({"name": name, "pass": bool(condition), "detail": detail})

    @property
    def passed(self) -> bool:
        return all(check["pass"] for check in self.checks)


def verify_checksums(bundle: Path, verification: Verification) -> None:
    checksum_path = bundle / "checksums.sha256"
    verification.require("checksums exist", checksum_path.is_file(), str(checksum_path))
    if not checksum_path.is_file():
        return
    declared: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(checksum_path.read_text(encoding="ascii").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            errors.append(f"line {line_number} is invalid")
            continue
        digest, relative_name = match.groups()
        relative = PurePosixPath(relative_name)
        if relative.is_absolute() or ".." in relative.parts or relative_name == "checksums.sha256":
            errors.append(f"line {line_number} has unsafe path {relative_name!r}")
            continue
        if relative_name in declared:
            errors.append(f"line {line_number} duplicates {relative_name}")
            continue
        declared[relative_name] = digest

    actual = {
        path.relative_to(bundle).as_posix(): path
        for path in bundle.rglob("*")
        if path.is_file() and path != checksum_path
    }
    if set(actual) != set(declared):
        errors.append(
            f"file set differs: missing={sorted(set(actual) - set(declared))}, "
            f"extra={sorted(set(declared) - set(actual))}"
        )
    for name in sorted(set(actual) & set(declared)):
        if actual[name].is_symlink():
            errors.append(f"{name} is a symbolic link")
        elif sha256(actual[name]) != declared[name]:
            errors.append(f"{name} checksum differs")
    verification.require(
        "bundle checksums",
        not errors,
        "; ".join(errors) if errors else f"verified {len(actual)} files",
    )


def verify_bundle(bundle: Path) -> dict[str, Any]:
    verification = Verification()
    verify_checksums(bundle, verification)

    manifest_path = bundle / "manifest.json"
    report_path = bundle / "conformance-report.json"
    binary_path = bundle / "contract/receiver-registry"
    verification.require("manifest exists", manifest_path.is_file(), str(manifest_path))
    verification.require("conformance report exists", report_path.is_file(), str(report_path))
    verification.require("contract binary exists", binary_path.is_file(), str(binary_path))
    if not all(path.is_file() for path in (manifest_path, report_path, binary_path)):
        return {"pass": False, "checks": verification.checks}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source = manifest.get("source", {})
    commit = source.get("commit")
    tree = source.get("tree")
    source_ids_valid = (
        isinstance(commit, str)
        and SHA1.fullmatch(commit) is not None
        and isinstance(tree, str)
        and SHA1.fullmatch(tree) is not None
    )
    verification.require("source commit and tree are pinned", source_ids_valid, f"{commit}/{tree}")
    if source_ids_valid:
        try:
            observed_tree = git_bytes("rev-parse", f"{commit}^{{tree}}").decode().strip()
        except subprocess.CalledProcessError as exc:
            observed_tree = f"git error {exc.returncode}"
        verification.require("source tree matches commit", observed_tree == tree, observed_tree)
        for review_path in source.get("review_paths", []):
            try:
                git_bytes("cat-file", "-e", f"{commit}:{review_path}")
            except subprocess.CalledProcessError:
                exists = False
            else:
                exists = True
            verification.require(f"source contains {review_path}", exists, str(commit))

    candidate = manifest.get("contract_candidate", {})
    verification.require(
        "candidate binary SHA-256",
        SHA256.fullmatch(str(candidate.get("binary_sha256", ""))) is not None
        and sha256(binary_path) == candidate.get("binary_sha256"),
        sha256(binary_path),
    )
    verification.require(
        "candidate binary CKB data hash",
        ckb_hash(binary_path) == candidate.get("binary_ckb_data_hash"),
        ckb_hash(binary_path),
    )
    deployment_status = candidate.get("deployment_status")
    if deployment_status == "not_deployed":
        verification.require(
            "candidate is not claimed as deployed",
            candidate.get("future_registry_code_hash") is None,
            str(deployment_status),
        )
    else:
        verification.require(
            "candidate is bound to immutable testnet deployment",
            deployment_status == "deployed_testnet_data1"
            and candidate.get("registry_code_hash") == candidate.get("binary_ckb_data_hash"),
            str(deployment_status),
        )

        deployed = manifest.get("immutable_testnet_deployment", {})
        deployed_bundle_name = "evidence/registry-v2-testnet-2026-09-11-data1-final"
        deployed_bundle = ROOT / deployed_bundle_name
        deployed_manifest = deployed_bundle / "manifest.json"
        deployed_checksums = deployed_bundle / "checksums.sha256"
        verification.require(
            "immutable lifecycle bundle is pinned",
            deployed.get("bundle") == deployed_bundle_name
            and deployed.get("status") == "signed_chain_evidence_complete_ci_provenance_pending"
            and deployed.get("registry_hash_type") == "data1"
            and deployed.get("registry_code_hash") == candidate.get("binary_ckb_data_hash")
            and deployed_manifest.is_file()
            and deployed_checksums.is_file()
            and sha256(deployed_manifest) == deployed.get("manifest_sha256")
            and sha256(deployed_checksums) == deployed.get("checksums_sha256"),
            str(deployed.get("bundle")),
        )

    conformance = manifest.get("conformance", {})
    corpus_hash = conformance.get("corpus_sha256")
    if source_ids_valid:
        try:
            corpus_bytes = git_bytes(
                "show", f"{commit}:tests/registry/fixtures/registry_v2_conformance.json"
            )
        except subprocess.CalledProcessError:
            observed_corpus_hash = "unavailable"
        else:
            observed_corpus_hash = sha256_bytes(corpus_bytes)
        verification.require(
            "corpus is bound to source commit",
            observed_corpus_hash == corpus_hash,
            observed_corpus_hash,
        )
    verification.require(
        "conformance report passed",
        report.get("summary", {}).get("conformant") is True
        and report.get("summary", {}).get("cross_language_equal") is True
        and report.get("summary", {}).get("failed_case_count") == 0,
        json.dumps(report.get("summary", {}), sort_keys=True),
    )
    verification.require(
        "conformance report source matches manifest",
        report.get("source", {}).get("commit") == commit
        and report.get("source", {}).get("tree") == tree
        and report.get("source", {}).get("tracked_worktree_clean") is True,
        json.dumps(report.get("source", {}), sort_keys=True),
    )
    verification.require(
        "conformance report corpus matches manifest",
        report.get("corpus_sha256") == corpus_hash,
        str(report.get("corpus_sha256")),
    )

    recorded_checks = manifest.get("verification", {}).get("checks", [])
    verification.require(
        "all recorded checks passed",
        bool(recorded_checks)
        and manifest.get("verification", {}).get("all_passed") is True
        and all(check.get("exit_code") == 0 for check in recorded_checks),
        f"{len(recorded_checks)} recorded checks",
    )
    browser_evidence = manifest.get("browser_evidence")
    browser_report_path = bundle / "browser-qa-report.json"
    if deployment_status == "deployed_testnet_data1" or browser_evidence is not None:
        browser_evidence = browser_evidence or {}
        verification.require(
            "browser report exists",
            browser_evidence.get("report") == "browser-qa-report.json"
            and browser_report_path.is_file(),
            str(browser_evidence.get("report")),
        )
    if browser_evidence is not None and browser_report_path.is_file():
        browser_report = json.loads(browser_report_path.read_text(encoding="utf-8"))
        verification.require(
            "browser report is bound to source",
            browser_report.get("source_commit") == commit
            and browser_report.get("source_tree") == tree
            and browser_report.get("worktree_clean") is True
            and browser_evidence.get("source_commit") == commit
            and browser_evidence.get("source_tree") == tree
            and browser_evidence.get("worktree_clean") is True,
            f"{browser_report.get('source_commit')}/{browser_report.get('source_tree')}",
        )
        total_tests = browser_report.get("total_tests")
        verification.require(
            "browser and accessibility checks passed",
            isinstance(total_tests, int)
            and not isinstance(total_tests, bool)
            and total_tests >= 9
            and browser_report.get("completed_tests") == total_tests
            and browser_report.get("passed_tests") == total_tests
            and browser_report.get("failed_tests") == 0
            and browser_report.get("failures") == []
            and browser_report.get("accessibility_violations") == 0
            and browser_report.get("route") == "/app/registry"
            and browser_report.get("pass") is True
            and browser_evidence.get("total_tests") == total_tests
            and browser_evidence.get("accessibility_violations") == 0
            and browser_evidence.get("route") == "/app/registry"
            and browser_evidence.get("pass") is True,
            f"{total_tests} tests; {browser_report.get('accessibility_violations')} findings",
        )
    verification.require(
        "private keys excluded",
        manifest.get("private_keys_included") is False,
        str(manifest.get("private_keys_included")),
    )
    sdk_lifecycle_status = manifest.get("external_dependencies", {}).get(
        "fresh_sdk_testnet_lifecycle"
    )
    verification.require(
        "browser SDK lifecycle remains external",
        sdk_lifecycle_status
        in {"blocked_browser_wallet_approval", "blocked_external_signer_and_testnet_funds"},
        str(sdk_lifecycle_status),
    )
    return {"pass": verification.passed, "checks": verification.checks}


def main() -> None:
    args = parse_args()
    result = verify_bundle(args.bundle.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
