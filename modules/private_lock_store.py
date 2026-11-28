"""SQLite persistence contract for Private Lock attempt state.

This adapter is opt-in and isolated. It never opens a database itself: callers
must inject a trusted server-side connection factory. No table is created on
import or construction. The caller must invoke initialize_schema() explicitly
against an approved non-production database.

This module does not authenticate users, verify PINs, authorize access, or
provide encryption for private content.
"""

import sqlite3
import time

from modules.private_lock import (
    DEFAULT_LOCKOUT_SECONDS,
    DEFAULT_MAX_ATTEMPTS,
    PrivateLockError,
    _calculate_lockout_deadline,
    _validate_timestamp,
    verify_pin,
)


class PrivateLockStoreError(RuntimeError):
    """Raised when the persistence adapter cannot safely perform an operation."""


def _validate_user_id(user_id):
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise PrivateLockError("A positive Phase 1 integer user ID is required.")
    return user_id


def _state_from_row(row):
    if row is None:
        return 0, 0.0
    failures, locked_until = row
    if isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
        raise PrivateLockStoreError("Stored PIN attempt counter is invalid.")
    try:
        locked_until = _validate_timestamp(locked_until)
    except PrivateLockError as exc:
        raise PrivateLockStoreError("Stored PIN lockout deadline is invalid.") from exc
    return failures, locked_until


class SqlitePrivateLockAttemptStore:
    """Persist failed-attempt state using SQLite write transactions.

    connection_factory must return a new sqlite3.Connection to a trusted
    server-side database. Do not pass a browser-provided or user-controlled
    database path. Each write uses BEGIN IMMEDIATE so concurrent writers
    serialize before reading/updating a user's counter.
    """

    def __init__(self, connection_factory):
        if not callable(connection_factory):
            raise PrivateLockStoreError("A trusted connection factory is required.")
        self._connection_factory = connection_factory

    def initialize_schema(self):
        """Create the isolated attempt-state table when explicitly requested."""
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS private_lock_attempts (
                    user_id INTEGER PRIMARY KEY CHECK (user_id > 0),
                    failed_attempts INTEGER NOT NULL DEFAULT 0
                        CHECK (failed_attempts >= 0),
                    locked_until REAL NOT NULL DEFAULT 0
                        CHECK (locked_until >= 0)
                )
                """
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_state(self, user_id):
        """Return persisted state; absent rows are treated as a fresh state."""
        user_id = _validate_user_id(user_id)
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT failed_attempts, locked_until "
                "FROM private_lock_attempts WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            failures, locked_until = _state_from_row(row)
            return {"failed_attempts": failures, "locked_until": locked_until}
        finally:
            connection.close()

    def record_attempt(
        self,
        user_id,
        *,
        success,
        now=None,
        max_attempts=DEFAULT_MAX_ATTEMPTS,
        lockout_seconds=DEFAULT_LOCKOUT_SECONDS,
    ):
        """Atomically record one already-verified PIN attempt.

        The caller must perform PIN verification before calling this method.
        now is intended only for deterministic tests; production callers must
        omit it so the server clock is used. Never pass client timestamps.
        """
        user_id = _validate_user_id(user_id)
        if not isinstance(success, bool):
            raise PrivateLockError("success must be boolean.")
        if (
            isinstance(max_attempts, bool)
            or not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise PrivateLockError("max_attempts must be a positive integer.")
        if (
            isinstance(lockout_seconds, bool)
            or not isinstance(lockout_seconds, int)
            or lockout_seconds < 1
        ):
            raise PrivateLockError("lockout_seconds must be a positive integer.")
        current = time.time() if now is None else _validate_timestamp(now)

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT failed_attempts, locked_until "
                "FROM private_lock_attempts WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            failures, locked_until = _state_from_row(row)

            if current < locked_until:
                next_failures, next_locked_until = failures, locked_until
            elif success:
                next_failures, next_locked_until = 0, 0.0
            else:
                next_failures = failures + 1
                next_locked_until = (
                    _calculate_lockout_deadline(current, lockout_seconds)
                    if next_failures >= max_attempts
                    else 0.0
                )

            connection.execute(
                """
                INSERT INTO private_lock_attempts
                    (user_id, failed_attempts, locked_until)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    failed_attempts = excluded.failed_attempts,
                    locked_until = excluded.locked_until
                """,
                (user_id, next_failures, next_locked_until),
            )
            connection.commit()
            return {
                "failed_attempts": next_failures,
                "locked_until": next_locked_until,
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def verify_and_record_attempt(
        self,
        user_id,
        pin,
        encoded_hash,
        *,
        now=None,
        max_attempts=DEFAULT_MAX_ATTEMPTS,
        lockout_seconds=DEFAULT_LOCKOUT_SECONDS,
    ):
        """Atomically enforce lockout, verify a PIN, and persist its outcome.

        encoded_hash must be fetched by trusted server code for this user.
        PIN verification runs while holding SQLite's write reservation so
        parallel attempts cannot all pass a stale pre-check. Neither the PIN
        nor its hash is persisted by this method. Never call with client-chosen
        user IDs, hashes, timestamps, or database connections.
        """
        user_id = _validate_user_id(user_id)
        if (
            isinstance(max_attempts, bool)
            or not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise PrivateLockError("max_attempts must be a positive integer.")
        if (
            isinstance(lockout_seconds, bool)
            or not isinstance(lockout_seconds, int)
            or lockout_seconds < 1
        ):
            raise PrivateLockError("lockout_seconds must be a positive integer.")
        current = time.time() if now is None else _validate_timestamp(now)

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT failed_attempts, locked_until "
                "FROM private_lock_attempts WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            failures, locked_until = _state_from_row(row)

            if current < locked_until:
                result = {
                    "verified": False,
                    "locked": True,
                    "failed_attempts": failures,
                    "locked_until": locked_until,
                }
            else:
                verified = verify_pin(pin, encoded_hash)
                if verified:
                    failures, locked_until = 0, 0.0
                else:
                    failures += 1
                    locked_until = (
                        _calculate_lockout_deadline(current, lockout_seconds)
                        if failures >= max_attempts
                        else 0.0
                    )
                connection.execute(
                    """
                    INSERT INTO private_lock_attempts
                        (user_id, failed_attempts, locked_until)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        failed_attempts = excluded.failed_attempts,
                        locked_until = excluded.locked_until
                    """,
                    (user_id, failures, locked_until),
                )
                result = {
                    "verified": verified,
                    "locked": current < locked_until,
                    "failed_attempts": failures,
                    "locked_until": locked_until,
                }
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _connect(self):
        try:
            connection = self._connection_factory()
        except Exception as exc:
            raise PrivateLockStoreError("Could not open trusted lock-state storage.") from exc
        if not isinstance(connection, sqlite3.Connection):
            raise PrivateLockStoreError("Connection factory must return sqlite3.Connection.")
        return connection
