from pathlib import Path

from tools import check_documentation


def test_markdown_files_prunes_generated_test_and_build_trees(tmp_path: Path, monkeypatch) -> None:
    authoritative = tmp_path / "docs" / "guide.md"
    generated_test = tmp_path / "test-results" / "failure.md"
    generated_build = tmp_path / ".next-review" / "output.md"
    dependency = tmp_path / "node_modules" / "package" / "README.md"
    for path in (authoritative, generated_test, generated_build, dependency):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Markdown\n", encoding="utf-8")

    monkeypatch.setattr(check_documentation, "ROOT", tmp_path)

    assert check_documentation.markdown_files() == [authoritative]
