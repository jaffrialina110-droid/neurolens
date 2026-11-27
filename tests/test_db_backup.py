import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from modules.db_backup import BackupError, backup_sha256, create_sqlite_backup


class DatabaseBackupTests(unittest.TestCase):
    def test_backup_is_valid_and_source_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite3"
            connection = sqlite3.connect(source)
            connection.execute("CREATE TABLE sample (value TEXT)")
            connection.execute("INSERT INTO sample VALUES ('staging-only')")
            connection.commit()
            connection.close()

            original_size = source.stat().st_size
            payload = create_sqlite_backup(source)
            self.assertEqual(source.stat().st_size, original_size)
            self.assertEqual(backup_sha256(payload), hashlib.sha256(payload).hexdigest())

            restored = sqlite3.connect(":memory:")
            restored.deserialize(payload)
            self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(restored.execute("SELECT value FROM sample").fetchone()[0], "staging-only")
            restored.close()

    def test_missing_or_empty_database_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sqlite3"
            with self.assertRaises(BackupError):
                create_sqlite_backup(missing)
            empty = Path(directory) / "empty.sqlite3"
            empty.touch()
            with self.assertRaises(BackupError):
                create_sqlite_backup(empty)

    def test_size_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite3"
            connection = sqlite3.connect(source)
            connection.execute("CREATE TABLE sample (value TEXT)")
            connection.commit()
            connection.close()
            with self.assertRaises(BackupError):
                create_sqlite_backup(source, max_bytes=1)


if __name__ == "__main__":
    unittest.main()
