import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "database_migration_preflight.py"
SPEC = importlib.util.spec_from_file_location("database_migration_preflight", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DatabasePreflightTests(unittest.TestCase):
    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sqlite3"
            report = MODULE.inspect_database(missing)
            self.assertFalse(report["exists"])
            self.assertFalse(missing.exists())
            self.assertEqual(report["tables"], [])

    def test_existing_database_reports_schema_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sample.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)"
                )
                connection.execute(
                    "INSERT INTO users (username) VALUES (?)", ("sample-user",)
                )

            report = MODULE.inspect_database(database)
            self.assertTrue(report["exists"])
            self.assertEqual(report["integrity"], "ok")
            self.assertEqual(report["foreign_key_violations"], 0)
            users = next(table for table in report["tables"] if table["name"] == "users")
            self.assertEqual(users["row_count"], 1)
            self.assertEqual(
                [column["name"] for column in users["columns"]],
                ["id", "username"],
            )

    def test_comparison_does_not_claim_same_tables_are_compatible(self):
        reports = [
            {"path": "one.db", "tables": [
                {"name": "users", "row_count": 1, "columns": [{"name": "id"}]}
            ]},
            {"path": "two.db", "tables": [
                {"name": "users", "row_count": 2, "columns": [{"name": "user_id"}]}
            ]},
        ]
        comparison = MODULE.build_comparison(reports)
        self.assertEqual(len(comparison["shared_table_names"]["users"]), 2)
        self.assertIn("do not imply compatible schemas", comparison["note"])


if __name__ == "__main__":
    unittest.main()
