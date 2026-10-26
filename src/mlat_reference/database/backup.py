"""Consistent SQLite backups/restores that never overwrite an existing file."""

import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import time


def copy_database(
    source: str | Path, destination: str | Path, *, timeout_seconds: float = 30
) -> dict:
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if os.path.lexists(destination):
        raise FileExistsError("Destination already exists; choose a new backup/restore path")
    if not 0 < timeout_seconds <= 3600:
        raise ValueError("Backup timeout must be within (0, 3600] seconds")
    deadline = time.monotonic() + timeout_seconds
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".mlat-backup-", suffix=".db", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    pages = 0

    def progress(_status, remaining, total):
        nonlocal pages
        pages = total
        if time.monotonic() > deadline:
            raise TimeoutError("SQLite backup deadline exceeded; retry during a quieter window")

    try:
        reader = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=5)
        writer = sqlite3.connect(temporary)
        try:
            reader.backup(writer, pages=128, progress=progress, sleep=0.01)
            writer.execute("PRAGMA journal_mode=DELETE")
            integrity = writer.execute("PRAGMA integrity_check").fetchall()
            if integrity != [("ok",)]:
                raise ValueError("SQLite backup integrity check failed")
            tables = {
                row[0]
                for row in writer.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            if not {"positions", "receivers"}.issubset(tables):
                raise ValueError("Source is not an MLAT database")
            version = writer.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise ValueError(
                    "Database schema is newer than this application's supported version"
                )
        finally:
            writer.close()
            reader.close()
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        # Atomic creation on the same filesystem. Unlike replace(), this cannot
        # destroy a destination that appeared while the backup was running.
        os.link(temporary, destination)
        digest = hashlib.sha256()
        with destination.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return {
            "status": "PASS",
            "integrity": "ok",
            "schema_version": version,
            "pages": pages,
            "bytes": destination.stat().st_size,
            "sha256": digest.hexdigest(),
        }
    finally:
        temporary.unlink(missing_ok=True)
