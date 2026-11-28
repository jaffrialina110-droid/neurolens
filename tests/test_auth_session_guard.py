import unittest

from modules.auth_session_guard import (
    ActiveAuthSession,
    AuthSessionError,
    resolve_active_auth_session,
    session_generation_matches,
)


class AuthSessionGuardTests(unittest.TestCase):
    def setUp(self):
        self.user = {"id": "legacy-42", "username": "sample"}
        self.session_id = "server-generated-session-reference"
        self.generation = 7
        self.active = True
        self.calls = []

    def resolve(self):
        return resolve_active_auth_session(
            current_user_fn=lambda: self.user,
            auth_session_id_fn=lambda: self.session_id,
            account_is_active_fn=lambda user_id: self.calls.append(
                ("active", user_id)
            ) or self.active,
            session_generation_fn=lambda user_id: self.calls.append(
                ("generation", user_id)
            ) or self.generation,
        )

    def test_returns_immutable_verified_session_context(self):
        result = self.resolve()
        self.assertEqual(
            result,
            ActiveAuthSession("legacy-42", self.session_id, 7),
        )
        self.assertEqual(
            self.calls,
            [("active", "legacy-42"), ("generation", "legacy-42")],
        )

    def test_rechecks_account_status_on_each_resolution(self):
        self.resolve()
        self.active = False
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_inactive_or_unverifiable_account_fails_closed(self):
        self.active = None
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_missing_user_fails_closed(self):
        self.user = None
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_custom_user_dict_subclass_fails_closed_before_field_access(self):
        class HostileUserDict(dict):
            def get(self, key, default=None):
                raise RuntimeError("custom mapping behavior")

        self.user = HostileUserDict(id="legacy-42")
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_rejects_custom_string_subclass_session_reference(self):
        class HostileString(str):
            def isprintable(self):
                raise RuntimeError("hostile session string")

        self.session_id = HostileString("server-session")
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_rejects_integer_subclasses_for_generation(self):
        class HostileInteger(int):
            def __lt__(self, other):
                raise RuntimeError("hostile generation comparison")

        self.generation = HostileInteger(7)
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_rejects_integer_subclass_user_id(self):
        class HostileInteger(int):
            def __str__(self):
                raise RuntimeError("hostile user id conversion")

        self.user = {"id": HostileInteger(42)}
        with self.assertRaises(AuthSessionError):
            self.resolve()

    def test_missing_or_invalid_session_reference_fails_closed(self):
        for value in (None, "", "   ", "bad\nreference", 123, "x" * 257):
            with self.subTest(value=value):
                self.session_id = value
                with self.assertRaises(AuthSessionError):
                    self.resolve()

    def test_generation_change_is_reflected_for_session_binding(self):
        first = self.resolve()
        self.generation += 1
        second = self.resolve()
        self.assertNotEqual(first.session_generation, second.session_generation)
        self.assertEqual(second.session_generation, 8)

    def test_invalid_generation_fails_closed(self):
        for value in (None, -1, True, "7"):
            with self.subTest(value=value):
                self.generation = value
                with self.assertRaises(AuthSessionError):
                    self.resolve()

    def test_invalid_user_ids_fail_closed(self):
        for value in (None, True, "", "   ", "x" * 129, [], {}):
            with self.subTest(value=value):
                self.user = {"id": value}
                with self.assertRaises(AuthSessionError):
                    self.resolve()

    def test_verified_context_is_immutable(self):
        from dataclasses import FrozenInstanceError

        result = self.resolve()
        with self.assertRaises(FrozenInstanceError):
            result.legacy_user_id = "different-user"

    def test_trusted_callback_errors_fail_closed_without_exposing_details(self):
        callbacks = (
            {"current_user_fn": lambda: (_ for _ in ()).throw(OSError("secret db path"))},
            {"auth_session_id_fn": lambda: (_ for _ in ()).throw(OSError("secret session"))},
            {"account_is_active_fn": lambda user_id: (_ for _ in ()).throw(OSError("secret account"))},
            {"session_generation_fn": lambda user_id: (_ for _ in ()).throw(OSError("secret generation"))},
        )
        for override in callbacks:
            with self.subTest(override=tuple(override)):
                args = {
                    "current_user_fn": lambda: self.user,
                    "auth_session_id_fn": lambda: self.session_id,
                    "account_is_active_fn": lambda user_id: True,
                    "session_generation_fn": lambda user_id: self.generation,
                }
                args.update(override)
                with self.assertRaises(AuthSessionError) as raised:
                    resolve_active_auth_session(**args)
                self.assertNotIn("secret", str(raised.exception))

    def test_missing_trusted_callback_fails_closed(self):
        with self.assertRaises(AuthSessionError):
            resolve_active_auth_session(
                current_user_fn=lambda: self.user,
                auth_session_id_fn=lambda: self.session_id,
                account_is_active_fn=lambda user_id: True,
                session_generation_fn=None,
            )

    def test_login_generation_must_match_current_server_generation(self):
        self.assertTrue(session_generation_matches(7, 7))
        self.assertFalse(session_generation_matches(7, 8))

    def test_invalid_generation_values_never_match(self):
        for value in (None, True, -1, "7", 7.0):
            with self.subTest(value=value):
                self.assertFalse(session_generation_matches(value, 7))
                self.assertFalse(session_generation_matches(7, value))


if __name__ == "__main__":
    unittest.main()
