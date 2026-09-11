#!/usr/bin/env python3
"""Check repository hygiene and fail closed for stable release evidence."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_documentation import verify_documentation
from tools.check_environment_documentation import undocumented_variables
from tools.registry.verify_registry_v2_evidence import verify_bundle

STABLE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX32 = re.compile(r"^0x[0-9a-f]{64}$")
PRIMARY_BROWSER_ROUTE = "/app/registry"
MINIMUM_BROWSER_TESTS = 9
REQUIRED_FILES = (
    ".env.example",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "RELEASE.md",
    "MAINTAINERS.md",
    "CODE_OF_CONDUCT.md",
    "docs/ENVIRONMENT.md",
    "docs/audit/REPOSITORY_AUDIT.md",
)
FORBIDDEN_TRACKED_PARTS = {
    ".next",
    "__pycache__",
    "node_modules",
    "playwright-report",
    "target",
    "test-results",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
)
AUDIT_REVIEW_PATHS = (
    "contracts/registry-v2",
    "src/ckb_registry",
    "sdk/typescript/src",
    "tests/registry/fixtures/registry_v2_conformance.json",
)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def safe_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty repository-relative path")
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"{field} leaves the repository") from exc
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_public_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or host == "localhost"
        or host.endswith((".localhost", ".local", ".example", ".invalid", ".test"))
        or host in {"example.com", "example.net", "example.org"}
        or host.endswith((".example.com", ".example.net", ".example.org"))
        or "." not in host
    ):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


def repository_checks() -> list[Check]:
    documentation_failures = verify_documentation()
    missing_environment_variables = undocumented_variables()
    checks = [
        Check(
            "required release files",
            all((ROOT / path).is_file() for path in REQUIRED_FILES),
            ", ".join(path for path in REQUIRED_FILES if not (ROOT / path).is_file()) or "present",
        ),
        Check(
            "local documentation links",
            not documentation_failures,
            "; ".join(documentation_failures) or "all local links resolve",
        ),
        Check(
            "environment documentation",
            not missing_environment_variables,
            ", ".join(missing_environment_variables) or "all discovered variables documented",
        ),
    ]

    ignored = git("check-ignore", "-q", "artifacts/release-output", check=False)
    checks.append(Check("generated artifact policy", ignored.returncode == 0, "artifacts/ ignored"))

    tracked = git("ls-files").stdout.splitlines()
    forbidden: list[str] = []
    for value in tracked:
        path = Path(value)
        if (
            (path.name.startswith(".env") and value != ".env.example")
            or value == ".coverage"
            or value.startswith(("data/", "deploy/", "logs/"))
        ):
            forbidden.append(value)
        elif path.suffix in {".db", ".pyc"} or any(
            part in FORBIDDEN_TRACKED_PARTS or part.startswith(".next-") for part in path.parts
        ):
            forbidden.append(value)
    checks.append(
        Check(
            "generated and private files are untracked",
            not forbidden,
            ", ".join(forbidden) or "no forbidden tracked paths",
        )
    )

    secret_hits: list[str] = []
    for value in tracked:
        if value.endswith(".bin"):
            continue
        path = ROOT / value
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            secret_hits.append(value)
    checks.append(
        Check(
            "high-confidence secret scan",
            not secret_hits,
            ", ".join(secret_hits) or "no high-confidence secret patterns",
        )
    )
    return checks


def _read_json(path: Path, field: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read {field}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{field} must contain a JSON object")
    return value


def _unchanged_since(commit: str, paths: tuple[str, ...]) -> bool:
    if not COMMIT.fullmatch(commit):
        return False
    ancestor = git("merge-base", "--is-ancestor", commit, "HEAD", check=False)
    if ancestor.returncode != 0:
        return False
    return git("diff", "--quiet", commit, "HEAD", "--", *paths, check=False).returncode == 0


def stable_release_checks(
    manifest_path: Path, *, release_ref: str, live: bool = False
) -> list[Check]:
    checks: list[Check] = []
    clean = not git("status", "--porcelain=v1", "--untracked-files=all").stdout.strip()
    checks.append(Check("clean release worktree", clean, "clean" if clean else "changes present"))
    checks.append(
        Check("stable semantic version tag", bool(STABLE_TAG.fullmatch(release_ref)), release_ref)
    )

    try:
        manifest = _read_json(manifest_path, "release manifest")
    except ValueError as exc:
        return checks + [Check("release manifest", False, str(exc))]

    checks.append(
        Check(
            "release manifest version",
            manifest.get("schema_version") == 1 and manifest.get("release_version") == release_ref,
            str(manifest.get("release_version")),
        )
    )

    operations = manifest.get("operations")
    required_operations = {
        "strict_production_mode": True,
        "demo_mode": False,
        "simulate_if_unavailable": False,
        "ckb_ssl_verify": True,
        "registry_hash_type": "data1",
        "allow_mutable_registry_code": False,
        "rate_limit_enabled": True,
        "admin_api_enabled": False,
    }
    operations_valid = isinstance(operations, dict) and all(
        operations.get(key) == value for key, value in required_operations.items()
    )
    origins = operations.get("cors_allowed_origins", []) if isinstance(operations, dict) else []
    cors_valid = bool(origins) and all(is_public_https_url(origin) for origin in origins)
    checks.append(
        Check(
            "production operation settings",
            operations_valid and cors_valid,
            json.dumps(operations, sort_keys=True),
        )
    )

    audit_commit = ""
    audit_binary_sha256 = ""
    audit_binary_ckb_data_hash = ""
    try:
        audit_path = safe_path(manifest.get("security_review_attestation"), "security review")
        audit = _read_json(audit_path, "security review attestation")
        audit_commit = str(audit.get("source_commit", ""))
        audit_binary_sha256 = str(audit.get("contract_binary_sha256", ""))
        audit_binary_ckb_data_hash = str(audit.get("contract_binary_ckb_data_hash", ""))
        report_path = safe_path(audit.get("report_path"), "security review report")
        report_hash_valid = report_path.is_file() and sha256(report_path) == audit.get(
            "report_sha256"
        )
        audit_valid = (
            audit.get("schema_version") == 1
            and audit.get("independent") is True
            and audit.get("conclusion") in {"pass", "pass_with_findings"}
            and audit.get("unresolved_critical_findings") == 0
            and audit.get("unresolved_high_findings") == 0
            and isinstance(audit.get("reviewer"), str)
            and bool(audit["reviewer"].strip())
            and is_public_https_url(audit.get("report_url"))
            and is_public_https_url(audit.get("signature_or_account_url"))
            and SHA256.fullmatch(audit_binary_sha256) is not None
            and HEX32.fullmatch(audit_binary_ckb_data_hash) is not None
            and report_hash_valid
            and _unchanged_since(audit_commit, AUDIT_REVIEW_PATHS)
        )
    except (KeyError, ValueError) as exc:
        audit_valid = False
        report_hash_valid = False
        audit_commit = str(exc)
    checks.append(
        Check(
            "independent security review",
            audit_valid,
            f"source={audit_commit} report_hash={report_hash_valid}",
        )
    )

    try:
        lifecycle_path = safe_path(manifest.get("lifecycle_evidence_bundle"), "lifecycle bundle")
        lifecycle = _read_json(lifecycle_path / "manifest.json", "lifecycle manifest")
        contract = lifecycle.get("contract", {})
        if not isinstance(contract, dict):
            raise ValueError("lifecycle contract must be a JSON object")
        lifecycle_valid = (
            lifecycle.get("status") == "complete"
            and lifecycle.get("private_keys_included") is False
            and contract.get("registry_script_hash_type") == "data1"
            and contract.get("type_script_hash_for_registry_code_hash")
            == contract.get("binary_ckb_data_hash")
            and HEX32.fullmatch(str(contract.get("binary_ckb_data_hash", ""))) is not None
            and verify_bundle(lifecycle_path, live=live).get("pass") is True
        )
    except (KeyError, OSError, ValueError) as exc:
        lifecycle_valid = False
        lifecycle_path = Path(str(exc))
    checks.append(
        Check("immutable signed lifecycle evidence", lifecycle_valid, str(lifecycle_path))
    )
    review_deployment_link_valid = (
        audit_valid
        and lifecycle_valid
        and contract.get("binary_sha256") == audit_binary_sha256
        and contract.get("binary_ckb_data_hash") == audit_binary_ckb_data_hash
    )
    checks.append(
        Check(
            "reviewed binary matches lifecycle deployment",
            review_deployment_link_valid,
            f"review={audit_binary_ckb_data_hash} deployment="
            f"{contract.get('binary_ckb_data_hash') if lifecycle_valid else 'unverified'}",
        )
    )

    try:
        browser_path = safe_path(manifest.get("browser_qa_report"), "browser QA report")
        browser = _read_json(browser_path, "browser QA report")
        browser_commit = str(browser.get("source_commit", ""))
        browser_tree = str(browser.get("source_tree", ""))
        observed_browser_tree = (
            git("rev-parse", f"{browser_commit}^{{tree}}", check=False).stdout.strip()
            if COMMIT.fullmatch(browser_commit)
            else ""
        )
        browser_valid = (
            browser.get("schema_version") == 1
            and browser.get("pass") is True
            and browser.get("worktree_clean") is True
            and browser.get("route") == PRIMARY_BROWSER_ROUTE
            and browser_tree == observed_browser_tree
            and isinstance(browser.get("total_tests"), int)
            and browser["total_tests"] >= MINIMUM_BROWSER_TESTS
            and browser.get("completed_tests") == browser["total_tests"]
            and browser.get("passed_tests") == browser["total_tests"]
            and browser.get("accessibility_violations") == 0
            and browser.get("failed_tests") == 0
            and _unchanged_since(browser_commit, ("reference/mlat/frontend",))
        )
    except (OSError, ValueError) as exc:
        browser_valid = False
        browser_commit = str(exc)
    checks.append(Check("browser and accessibility evidence", browser_valid, browser_commit))

    deployment_url = manifest.get("public_deployment_url")
    url_valid = is_public_https_url(deployment_url)
    live_valid = not live
    if live and url_valid:
        try:
            with urllib.request.urlopen(
                f"{deployment_url.rstrip('/')}/healthz", timeout=15
            ) as response:
                live_valid = response.status == 200
        except OSError:
            live_valid = False
    checks.append(
        Check(
            "public HTTPS deployment",
            url_valid and live_valid,
            str(deployment_url),
        )
    )
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("repository", "stable"), default="repository")
    parser.add_argument("--manifest", type=Path, default=ROOT / "release" / "release.json")
    parser.add_argument("--release-ref", default=os.getenv("GITHUB_REF_NAME", ""))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = repository_checks()
    if args.profile == "stable":
        checks.extend(
            stable_release_checks(
                args.manifest.resolve(), release_ref=args.release_ref, live=args.live
            )
        )
    result = {"pass": all(check.passed for check in checks), "checks": [asdict(c) for c in checks]}
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
