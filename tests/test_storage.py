import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import modules.storage as storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path_patch = patch.object(
            storage, "DB_PATH", str(Path(self.temp_dir.name) / "storage.sqlite3")
        )
        self.db_path_patch.start()
        storage.init_db()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def create_user(self, username):
        with storage.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users
                   (username, email, display_name, password_hash)
                   VALUES (?, ?, ?, ?)""",
                (username, f"{username}@example.test", username, "test-hash"),
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,)
            )
            return user_id

    def test_foreign_keys_reject_orphan_posts(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with storage.get_connection() as conn:
                conn.execute(
                    "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                    (999999, "orphan post"),
                )

    def test_deleting_user_cascades_profile_and_posts(self):
        user_id = self.create_user("cascade_user")
        with storage.get_connection() as conn:
            conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (user_id, "temporary post"),
            )

        with storage.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

        with storage.get_connection() as conn:
            self.assertIsNone(
                conn.execute(
                    "SELECT user_id FROM user_profiles WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            )
            self.assertEqual(
                conn.execute(
                    "SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)
                ).fetchone()[0],
                0,
            )

    def test_user_cannot_react_twice_to_same_post(self):
        user_id = self.create_user("reaction_user")
        with storage.get_connection() as conn:
            post_id = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (user_id, "hello"),
            ).lastrowid
            conn.execute(
                "INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                (post_id, user_id, "🧠"),
            )

        with self.assertRaises(sqlite3.IntegrityError):
            with storage.get_connection() as conn:
                conn.execute(
                    "INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                    (post_id, user_id, "❤️"),
                )


if __name__ == "__main__":
    unittest.main()
