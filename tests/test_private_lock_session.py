import unittest

from modules.private_lock_session import (
    locked_private_session,
    unlock_private_session,
    validate_private_session,
)


class PrivateLockSessionTests(unittest.TestCase):
    def setUp(self):
        self.record = unlock_private_session(7, "auth-session-A", now=100)

    def test_unlock_record_is_bound_to_user_and_auth_session(self):
        self.assertEqual(
            self.record,
            {
                "unlocked": True,
                "user_id": 7,
                "auth_session_id": "auth-session-A",
                "last_activity_at": 100.0,
            },
        )

    def test_valid_activity_refreshes_last_activity(self):
        valid, refreshed = validate_private_session(
            self.record, user_id=7, auth_session_id="auth-session-A",
            now=200, timeout_seconds=900,
        )
        self.assertTrue(valid)
        self.assertEqual(refreshed["last_activity_at"], 200.0)

    def test_unknown_record_fields_are_not_carried_forward(self):
        record = dict(self.record, unexpected_private_field="must-not-propagate")
        valid, refreshed = validate_private_session(
            record, user_id=7, auth_session_id="auth-session-A", now=110,
        )
        self.assertTrue(valid)
        self.assertEqual(
            set(refreshed),
            {"unlocked", "user_id", "auth_session_id", "last_activity_at"},
        )

    def test_custom_dict_subclasses_fail_closed(self):
        class UntrustedRecord(dict):
            def get(self, key, default=None):
                raise RuntimeError("custom mapping execution")

        valid, locked = validate_private_session(
            UntrustedRecord(self.record), user_id=7,
            auth_session_id="auth-session-A", now=110,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_logout_or_missing_auth_session_fails_closed(self):
        valid, locked = validate_private_session(
            self.record, user_id=7, auth_session_id="", now=110,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_account_switch_invalidates_private_session(self):
        valid, locked = validate_private_session(
            self.record, user_id=8, auth_session_id="auth-session-B", now=110,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_auth_session_rotation_invalidates_private_session(self):
        valid, _ = validate_private_session(
            self.record, user_id=7, auth_session_id="auth-session-B", now=110,
        )
        self.assertFalse(valid)

    def test_inactivity_timeout_locks_session(self):
        valid, locked = validate_private_session(
            self.record, user_id=7, auth_session_id="auth-session-A",
            now=1000, timeout_seconds=900,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_clock_rollback_fails_closed(self):
        valid, _ = validate_private_session(
            self.record, user_id=7, auth_session_id="auth-session-A", now=99,
        )
        self.assertFalse(valid)

    def test_malformed_or_client_locked_records_fail_closed(self):
        for record in (None, {}, {"unlocked": False}, {"unlocked": True}):
            with self.subTest(record=record):
                valid, _ = validate_private_session(
                    record, user_id=7, auth_session_id="auth-session-A", now=110,
                )
                self.assertFalse(valid)

    def test_invalid_user_and_timeout_are_rejected(self):
        with self.assertRaises(ValueError):
            unlock_private_session(True, "auth-session-A", now=100)
        with self.assertRaises(ValueError):
            validate_private_session(
                self.record, user_id=7, auth_session_id="auth-session-A",
                now=100, timeout_seconds=0,
            )

    def test_malformed_auth_session_references_are_rejected(self):
        for value in (None, "", "   ", "bad\nreference", "x" * 257, 123):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    unlock_private_session(7, value, now=100)
                valid, locked = validate_private_session(
                    self.record, user_id=7, auth_session_id=value, now=110,
                )
                self.assertFalse(valid)
                self.assertEqual(locked, locked_private_session())

    def test_locked_state_does_not_retain_identity(self):
        self.assertEqual(
            locked_private_session(),
            {
                "unlocked": False,
                "user_id": None,
                "auth_session_id": None,
                "last_activity_at": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
