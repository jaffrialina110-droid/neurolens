import unittest

from modules.authenticated_context import (
    AuthenticatedLegacyContext,
    from_server_current_user,
)
from modules.account_adapter import AccountContextError


class ServerCurrentUserContextTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "id": "legacy-id-007",
            "username": "member",
            "email": "member@example.test",
            "display_name": "Member",
            "role": "user",
            "password_hash": "must-not-leak",
        }

    def test_invokes_server_accessor_once_and_returns_immutable_context(self):
        calls = []

        def current_user():
            calls.append("called")
            return self.user

        context = from_server_current_user(current_user)
        self.assertEqual(calls, ["called"])
        self.assertIsInstance(context, AuthenticatedLegacyContext)
        self.assertEqual(context.legacy_user_id, "legacy-id-007")
        self.assertEqual(context.identity_source, "legacy_app")
        self.assertFalse(hasattr(context, "password_hash"))
        with self.assertRaises((AttributeError, TypeError)):
            context.legacy_user_id = "changed"

    def test_rejects_non_callable_instead_of_accepting_client_user_data(self):
        with self.assertRaises(AccountContextError):
            from_server_current_user(self.user)

    def test_rejects_missing_authenticated_session(self):
        with self.assertRaises(AccountContextError):
            from_server_current_user(lambda: None)

    def test_trusted_accessor_errors_fail_closed_without_leaking_details(self):
        def fail():
            raise OSError("private database connection string")

        with self.assertRaises(AccountContextError) as raised:
            from_server_current_user(fail)
        self.assertNotIn("private database", str(raised.exception))

    def test_rejects_incomplete_session_user(self):
        with self.assertRaises(AccountContextError):
            from_server_current_user(lambda: {"id": "legacy-only"})

    def test_does_not_coerce_legacy_id_to_phase1_integer(self):
        context = from_server_current_user(lambda: self.user)
        self.assertEqual(context.legacy_user_id, "legacy-id-007")
        self.assertIsInstance(context.legacy_user_id, str)


if __name__ == "__main__":
    unittest.main()
