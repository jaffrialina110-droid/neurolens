import unittest

from modules.account_adapter import (
    AccountContextError,
    from_legacy_session_user,
)


class LegacyAccountAdapterTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "id": "a1b2c3legacy",
            "username": "ayna_user",
            "email": "ayna@example.test",
            "display_name": "Ayna",
            "role": "user",
        }

    def test_preserves_legacy_id_without_integer_coercion(self):
        context = from_legacy_session_user(self.user)
        self.assertEqual(context["legacy_user_id"], "a1b2c3legacy")
        self.assertIsInstance(context["legacy_user_id"], str)
        self.assertEqual(context["identity_source"], "legacy_app")

    def test_returns_only_minimal_account_context(self):
        context = from_legacy_session_user(self.user)
        self.assertEqual(
            set(context),
            {
                "legacy_user_id",
                "username",
                "email",
                "display_name",
                "role",
                "identity_source",
            },
        )

    def test_rejects_missing_user(self):
        with self.assertRaises(AccountContextError):
            from_legacy_session_user(None)

    def test_rejects_missing_legacy_id(self):
        user = dict(self.user)
        user.pop("id")
        with self.assertRaises(AccountContextError):
            from_legacy_session_user(user)

    def test_rejects_missing_required_profile_field(self):
        user = dict(self.user)
        user["role"] = ""
        with self.assertRaises(AccountContextError):
            from_legacy_session_user(user)

    def test_rejects_whitespace_only_legacy_id(self):
        user = dict(self.user)
        user["id"] = "   "
        with self.assertRaises(AccountContextError):
            from_legacy_session_user(user)

    def test_rejects_non_string_profile_values(self):
        user = dict(self.user)
        user["email"] = 123
        with self.assertRaises(AccountContextError):
            from_legacy_session_user(user)

    def test_trims_profile_fields_but_preserves_legacy_id_exactly(self):
        user = dict(self.user)
        user["id"] = " legacy-id "
        user["username"] = "  ayna_user  "
        context = from_legacy_session_user(user)
        self.assertEqual(context["legacy_user_id"], " legacy-id ")
        self.assertEqual(context["username"], "ayna_user")

    def test_does_not_return_password_or_secret_fields(self):
        user = dict(self.user)
        user.update({
            "password": "never-return-this",
            "password_hash": "hash",
            "password_salt": "salt",
            "access_token": "token",
        })
        context = from_legacy_session_user(user)
        self.assertNotIn("password", context)
        self.assertNotIn("password_hash", context)
        self.assertNotIn("password_salt", context)
        self.assertNotIn("access_token", context)


if __name__ == "__main__":
    unittest.main()
