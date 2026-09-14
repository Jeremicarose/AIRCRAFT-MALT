#!/usr/bin/env python3
"""Fail when authoritative Markdown links point at missing repository paths."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".next",
    "node_modules",
    "playwright-report",
    "target",
    "test-results",
}
SKIP_TREES = {
    Path(".pytest_cache"),
    Path("ckb-cli"),
    Path("data"),
    Path("deploy"),
    Path("evidence/registry-v2-testnet-2026-07-30-final"),
    Path("evidence/mlat-reference/reproducible-benchmark-v2/source"),
}


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for current_root, directory_names, file_names in os.walk(ROOT):
        current = Path(current_root)
        directory_names[:] = [
            name
            for name in directory_names
            if not _skip_directory((current / name).relative_to(ROOT))
        ]
        files.extend(current / name for name in file_names if name.endswith(".md"))
    return sorted(files)


def _skip_directory(relative: Path) -> bool:
    return (
        relative.name in SKIP_DIRECTORY_NAMES
        or relative.name.startswith(".next-")
        or any(relative == tree or tree in relative.parents for tree in SKIP_TREES)
    )


def local_link_failures(path: Path) -> list[str]:
    failures = []
    content = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(content.splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            destination = match.group(1).strip()
            if destination.startswith("<") and destination.endswith(">"):
                destination = destination[1:-1]
            if not destination or destination.startswith(SKIP_PREFIXES):
                continue
            destination = unquote(destination.split("#", 1)[0])
            if not destination:
                continue
            target = (path.parent / destination).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{path.relative_to(ROOT)}:{line_number}: link leaves repository: {destination}"
                )
                continue
            if not target.exists():
                failures.append(
                    f"{path.relative_to(ROOT)}:{line_number}: missing link target: {destination}"
                )
    return failures


def verify_documentation() -> list[str]:
    failures = []
    for path in markdown_files():
        failures.extend(local_link_failures(path))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = verify_documentation()
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 2
    if not args.quiet:
        print(f"documentation links: pass ({len(markdown_files())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
