"""Read-only, integrity-checked SQLite snapshot helper for NeuroLens."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when a safe database snapshot cannot be created."""


def create_sqlite_backup(database_path: str | Path, max_bytes: int = 512 * 1024 * 1024) -> bytes:
    """Create a consistent SQLite snapshot without writing to the source DB."""
    path = Path(database_path)
    if not path.is_file():
        raise BackupError("Database file is unavailable.")
    if path.stat().st_size <= 0:
        raise BackupError("Database file is empty.")
    if path.stat().st_size > max_bytes:
        raise BackupError("Database exceeds the configured backup size limit.")

    source = None
    snapshot = None
    try:
        source = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        snapshot = sqlite3.connect(":memory:")
        source.backup(snapshot)
        integrity = snapshot.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise BackupError("Database integrity check failed.")
        payload = snapshot.serialize()
        if not payload or len(payload) > max_bytes:
            raise BackupError("Backup snapshot is empty or exceeds the size limit.")
        return payload
    except BackupError:
        raise
    except (OSError, sqlite3.Error, AttributeError) as exc:
        raise BackupError("Could not create a verified database backup.") from exc
    finally:
        if snapshot is not None:
            snapshot.close()
        if source is not None:
            source.close()


def backup_sha256(payload: bytes) -> str:
    if not isinstance(payload, bytes) or not payload:
        raise BackupError("A non-empty backup payload is required.")
    return hashlib.sha256(payload).hexdigest()
