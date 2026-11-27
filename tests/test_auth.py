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


if __name__ == "__main__":
    unittest.main()
