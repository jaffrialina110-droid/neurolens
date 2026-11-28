"""Isolated end-to-end contract tests for account-to-Private-Lock flow.

These tests use fixture identities, in-memory callbacks, and a temporary SQLite
database. They do not import app.py, contact Supabase, or touch production data.
"""
import os
import sqlite3
import tempfile
import unittest

from modules.authenticated_context import from_server_current_user
from modules.identity_mapping import IdentityMappingError, resolve_phase1_user_id
from modules.private_lock import hash_pin
from modules.private_lock_session import (
    locked_private_session,
    unlock_private_session,
    validate_private_session,
)
from modules.private_lock_store import SqlitePrivateLockAttemptStore


class PrivateLockIntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.temp_dir.name, "staging-contract.sqlite3")

        def connect():
            return sqlite3.connect(db_path, timeout=10)

        self.store = SqlitePrivateLockAttemptStore(connect)
        self.store.initialize_schema()
        self.mapping = {"legacy-A": 101, "legacy-B": 202}
        self.pin_hashes = {
            101: hash_pin("135790"),
            202: hash_pin("246802"),
        }
        self.session_record = locked_private_session()

    def tearDown(self):
        self.temp_dir.cleanup()

    def current_user(self, legacy_id="legacy-A", *, role="user"):
        return {
            "id": legacy_id,
            "username": "fixture-user",
            "email": "fixture@example.test",
            "display_name": "Fixture User",
            "role": role,
        }

    def authenticate_and_resolve(self, legacy_id="legacy-A"):
        context = from_server_current_user(
            lambda: self.current_user(legacy_id)
        )
        phase1_id = resolve_phase1_user_id(
            context, lambda exact_legacy_id: self.mapping.get(exact_legacy_id)
        )
        return context, phase1_id

    def test_valid_account_mapping_pin_and_session_unlock(self):
        context, phase1_id = self.authenticate_and_resolve()
        result = self.store.verify_and_record_attempt(
            phase1_id, "135790", self.pin_hashes[phase1_id],
            max_attempts=5, lockout_seconds=300, now=100,
        )
        self.assertTrue(result["verified"])
        self.assertFalse(result["locked"])
        self.session_record = unlock_private_session(
            phase1_id, "server-auth-session-A", now=100
        )
        valid, refreshed = validate_private_session(
            self.session_record, user_id=phase1_id,
            auth_session_id="server-auth-session-A", now=110,
        )
        self.assertTrue(valid)
        self.assertEqual(refreshed["user_id"], 101)
        self.assertEqual(context.legacy_user_id, "legacy-A")

    def test_missing_mapping_fails_before_pin_hash_lookup(self):
        context = from_server_current_user(
            lambda: self.current_user("legacy-unmapped")
        )
        hash_lookups = []
        with self.assertRaises(IdentityMappingError):
            phase1_id = resolve_phase1_user_id(
                context,
                lambda legacy_id: self.mapping.get(legacy_id),
            )
            hash_lookups.append(phase1_id)
        self.assertEqual(hash_lookups, [])

    def test_wrong_pin_never_creates_unlocked_session(self):
        _, phase1_id = self.authenticate_and_resolve()
        result = self.store.verify_and_record_attempt(
            phase1_id, "000000", self.pin_hashes[phase1_id], now=100
        )
        self.assertFalse(result["verified"])
        self.assertEqual(self.session_record, locked_private_session())

    def test_lockout_blocks_correct_pin_until_deadline(self):
        _, phase1_id = self.authenticate_and_resolve()
        for timestamp in range(100, 105):
            result = self.store.verify_and_record_attempt(
                phase1_id, "000000", self.pin_hashes[phase1_id],
                max_attempts=5, lockout_seconds=60, now=timestamp,
            )
        self.assertTrue(result["locked"])
        blocked = self.store.verify_and_record_attempt(
            phase1_id, "135790", self.pin_hashes[phase1_id],
            max_attempts=5, lockout_seconds=60, now=120,
        )
        self.assertFalse(blocked["verified"])
        self.assertTrue(blocked["locked"])
        allowed = self.store.verify_and_record_attempt(
            phase1_id, "135790", self.pin_hashes[phase1_id],
            max_attempts=5, lockout_seconds=60, now=165,
        )
        self.assertTrue(allowed["verified"])

    def test_account_switch_invalidates_existing_private_session(self):
        _, first_id = self.authenticate_and_resolve("legacy-A")
        self.session_record = unlock_private_session(
            first_id, "server-auth-session-A", now=100
        )
        _, second_id = self.authenticate_and_resolve("legacy-B")
        valid, locked = validate_private_session(
            self.session_record, user_id=second_id,
            auth_session_id="server-auth-session-B", now=110,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_auth_session_rotation_invalidates_existing_private_session(self):
        _, phase1_id = self.authenticate_and_resolve()
        self.session_record = unlock_private_session(
            phase1_id, "server-auth-session-A", now=100
        )
        valid, locked = validate_private_session(
            self.session_record, user_id=phase1_id,
            auth_session_id="server-auth-session-B", now=110,
        )
        self.assertFalse(valid)
        self.assertEqual(locked, locked_private_session())

    def test_private_lock_attempts_are_isolated_by_mapped_account(self):
        _, first_id = self.authenticate_and_resolve("legacy-A")
        _, second_id = self.authenticate_and_resolve("legacy-B")
        self.store.verify_and_record_attempt(
            first_id, "000000", self.pin_hashes[first_id], now=100
        )
        self.assertEqual(self.store.get_state(first_id)["failed_attempts"], 1)
        self.assertEqual(self.store.get_state(second_id)["failed_attempts"], 0)

    def test_staff_role_has_no_implicit_pin_or_session_bypass(self):
        staff_context = from_server_current_user(
            lambda: self.current_user("legacy-A", role="staff")
        )
        staff_id = resolve_phase1_user_id(
            staff_context, lambda legacy_id: self.mapping.get(legacy_id)
        )
        self.assertEqual(staff_id, 101)
        self.assertEqual(self.session_record, locked_private_session())
        result = self.store.verify_and_record_attempt(
            staff_id, "wrong", self.pin_hashes[staff_id], now=100
        )
        self.assertFalse(result["verified"])
        self.assertEqual(self.session_record, locked_private_session())


if __name__ == "__main__":
    unittest.main()
