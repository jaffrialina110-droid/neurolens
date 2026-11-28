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


    def test_owner_scoped_reads_cover_profile_comments_reactions_appointments_and_notes(self):
        first_user = self.create_user("owner_first")
        second_user = self.create_user("owner_second")
        with storage.get_connection() as conn:
            conn.execute("UPDATE user_profiles SET bio = ? WHERE user_id = ?",
                         ("first bio", first_user))
            conn.execute("UPDATE user_profiles SET bio = ? WHERE user_id = ?",
                         ("second bio", second_user))
            first_post = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (first_user, "first post"),
            ).lastrowid
            second_post = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)",
                (second_user, "second post"),
            ).lastrowid
            conn.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                         (first_post, first_user, "first comment"))
            conn.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                         (second_post, second_user, "second comment"))
            conn.execute("INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                         (first_post, first_user, "🧠"))
            conn.execute("INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                         (second_post, second_user, "❤️"))
            conn.execute("""INSERT INTO appointments
                         (user_id, appointment_type, preferred_date, preferred_time, purpose)
                         VALUES (?, ?, ?, ?, ?)""",
                         (first_user, "consultation", "2026-12-01", "10:00", "first purpose"))
            conn.execute("""INSERT INTO appointments
                         (user_id, appointment_type, preferred_date, preferred_time, purpose)
                         VALUES (?, ?, ?, ?, ?)""",
                         (second_user, "consultation", "2026-12-02", "11:00", "second purpose"))
            conn.execute("INSERT INTO research_notes (user_id, title, content) VALUES (?, ?, ?)",
                         (first_user, "first note", "first content"))
            conn.execute("INSERT INTO research_notes (user_id, title, content) VALUES (?, ?, ?)",
                         (second_user, "second note", "second content"))

        self.assertEqual(storage.get_profile_for_user(first_user)["bio"], "first bio")
        self.assertEqual(storage.get_profile_for_user(second_user)["bio"], "second bio")
        self.assertEqual([r["content"] for r in storage.get_comments_for_user(first_user)],
                         ["first comment"])
        self.assertEqual([r["content"] for r in storage.get_comments_for_user(second_user)],
                         ["second comment"])
        self.assertEqual([r["emoji"] for r in storage.get_reactions_for_user(first_user)],
                         ["🧠"])
        self.assertEqual([r["emoji"] for r in storage.get_reactions_for_user(second_user)],
                         ["❤️"])
        self.assertEqual([r["purpose"] for r in storage.get_appointments_for_user(first_user)],
                         ["first purpose"])
        self.assertEqual([r["purpose"] for r in storage.get_appointments_for_user(second_user)],
                         ["second purpose"])
        self.assertEqual([r["title"] for r in storage.get_research_notes_for_user(first_user)],
                         ["first note"])
        self.assertEqual([r["title"] for r in storage.get_research_notes_for_user(second_user)],
                         ["second note"])

    def test_all_owner_scoped_read_helpers_reject_invalid_ids(self):
        helpers = (
            storage.get_posts_for_user, storage.get_activity_for_user,
            storage.get_profile_for_user, storage.get_comments_for_user,
            storage.get_reactions_for_user, storage.get_appointments_for_user,
            storage.get_research_notes_for_user,
        )
        for helper in helpers:
            for invalid_id in (0, -1, True, "1", None):
                with self.subTest(helper=helper.__name__, user_id=invalid_id):
                    with self.assertRaises(ValueError):
                        helper(invalid_id)



    def test_cross_user_updates_and_deletes_are_rejected(self):
        owner = self.create_user("mutation_owner")
        other = self.create_user("mutation_other")
        with storage.get_connection() as conn:
            owner_post = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)", (owner, "owner post")
            ).lastrowid
            other_post = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)", (other, "other post")
            ).lastrowid
            owner_comment = conn.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                (owner_post, owner, "owner comment"),
            ).lastrowid
            other_comment = conn.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                (other_post, other, "other comment"),
            ).lastrowid
            owner_reaction = conn.execute(
                "INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                (owner_post, owner, "🧠"),
            ).lastrowid
            other_reaction = conn.execute(
                "INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                (other_post, other, "❤️"),
            ).lastrowid
            owner_appointment = conn.execute(
                """INSERT INTO appointments
                   (user_id, appointment_type, preferred_date, preferred_time, purpose)
                   VALUES (?, ?, ?, ?, ?)""",
                (owner, "consultation", "2026-12-10", "10:00", "owner purpose"),
            ).lastrowid
            other_appointment = conn.execute(
                """INSERT INTO appointments
                   (user_id, appointment_type, preferred_date, preferred_time, purpose)
                   VALUES (?, ?, ?, ?, ?)""",
                (other, "consultation", "2026-12-11", "11:00", "other purpose"),
            ).lastrowid
            owner_note = conn.execute(
                "INSERT INTO research_notes (user_id, title, content) VALUES (?, ?, ?)",
                (owner, "owner note", "owner text"),
            ).lastrowid
            other_note = conn.execute(
                "INSERT INTO research_notes (user_id, title, content) VALUES (?, ?, ?)",
                (other, "other note", "other text"),
            ).lastrowid

        self.assertFalse(storage.update_post_for_user(owner, other_post, "hacked"))
        self.assertFalse(storage.delete_post_for_user(owner, other_post))
        self.assertFalse(storage.update_comment_for_user(owner, other_comment, "hacked"))
        self.assertFalse(storage.delete_comment_for_user(owner, other_comment))
        self.assertFalse(storage.update_reaction_for_user(owner, other_reaction, "🔥"))
        self.assertFalse(storage.delete_reaction_for_user(owner, other_reaction))
        self.assertFalse(storage.update_appointment_for_user(
            owner, other_appointment, "changed", "2026-12-20", "12:00", "hacked"
        ))
        self.assertFalse(storage.delete_appointment_for_user(owner, other_appointment))
        self.assertFalse(storage.update_research_note_for_user(
            owner, other_note, "hacked", "hacked"
        ))
        self.assertFalse(storage.delete_research_note_for_user(owner, other_note))

        with storage.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT content FROM posts WHERE id = ?",
                                          (other_post,)).fetchone()["content"], "other post")
            self.assertEqual(conn.execute("SELECT content FROM comments WHERE id = ?",
                                          (other_comment,)).fetchone()["content"], "other comment")
            self.assertEqual(conn.execute("SELECT emoji FROM reactions WHERE id = ?",
                                          (other_reaction,)).fetchone()["emoji"], "❤️")
            self.assertEqual(conn.execute("SELECT purpose FROM appointments WHERE id = ?",
                                          (other_appointment,)).fetchone()["purpose"], "other purpose")
            self.assertEqual(conn.execute("SELECT title FROM research_notes WHERE id = ?",
                                          (other_note,)).fetchone()["title"], "other note")

    def test_owner_can_update_and_delete_own_records(self):
        user = self.create_user("own_mutations")
        with storage.get_connection() as conn:
            post = conn.execute(
                "INSERT INTO posts (user_id, content) VALUES (?, ?)", (user, "old post")
            ).lastrowid
            comment = conn.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                (post, user, "old comment"),
            ).lastrowid
            reaction = conn.execute(
                "INSERT INTO reactions (post_id, user_id, emoji) VALUES (?, ?, ?)",
                (post, user, "🧠"),
            ).lastrowid
            appointment = conn.execute(
                """INSERT INTO appointments
                   (user_id, appointment_type, preferred_date, preferred_time, purpose)
                   VALUES (?, ?, ?, ?, ?)""",
                (user, "consultation", "2026-12-12", "09:00", "old purpose"),
            ).lastrowid
            note = conn.execute(
                "INSERT INTO research_notes (user_id, title, content) VALUES (?, ?, ?)",
                (user, "old title", "old content"),
            ).lastrowid

        self.assertTrue(storage.update_profile_for_user(user, "new bio", False))
        self.assertTrue(storage.update_post_for_user(user, post, "new post"))
        self.assertTrue(storage.update_comment_for_user(user, comment, "new comment"))
        self.assertTrue(storage.update_reaction_for_user(user, reaction, "🔥"))
        self.assertTrue(storage.update_appointment_for_user(
            user, appointment, "follow-up", "2026-12-13", "10:30", "new purpose"
        ))
        self.assertTrue(storage.update_research_note_for_user(user, note, "new title", "new content"))
        self.assertTrue(storage.delete_comment_for_user(user, comment))
        self.assertTrue(storage.delete_reaction_for_user(user, reaction))
        self.assertTrue(storage.delete_appointment_for_user(user, appointment))
        self.assertTrue(storage.delete_research_note_for_user(user, note))
        self.assertTrue(storage.delete_post_for_user(user, post))
        self.assertEqual(storage.get_profile_for_user(user)["bio"], "new bio")

    def test_mutation_helpers_reject_invalid_ids_and_fields(self):
        user = self.create_user("invalid_mutations")
        for invalid in (0, -1, True, "1", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    storage.update_post_for_user(user, invalid, "text")
                with self.assertRaises(ValueError):
                    storage.delete_post_for_user(user, invalid)
        with self.assertRaises(ValueError):
            storage.update_post_for_user(user, 1, "  ")
        with self.assertRaises(ValueError):
            storage.update_profile_for_user(user, "bio", 1)



if __name__ == "__main__":
    unittest.main()
