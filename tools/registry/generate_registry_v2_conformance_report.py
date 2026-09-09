#!/usr/bin/env python3
"""Run all Registry V2 implementations and write their conformance matrix."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from .registry_v2_conformance import evaluate_python  # type: ignore[import-not-found]
except ImportError:
    from registry_v2_conformance import evaluate_python  # noqa: E402

IMPLEMENTATIONS = ("rust", "python", "typescript")
CATEGORIES = (
    ("record", "record_cases"),
    ("identity", "identity_cases"),
    ("type_id", "type_id_vectors"),
    ("creation", "creation_cases"),
    ("transition", "transition_cases"),
    ("script", "script_cases"),
    ("discovery", "discovery_cases"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests/registry/fixtures/registry_v2_conformance.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/registry-v2/conformance-report.json",
    )
    return parser.parse_args()


def _run_json(command: list[str], cwd: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{' '.join(command)} did not emit one JSON document") from exc


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _source_provenance() -> Dict[str, Any]:
    tracked_status = _git_value("status", "--short", "--untracked-files=no")
    return {
        "commit": _git_value("rev-parse", "HEAD"),
        "tree": _git_value("rev-parse", "HEAD^{tree}"),
        "tracked_worktree_clean": not bool(tracked_status),
    }


def _expected(category: str, case: Dict[str, Any]) -> Dict[str, Any]:
    if category == "record":
        return {
            "accepted": case["valid"],
            "creation_accepted": case["creation_valid"],
        }
    if category == "identity":
        return {
            "accepted": case["valid"],
            "normalized": case["value"].lower() if case["valid"] else None,
        }
    if category == "type_id":
        return {"accepted": True, "value": case["expected"]}
    if category == "creation":
        return {
            "accepted": case["valid"],
            "receiver_identity": case["args"].lower() if case["valid"] else None,
        }
    if category == "transition":
        return {
            "accepted": case["valid"],
            "action": case.get("action") if case["valid"] else None,
        }
    if category == "script":
        return {
            "accepted": case["valid"],
            "receiver_identity": case["args"].lower() if case["valid"] else None,
        }
    return {
        "active_identities": case["expected_active_identities"],
        "including_revoked_identities": case["expected_including_revoked_identities"],
        "quarantined_identities": case["quarantined_identities"],
    }


def _case_definitions(corpus: Dict[str, Any]) -> list[Dict[str, Any]]:
    definitions = []
    for category, key in CATEGORIES:
        for case in corpus[key]:
            definitions.append(
                {
                    "id": f"{category}/{case['name']}",
                    "category": category,
                    "expected": _expected(category, case),
                }
            )
    return definitions


def _index_results(result: Dict[str, Any], expected_ids: set[str]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in result.get("results", []):
        case_id = item.get("id")
        if not isinstance(case_id, str) or case_id in indexed:
            raise ValueError(
                f"{result.get('implementation')} emitted an invalid or duplicate case id"
            )
        indexed[case_id] = item["outcome"]
    if set(indexed) != expected_ids:
        missing = sorted(expected_ids - set(indexed))
        extra = sorted(set(indexed) - expected_ids)
        raise ValueError(
            f"{result.get('implementation')} result set differs from corpus; "
            f"missing={missing}, extra={extra}"
        )
    return indexed


def _same_json(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(
        right,
        sort_keys=True,
        separators=(",", ":"),
    )


def build_report(
    corpus: Dict[str, Any],
    corpus_bytes: bytes,
    runtime_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    definitions = _case_definitions(corpus)
    expected_ids = {definition["id"] for definition in definitions}
    indexed = {
        name: _index_results(runtime_results[name], expected_ids) for name in IMPLEMENTATIONS
    }
    cases = []
    for definition in definitions:
        case_id = definition["id"]
        outcomes = {name: indexed[name][case_id] for name in IMPLEMENTATIONS}
        first = outcomes[IMPLEMENTATIONS[0]]
        implementations_equal = all(_same_json(outcome, first) for outcome in outcomes.values())
        expected = definition["expected"]
        matches_expected = all(
            all(_same_json(outcome.get(key), value) for key, value in expected.items())
            for outcome in outcomes.values()
        )
        cases.append(
            {
                **definition,
                "outcomes": outcomes,
                "implementations_equal": implementations_equal,
                "matches_expected": matches_expected,
                "pass": implementations_equal and matches_expected,
            }
        )

    passed = sum(case["pass"] for case in cases)
    return {
        "report_schema_version": 1,
        "protocol": "ckb-receiver-registry-v2",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": _source_provenance(),
        "corpus": "tests/registry/fixtures/registry_v2_conformance.json",
        "corpus_schema_version": corpus["schema_version"],
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "implementations": list(IMPLEMENTATIONS),
        "summary": {
            "case_count": len(cases),
            "implementation_count": len(IMPLEMENTATIONS),
            "assertion_count": len(cases) * len(IMPLEMENTATIONS),
            "passed_case_count": passed,
            "failed_case_count": len(cases) - passed,
            "cross_language_equal": all(case["implementations_equal"] for case in cases),
            "conformant": passed == len(cases),
        },
        "cases": cases,
    }


def main() -> None:
    args = parse_args()
    corpus_path = args.corpus.resolve()
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    logging.getLogger("ckb_registry.discovery").setLevel(logging.CRITICAL)

    subprocess.run(
        ["npm", "run", "build", "--silent"],
        cwd=ROOT / "sdk/typescript",
        check=True,
    )
    runtime_results = {
        "rust": _run_json(
            [
                "cargo",
                "run",
                "--quiet",
                "--locked",
                "--example",
                "conformance",
                "--",
                str(corpus_path),
            ],
            ROOT / "contracts/registry-v2",
        ),
        "python": evaluate_python(corpus),
        "typescript": _run_json(
            ["node", "dist/test/conformance-runner.js", str(corpus_path)],
            ROOT / "sdk/typescript",
        ),
    }
    for name, result in runtime_results.items():
        if result.get("implementation") != name:
            raise ValueError(f"{name} runner identified itself as {result.get('implementation')!r}")
        if result.get("corpus_schema_version") != corpus["schema_version"]:
            raise ValueError(f"{name} runner used a different corpus schema version")

    report = build_report(corpus, corpus_bytes, runtime_results)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
    if not report["summary"]["conformant"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
