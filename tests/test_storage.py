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


    def test_user_scoped_reads_do_not_return_another_users_posts_or_activity(self):
        first_user = self.create_user("scope_first")
        second_user = self.create_user("scope_second")
        with storage.get_connection() as conn:
            conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (first_user, "first user's private-to-owner post"),
            )
            conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (second_user, "second user's post"),
            )
            conn.execute(
                """INSERT INTO activity_log (user_id, activity_type, points)
                   VALUES (?, ?, ?)""",
                (first_user, "first-only", 3),
            )
            conn.execute(
                """INSERT INTO activity_log (user_id, activity_type, points)
                   VALUES (?, ?, ?)""",
                (second_user, "second-only", 5),
            )

        first_posts = storage.get_posts_for_user(first_user)
        second_posts = storage.get_posts_for_user(second_user)
        first_activity = storage.get_activity_for_user(first_user)
        second_activity = storage.get_activity_for_user(second_user)

        self.assertEqual([row["content"] for row in first_posts],
                         ["first user's private-to-owner post"])
        self.assertEqual([row["content"] for row in second_posts],
                         ["second user's post"])
        self.assertEqual([row["activity_type"] for row in first_activity],
                         ["first-only"])
        self.assertEqual([row["activity_type"] for row in second_activity],
                         ["second-only"])

    def test_user_scoped_reads_reject_invalid_or_ambiguous_ids(self):
        for invalid_id in (0, -1, True, "1", None):
            with self.subTest(user_id=invalid_id):
                with self.assertRaises(ValueError):
                    storage.get_posts_for_user(invalid_id)
                with self.assertRaises(ValueError):
                    storage.get_activity_for_user(invalid_id)

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
