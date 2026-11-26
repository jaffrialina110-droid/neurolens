"""Regression tests for the real AI conversation helper functions in app.py.

The helpers are extracted with AST so tests do not import/run the Streamlit app.
"""
import ast
import datetime
import pathlib
import secrets
import sqlite3
import unittest

from modules.ai_chat_crypto import (
    AIChatCryptoError, decrypt_ai_message, encrypt_ai_message
)

TEST_SECRET = "ownership-test-master-secret-at-least-32-bytes"


APP_PATH = pathlib.Path(__file__).resolve().parents[1] / "app.py"
HELPER_NAMES = {
    "ayna_conversation_belongs_to_user",
    "ayna_save_message",
    "ayna_load_messages",
    "ayna_create_conversation",
}


class AIConversationOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE ai_conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE ai_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                content_version INTEGER NOT NULL DEFAULT 0,
                encryption_nonce TEXT
            );
            """
        )

        def db_execute(query, values=()):
            try:
                self.connection.execute(query, values)
                self.connection.commit()
                return True
            except sqlite3.Error:
                return False

        def db_fetch_one(query, values=()):
            row = self.connection.execute(query, values).fetchone()
            return dict(row) if row else None

        def db_fetch_all(query, values=()):
            return [
                dict(row)
                for row in self.connection.execute(query, values).fetchall()
            ]

        source = APP_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        selected = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in HELPER_NAMES
        ]
        found = {node.name for node in selected}
        self.assertEqual(found, HELPER_NAMES)

        namespace = {
            "db_execute": db_execute,
            "db_fetch_one": db_fetch_one,
            "db_fetch_all": db_fetch_all,
            "datetime": datetime.datetime,
            "secrets": secrets,
            "get_secret": lambda key: TEST_SECRET,
            "encrypt_ai_message": encrypt_ai_message,
            "decrypt_ai_message": decrypt_ai_message,
            "AIChatCryptoError": AIChatCryptoError,
        }
        module = ast.Module(body=selected, type_ignores=[])
        exec(compile(module, str(APP_PATH), "exec"), namespace)
        self.helpers = namespace

    def tearDown(self):
        self.connection.close()

    def test_create_conversation_fills_required_schema_fields(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "A private topic"
        )
        row = self.connection.execute(
            "SELECT * FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()

        self.assertTrue(conversation_id)
        self.assertEqual(row["user_id"], "user-a")
        self.assertTrue(row["created_at"])
        self.assertTrue(row["updated_at"])

    def test_user_cannot_load_another_users_conversation(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "A private topic"
        )
        self.helpers["ayna_save_message"](
            conversation_id, "user-a", "user", "private text"
        )

        self.assertEqual(
            self.helpers["ayna_load_messages"](conversation_id, "user-b"),
            [],
        )
        self.assertFalse(
            self.helpers["ayna_conversation_belongs_to_user"](
                conversation_id, "user-b"
            )
        )

    def test_user_cannot_write_to_another_users_conversation(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "A private topic"
        )

        saved = self.helpers["ayna_save_message"](
            conversation_id, "user-b", "user", "unauthorized text"
        )

        self.assertFalse(saved)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM ai_messages"
            ).fetchone()[0],
            0,
        )

    def test_owner_can_save_and_load_own_messages(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "A private topic"
        )
        saved = self.helpers["ayna_save_message"](
            conversation_id, "user-a", "user", "my own text"
        )

        messages = self.helpers["ayna_load_messages"](
            conversation_id, "user-a"
        )

        self.assertTrue(saved)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "my own text")

    def test_database_stores_ciphertext_not_plaintext(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "A private topic"
        )
        self.helpers["ayna_save_message"](
            conversation_id, "user-a", "user", "sensitive words"
        )
        row = self.connection.execute(
            "SELECT content, content_version, encryption_nonce "
            "FROM ai_messages"
        ).fetchone()

        self.assertEqual(row["content_version"], 1)
        self.assertTrue(row["encryption_nonce"])
        self.assertNotIn("sensitive words", row["content"])

    def test_conversation_title_does_not_copy_private_prompt(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "Highly private first question"
        )
        row = self.connection.execute(
            "SELECT title FROM ai_conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        self.assertEqual(row["title"], "Ask Ayna conversation")
        self.assertNotIn("Highly private", row["title"])

    def test_missing_key_prevents_persistent_plaintext_write(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "Private topic"
        )
        self.helpers["get_secret"] = lambda key: ""
        saved = self.helpers["ayna_save_message"](
            conversation_id, "user-a", "user", "must not be stored"
        )
        self.assertFalse(saved)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM ai_messages"
            ).fetchone()[0],
            0,
        )

    def test_legacy_plaintext_rows_remain_readable(self):
        conversation_id = self.helpers["ayna_create_conversation"](
            "user-a", "Legacy topic"
        )
        self.connection.execute(
            "INSERT INTO ai_messages "
            "(id, conversation_id, user_id, role, content, created_at, "
            "content_version, encryption_nonce) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, NULL)",
            ("legacy-1", conversation_id, "user-a", "user",
             "old plaintext", "2026-01-01T00:00:00"),
        )
        self.connection.commit()

        messages = self.helpers["ayna_load_messages"](
            conversation_id, "user-a"
        )
        self.assertEqual(messages[0]["content"], "old plaintext")


if __name__ == "__main__":
    unittest.main()
