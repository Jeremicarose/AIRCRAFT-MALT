#!/usr/bin/env python3
"""Fail when application code reads an undocumented environment variable."""

from __future__ import annotations

import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "ENVIRONMENT.md"
SOURCE_ROOTS = (ROOT / "src", ROOT / "tools", ROOT / "reference" / "mlat" / "frontend")
SOURCE_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".tsx"}
SKIP_PARTS = {".next", ".vercel", "node_modules", "target", "tmp", "dist", "out"}
ENV_PATTERNS = (
    re.compile(
        r"(?:os\.getenv|os\.environ\.get|env_bool|_env_bool|_split_csv|env\.get)"
        r"\(\s*[\"']([A-Z][A-Z0-9_]*)[\"']"
    ),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]*)[\"']\s*\]"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)"),
)
SHELL_PATTERN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::[-+?])?")
INTERNAL_SHELL_NAMES = {
    "API_PID",
    "API_READY",
    "BASH_SOURCE",
    "PROCESSOR_PID",
    "PYTHONPATH",
    "ROOT_DIR",
}


def source_files() -> list[Path]:
    files: list[Path] = []
    for source_root in SOURCE_ROOTS:
        for directory, names, filenames in os.walk(source_root):
            names[:] = [
                name for name in names if name not in SKIP_PARTS and not name.startswith(".next-")
            ]
            directory_path = Path(directory)
            for filename in filenames:
                path = directory_path / filename
                relative_parts = path.relative_to(source_root).parts[:-1]
                if any(part in SKIP_PARTS or part.startswith(".next-") for part in relative_parts):
                    continue
                if path.suffix in SOURCE_SUFFIXES:
                    files.append(path)
    files.extend(ROOT.glob("*.sh"))
    return sorted(set(files))


def discovered_variables() -> set[str]:
    variables: set[str] = set()
    for path in source_files():
        content = path.read_text(encoding="utf-8")
        for pattern in ENV_PATTERNS:
            variables.update(pattern.findall(content))
        if path.suffix == ".sh":
            variables.update(SHELL_PATTERN.findall(content))
    return variables - INTERNAL_SHELL_NAMES


def documented_variables() -> set[str]:
    return set(re.findall(r"`([A-Z][A-Z0-9_]*)`", REFERENCE.read_text(encoding="utf-8")))


def undocumented_variables() -> list[str]:
    return sorted(discovered_variables() - documented_variables())


def main() -> int:
    missing = undocumented_variables()
    if missing:
        print("undocumented environment variables: " + ", ".join(missing))
        return 1
    print(f"environment documentation: pass ({len(discovered_variables())} variables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
