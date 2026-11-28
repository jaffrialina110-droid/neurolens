import unittest

from modules.private_lock import (
    PrivateLockError,
    hash_pin,
    is_rate_limited,
    new_attempt_state,
    private_session_expired,
    record_pin_attempt,
    verify_pin,
)


class PrivateLockPrimitiveTests(unittest.TestCase):
    def test_hash_is_salted_and_verifies(self):
        first = hash_pin("739152", iterations=100_000)
        second = hash_pin("739152", iterations=100_000)
        self.assertNotEqual(first, second)
        self.assertTrue(verify_pin("739152", first))
        self.assertFalse(verify_pin("739153", first))
        self.assertNotIn("739152", first)

    def test_rejects_weak_or_non_numeric_pin(self):
        for invalid in ("1234", "12345", "1234567890123", "12ab56", "１２３４５６", None, 123456):
            with self.subTest(pin=invalid):
                with self.assertRaises(PrivateLockError):
                    hash_pin(invalid)

    def test_rejects_weak_salt_and_iterations(self):
        with self.assertRaises(PrivateLockError):
            hash_pin("123456", salt=b"short", iterations=100_000)
        with self.assertRaises(PrivateLockError):
            hash_pin("123456", iterations=99_999)

    def test_malformed_hash_fails_closed(self):
        for malformed in (None, "", "sha256$1$aa$bb", "pbkdf2_sha256$bad$aa$bb"):
            with self.subTest(value=malformed):
                self.assertFalse(verify_pin("123456", malformed))

    def test_attempt_counter_and_timed_lockout(self):
        state = new_attempt_state()
        for now in (100, 101, 102, 103):
            state = record_pin_attempt(
                state, success=False, now=now, max_attempts=5, lockout_seconds=60
            )
        self.assertFalse(is_rate_limited(state, now=103))
        state = record_pin_attempt(
            state, success=False, now=104, max_attempts=5, lockout_seconds=60
        )
        self.assertTrue(is_rate_limited(state, now=105))
        self.assertFalse(is_rate_limited(state, now=164))

    def test_success_resets_failed_attempts(self):
        state = {"failed_attempts": 3, "locked_until": 0.0}
        self.assertEqual(
            record_pin_attempt(state, success=True, now=200),
            {"failed_attempts": 0, "locked_until": 0.0},
        )

    def test_attempts_during_lockout_do_not_extend_deadline(self):
        state = {"failed_attempts": 5, "locked_until": 500.0}
        self.assertEqual(
            record_pin_attempt(state, success=False, now=400),
            state,
        )

    def test_invalid_attempt_state_fails_closed(self):
        for invalid in (None, {}, {"failed_attempts": True, "locked_until": 0.0},
                        {"failed_attempts": 1, "locked_until": -1}):
            with self.subTest(state=invalid):
                with self.assertRaises(PrivateLockError):
                    is_rate_limited(invalid, now=10)

    def test_private_session_inactivity_timeout(self):
        # The caller supplies last_activity_at, not the original unlock time.
        self.assertFalse(private_session_expired(200, now=1099, timeout_seconds=900))
        self.assertTrue(private_session_expired(200, now=1100, timeout_seconds=900))

    def test_non_finite_timestamps_are_rejected(self):
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(timestamp=invalid):
                with self.assertRaises(PrivateLockError):
                    private_session_expired(invalid, now=1000)
                with self.assertRaises(PrivateLockError):
                    is_rate_limited({"failed_attempts": 0, "locked_until": invalid}, now=1000)


if __name__ == "__main__":
    unittest.main()
