"""Regression tests for the real AI conversation helper functions in app.py.

The helpers are extracted with AST so tests do not import/run the Streamlit app.
"""
import ast
import datetime
import pathlib
import secrets
import sqlite3
import unittest


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
                created_at TEXT NOT NULL
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


if __name__ == "__main__":
    unittest.main()
