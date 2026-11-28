import os
import sqlite3
import tempfile
import threading
import unittest

from modules.private_lock import PrivateLockError, hash_pin
from modules.private_lock_store import (
    PrivateLockStoreError,
    SqlitePrivateLockAttemptStore,
)


class SqlitePrivateLockAttemptStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "private-lock-test.sqlite3")

        def connect():
            return sqlite3.connect(self.db_path, timeout=10)

        self.store = SqlitePrivateLockAttemptStore(connect)
        self.store.initialize_schema()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_requires_trusted_connection_factory(self):
        with self.assertRaises(PrivateLockStoreError):
            SqlitePrivateLockAttemptStore(None)

    def test_schema_is_not_created_until_explicit_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "lazy.sqlite3")
            store = SqlitePrivateLockAttemptStore(lambda: sqlite3.connect(path))
            self.assertFalse(os.path.exists(path))
            store.initialize_schema()
            self.assertTrue(os.path.exists(path))

    def test_new_user_has_fresh_state(self):
        self.assertEqual(
            self.store.get_state(12),
            {"failed_attempts": 0, "locked_until": 0.0},
        )

    def test_failed_attempts_persist_across_connections(self):
        state = self.store.record_attempt(12, success=False, now=100)
        self.assertEqual(state, {"failed_attempts": 1, "locked_until": 0.0})
        self.assertEqual(self.store.get_state(12), state)

    def test_record_attempt_rejects_lockout_deadline_overflow_without_writing(self):
        with self.assertRaises(PrivateLockError):
            self.store.record_attempt(
                12, success=False, now=1e308, max_attempts=1,
                lockout_seconds=10**308,
            )
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 0)

    def test_atomic_verification_rejects_lockout_deadline_overflow_without_writing(self):
        encoded = hash_pin("123456")
        with self.assertRaises(PrivateLockError):
            self.store.verify_and_record_attempt(
                12, "000000", encoded, now=1e308, max_attempts=1,
                lockout_seconds=10**308,
            )
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 0)

    def test_lockout_is_persisted_and_enforced(self):
        state = {"failed_attempts": 0, "locked_until": 0.0}
        for now in (100, 101, 102, 103):
            state = self.store.record_attempt(
                12, success=False, now=now, max_attempts=5, lockout_seconds=60
            )
        state = self.store.record_attempt(
            12, success=False, now=104, max_attempts=5, lockout_seconds=60
        )
        self.assertEqual(state, {"failed_attempts": 5, "locked_until": 164.0})
        self.assertEqual(self.store.get_state(12), state)
        self.assertEqual(
            self.store.record_attempt(12, success=False, now=120),
            state,
        )

    def test_success_resets_persisted_counter(self):
        self.store.record_attempt(12, success=False, now=100)
        self.assertEqual(
            self.store.record_attempt(12, success=True, now=101),
            {"failed_attempts": 0, "locked_until": 0.0},
        )

    def test_users_have_separate_attempt_states(self):
        self.store.record_attempt(12, success=False, now=100)
        self.store.record_attempt(13, success=False, now=100)
        self.store.record_attempt(13, success=False, now=101)
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 1)
        self.assertEqual(self.store.get_state(13)["failed_attempts"], 2)

    def test_invalid_user_ids_and_attempt_arguments_are_rejected(self):
        for user_id in (0, -1, True, "12", 12.0):
            with self.subTest(user_id=user_id):
                with self.assertRaises(PrivateLockError):
                    self.store.get_state(user_id)
        with self.assertRaises(PrivateLockError):
            self.store.record_attempt(12, success=1, now=100)

    def test_parallel_failures_are_not_lost(self):
        errors = []
        barrier = threading.Barrier(8)

        def fail_once():
            try:
                barrier.wait()
                self.store.record_attempt(44, success=False, max_attempts=100, now=500)
            except Exception as exc:  # surfaced in the parent test
                errors.append(exc)

        threads = [threading.Thread(target=fail_once) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(self.store.get_state(44)["failed_attempts"], 8)

    def test_corrupt_persisted_attempt_state_fails_closed(self):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("PRAGMA ignore_check_constraints = ON")
            connection.execute(
                "INSERT INTO private_lock_attempts "
                "(user_id, failed_attempts, locked_until) VALUES (77, -1, 0)"
            )
            connection.execute(
                "INSERT INTO private_lock_attempts "
                "(user_id, failed_attempts, locked_until) VALUES (78, 1, ?)",
                (float("inf"),),
            )
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(PrivateLockStoreError):
            self.store.get_state(77)
        with self.assertRaises(PrivateLockStoreError):
            self.store.get_state(78)
        with self.assertRaises(PrivateLockStoreError):
            self.store.verify_and_record_attempt(78, "123456", "invalid", now=100)
        with self.assertRaises(PrivateLockStoreError):
            self.store.verify_and_record_attempt(77, "123456", "invalid", now=100)

    def test_no_raw_pin_or_secret_fields_are_stored(self):
        self.store.record_attempt(12, success=False, now=100)
        connection = sqlite3.connect(self.db_path)
        try:
            columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(private_lock_attempts)"
                )
            }
        finally:
            connection.close()
        self.assertEqual(
            columns, {"user_id", "failed_attempts", "locked_until"}
        )


    def test_atomic_verification_rejects_wrong_pin_and_persists_failure(self):
        encoded = hash_pin("123456")
        result = self.store.verify_and_record_attempt(
            12, "000000", encoded, now=100
        )
        self.assertFalse(result["verified"])
        self.assertFalse(result["locked"])
        self.assertEqual(result["failed_attempts"], 1)
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 1)

    def test_atomic_verification_success_resets_failure_counter(self):
        encoded = hash_pin("123456")
        self.store.record_attempt(12, success=False, now=100)
        result = self.store.verify_and_record_attempt(
            12, "123456", encoded, now=101
        )
        self.assertTrue(result["verified"])
        self.assertFalse(result["locked"])
        self.assertEqual(result["failed_attempts"], 0)
        self.assertEqual(result["locked_until"], 0.0)

    def test_active_lockout_blocks_even_a_correct_pin(self):
        encoded = hash_pin("123456")
        for now in range(100, 105):
            self.store.verify_and_record_attempt(
                12, "000000", encoded, now=now,
                max_attempts=5, lockout_seconds=60,
            )
        result = self.store.verify_and_record_attempt(
            12, "123456", encoded, now=120,
            max_attempts=5, lockout_seconds=60,
        )
        self.assertFalse(result["verified"])
        self.assertTrue(result["locked"])
        self.assertEqual(result["failed_attempts"], 5)
        self.assertEqual(result["locked_until"], 164.0)

    def test_correct_pin_is_allowed_exactly_at_lockout_deadline(self):
        encoded = hash_pin("123456")
        for now in range(100, 105):
            self.store.verify_and_record_attempt(
                12, "000000", encoded, now=now,
                max_attempts=5, lockout_seconds=60,
            )
        result = self.store.verify_and_record_attempt(
            12, "123456", encoded, now=164,
            max_attempts=5, lockout_seconds=60,
        )
        self.assertTrue(result["verified"])
        self.assertFalse(result["locked"])
        self.assertEqual(result["failed_attempts"], 0)
        self.assertEqual(result["locked_until"], 0.0)

    def test_atomic_verification_rejects_malformed_hash(self):
        result = self.store.verify_and_record_attempt(
            12, "123456", "not-a-valid-hash", now=100
        )
        self.assertFalse(result["verified"])
        self.assertEqual(result["failed_attempts"], 1)

    def test_parallel_wrong_pin_verifications_are_serialized(self):
        encoded = hash_pin("123456")
        errors = []
        barrier = threading.Barrier(6)

        def fail_once():
            try:
                barrier.wait()
                self.store.verify_and_record_attempt(
                    55, "000000", encoded, max_attempts=20, now=500
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=fail_once) for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(self.store.get_state(55)["failed_attempts"], 6)


    def test_atomic_verification_rejects_invalid_lockout_parameters(self):
        encoded = hash_pin("123456")
        for kwargs in (
            {"max_attempts": 0},
            {"max_attempts": True},
            {"lockout_seconds": 0},
            {"lockout_seconds": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(PrivateLockError):
                    self.store.verify_and_record_attempt(
                        12, "000000", encoded, now=100, **kwargs
                    )
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 0)

    def test_connection_factory_must_return_sqlite_connection(self):
        store = SqlitePrivateLockAttemptStore(lambda: object())
        with self.assertRaises(PrivateLockStoreError):
            store.get_state(12)

    def test_record_attempt_rejects_invalid_lockout_parameters_without_writing(self):
        for kwargs in (
            {"max_attempts": 0},
            {"max_attempts": True},
            {"lockout_seconds": 0},
            {"lockout_seconds": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(PrivateLockError):
                    self.store.record_attempt(
                        12, success=False, now=100, **kwargs
                    )
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 0)

    def test_atomic_verification_rejects_invalid_user_ids_before_storage_access(self):
        encoded = hash_pin("123456")
        for user_id in (0, -1, True, "12", 12.0):
            with self.subTest(user_id=user_id):
                with self.assertRaises(PrivateLockError):
                    self.store.verify_and_record_attempt(
                        user_id, "000000", encoded, now=100
                    )
        self.assertEqual(self.store.get_state(12)["failed_attempts"], 0)

if __name__ == "__main__":
    unittest.main()
