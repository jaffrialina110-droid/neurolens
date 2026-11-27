import sqlite3
import tempfile
import unittest
from pathlib import Path

from modules.db_backup import BackupError, backup_sha256, create_sqlite_backup


class DatabaseBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "neurolens.db"
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT)")
        connection.execute("INSERT INTO users VALUES ('u1', 'sample')")
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_backup_is_valid_and_contains_source_rows(self):
        payload = create_sqlite_backup(self.path)
        restored = sqlite3.connect(":memory:")
        restored.deserialize(payload)
        rows = restored.execute("SELECT id, username FROM users").fetchall()
        self.assertEqual(rows, [("u1", "sample")])
        self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        restored.close()

    def test_source_database_is_not_modified(self):
        before = self.path.read_bytes()
        create_sqlite_backup(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_database_is_rejected(self):
        with self.assertRaises(BackupError):
            create_sqlite_backup(self.path.parent / "missing.db")

    def test_empty_file_is_rejected(self):
        empty = self.path.parent / "empty.db"
        empty.touch()
        with self.assertRaises(BackupError):
            create_sqlite_backup(empty)

    def test_size_limit_is_enforced(self):
        with self.assertRaises(BackupError):
            create_sqlite_backup(self.path, max_bytes=10)

    def test_checksum_is_deterministic(self):
        payload = create_sqlite_backup(self.path)
        self.assertEqual(backup_sha256(payload), backup_sha256(payload))
        self.assertEqual(len(backup_sha256(payload)), 64)


if __name__ == "__main__":
    unittest.main()
