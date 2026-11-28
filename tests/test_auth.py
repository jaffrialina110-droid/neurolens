import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import modules.storage as storage
from modules.auth import authenticate_user, hash_password, register_user, verify_password


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path_patch = patch.object(
            storage, "DB_PATH", str(Path(self.temp_dir.name) / "test.sqlite3")
        )
        self.db_path_patch.start()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_password_hash_uses_unique_salt(self):
        first = hash_password("correct horse battery staple")
        second = hash_password("correct horse battery staple")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("correct horse battery staple", first))
        self.assertFalse(verify_password("wrong password", first))

    def test_register_and_authenticate(self):
        ok, message = register_user(
            "ayna_test", "ayna@example.test", "Ayna Test",
            "safe-test-password-123"
        )
        self.assertTrue(ok, message)
        user = authenticate_user("ayna_test", "safe-test-password-123")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "ayna@example.test")

    def test_duplicate_account_is_rejected(self):
        register_user(
            "ayna_test", "ayna@example.test", "Ayna Test",
            "safe-test-password-123"
        )
        ok, _ = register_user(
            "ayna_test", "other@example.test", "Another",
            "another-safe-password-123"
        )
        self.assertFalse(ok)

    def test_weak_password_is_rejected(self):
        ok, _ = register_user(
            "short_user", "short@example.test", "Short", "tiny"
        )
        self.assertFalse(ok)

    def test_login_is_case_insensitive_for_username_and_email(self):
        ok, message = register_user(
            "Ayna_Test", "Ayna@Example.Test", "Ayna Test",
            "safe-test-password-123"
        )
        self.assertTrue(ok, message)
        by_username = authenticate_user("AYNA_TEST", "safe-test-password-123")
        by_email = authenticate_user("AYNA@EXAMPLE.TEST", "safe-test-password-123")
        self.assertIsNotNone(by_username)
        self.assertIsNotNone(by_email)
        self.assertEqual(by_username["id"], by_email["id"])

    def test_corrupted_password_hash_fails_closed(self):
        from modules.storage import get_connection, init_db

        ok, message = register_user(
            "corrupt_user", "corrupt@example.test", "Corrupt User",
            "safe-test-password-123"
        )
        self.assertTrue(ok, message)
        init_db()
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                ("not-a-valid-hash", "corrupt_user"),
            )
        self.assertIsNone(
            authenticate_user("corrupt_user", "safe-test-password-123")
        )


if __name__ == "__main__":
    unittest.main()
