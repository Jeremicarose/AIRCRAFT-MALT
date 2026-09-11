from pathlib import Path

import pytest

from tools.registry import generate_registry_v2_review_evidence as review


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
