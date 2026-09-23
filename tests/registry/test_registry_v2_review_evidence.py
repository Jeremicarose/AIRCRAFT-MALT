from pathlib import Path
import json

import pytest

from tools.registry import generate_registry_v2_review_evidence as review
from tools.registry import verify_registry_v2_review_evidence as verifier


def test_clean_worktree_rejects_modified_and_untracked_files(monkeypatch):
    monkeypatch.setattr(
        review,
        "git",
        lambda *args: " M src/ckb_registry/record.py\n?? local-helper.py",
    )

    with pytest.raises(RuntimeError, match="tracked or untracked changes"):
        review.require_clean_worktree()


def test_clean_worktree_allows_only_the_bundle_being_generated(monkeypatch, tmp_path):
    output = review.ROOT / "evidence" / "review-test"
    monkeypatch.setattr(
        review,
        "git",
        lambda *args: "?? evidence/review-test/logs/python-tests.txt",
    )

    review.require_clean_worktree(output)

    with pytest.raises(RuntimeError, match="tracked or untracked changes"):
        review.require_clean_worktree(Path(tmp_path) / "outside-repository")


def test_review_generator_accepts_the_pinned_node_version(monkeypatch):
    monkeypatch.setattr(
        review,
        "tool_version",
        lambda command: f"v{review.PINNED_NODE_VERSION}",
    )

    review.require_pinned_node_version()


def test_review_generator_rejects_an_unpinned_node_version(monkeypatch):
    monkeypatch.setattr(review, "tool_version", lambda command: "v20.19.6")

    with pytest.raises(RuntimeError, match=r"Node\.js 22\.23\.1 is required.*nvm use"):
        review.require_pinned_node_version()


def test_review_generator_cleans_contract_before_building_it():
    check_names = [check.name for check in review.CHECKS]

    assert "contract-clean" in check_names
    assert check_names.index("contract-clean") < check_names.index("contract-tests")


def browser_report(commit: str, tree: str) -> dict:
    return {
        "schema_version": 1,
        "source_commit": commit,
        "source_tree": tree,
        "worktree_clean": True,
        "route": "/app/registry",
        "total_tests": 9,
        "completed_tests": 9,
        "passed_tests": 9,
        "failed_tests": 0,
        "failures": [],
        "accessibility_violations": 0,
        "pass": True,
    }


def test_browser_report_must_pass_and_match_source(tmp_path):
    commit = "a" * 40
    tree = "b" * 40
    path = tmp_path / "browser.json"
    path.write_text(json.dumps(browser_report(commit, tree)), encoding="utf-8")

    assert review.validate_browser_report(path, commit, tree)["total_tests"] == 9


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_tree", "c" * 40, "source_tree"),
        ("worktree_clean", False, "worktree_clean"),
        ("total_tests", 8, "at least 9"),
        ("accessibility_violations", 1, "accessibility_violations"),
        ("pass", False, "pass"),
    ],
)
def test_browser_report_fails_closed(tmp_path, field, value, message):
    commit = "a" * 40
    tree = "b" * 40
    report = browser_report(commit, tree)
    report[field] = value
    path = tmp_path / "browser.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(RuntimeError, match=message):
        review.validate_browser_report(path, commit, tree)


def test_github_ci_provenance_fails_closed_on_wrong_source(tmp_path):
    commit = "a" * 40
    report = {
        "schema_version": 1,
        "provider": "github_actions",
        "repository": "Jeremicarose/AIRCRAFT-MALT",
        "source_commit": "b" * 40,
        "repository_ci_run": {},
        "frontend_browser_job": {},
        "artifacts": [],
    }
    (tmp_path / "github-ci-provenance.json").write_text(json.dumps(report), encoding="utf-8")
    manifest = {
        "external_dependencies": {"github_ci_provenance": "completed"},
        "github_ci_provenance": {
            "report": "github-ci-provenance.json",
            "source_commit": commit,
        },
    }
    verification = verifier.Verification()

    verifier.verify_github_ci_provenance(tmp_path, manifest, commit, verification)

    assert not verification.passed
    assert any(
        check["name"] == "public GitHub CI source matches bundle" and check["pass"] is False
        for check in verification.checks
    )
